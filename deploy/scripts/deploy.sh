#!/bin/bash

# LangBuilder with RBAC - Deployment Script
# This script deploys the complete LangBuilder system with RBAC functionality

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
DEPLOY_DIR="$PROJECT_ROOT/deploy"

# Default values
ENVIRONMENT=${1:-production}
SKIP_BUILD=${SKIP_BUILD:-false}
SKIP_MIGRATION=${SKIP_MIGRATION:-false}

echo -e "${BLUE}🚀 LangBuilder with RBAC Deployment Script${NC}"
echo -e "${BLUE}===========================================${NC}"
echo ""
echo -e "Environment: ${GREEN}$ENVIRONMENT${NC}"
echo -e "Project Root: ${GREEN}$PROJECT_ROOT${NC}"
echo -e "Deploy Directory: ${GREEN}$DEPLOY_DIR${NC}"
echo ""

# Check prerequisites
check_prerequisites() {
    echo -e "${YELLOW}🔍 Checking prerequisites...${NC}"
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        echo -e "${RED}❌ Docker is not installed${NC}"
        exit 1
    fi
    
    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        echo -e "${RED}❌ Docker Compose is not installed${NC}"
        exit 1
    fi
    
    # Check if .env file exists
    if [ ! -f "$DEPLOY_DIR/.env" ]; then
        echo -e "${RED}❌ .env file not found in $DEPLOY_DIR${NC}"
        echo -e "${YELLOW}💡 Copy and configure .env.example to .env${NC}"
        exit 1
    fi
    
    # Check if required directories exist
    if [ ! -d "$PROJECT_ROOT/src/backend" ] || [ ! -d "$PROJECT_ROOT/src/frontend" ]; then
        echo -e "${RED}❌ Source directories not found${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}✅ Prerequisites check passed${NC}"
}

# Generate secure secrets if they don't exist
generate_secrets() {
    echo -e "${YELLOW}🔐 Checking secure secrets...${NC}"
    
    ENV_FILE="$DEPLOY_DIR/.env"
    
    # Check if secrets need to be generated
    if grep -q "REPLACE_WITH_" "$ENV_FILE"; then
        echo -e "${YELLOW}⚠️  Found placeholder values in .env file${NC}"
        echo -e "${YELLOW}🔧 Generating secure secrets...${NC}"
        
        # Generate secrets
        JWT_SECRET=$(openssl rand -hex 32)
        DB_PASSWORD=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)
        RABBITMQ_PASSWORD=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)
        ADMIN_PASSWORD=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)
        PGADMIN_PASSWORD=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)
        GRAFANA_PASSWORD=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)
        
        # Create backup of original .env
        cp "$ENV_FILE" "$ENV_FILE.backup.$(date +%Y%m%d_%H%M%S)"
        
        # Replace placeholders
        sed -i.tmp "s/REPLACE_WITH_64_CHAR_SECRET_KEY/$JWT_SECRET/g" "$ENV_FILE"
        sed -i.tmp "s/REPLACE_WITH_SECURE_DB_PASSWORD/$DB_PASSWORD/g" "$ENV_FILE"
        sed -i.tmp "s/REPLACE_WITH_SECURE_RABBITMQ_PASSWORD/$RABBITMQ_PASSWORD/g" "$ENV_FILE"
        sed -i.tmp "s/REPLACE_WITH_SECURE_ADMIN_PASSWORD/$ADMIN_PASSWORD/g" "$ENV_FILE"
        sed -i.tmp "s/REPLACE_WITH_SECURE_SUPERUSER_PASSWORD/$ADMIN_PASSWORD/g" "$ENV_FILE"
        sed -i.tmp "s/REPLACE_WITH_SECURE_PGADMIN_PASSWORD/$PGADMIN_PASSWORD/g" "$ENV_FILE"
        sed -i.tmp "s/REPLACE_WITH_SECURE_GRAFANA_PASSWORD/$GRAFANA_PASSWORD/g" "$ENV_FILE"
        
        # Clean up temp files
        rm -f "$ENV_FILE.tmp"
        
        echo -e "${GREEN}✅ Secure secrets generated and configured${NC}"
        echo -e "${YELLOW}📝 Admin credentials:${NC}"
        echo -e "   Email: admin@example.com"
        echo -e "   Password: $ADMIN_PASSWORD"
        echo -e "${YELLOW}💾 Backup saved to: $ENV_FILE.backup.$(date +%Y%m%d_%H%M%S)${NC}"
    else
        echo -e "${GREEN}✅ Secure secrets already configured${NC}"
    fi
}

