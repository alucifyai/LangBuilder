# LangBuilder with RBAC - Quick Start Deployment

## 🚀 5-Minute Deployment Guide

This quick start guide will get you running LangBuilder with full RBAC functionality in just a few steps.

### Prerequisites

- Docker & Docker Compose installed
- 8GB+ RAM, 20GB+ disk space
- Linux/macOS/Windows with WSL2

### Step 1: Clone and Configure

```bash
# Clone repository
git clone <repository-url> langbuilder-rbac
cd langbuilder-rbac

# Copy and configure environment
cp deploy/.env.example deploy/.env

# Generate secure secrets
openssl rand -hex 32  # Use for LANGFLOW_SECRET_KEY
openssl rand -base64 32  # Use for passwords
```

### Step 2: Update Environment File

Edit `deploy/.env` and replace these values:

```bash
# Required changes
DOMAIN=your-domain.com                    # Your domain
LANGFLOW_SECRET_KEY=<64-char-hex-key>     # From step 1
POSTGRES_PASSWORD=<secure-password>       # From step 1
RABBITMQ_DEFAULT_PASS=<secure-password>   # From step 1
RBAC_SUPER_USER_PASSWORD=<admin-password> # From step 1
```

### Step 3: Deploy with One Command

```bash
# Run automated deployment
./deploy/scripts/deploy.sh
```

This script will:
- ✅ Build custom Docker images with RBAC
- ✅ Run database migrations
- ✅ Initialize RBAC system
- ✅ Deploy all services
- ✅ Run health checks

### Step 4: Access Your System

After deployment completes:

- **Frontend**: http://localhost:80
- **RBAC Admin**: http://localhost:80/admin/rbac
- **API Docs**: http://localhost:7860/docs
- **Database Admin**: http://localhost:5050

### Step 5: Initial Setup

1. **Login** with admin credentials from your `.env` file
2. **Create your first workspace** in the RBAC admin interface
3. **Set up roles and permissions** for your team
4. **Start building flows** with proper access control

---

## 🏃‍♂️ Alternative: Manual Deployment

If you prefer manual control:

### 1. Build Images

```bash
# Backend with RBAC
docker build -f deploy/Dockerfile.backend -t langbuilder-rbac-backend:latest .

# Frontend with RBAC
docker build -f deploy/Dockerfile.frontend -t langbuilder-rbac-frontend:latest .
```

### 2. Update Docker Compose

```bash
# Replace default images with RBAC versions
sed -i 's/langflowai\/langflow-backend:latest/langbuilder-rbac-backend:latest/' deploy/docker-compose.yml
sed -i 's/langflowai\/langflow-frontend:latest/langbuilder-rbac-frontend:latest/' deploy/docker-compose.yml
```

### 3. Start Database and Migrate

```bash
cd deploy

# Start database
docker-compose up -d db

# Wait and run migrations
sleep 30
docker-compose run --rm backend alembic upgrade head
```

### 4. Deploy All Services

```bash
# Deploy complete system
docker-compose up -d

# Check status
docker-compose ps
```

---

## 🔧 Verification

Run the health check script:

```bash
./deploy/scripts/health-check.sh
```

Expected output:
```
🎉 All health checks passed!
✅ LangBuilder with RBAC is fully operational
```

---

## 🛠️ Troubleshooting

### Common Issues

**Services not starting:**
```bash
# Check logs
docker-compose logs backend
docker-compose logs frontend

# Restart services
docker-compose restart
```

**Database connection failed:**
```bash
# Check database status
docker-compose exec db pg_isready -U langflow

# Reset database (⚠️ DATA LOSS)
docker-compose down -v
docker-compose up -d db
```

**RBAC APIs not responding:**
```bash
# Test RBAC endpoint
curl http://localhost:7860/api/v1/rbac/permissions/resource-types

# Check backend logs for RBAC
docker-compose logs backend | grep -i rbac
```

### Get Help

- 📖 **Full Documentation**: `docs/COMPREHENSIVE_DEPLOYMENT_GUIDE.md`
- 🔍 **Health Checks**: `./deploy/scripts/health-check.sh --verbose`
- 💾 **Backup System**: `./deploy/scripts/backup.sh`

---

## 🎯 What You Get

### Core Features
- ✅ **Multi-tenant Workspaces** - Isolate teams and projects
- ✅ **Hierarchical Projects** - Organize workflows by project
- ✅ **Environment Management** - Dev/staging/prod environments
- ✅ **Granular Permissions** - 30+ permission types
- ✅ **Role-based Access** - Custom roles with inheritance
- ✅ **Service Accounts** - API access with scoped permissions
- ✅ **Audit Logging** - Complete compliance trail
- ✅ **User Groups** - Team management with SCIM support

### Performance
- ⚡ **Sub-100ms** permission checks
- 🚀 **5-minute TTL** permission caching
- 📊 **Optimized queries** with proper indexing
- 🔄 **Async processing** for all operations

### Security
- 🔐 **JWT authentication** with secure tokens
- 🛡️ **Permission-based UI** rendering
- 📝 **Comprehensive audit** logging
- 🔒 **IP restrictions** and time-based access
- 🚨 **Break-glass access** for emergencies

---

## 🚀 Production Deployment

For production deployment:

1. **Update Domain**: Set your actual domain in `.env`
2. **Enable SSL**: Configure Let's Encrypt or custom certificates
3. **Security**: Review firewall rules and security groups
4. **Monitoring**: Set up Grafana dashboards and alerts
5. **Backups**: Schedule automatic backups with retention

See `docs/COMPREHENSIVE_DEPLOYMENT_GUIDE.md` for detailed production configuration.

---

## 🎉 You're Ready!

Your LangBuilder system with enterprise-grade RBAC is now running. Start building secure, collaborative AI workflows with proper access control and audit trails.

**Next Steps:**
1. Explore the RBAC admin interface
2. Create workspaces for your teams
3. Set up projects and environments
4. Build your first access-controlled flow
5. Monitor usage through audit logs

**Need Help?** Check the comprehensive deployment guide for advanced configuration and troubleshooting.