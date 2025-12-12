# Security Implementation Documentation

## Overview

This document explains all security measures implemented in the Warranty Register deployment.

## 1. SSH Security

### Authentication
- **Root login disabled**: `PermitRootLogin no`
````markdown
# Security Implementation Documentation

## Overview

This document explains all security measures implemented in the Warranty Register deployment.

## 1. SSH Security

### Authentication
- **Root login disabled**: `PermitRootLogin no`
- **Password authentication disabled**: `PasswordAuthentication no`
- **Only public key authentication allowed**: `PubkeyAuthentication yes`
- **Strong key exchange algorithms**: curve25519-sha256, diffie-hellman-group16/18

### Explicit SSH key usage
Use the identity file when connecting to the server to ensure the correct private key is used and avoid authentication failures. Example:

```bash
ssh -i ~/.ssh/id_ed25519 user@server
```

Advantages:
- **Deterministic authentication:** Forces use of the specified private key, preventing `Too many authentication failures` when the SSH agent offers multiple keys.
- **Stronger key type:** ED25519 (used above) is recommended for better security and smaller keys compared with older RSA keys.
- **Avoids password auth:** Keeps connections key-based, removing risks from password-based logins.
- **Simple for scripts:** Explicit `-i` makes automated deploys and rsync commands predictable.

### Access Control
- **AllowUsers directive**: Only specified users can SSH
- **MaxAuthTries = 3**: Limits brute force attempts
- **LoginGraceTime = 60**: Reduces connection hanging

### Why These Measures?
- Password authentication is vulnerable to brute force attacks
- Key-based authentication is cryptographically stronger
- Disabling root login prevents privilege escalation attacks

## 2. Firewall (UFW)

### Allowed Ports
- **22/tcp**: SSH access
- **80/tcp**: HTTP (redirects to HTTPS)
- **443/tcp**: HTTPS

### Default Policy
- **Incoming**: DENY ALL
- **Outgoing**: ALLOW ALL

### Why?
- Minimizes attack surface by only exposing necessary ports
- PostgreSQL (5432) is not exposed externally
- All internal communication happens over Docker network

## 3. Fail2Ban

### Configuration
- **Ban time**: 1 hour
- **Max retries**: 3
- **Find time**: 10 minutes

### Protected Services
- SSH (sshd filter)
- Nginx HTTP auth
- Nginx rate limiting

### Why?
- Automatically blocks IPs after failed login attempts
- Prevents brute force attacks
- Logs all suspicious activity

## 4. API Security

### JWT Authentication
- **Algorithm**: HS256
- **Token expiry**: 30 minutes
- **Secure secret key**: 64+ character random string

### API Key Authentication
- For service-to-service communication (Next.js → API)
- Stored in environment variables
- Never exposed in client-side code

### Rate Limiting (Nginx)
- **Rate**: 10 requests/second per IP
- **Burst**: 20 requests allowed
- Prevents DDoS and abuse

### Why?
- JWT provides stateless authentication
- API keys allow secure backend communication
- Rate limiting prevents resource exhaustion

## 5. HTTPS/SSL

### Configuration
- **TLS versions**: 1.2, 1.3 only
- **Strong ciphers**: ECDHE with AES-GCM
- **HSTS enabled**: 1 year max-age

### Let's Encrypt
- Auto-renewal every 12 hours (certbot check)
- Free, trusted certificates

### Security Headers
```
X-Frame-Options: SAMEORIGIN
X-Content-Type-Options: nosniff
X-XSS-Protection: 1; mode=block
Content-Security-Policy: default-src 'self'
Strict-Transport-Security: max-age=31536000
Referrer-Policy: strict-origin-when-cross-origin
```

### Why?
- Encrypts all traffic in transit
- Security headers prevent common attacks (XSS, clickjacking)
- HSTS ensures browsers always use HTTPS

## 6. Docker Security

### Non-root User
- API container runs as non-root `appuser`
- Reduces container escape impact

### Network Isolation
- Custom Docker network (`warranty-network`)
- Services communicate internally only
- Only Nginx exposed to internet