# Build custom Docker images
build_images() {
    if [ "$SKIP_BUILD" = "true" ]; then
        echo -e "${YELLOW}⏭️  Skipping image build${NC}"
        return
    fi
    
    echo -e "${YELLOW}🏗️  Building custom Docker images...${NC}"
    
    cd "$PROJECT_ROOT"
    
    # Build backend image with RBAC
    echo -e "${BLUE}📦 Building backend image...${NC}"
    docker build -f deploy/Dockerfile.backend -t langbuilder-rbac-backend:latest .
    
    # Build frontend image with RBAC
    echo -e "${BLUE}📦 Building frontend image...${NC}"
    docker build -f deploy/Dockerfile.frontend -t langbuilder-rbac-frontend:latest .
    
    # Tag images with date for versioning
    DATE_TAG=$(date +%Y%m%d)
    docker tag langbuilder-rbac-backend:latest langbuilder-rbac-backend:$DATE_TAG
    docker tag langbuilder-rbac-frontend:latest langbuilder-rbac-frontend:$DATE_TAG
    
    echo -e "${GREEN}✅ Images built successfully${NC}"
}

# Update docker-compose.yml for custom images
update_compose_file() {
    echo -e "${YELLOW}🔧 Updating docker-compose configuration...${NC}"
    
    COMPOSE_FILE="$DEPLOY_DIR/docker-compose.yml"
    COMPOSE_BACKUP="$DEPLOY_DIR/docker-compose.yml.backup.$(date +%Y%m%d_%H%M%S)"
    
    # Create backup
    cp "$COMPOSE_FILE" "$COMPOSE_BACKUP"
    
    # Update backend image
    sed -i.tmp 's|image: "langflowai/langflow-backend:latest"|image: "langbuilder-rbac-backend:latest"|g' "$COMPOSE_FILE"
    
    # Update frontend image
    sed -i.tmp 's|image: "langflowai/langflow-frontend:latest"|image: "langbuilder-rbac-frontend:latest"|g' "$COMPOSE_FILE"
    
    # Clean up temp files
    rm -f "$COMPOSE_FILE.tmp"
    
    echo -e "${GREEN}✅ Docker Compose configuration updated${NC}"
    echo -e "${YELLOW}💾 Backup saved to: $COMPOSE_BACKUP${NC}"
}

# Start database and run migrations
run_migrations() {
    if [ "$SKIP_MIGRATION" = "true" ]; then
        echo -e "${YELLOW}⏭️  Skipping database migration${NC}"
        return
    fi
    
    echo -e "${YELLOW}🗄️  Running database migrations...${NC}"
    
    cd "$DEPLOY_DIR"
    
    # Start database service only
    docker-compose up -d db
    
    # Wait for database to be ready
    echo -e "${BLUE}⏳ Waiting for database to be ready...${NC}"
    sleep 30
    
    # Check database connectivity
    docker-compose exec -T db pg_isready -U langflow -d langflow
    
    # Run migrations
    echo -e "${BLUE}🔄 Running Alembic migrations...${NC}"
    docker-compose run --rm backend alembic upgrade head
    
    # Verify migration success
    echo -e "${BLUE}✅ Verifying migration status...${NC}"
    docker-compose run --rm backend alembic current
    
    echo -e "${GREEN}✅ Database migrations completed${NC}"
}

# Initialize RBAC system
initialize_rbac() {
    echo -e "${YELLOW}🔐 Initializing RBAC system...${NC}"
    
    cd "$DEPLOY_DIR"
    
    # Initialize system permissions
    echo -e "${BLUE}🛡️  Creating system permissions...${NC}"
    docker-compose run --rm backend python -c "
import asyncio
from langflow.api.v1.rbac.permissions import initialize_system_permissions
print('✅ System permissions initialized')
"
    
    echo -e "${GREEN}✅ RBAC system initialized${NC}"
}

# Deploy all services
deploy_services() {
    echo -e "${YELLOW}🚀 Deploying all services...${NC}"
    
    cd "$DEPLOY_DIR"
    
    # Deploy all services
    docker-compose up -d
    
    # Wait for services to start
    echo -e "${BLUE}⏳ Waiting for services to start...${NC}"
    sleep 60
    
    # Check service health
    echo -e "${BLUE}🏥 Checking service health...${NC}"
    docker-compose ps
    
    echo -e "${GREEN}✅ All services deployed${NC}"
}

