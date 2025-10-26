#!/usr/bin/env python3
"""
Rollback to old preset system
Run this if you need to revert to the original presets.json
"""

import os
import sys
import shutil
import glob

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BACKUP_DIR = os.path.join(BASE_DIR, 'backups')

def rollback():
    """Restore most recent backup"""
    print("🔄 Rolling back to old preset system...")

    # Find most recent backup
    backups = glob.glob(os.path.join(BACKUP_DIR, 'presets_backup_*.json'))
    if not backups:
        print("✗ No backups found!")
        return False

    latest_backup = max(backups, key=os.path.getctime)
    print(f"   Found backup: {os.path.basename(latest_backup)}")

    # Restore backup
    dest = os.path.join(BASE_DIR, 'presets.json')
    shutil.copy2(latest_backup, dest)
    print(f"   ✓ Restored to: {dest}")

    # Update .env
    env_file = os.path.join(BASE_DIR, '.env')
    if os.path.exists(env_file):
        with open(env_file, 'r') as f:
            content = f.read()

        content = content.replace('ENABLE_HIERARCHICAL_PRESETS=true',
                                'ENABLE_HIERARCHICAL_PRESETS=false')

        with open(env_file, 'w') as f:
            f.write(content)

        print(f"   ✓ Disabled hierarchical presets in .env")

    print("\n✓ Rollback complete! Restart the application.")
    return True

if __name__ == '__main__':
    if rollback():
        sys.exit(0)
    else:
        sys.exit(1)
