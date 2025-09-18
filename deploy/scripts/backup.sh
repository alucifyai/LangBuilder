#!/bin/bash

# LangBuilder with RBAC - Backup Script
# Comprehensive backup solution for the entire system

set -e

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

# Default backup configuration
BACKUP_DIR=${BACKUP_DIR:-"/backups/langbuilder-rbac"}
RETENTION_DAYS=${RETENTION_DAYS:-30}
COMPRESS=${COMPRESS:-true}
INCLUDE_IMAGES=${INCLUDE_IMAGES:-false}

# Generate timestamp
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_NAME="langbuilder_rbac_backup_$TIMESTAMP"

echo -e "${BLUE}💾 LangBuilder with RBAC - Backup Script${NC}"
echo -e "${BLUE}=======================================${NC}"
echo ""
echo -e "Backup Directory: ${GREEN}$BACKUP_DIR${NC}"
echo -e "Backup Name: ${GREEN}$BACKUP_NAME${NC}"
echo -e "Retention: ${GREEN}$RETENTION_DAYS days${NC}"
echo ""

# Create backup directory
create_backup_dir() {
    log_info "Creating backup directory..."
    
    mkdir -p "$BACKUP_DIR/$BACKUP_NAME"
    
    if [ $? -eq 0 ]; then
        log_success "Backup directory created: $BACKUP_DIR/$BACKUP_NAME"
    else
        log_error "Failed to create backup directory"
        exit 1
    fi
}

# Utility functions
log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Backup database
backup_database() {
    log_info "Backing up PostgreSQL database..."
    
    cd "$DEPLOY_DIR"
    
    # Create database dump
    if docker-compose exec -T db pg_dump -U langflow langflow > "$BACKUP_DIR/$BACKUP_NAME/database.sql"; then
        log_success "Database backup completed"
        
        # Get database size
        local db_size=$(du -h "$BACKUP_DIR/$BACKUP_NAME/database.sql" | cut -f1)
        log_info "Database backup size: $db_size"
        
        # Create compressed backup if enabled
        if [ "$COMPRESS" = "true" ]; then
            log_info "Compressing database backup..."
            gzip "$BACKUP_DIR/$BACKUP_NAME/database.sql"
            log_success "Database backup compressed"
        fi
    else
        log_error "Database backup failed"
        return 1
    fi
}

# Backup configuration files
backup_configuration() {
    log_info "Backing up configuration files..."
    
    # Create config backup directory
    mkdir -p "$BACKUP_DIR/$BACKUP_NAME/config"
    
    # Backup environment file
    if [ -f "$DEPLOY_DIR/.env" ]; then
        cp "$DEPLOY_DIR/.env" "$BACKUP_DIR/$BACKUP_NAME/config/env_$TIMESTAMP"
        log_success "Environment configuration backed up"
    else
        log_warning "Environment file not found"
    fi
    
    # Backup docker-compose file
    if [ -f "$DEPLOY_DIR/docker-compose.yml" ]; then
        cp "$DEPLOY_DIR/docker-compose.yml" "$BACKUP_DIR/$BACKUP_NAME/config/docker-compose_$TIMESTAMP.yml"
        log_success "Docker Compose configuration backed up"
    else
        log_warning "Docker Compose file not found"
    fi
    
    # Backup nginx configuration
    if [ -f "$DEPLOY_DIR/nginx-rbac.conf" ]; then
        cp "$DEPLOY_DIR/nginx-rbac.conf" "$BACKUP_DIR/$BACKUP_NAME/config/nginx-rbac_$TIMESTAMP.conf"
        log_success "Nginx RBAC configuration backed up"
    fi
    
    # Backup deployment scripts
    if [ -d "$DEPLOY_DIR/scripts" ]; then
        cp -r "$DEPLOY_DIR/scripts" "$BACKUP_DIR/$BACKUP_NAME/config/"
        log_success "Deployment scripts backed up"
    fi
    
    # Backup custom configurations
    if [ -d "$DEPLOY_DIR/custom" ]; then
        cp -r "$DEPLOY_DIR/custom" "$BACKUP_DIR/$BACKUP_NAME/config/"
        log_success "Custom configurations backed up"
    fi
}

