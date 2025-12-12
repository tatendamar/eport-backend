# Warranty Register - Complete Deployment Guide

This project contains the complete solution for the ePort technical assessment, including:

1. **Ubuntu Server Setup** - User creation, SSH hardening, firewall configuration
2. **Python Warranty Register API** - FastAPI application with PostgreSQL
3. **Docker Deployment** - Containerized setup with Docker Compose
4. **Nginx Reverse Proxy** - HTTPS with Let's Encrypt SSL
5. **Next.js Integration** - Warranty registration from the Asset Manager app



````markdown
# Warranty Register - Complete Deployment Guide

Public URLs
-----------

- Frontend (Next.js) hosted on Vercel: https://eport-web-app.vercel.app/
   - To create an admin account, first visit: https://eport-web-app.vercel.app/admin-signup
      - Sign up with an email address and follow the frontend flow to add assets and register warranties.
      - After creating the initial admin account, that admin should invite user from the admin dashboard.
- Backend (Warranty API): https://server10.eport.ws/
   - Use the backend to view and edit warranties (requires signing in as admin)

Default credentials (for quick local testing)
-----------------------------------------
- Email: admin@warranty.local
- Password: Admin@123


```
1. **Ubuntu Server Setup** - User creation, SSH hardening, firewall configuration
2. **Python Warranty Register API** - FastAPI application with PostgreSQL
3. **Docker Deployment** - Containerized setup with Docker Compose

```

## 🚀 Quick Start

### Prerequisites

- Ubuntu 24.04 Server with root access
- Domain name pointing to your server (e.g., server50.eport.ws)
- SSH key pair generated on your local machine

### Step 1: Initial Server Setup

1. SSH into your server as root or your deploy user (example using your SSH key):
   ```bash
   # As root (if needed)
   ssh root@your-server-ip

   # As your deploy user using your private key (replace placeholders):
   ssh -i ~/.ssh/<your_private_key> <your_user>@<your_server_domain>

   # When connecting as the `eport` user, use the same private key (replace placeholders):
   ssh -i ~/.ssh/<your_private_key> eport@<your_server_domain>
   ```

### Step 2: Deploy the Application

1. Clone/upload the project files to your server:
   ```bash
   git clone https://github.com/your-repo/eport-fast.git /opt/warranty-register
   # OR upload files via SCP
   ```

2. Run the deployment script:
   ```bash
   cd /opt/warranty-register
   chmod +x scripts/deploy-app.sh
   sudo bash scripts/deploy-app.sh server50.eport.ws
   ```

3. The script will:
   - Generate secure credentials
   - Build and start Docker containers
   - Obtain SSL certificate from Let's Encrypt
   - Configure Nginx reverse proxy

### Step 3: Verify Deployment

```bash
# Check health endpoint
curl https://server50.eport.ws/health

# View API documentation
# Open: https://server50.eport.ws/docs
```

## 🧭 Running Locally

You can run the services locally for development and testing.

Option A — Docker Compose (recommended):

```bash
# from the project root
docker compose build
docker compose up -d

# API will be available at http://localhost:8000
# Frontend (if running locally) typically at http://localhost:3000
```

Option B — Run FastAPI directly (developer mode):

```bash
# create venv and install
python3 -m venv .venv
source .venv/bin/activate
pip install -r warranty-api/requirements.txt

# run the API (reload enabled)
uvicorn warranty_api.app.main:app --host 0.0.0.0 --port 8000 --reload
```

Option C — Run Next.js frontend locally (if you have the frontend repo):

```bash
cd /path/to/eport-web
npm install
npm run dev

# Open http://localhost:3000 and visit /admin-signup to create an admin
```

When testing locally, sign up via the frontend at `/admin-signup` and then use the backend at `http://localhost:8000` (or the mapped host) to view and edit warranties.


## 🗄️ PostgreSQL Optimization
## 🗄️ PostgreSQL Optimization & ## 🔐 Security Implementation

PostgreSQL tuning details and rationale have moved to a dedicated document: [docs/POSTGRESQL_OPTIMIZATION.md](docs/POSTGRESQL_OPTIMIZATION.md). Please consult that file for recommended settings for various server sizes and maintenance advice.

Security and hardening guidance has its own documentation as well. See [docs/SECURITY.md](docs/SECURITY.md) (if present) or the Security section above for an overview.

## 📡 API Endpoints

### Authentication
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/auth/register` | POST | Register new user |
| `/api/v1/auth/login` | POST | User login |
| `/api/v1/auth/me` | GET | Get current user |
| `/api/v1/auth/create-admin` | POST | Create admin (admin only) |

### Warranty Management
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/warranties/register` | POST | Register warranty |
| `/api/v1/warranties/check/{asset_id}` | GET | Check warranty status |
| `/api/v1/warranties/` | GET | List all warranties |
| `/api/v1/warranties/{id}` | GET | Get warranty details |
| `/api/v1/warranties/{id}/status` | PUT | Update warranty status |


