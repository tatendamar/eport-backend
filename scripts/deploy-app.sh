#!/bin/bash
# =============================================================================
# Deploy Warranty Register Application
# =============================================================================
# This script deploys the Warranty Register app with Docker and configures SSL
#
# Run as: bash deploy-app.sh <domain-name>
# Example: bash deploy-app.sh server50.eport.ws
# =============================================================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

echo_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

echo_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check arguments
if [ -z "$1" ]; then
    echo_error "Please provide domain name"
    echo "Usage: $0 <domain-name>"
    echo "Example: $0 server50.eport.ws"
    exit 1
fi

DOMAIN_NAME="$1"
APP_DIR="/opt/warranty-register"
EMAIL="${2:-admin@${DOMAIN_NAME}}"

echo "=============================================="
echo "  Deploying Warranty Register Application"
echo "=============================================="
echo ""
echo_info "Domain: ${DOMAIN_NAME}"
echo_info "App Directory: ${APP_DIR}"
echo ""

# =============================================================================
# STEP 1: Create Application Directory
# =============================================================================
echo_info "Creating application directory..."
mkdir -p "${APP_DIR}"
cd "${APP_DIR}"

# =============================================================================
# STEP 2: Generate Secure Credentials
# =============================================================================
echo_info "Generating secure credentials..."

# Generate random passwords
DB_PASSWORD=$(openssl rand -base64 32 | tr -dc 'a-zA-Z0-9' | head -c 32)
SECRET_KEY=$(openssl rand -base64 48 | tr -dc 'a-zA-Z0-9' | head -c 64)
API_KEY=$(openssl rand -base64 32 | tr -dc 'a-zA-Z0-9' | head -c 32)

# Create .env file
cat > .env << EOF
# Database
POSTGRES_USER=warranty_user
POSTGRES_PASSWORD=${DB_PASSWORD}
POSTGRES_DB=warranty_db

# API
SECRET_KEY=${SECRET_KEY}
API_KEY=${API_KEY}
ALLOWED_ORIGINS=https://${DOMAIN_NAME}
DEBUG=false

# Domain
DOMAIN_NAME=${DOMAIN_NAME}
EMAIL=${EMAIL}
EOF

echo_info "Credentials generated and saved to .env"
echo_warn "API Key: ${API_KEY} (save this for Next.js integration)"

# =============================================================================
# STEP 3: Copy Application Files
# =============================================================================
echo_info "Copying application files..."

# Assuming the files are in the current directory or a known location
# If running from the eport-fast directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
SOURCE_DIR="$(dirname "$SCRIPT_DIR")"

# Copy files
cp -r "${SOURCE_DIR}/warranty-api" "${APP_DIR}/" 2>/dev/null || echo_warn "warranty-api already exists or not found"
cp -r "${SOURCE_DIR}/postgres" "${APP_DIR}/" 2>/dev/null || echo_warn "postgres already exists or not found"
cp -r "${SOURCE_DIR}/nginx" "${APP_DIR}/" 2>/dev/null || echo_warn "nginx already exists or not found"
cp "${SOURCE_DIR}/docker-compose.yml" "${APP_DIR}/" 2>/dev/null || echo_warn "docker-compose.yml already exists or not found"

# Create certbot directories
mkdir -p "${APP_DIR}/certbot/conf"
mkdir -p "${APP_DIR}/certbot/www"

# =============================================================================
# STEP 4: Initial Deployment (HTTP only)
# =============================================================================
echo_info "Starting initial deployment (HTTP only)..."

# Stop any existing containers
docker compose down 2>/dev/null || true

# Build and start containers
docker compose up -d --build db api nginx

# Wait for services to be healthy
echo_info "Waiting for services to start..."
sleep 10

# Check if API is responding
if curl -s http://localhost:8000/health | grep -q "healthy"; then
    echo_info "API is healthy"
else
    echo_warn "API health check failed, waiting longer..."
    sleep 10
fi

# =============================================================================
# STEP 5: Obtain SSL Certificate
# =============================================================================
echo_info "Obtaining SSL certificate from Let's Encrypt..."

# Stop nginx temporarily
docker compose stop nginx

# Download recommended TLS parameters
if [ ! -f "${APP_DIR}/certbot/conf/options-ssl-nginx.conf" ]; then
    curl -s https://raw.githubusercontent.com/certbot/certbot/master/certbot-nginx/certbot_nginx/_internal/tls_configs/options-ssl-nginx.conf > "${APP_DIR}/certbot/conf/options-ssl-nginx.conf"
