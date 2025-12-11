#!/bin/bash

# Restore .env files from backup
# Usage: ./restore-env.sh

BACKUP_DIR="$HOME/.env-backups/alfred"
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "Restoring .env files from $BACKUP_DIR..."

# Array of backup files and their destination paths
declare -A env_files=(
    ["github_daily_report.env"]="github-agent/github_daily_report/.env"
    ["team-visibility-system.env"]="team-visibility-system/.env"
    ["team-management-system.env"]="team-management-system/.env"
    ["discord-bot.env"]="discord-bot/.env"
)

# Restore each .env file
for backup_file in "${!env_files[@]}"; do
    source_path="$BACKUP_DIR/$backup_file"
    dest_path="$PROJECT_ROOT/${env_files[$backup_file]}"

    if [ -f "$source_path" ]; then
        # Create directory if it doesn't exist
        mkdir -p "$(dirname "$dest_path")"

        # Copy the file
        cp "$source_path" "$dest_path"
        echo "✓ Restored: ${env_files[$backup_file]}"
    else
        echo "✗ Backup not found: $backup_file"
    fi
done

echo ""
echo "Restore complete!"