# Backup volumes and data
backup_volumes() {
    log_info "Backing up Docker volumes..."
    
    cd "$DEPLOY_DIR"
    
    # Create volumes backup directory
    mkdir -p "$BACKUP_DIR/$BACKUP_NAME/volumes"
    
    # Get list of volumes
    local volumes=$(docker-compose config --volumes 2>/dev/null || echo "")
    
    if [ -n "$volumes" ]; then
        for volume in $volumes; do
            log_info "Backing up volume: $volume"
            
            # Create volume backup using docker
            if docker run --rm -v "${volume}:/source:ro" -v "$BACKUP_DIR/$BACKUP_NAME/volumes:/backup" alpine tar czf "/backup/${volume}_${TIMESTAMP}.tar.gz" -C /source .; then
                log_success "Volume $volume backed up"
            else
                log_warning "Failed to backup volume: $volume"
            fi
        done
    else
        log_info "No named volumes found"
    fi
}

# Backup Docker images
backup_images() {
    if [ "$INCLUDE_IMAGES" != "true" ]; then
        log_info "Skipping Docker image backup (INCLUDE_IMAGES=false)"
        return
    fi
    
    log_info "Backing up Docker images..."
    
    # Create images backup directory
    mkdir -p "$BACKUP_DIR/$BACKUP_NAME/images"
    
    # Backup custom RBAC images
    local images=("langbuilder-rbac-backend:latest" "langbuilder-rbac-frontend:latest")
    
    for image in "${images[@]}"; do
        if docker image inspect "$image" > /dev/null 2>&1; then
            log_info "Backing up image: $image"
            
            local image_file=$(echo "$image" | tr '/:' '_')
            if docker save "$image" | gzip > "$BACKUP_DIR/$BACKUP_NAME/images/${image_file}_${TIMESTAMP}.tar.gz"; then
                log_success "Image $image backed up"
            else
                log_warning "Failed to backup image: $image"
            fi
        else
            log_warning "Image not found: $image"
        fi
    done
}

# Backup application data
backup_application_data() {
    log_info "Backing up application data..."
    
    cd "$DEPLOY_DIR"
    
    # Create app data backup directory
    mkdir -p "$BACKUP_DIR/$BACKUP_NAME/app_data"
    
    # Backup RBAC specific data if it exists
    if docker-compose exec -T backend test -d /app/data/rbac 2>/dev/null; then
        log_info "Backing up RBAC application data..."
        docker-compose exec -T backend tar czf - -C /app/data rbac > "$BACKUP_DIR/$BACKUP_NAME/app_data/rbac_data_$TIMESTAMP.tar.gz"
        log_success "RBAC application data backed up"
    fi
    
    # Backup logs if accessible
    if docker-compose exec -T backend test -d /app/logs 2>/dev/null; then
        log_info "Backing up application logs..."
        docker-compose exec -T backend tar czf - -C /app logs > "$BACKUP_DIR/$BACKUP_NAME/app_data/logs_$TIMESTAMP.tar.gz"
        log_success "Application logs backed up"
    fi
}

# Create system info snapshot
create_system_info() {
    log_info "Creating system information snapshot..."
    
    # Create system info file
    cat > "$BACKUP_DIR/$BACKUP_NAME/system_info.txt" << EOF
LangBuilder with RBAC - System Information
==========================================

Backup Date: $(date)
Backup Script Version: 1.0
System: $(uname -a)
Docker Version: $(docker --version)
Docker Compose Version: $(docker-compose --version)

Service Status:
EOF
    
    cd "$DEPLOY_DIR"
    
    # Add service status
    echo "" >> "$BACKUP_DIR/$BACKUP_NAME/system_info.txt"
    docker-compose ps >> "$BACKUP_DIR/$BACKUP_NAME/system_info.txt" 2>/dev/null || echo "Could not retrieve service status" >> "$BACKUP_DIR/$BACKUP_NAME/system_info.txt"
    
    # Add environment info (sanitized)
    echo "" >> "$BACKUP_DIR/$BACKUP_NAME/system_info.txt"
    echo "Environment Configuration (sanitized):" >> "$BACKUP_DIR/$BACKUP_NAME/system_info.txt"
    if [ -f ".env" ]; then
        grep -E "^[A-Z_]+=.*$" .env | sed 's/=.*/=***/' >> "$BACKUP_DIR/$BACKUP_NAME/system_info.txt"
    fi
    
    log_success "System information snapshot created"
}

