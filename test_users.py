"""
Quick test user creation for dashboard testing
Run with: python test_users.py
"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'aSurveyWeb.settings')
django.setup()

from WebSurvey.models import User

print("Creating test users...\n")

# Create teacher
try:
    if User.objects.filter(username='teacher1').exists():
        print("✓ Teacher account already exists")
    else:
        teacher = User.objects.create_user(
            username='teacher1',
            email='teacher@example.com',
            password='teacher123',
            first_name='John',
            last_name='Smith',
            role='teacher'
        )
        print("✓ Teacher account created")
except Exception as e:
    print(f"✗ Teacher creation failed: {e}")

# Create student
try:
    if User.objects.filter(username='student1').exists():
        print("✓ Student account already exists")
    else:
        student = User.objects.create_user(
            username='student1',
            email='student@example.com',
            password='student123',
            first_name='Jane',
            last_name='Doe',
            role='student'
        )
        print("✓ Student account created")
except Exception as e:
    print(f"✗ Student creation failed: {e}")

print("\n" + "="*50)
print("TEST LOGIN CREDENTIALS")
print("="*50)
print("\nTeacher Account:")
print("  URL: http://localhost:8000/login/")
print("  Username: teacher1")
print("  Password: teacher123")
print("  Role: Teacher")

print("\nStudent Account:")
print("  URL: http://localhost:8000/login/")
print("  Username: student1")
print("  Password: student123")
print("  Role: Student")

print("\nAdmin Account:")
print("  URL: http://localhost:8000/admin/")
print("  Username: admin")
print("  Password: (set during createsuperuser)")
print("\n" + "="*50)

