#!/usr/bin/env python3
"""
Preset Migration Script
Safely migrate from flat presets.json to hierarchical_presets.json

This script:
1. Backs up existing presets.json
2. Validates hierarchical_presets.json
3. Copies hierarchical_presets.json from files/ folder
4. Preserves backward compatibility
"""

import os
import sys
import json
import shutil
from datetime import datetime

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OLD_PRESETS = os.path.join(BASE_DIR, 'presets.json')
NEW_PRESETS_SOURCE = os.path.join(BASE_DIR, 'files', 'hierarchical_presets.json')
NEW_PRESETS_DEST = os.path.join(BASE_DIR, 'hierarchical_presets.json')
BACKUP_DIR = os.path.join(BASE_DIR, 'backups')


def create_backup():
    """Backup existing presets.json"""
    print("📦 Creating backup...")

    if not os.path.exists(BACKUP_DIR):
        os.makedirs(BACKUP_DIR)
        print(f"   Created backup directory: {BACKUP_DIR}")

    if os.path.exists(OLD_PRESETS):
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_path = os.path.join(BACKUP_DIR, f'presets_backup_{timestamp}.json')
        shutil.copy2(OLD_PRESETS, backup_path)
        print(f"   ✓ Backed up to: {backup_path}")
        return backup_path
    else:
        print(f"   ⚠ No existing presets.json found (this is OK for new installs)")
        return None


def validate_hierarchical_presets():
    """Validate the new hierarchical presets file"""
    print("\n🔍 Validating hierarchical_presets.json...")

    if not os.path.exists(NEW_PRESETS_SOURCE):
        print(f"   ✗ Error: {NEW_PRESETS_SOURCE} not found!")
        print(f"   Make sure files/hierarchical_presets.json exists")
        return False

    try:
        with open(NEW_PRESETS_SOURCE, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Validate structure
        required_keys = ['version', 'categories', 'preset_packs', 'universal_options']
        for key in required_keys:
            if key not in data:
                print(f"   ✗ Missing required key: {key}")
                return False

        # Count categories
        num_categories = len(data.get('categories', {}))
        num_packs = len(data.get('preset_packs', {}).get('packs', []))

        print(f"   ✓ Valid JSON structure")
        print(f"   ✓ Version: {data.get('version')}")
        print(f"   ✓ Categories: {num_categories}")
        print(f"   ✓ Preset Packs: {num_packs}")

        # List categories
        print(f"\n   📂 Available categories:")
        for cat_id, cat_data in data.get('categories', {}).items():
            num_types = len(cat_data.get('level2_types', {}))
            print(f"      - {cat_data.get('name')} ({num_types} sub-types)")

        return True

    except json.JSONDecodeError as e:
        print(f"   ✗ Invalid JSON: {e}")
        return False
    except Exception as e:
        print(f"   ✗ Error: {e}")
        return False


def install_hierarchical_presets():
    """Copy hierarchical presets to main directory"""
    print("\n📥 Installing hierarchical presets...")

    try:
        shutil.copy2(NEW_PRESETS_SOURCE, NEW_PRESETS_DEST)
        print(f"   ✓ Copied to: {NEW_PRESETS_DEST}")

        # Verify installation
        file_size = os.path.getsize(NEW_PRESETS_DEST)
        print(f"   ✓ File size: {file_size:,} bytes (~{file_size/1024:.1f} KB)")

        return True

    except Exception as e:
        print(f"   ✗ Error copying file: {e}")
        return False


def update_env_file():
    """Add feature flag to .env file"""
    print("\n⚙️  Updating .env file...")

    env_file = os.path.join(BASE_DIR, '.env')
    env_example = os.path.join(BASE_DIR, '.env.example')

    # Create .env from .env.example if it doesn't exist
    if not os.path.exists(env_file) and os.path.exists(env_example):
        shutil.copy2(env_example, env_file)
        print(f"   ✓ Created .env from .env.example")

    if os.path.exists(env_file):
        # Read existing content
        with open(env_file, 'r') as f:
            content = f.read()

        # Check if feature flag already exists
        if 'ENABLE_HIERARCHICAL_PRESETS' not in content:
            # Add feature flag
            new_content = content.rstrip() + "\n\n# Hierarchical Preset System\n"
            new_content += "ENABLE_HIERARCHICAL_PRESETS=true\n"

            with open(env_file, 'w') as f:
                f.write(new_content)

            print(f"   ✓ Added ENABLE_HIERARCHICAL_PRESETS=true")
        else:
            print(f"   ℹ Feature flag already exists in .env")
    else:
        print(f"   ⚠ .env file not found - you'll need to create one manually")
        print(f"   Add this line: ENABLE_HIERARCHICAL_PRESETS=true")


def create_rollback_script():
    """Create a rollback script in case migration fails"""
    print("\n🔄 Creating rollback script...")

    rollback_script = os.path.join(BASE_DIR, 'rollback_presets.py')

    script_content = '''#!/usr/bin/env python3
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

    print("\\n✓ Rollback complete! Restart the application.")
    return True

if __name__ == '__main__':
    if rollback():
        sys.exit(0)
    else:
        sys.exit(1)
'''

    with open(rollback_script, 'w') as f:
        f.write(script_content)

    # Make it executable
    os.chmod(rollback_script, 0o755)

    print(f"   ✓ Created: {rollback_script}")
    print(f"   Run 'python rollback_presets.py' to revert if needed")


def print_summary():
    """Print migration summary and next steps"""
    print("\n" + "="*70)
    print("✅ MIGRATION COMPLETE!")
    print("="*70)

    print("\n📋 What was done:")
    print("   1. ✓ Backed up original presets.json")
    print("   2. ✓ Validated hierarchical_presets.json")
    print("   3. ✓ Installed new hierarchical presets")
    print("   4. ✓ Updated .env with feature flag")
    print("   5. ✓ Created rollback script")

    print("\n🚀 Next steps:")
    print("   1. Review changes in your code editor")
    print("   2. Restart the Flask application")
    print("   3. Test both old and new preset systems")
    print("   4. Check logs/app.log for any errors")

    print("\n⚠️  Important notes:")
    print("   - Original presets.json backed up to: backups/")
    print("   - Feature flag: ENABLE_HIERARCHICAL_PRESETS=true")
    print("   - To rollback: python rollback_presets.py")
    print("   - Both systems will coexist during transition")

    print("\n📚 Documentation:")
    print("   - See files/integration_guide.md for implementation details")
    print("   - See files/ui_wireframe.md for UI design")
    print("   - See files/workflow_guide.md for user workflows")


def main():
    """Main migration process"""
    print("="*70)
    print("COMFYUI PROMPT GENERATOR - PRESET MIGRATION")
    print("="*70)
    print("\nThis will migrate from flat presets to hierarchical presets")
    print("The old system will be backed up and can be restored.\n")

    # Confirm
    response = input("Continue with migration? [y/N]: ")
    if response.lower() not in ['y', 'yes']:
        print("Migration cancelled.")
        return

    # Step 1: Backup
    backup_path = create_backup()

    # Step 2: Validate
    if not validate_hierarchical_presets():
        print("\n✗ Validation failed! Migration aborted.")
        return

    # Step 3: Install
    if not install_hierarchical_presets():
        print("\n✗ Installation failed! Migration aborted.")
        return

    # Step 4: Update .env
    update_env_file()

    # Step 5: Create rollback
    create_rollback_script()

    # Step 6: Summary
    print_summary()


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nMigration cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