fi

if [ ! -f "${APP_DIR}/certbot/conf/ssl-dhparams.pem" ]; then
    curl -s https://raw.githubusercontent.com/certbot/certbot/master/certbot/certbot/ssl-dhparams.pem > "${APP_DIR}/certbot/conf/ssl-dhparams.pem"
fi

# Create dummy certificate for initial nginx start
echo_info "Creating dummy certificate for initial nginx start..."
mkdir -p "${APP_DIR}/certbot/conf/live/${DOMAIN_NAME}"
openssl req -x509 -nodes -newkey rsa:4096 -days 1 \
    -keyout "${APP_DIR}/certbot/conf/live/${DOMAIN_NAME}/privkey.pem" \
    -out "${APP_DIR}/certbot/conf/live/${DOMAIN_NAME}/fullchain.pem" \
    -subj "/CN=localhost"

# Update nginx config to use the domain
cat > "${APP_DIR}/nginx/conf.d/warranty.conf" << EOF
# HTTP Server - Redirect to HTTPS and handle ACME challenges
server {
    listen 80;
    listen [::]:80;
    server_name ${DOMAIN_NAME};

    # ACME challenge for Let's Encrypt
    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }

    # Redirect all other traffic to HTTPS
    location / {
        return 301 https://\$host\$request_uri;
    }
}

# HTTPS Server - Main configuration
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name ${DOMAIN_NAME};

    # SSL certificates (managed by Certbot)
    ssl_certificate /etc/letsencrypt/live/${DOMAIN_NAME}/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/${DOMAIN_NAME}/privkey.pem;
    
    # SSL configuration
    include /etc/letsencrypt/options-ssl-nginx.conf;
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data:;" always;
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

    # Rate limiting
    limit_req zone=api_limit burst=20 nodelay;
    limit_conn conn_limit 10;

    # API proxy
    location / {
        proxy_pass http://warranty_api;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_cache_bypass \$http_upgrade;
        proxy_read_timeout 90s;
        proxy_connect_timeout 90s;
        proxy_send_timeout 90s;
    }

    # Health check endpoint (no rate limit)
    location /health {
        limit_req off;
        proxy_pass http://warranty_api/health;
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF

# Remove default config
rm -f "${APP_DIR}/nginx/conf.d/default.conf"

# Start nginx with dummy certificate
docker compose start nginx

# Wait for nginx
sleep 5

# Obtain real certificate
echo_info "Requesting Let's Encrypt certificate..."
docker run --rm \
    -v "${APP_DIR}/certbot/conf:/etc/letsencrypt" \
    -v "${APP_DIR}/certbot/www:/var/www/certbot" \
    --network warranty-network \
    certbot/certbot certonly \
    --webroot \
    --webroot-path=/var/www/certbot \
    --email "${EMAIL}" \
    --agree-tos \
    --no-eff-email \
    -d "${DOMAIN_NAME}" \
    --force-renewal

# Reload nginx with real certificate
docker compose exec nginx nginx -s reload

echo_info "SSL certificate obtained successfully"

# =============================================================================
# STEP 6: Final Verification
# =============================================================================
echo_info "Verifying deployment..."

# Check HTTPS
if curl -sk "https://${DOMAIN_NAME}/health" | grep -q "healthy"; then
    echo_info "HTTPS is working correctly"
else
    echo_warn "HTTPS verification failed - please check manually"
fi

# =============================================================================
# Print Summary
# =============================================================================
echo ""
echo "=============================================="
echo "  Deployment Complete!"
echo "=============================================="
echo ""
echo_info "Application URL: https://${DOMAIN_NAME}"
echo_info "API Documentation: https://${DOMAIN_NAME}/docs"
echo ""
echo "Credentials:"
echo "============"
echo "Database User: warranty_user"
echo "Database Password: ${DB_PASSWORD}"
echo "API Key: ${API_KEY}"
echo "Secret Key: ${SECRET_KEY}"
echo ""
echo "Default Admin Login:"
echo "===================="
echo "Email: admin@warranty.local"
echo "Password: Admin@123"
echo ""
echo_warn "IMPORTANT: Change the default admin password after first login!"
echo_warn "Save the API Key for integration with Next.js app"
echo ""
echo "Useful commands:"
echo "================"
echo "View logs: docker compose logs -f"
echo "Restart services: docker compose restart"
echo "Stop services: docker compose down"
echo "Start services: docker compose up -d"
echo ""