# Create backup manifest
create_manifest() {
    log_info "Creating backup manifest..."
    
    cat > "$BACKUP_DIR/$BACKUP_NAME/MANIFEST.txt" << EOF
LangBuilder with RBAC - Backup Manifest
=======================================

Backup ID: $BACKUP_NAME
Created: $(date)
Type: Full System Backup
Retention: $RETENTION_DAYS days

Contents:
- database.sql$([ "$COMPRESS" = "true" ] && echo ".gz" || echo "") : PostgreSQL database dump
- config/ : Configuration files and scripts
- volumes/ : Docker volume backups
$([ "$INCLUDE_IMAGES" = "true" ] && echo "- images/ : Docker image backups" || echo "- images/ : Skipped (INCLUDE_IMAGES=false)")
- app_data/ : Application-specific data
- system_info.txt : System information snapshot
- MANIFEST.txt : This manifest file

Restoration Instructions:
1. Stop all services: docker-compose down
2. Restore database: docker-compose exec -T db psql -U langflow langflow < database.sql
3. Restore configuration: Copy files from config/ to deploy/
4. Restore volumes: Extract volume backups to appropriate locations
5. Start services: docker-compose up -d

For detailed restoration instructions, see:
docs/COMPREHENSIVE_DEPLOYMENT_GUIDE.md#backup--restoration
EOF
    
    log_success "Backup manifest created"
}

# Compress entire backup
compress_backup() {
    if [ "$COMPRESS" != "true" ]; then
        log_info "Skipping backup compression"
        return
    fi
    
    log_info "Compressing entire backup..."
    
    cd "$BACKUP_DIR"
    
    if tar czf "${BACKUP_NAME}.tar.gz" "$BACKUP_NAME/"; then
        log_success "Backup compressed to ${BACKUP_NAME}.tar.gz"
        
        # Get compressed size
        local compressed_size=$(du -h "${BACKUP_NAME}.tar.gz" | cut -f1)
        log_info "Compressed backup size: $compressed_size"
        
        # Remove uncompressed directory
        rm -rf "$BACKUP_NAME/"
        log_info "Uncompressed backup directory removed"
    else
        log_error "Failed to compress backup"
        return 1
    fi
}

# Clean old backups
cleanup_old_backups() {
    log_info "Cleaning up old backups (older than $RETENTION_DAYS days)..."
    
    # Find and remove old backup files
    find "$BACKUP_DIR" -name "langbuilder_rbac_backup_*.tar.gz" -mtime +$RETENTION_DAYS -type f -delete 2>/dev/null || true
    find "$BACKUP_DIR" -name "langbuilder_rbac_backup_*" -mtime +$RETENTION_DAYS -type d -exec rm -rf {} + 2>/dev/null || true
    
    log_success "Old backups cleaned up"
    
    # Show remaining backups
    local backup_count=$(find "$BACKUP_DIR" -name "langbuilder_rbac_backup_*" | wc -l)
    log_info "Remaining backups: $backup_count"
}

# Validate backup
validate_backup() {
    log_info "Validating backup..."
    
    local backup_path
    if [ "$COMPRESS" = "true" ]; then
        backup_path="$BACKUP_DIR/${BACKUP_NAME}.tar.gz"
        
        # Test archive integrity
        if tar tzf "$backup_path" > /dev/null 2>&1; then
            log_success "Backup archive is valid"
        else
            log_error "Backup archive is corrupted"
            return 1
        fi
    else
        backup_path="$BACKUP_DIR/$BACKUP_NAME"
        
        # Check if manifest exists
        if [ -f "$backup_path/MANIFEST.txt" ]; then
            log_success "Backup directory structure is valid"
        else
            log_error "Backup directory structure is invalid"
            return 1
        fi
    fi
    
    # Get backup size
    local backup_size=$(du -h "$backup_path" | cut -f1)
    log_info "Total backup size: $backup_size"
    
    return 0
}

