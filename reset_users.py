"""
Reset non-superuser users and run create_test_users.py to reseed test accounts.
Run with: python reset_users.py
This script will:
 - create a backup of db.sqlite3 -> db.sqlite3.bak (if file exists)
 - delete all users where is_superuser=False (this removes teachers/students but keeps superusers)
 - run create_test_users.py to recreate test accounts
"""
import os
import shutil
import subprocess
import sys

# ensure we're in project root
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(PROJECT_DIR, 'db.sqlite3')
BACKUP_PATH = os.path.join(PROJECT_DIR, 'db.sqlite3.bak')

print('Project dir:', PROJECT_DIR)

# Backup sqlite file if present
if os.path.exists(DB_PATH):
    print('Backing up', DB_PATH, 'to', BACKUP_PATH)
    shutil.copy2(DB_PATH, BACKUP_PATH)
else:
    print('No db.sqlite3 found to backup')

# Setup Django env
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'aSurveyWeb.settings')
import django
django.setup()

from django.contrib.auth import get_user_model
User = get_user_model()

# Delete non-superuser users
qs = User.objects.filter(is_superuser=False)
count = qs.count()
if count:
    print(f'Deleting {count} user(s) (non-superusers)')
    qs.delete()
else:
    print('No non-superuser users to delete')

# Run seeder script
seeder = os.path.join(PROJECT_DIR, 'create_test_users.py')
if os.path.exists(seeder):
    print('Running seeder:', seeder)
    # Use subprocess so create_test_users runs in a clean process
    res = subprocess.run([sys.executable, seeder], capture_output=True, text=True)
    print('Seeder stdout:\n', res.stdout)
    print('Seeder stderr:\n', res.stderr)
else:
    print('Seeder script create_test_users.py not found')

# Print current users
print('\nCurrent users:')
for u in User.objects.all():
    print('-', u.username, '(superuser)' if u.is_superuser else f'(role={getattr(u, "role", "N/A")})')

print('\nDone.')

