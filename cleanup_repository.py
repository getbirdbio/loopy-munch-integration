#!/usr/bin/env python3
"""
Repository Cleanup Script
========================

Clean up the android_frida repository by removing old, unused files
and organizing the core files needed for the Loopy-Make.com integration.
"""

import os
import shutil
import subprocess
from pathlib import Path

# Core files to keep
KEEP_FILES = {
    # Main service files
    'loopy_make_integration.py',
    'comprehensive_webhook_test.py', 
    'simulate_real_customer_flow.py',
    
    # Configuration
    'production.env',
    'production.env.template',
    
    # Utilities
    'check_webhook_urls.py',
    'get_ngrok_url.py',
    
    # Documentation
    'README.md',
    
    # Git
    '.gitignore',
    '.git',
    
    # Current analysis
    'repo_cleanup_analysis.md',
    'cleanup_repository.py',
}

# Files to archive (move to archive folder)
ARCHIVE_FILES = {
    # Customer data
    'customer_analysis.csv',
    'CoffeeLoyalty-customers-1748674919.csv',
    'CoffeeLoyalty-customers-1748675068.csv',
    'ALL_customer_codes.txt',
    'ACTIVE_customer_codes.txt',
    'ELIGIBLE_customer_codes.txt',
    'STAMPED_customer_codes.txt',
    'customer_codes.txt',
    'successful_withdrawals_20250531_094827.json',
    
    # Glen Thompson investigation
    'glen_creation_log.json',
    'glen_linking_log.json',
    'glen_thompson_summary.md',
    'glen_thompson_report.py',
    'add_glen_to_munch.py',
    'link_glen_loyalty_code.py',
    'search_glen_in_munch_focused.py',
    'search_glen_munch.py',
    'search_glen_using_bilateral_sync_method.py',
    
    # Old integration scripts (for reference)
    'loopy_munch_production_final.py',
    'loopy_munch_production_final_UPDATED.py',
    'make_com_rewards_bridge.py',
    'webhook_production_service.py',
}

# Directories to remove entirely
REMOVE_DIRS = {
    '__pycache__',
    'webhook_env',
}

# File patterns to remove (extensions/patterns)
REMOVE_PATTERNS = {
    '*.log',
    '*.db',
    '*.pyc',
}

def create_archive_folder():
    """Create archive folder for files we want to keep but not in main repo"""
    archive_path = Path('archive')
    archive_path.mkdir(exist_ok=True)
    print(f"📁 Created archive folder: {archive_path}")
    return archive_path

def move_to_archive(filename, archive_path):
    """Move file to archive folder"""
    src = Path(filename)
    if src.exists():
        dst = archive_path / filename
        try:
            shutil.move(str(src), str(dst))
            print(f"📦 Archived: {filename}")
            return True
        except Exception as e:
            print(f"❌ Failed to archive {filename}: {e}")
            return False
    return False

def remove_file(filename):
    """Remove a file"""
    try:
        os.remove(filename)
        print(f"🗑️ Removed: {filename}")
        return True
    except Exception as e:
        print(f"❌ Failed to remove {filename}: {e}")
        return False

def remove_directory(dirname):
    """Remove a directory and all contents"""
    try:
        shutil.rmtree(dirname)
        print(f"🗑️ Removed directory: {dirname}")
        return True
    except Exception as e:
        print(f"❌ Failed to remove directory {dirname}: {e}")
        return False

def get_all_files():
    """Get list of all files in current directory"""
    files = []
    for item in os.listdir('.'):
        if os.path.isfile(item):
            files.append(item)
    return files

def get_all_directories():
    """Get list of all directories in current directory"""
    dirs = []
    for item in os.listdir('.'):
        if os.path.isdir(item) and item != '.git':
            dirs.append(item)
    return dirs

def create_requirements_txt():
    """Create requirements.txt for the webhook service"""
    requirements = [
        "flask==2.3.3",
        "requests==2.31.0", 
        "python-dotenv==1.0.0"
    ]
    
    try:
        with open('requirements.txt', 'w') as f:
            f.write('\n'.join(requirements) + '\n')
        print("📝 Created requirements.txt")
    except Exception as e:
        print(f"❌ Failed to create requirements.txt: {e}")

def update_gitignore():
    """Update .gitignore with common patterns"""
    gitignore_content = """# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
*.db
*.log

# Environment files
.env
production.env

# ngrok
ngrok.log

# Archive folder
archive/

# OS
.DS_Store
Thumbs.db

# IDE
.vscode/
.idea/
*.swp
*.swo

# Temporary files
*.tmp
*.temp
nohup.out
"""
    
    try:
        with open('.gitignore', 'w') as f:
            f.write(gitignore_content)
        print("📝 Updated .gitignore")
    except Exception as e:
        print(f"❌ Failed to update .gitignore: {e}")

def main():
    """Main cleanup function"""
    print("🧹 REPOSITORY CLEANUP STARTING")
    print("=" * 60)
    
    # Get current files and directories
    all_files = get_all_files()
    all_dirs = get_all_directories()
    
    print(f"📊 Found {len(all_files)} files and {len(all_dirs)} directories")
    
    # Create archive folder
    archive_path = create_archive_folder()
    
    # Archive important files
    print("\n📦 Archiving important files...")
    archived_count = 0
    for filename in ARCHIVE_FILES:
        if move_to_archive(filename, archive_path):
            archived_count += 1
    
    # Remove unwanted directories
    print("\n🗑️ Removing unwanted directories...")
    removed_dirs = 0
    for dirname in REMOVE_DIRS:
        if dirname in all_dirs:
            if remove_directory(dirname):
                removed_dirs += 1
    
    # Remove unwanted files
    print("\n🗑️ Removing unwanted files...")
    removed_files = 0
    
    for filename in all_files:
        # Skip files we want to keep
        if filename in KEEP_FILES:
            continue
            
        # Skip files we already archived
        if filename in ARCHIVE_FILES:
            continue
            
        # Remove everything else
        if remove_file(filename):
            removed_files += 1
    
    # Create new files
    print("\n📝 Creating new files...")
    create_requirements_txt()
    update_gitignore()
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 CLEANUP SUMMARY")
    print("=" * 60)
    print(f"📦 Files archived: {archived_count}")
    print(f"🗑️ Files removed: {removed_files}")
    print(f"🗑️ Directories removed: {removed_dirs}")
    
    remaining_files = len([f for f in os.listdir('.') if os.path.isfile(f)])
    print(f"📁 Files remaining: {remaining_files}")
    
    print("\n✅ Core files kept:")
    for filename in sorted(KEEP_FILES):
        if os.path.exists(filename):
            print(f"   ✅ {filename}")
    
    print("\n📝 New files created:")
    print("   📝 requirements.txt")
    print("   📝 .gitignore (updated)")
    
    print("\n🎯 Next steps:")
    print("1. Review the remaining files")
    print("2. Update README.md with current setup")
    print("3. Commit the cleaned repository")
    print("4. Update production.env with your tokens")
    
    print("\n🎉 Repository cleanup complete!")

if __name__ == "__main__":
    main() 