# Generate backup report
generate_report() {
    echo ""
    echo -e "${GREEN}📋 Backup Completion Report${NC}"
    echo "============================"
    echo ""
    echo -e "${BLUE}Backup Details:${NC}"
    echo -e "   📁 Name: $BACKUP_NAME"
    echo -e "   📍 Location: $BACKUP_DIR"
    echo -e "   🗓️  Created: $(date)"
    echo -e "   ⏱️  Retention: $RETENTION_DAYS days"
    echo ""
    
    if [ "$COMPRESS" = "true" ]; then
        local backup_file="$BACKUP_DIR/${BACKUP_NAME}.tar.gz"
        if [ -f "$backup_file" ]; then
            local size=$(du -h "$backup_file" | cut -f1)
            echo -e "${BLUE}Backup File:${NC}"
            echo -e "   📦 File: ${BACKUP_NAME}.tar.gz"
            echo -e "   💾 Size: $size"
        fi
    else
        local backup_dir="$BACKUP_DIR/$BACKUP_NAME"
        if [ -d "$backup_dir" ]; then
            local size=$(du -h "$backup_dir" | tail -1 | cut -f1)
            echo -e "${BLUE}Backup Directory:${NC}"
            echo -e "   📁 Directory: $BACKUP_NAME"
            echo -e "   💾 Size: $size"
        fi
    fi
    
    echo ""
    echo -e "${BLUE}Contents:${NC}"
    echo -e "   🗄️  Database dump"
    echo -e "   ⚙️  Configuration files"
    echo -e "   💽 Docker volumes"
    echo -e "   📊 System information"
    if [ "$INCLUDE_IMAGES" = "true" ]; then
        echo -e "   🐳 Docker images"
    fi
    
    echo ""
    echo -e "${GREEN}✅ Backup completed successfully!${NC}"
    echo ""
    echo -e "${YELLOW}📖 Restoration Guide:${NC}"
    echo -e "   See docs/COMPREHENSIVE_DEPLOYMENT_GUIDE.md#backup--restoration"
    echo ""
}

# Show help
show_help() {
    echo "LangBuilder with RBAC - Backup Script"
    echo ""
    echo "Usage: $0 [options]"
    echo ""
    echo "Options:"
    echo "  --backup-dir DIR      Set backup directory (default: /backups/langbuilder-rbac)"
    echo "  --retention-days N    Set backup retention in days (default: 30)"
    echo "  --no-compress         Skip compression"
    echo "  --include-images      Include Docker images in backup"
    echo "  -h, --help            Show this help message"
    echo ""
    echo "Environment Variables:"
    echo "  BACKUP_DIR            Override backup directory"
    echo "  RETENTION_DAYS        Override retention period"
    echo "  COMPRESS              Enable/disable compression (true/false)"
    echo "  INCLUDE_IMAGES        Include Docker images (true/false)"
    echo ""
    echo "Examples:"
    echo "  $0                                    # Standard backup"
    echo "  $0 --backup-dir /custom/backup       # Custom backup location"
    echo "  $0 --retention-days 7                # Keep backups for 7 days"
    echo "  $0 --include-images                  # Include Docker images"
    echo "  COMPRESS=false $0                    # Uncompressed backup"
    echo ""
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --backup-dir)
            BACKUP_DIR="$2"
            shift 2
            ;;
        --retention-days)
            RETENTION_DAYS="$2"
            shift 2
            ;;
        --no-compress)
            COMPRESS=false
            shift
            ;;
        --include-images)
            INCLUDE_IMAGES=true
            shift
            ;;
        -h|--help)
            show_help
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
done

# Main backup process
main() {
    local start_time=$(date +%s)
    
    # Pre-flight checks
    if [ ! -f "$DEPLOY_DIR/docker-compose.yml" ]; then
        log_error "Docker Compose file not found in $DEPLOY_DIR"
        exit 1
    fi
    
    # Create backup directory
    create_backup_dir
    
    # Run backup steps
    backup_database
    backup_configuration
    backup_volumes
    backup_images
    backup_application_data
    create_system_info
    create_manifest
    
    # Validate backup before compression
    validate_backup
    
    # Compress if enabled
    compress_backup
    
    # Final validation
    validate_backup
    
    # Cleanup old backups
    cleanup_old_backups
    
    # Calculate duration
    local end_time=$(date +%s)
    local duration=$((end_time - start_time))
    
    # Generate report
    generate_report
    
    log_success "Backup completed in ${duration} seconds"
}

# Trap cleanup on exit
cleanup() {
    if [ -n "$BACKUP_NAME" ] && [ -d "$BACKUP_DIR/$BACKUP_NAME" ]; then
        log_warning "Cleaning up incomplete backup..."
        rm -rf "$BACKUP_DIR/$BACKUP_NAME"
    fi
}

trap cleanup EXIT

# Run main backup process
main