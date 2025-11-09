"""
Test script to create sample users for testing the authentication system
Run this with: python create_test_users.py
"""

import os
import django
from django.db import IntegrityError

# Setup Django environment so this script can be run directly
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'aSurveyWeb.settings')
django.setup()

from django.contrib.auth import get_user_model
User = get_user_model()


def create_or_update_user(username, email, password, first_name='', last_name='', role='student'):
    try:
        user, created = User.objects.get_or_create(username=username, defaults={
            'email': email,
            'first_name': first_name,
            'last_name': last_name,
            'role': role,
        })
        if created:
            user.set_password(password)
            user.save()
            print(f"✓ Created user: {username} (role={role})")
        else:
            # update fields if different
            changed = False
            if user.email != email:
                user.email = email
                changed = True
            if user.first_name != first_name:
                user.first_name = first_name
                changed = True
            if user.last_name != last_name:
                user.last_name = last_name
                changed = True
            if getattr(user, 'role', None) != role:
                try:
                    user.role = role
                    changed = True
                except Exception:
                    pass
            # Always ensure password is set to known test password (safe for local dev)
            user.set_password(password)
            changed = True
            if changed:
                user.save()
            print(f"→ Updated existing user: {username} (role={getattr(user, 'role', 'N/A')})")
        return user
    except IntegrityError as e:
        print(f"✗ IntegrityError creating/updating {username}: {e}")
    except Exception as e:
        print(f"✗ Error creating/updating {username}: {e}")


if __name__ == '__main__':
    # Create a teacher
    teacher = create_or_update_user(
        username='teacher1',
        email='teacher@example.com',
        password='teacher123',
        first_name='John',
        last_name='Teacher',
        role='teacher'
    )

    # Create a student
    student = create_or_update_user(
        username='student1',
        email='student@example.com',
        password='student123',
        first_name='Jane',
        last_name='Student',
        role='student'
    )

    print("\n=== Test Credentials ===")
    print("Teacher:")
    print("  Username: teacher1")
    print("  Password: teacher123")
    print("\nStudent:")
    print("  Username: student1")
    print("  Password: student123")
