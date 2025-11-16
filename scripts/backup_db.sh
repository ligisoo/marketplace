#!/bin/bash

# Database backup script for Ligisoo Marketplace
# This script creates daily backups of both PostgreSQL production DB and SQLite development DB

set -e  # Exit on any error

# Configuration
BACKUP_DIR="/home/ubuntu/marketplace/backups"
MAX_BACKUPS=7  # Keep 7 days of backups
DATE=$(date +%Y%m%d_%H%M%S)

# Create backup directory if it doesn't exist
mkdir -p "$BACKUP_DIR"

# Load environment variables
source /home/ubuntu/marketplace/.env

echo "Starting database backup at $(date)"

# Backup PostgreSQL production database if available
if [[ "$DB_NAME" ]] && [[ "$DB_USER" ]] && [[ "$DB_PASSWORD" ]]; then
    echo "Backing up PostgreSQL database..."
    PGPASSWORD="$DB_PASSWORD" pg_dump \
        -h "${DB_HOST:-localhost}" \
        -p "${DB_PORT:-5432}" \
        -U "$DB_USER" \
        -d "$DB_NAME" \
        --verbose \
        --clean \
        --create \
        --format=custom \
        > "$BACKUP_DIR/postgres_backup_$DATE.dump"
    
    echo "PostgreSQL backup completed: postgres_backup_$DATE.dump"
fi

# Backup SQLite database if it exists
SQLITE_DB="/home/ubuntu/marketplace/db.sqlite3"
if [[ -f "$SQLITE_DB" ]]; then
    echo "Backing up SQLite database..."
    cp "$SQLITE_DB" "$BACKUP_DIR/sqlite_backup_$DATE.db"
    echo "SQLite backup completed: sqlite_backup_$DATE.db"
fi

# Clean up old backups (keep only the most recent MAX_BACKUPS)
echo "Cleaning up old backups..."
cd "$BACKUP_DIR"

# Remove old PostgreSQL backups
ls -t postgres_backup_*.dump 2>/dev/null | tail -n +$((MAX_BACKUPS + 1)) | xargs rm -f

# Remove old SQLite backups  
ls -t sqlite_backup_*.db 2>/dev/null | tail -n +$((MAX_BACKUPS + 1)) | xargs rm -f

echo "Backup completed successfully at $(date)"
echo "Current backups in $BACKUP_DIR:"
ls -lah "$BACKUP_DIR"