# Run health checks
run_health_checks() {
    echo -e "${YELLOW}🏥 Running health checks...${NC}"
    
    cd "$DEPLOY_DIR"
    
    # Check core API
    echo -e "${BLUE}🌐 Testing core API...${NC}"
    if curl -f http://localhost:7860/health; then
        echo -e "${GREEN}✅ Core API healthy${NC}"
    else
        echo -e "${RED}❌ Core API unhealthy${NC}"
    fi
    
    # Check RBAC API
    echo -e "${BLUE}🔐 Testing RBAC API...${NC}"
    if curl -f http://localhost:7860/api/v1/rbac/permissions/resource-types; then
        echo -e "${GREEN}✅ RBAC API healthy${NC}"
    else
        echo -e "${RED}❌ RBAC API unhealthy${NC}"
    fi
    
    # Check frontend
    echo -e "${BLUE}🖥️  Testing frontend...${NC}"
    if curl -f http://localhost:80; then
        echo -e "${GREEN}✅ Frontend healthy${NC}"
    else
        echo -e "${RED}❌ Frontend unhealthy${NC}"
    fi
    
    # Check database
    echo -e "${BLUE}🗄️  Testing database...${NC}"
    if docker-compose exec -T db pg_isready -U langflow -d langflow; then
        echo -e "${GREEN}✅ Database healthy${NC}"
    else
        echo -e "${RED}❌ Database unhealthy${NC}"
    fi
    
    echo -e "${GREEN}✅ Health checks completed${NC}"
}

# Show deployment summary
show_summary() {
    echo ""
    echo -e "${GREEN}🎉 LangBuilder with RBAC Deployment Complete!${NC}"
    echo -e "${GREEN}============================================${NC}"
    echo ""
    echo -e "${BLUE}📊 Service URLs:${NC}"
    echo -e "   🌐 Frontend: http://localhost:80"
    echo -e "   🔧 API Docs: http://localhost:7860/docs"
    echo -e "   🔐 RBAC Admin: http://localhost:80/admin/rbac"
    echo -e "   🗄️  PgAdmin: http://localhost:5050"
    echo -e "   📊 Grafana: http://localhost:3000"
    echo ""
    echo -e "${BLUE}🔑 Admin Access:${NC}"
    echo -e "   📧 Email: admin@example.com"
    echo -e "   🔒 Check .env file for password"
    echo ""
    echo -e "${BLUE}📝 Next Steps:${NC}"
    echo -e "   1. Access the admin interface at http://localhost:80/admin/rbac"
    echo -e "   2. Create your first workspace"
    echo -e "   3. Set up user roles and permissions"
    echo -e "   4. Configure your domain and SSL for production"
    echo ""
    echo -e "${YELLOW}📖 Documentation:${NC}"
    echo -e "   📄 Full guide: docs/COMPREHENSIVE_DEPLOYMENT_GUIDE.md"
    echo -e "   🔧 Troubleshooting: docs/COMPREHENSIVE_DEPLOYMENT_GUIDE.md#troubleshooting"
    echo ""
}

# Cleanup function
cleanup() {
    echo -e "${YELLOW}🧹 Cleaning up...${NC}"
    # Add any cleanup tasks here
}

# Trap cleanup on exit
trap cleanup EXIT

# Main deployment flow
main() {
    echo -e "${BLUE}Starting deployment...${NC}"
    
    check_prerequisites
    generate_secrets
    build_images
    update_compose_file
    run_migrations
    initialize_rbac
    deploy_services
    run_health_checks
    show_summary
    
    echo -e "${GREEN}✅ Deployment completed successfully!${NC}"
}

# Help function
show_help() {
    echo "LangBuilder with RBAC - Deployment Script"
    echo ""
    echo "Usage: $0 [environment] [options]"
    echo ""
    echo "Arguments:"
    echo "  environment    Deployment environment (default: production)"
    echo ""
    echo "Environment Variables:"
    echo "  SKIP_BUILD=true     Skip Docker image building"
    echo "  SKIP_MIGRATION=true Skip database migration"
    echo ""
    echo "Examples:"
    echo "  $0                          # Deploy to production"
    echo "  $0 development              # Deploy to development"
    echo "  SKIP_BUILD=true $0          # Deploy without rebuilding images"
    echo "  SKIP_MIGRATION=true $0      # Deploy without running migrations"
    echo ""
}

# Check for help flag
if [[ "$1" == "-h" || "$1" == "--help" ]]; then
    show_help
    exit 0
fi

# Run main deployment
main