### Why?
- Principle of least privilege
- Container compromise has limited impact
- Network segmentation

## 7. PostgreSQL Security

### Authentication
- Password encryption: scram-sha-256
- Connection from Docker network only
- No external port exposure in production

### Why?
- SCRAM is more secure than MD5
- Database never directly accessible from internet

## 8. Additional Hardening

### Automatic Security Updates
- `unattended-upgrades` enabled
- Security patches applied automatically

### Kernel Hardening
- IP spoofing protection
- ICMP redirect disabled
- Source routing disabled
- TCP SYN cookies enabled
- Martian packet logging

### Filesystem Security
- Secure shared memory (noexec, nosuid)
- Proper file permissions

### Why?
- Reduces manual maintenance burden
- Hardens against network-level attacks
- Defense in depth approach

## 9. Logging and Monitoring

### SSH Logging
- All connections logged
- Failed attempts logged

### Nginx Logging
- Access logs with timing info
- Error logs for troubleshooting

### PostgreSQL Logging
- Slow queries (>1 second)
- Connection/disconnection events

### Why?
- Audit trail for security incidents
- Performance monitoring
- Compliance requirements



## Security Changes

- **HTTPS / TLS:** Installed Let's Encrypt certs and configured Nginx to serve TLS. Reason: encrypt traffic and protect credentials/API keys in transit. Files: `certbot/conf` & `nginx/conf.d/warranty.conf`.
- **HSTS:** Added `Strict-Transport-Security` header. Reason: enforce browsers use HTTPS (reduces downgrade attacks).
- **Content Security Policy:** Added `Content-Security-Policy` allowing `https://cdn.tailwindcss.com` and restricting other sources. Reason: mitigate XSS by limiting where scripts/styles can load. File: `nginx/conf.d/warranty.conf`.
- **Common security headers:** Added `X-Frame-Options: SAMEORIGIN`, `X-Content-Type-Options: nosniff`, `X-XSS-Protection`, and `Referrer-Policy`. Reason: protect against clickjacking, MIME sniffing, basic XSS, and reduce referrer leakage. File: `nginx/conf.d/warranty.conf`.
- **Strong DH params:** Generated `ssl-dhparams.pem` and included it in TLS config. Reason: improve key-exchange strength and forward secrecy. File: `certbot/conf/ssl-dhparams.pem`.
- **Recommended TLS options:** Included `options-ssl-nginx.conf` (from Certbot). Reason: use recommended protocols/ciphers and best-practice TLS defaults. File: `certbot/conf/options-ssl-nginx.conf`.
- **HTTP→HTTPS redirect + ACME handling:** HTTP vhost redirects, `.well-known/acme-challenge/` served from `/var/www/certbot`. Reason: ensure secure default and allow automatic Certbot renewals. File: `nginx/conf.d/warranty.conf`.
- **Rate / connection limits:** Added `limit_req` and `limit_conn` directives. Reason: basic mitigation against abusive or volumetric requests. File: `nginx/conf.d/warranty.conf`.
- **Proxy hardening:** Set `proxy_*` timeouts and forwarded `X-Forwarded-*` headers. Reason: preserve real client IPs for logging and avoid slow/half-open connections. File: `nginx/conf.d/warranty.conf`.
- **Safe cert sync process:** Avoided overwriting `certbot/` directly with rsync (permission/root-owned). Reason: prevent accidental broken permissions that would break renewals; when needed we rsync to `/tmp` then `sudo rsync` to preserve ownership.
- **Operational safety:** Backed up edited files and used `nginx -t` before reload. Example check: `docker compose exec nginx nginx -t`. Reason: prevent downtime from bad config and enable quick rollback.

````

## 10. Best Practices Summary

1. **Defense in Depth**: Multiple security layers
2. **Principle of Least Privilege**: Minimum necessary access
3. **Fail Secure**: Default deny policies
4. **Keep Updated**: Automatic security updates
5. **Encryption Everywhere**: TLS for all traffic
6. **Logging**: Comprehensive audit trails