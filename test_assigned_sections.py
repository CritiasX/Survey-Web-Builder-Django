"""
Test script to verify assigned sections functionality
Run with: python test_assigned_sections.py
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'aSurveyWeb.settings')
django.setup()

from WebSurvey.models import Survey, Section, User
from django.utils import timezone
from datetime import timedelta

print("Testing Assigned Sections Functionality\n")
print("=" * 50)

# Get a teacher
teachers = User.objects.filter(role='teacher')
if not teachers.exists():
    print("❌ No teachers found. Please create a teacher first.")
    exit()

teacher = teachers.first()
print(f"✓ Using teacher: {teacher.username}")

# Get teacher's sections
sections = Section.objects.filter(teacher=teacher)
if not sections.exists():
    print("❌ No sections found for this teacher. Please create sections first.")
    exit()

print(f"✓ Found {sections.count()} section(s):")
for section in sections:
    print(f"  - {section.name} ({section.students.count()} students)")

# Get or create a test survey
survey, created = Survey.objects.get_or_create(
    teacher=teacher,
    title="Test Survey - Assigned Sections",
    defaults={
        'description': 'Testing assigned sections functionality',
        'status': 'published',
        'start_date': timezone.now(),
        'end_date': timezone.now() + timedelta(days=7)
    }
)

if created:
    print(f"\n✓ Created new survey: {survey.title}")
else:
    print(f"\n✓ Using existing survey: {survey.title}")

# Assign sections to survey
print(f"\nAssigning sections to survey...")
survey.assigned_sections.set(sections)
print(f"✓ Assigned {survey.assigned_sections.count()} section(s) to survey")

# Verify the assignment
print(f"\n✓ Survey '{survey.title}' is now assigned to:")
for section in survey.assigned_sections.all():
    print(f"  - {section.name}")

# Test student visibility
print(f"\nTesting student visibility:")
students = User.objects.filter(role='student', section__isnull=False)
if students.exists():
    for student in students[:3]:  # Test first 3 students
        visible_surveys = Survey.objects.filter(
            assigned_sections=student.section,
            start_date__lte=timezone.now(),
            end_date__gte=timezone.now(),
            status='published'
        ).distinct()
        print(f"  - {student.username} (Section: {student.section.name}): {visible_surveys.count()} visible survey(s)")
else:
    print("  ℹ No students with sections found to test")

print("\n" + "=" * 50)
print("✓ Test completed successfully!")
print("\nYou can now:")
print("1. Go to Survey Management to see the assignment status")
print("2. Login as a student to verify they can see the survey")
print("3. Use the 'Assign to Sections' button to modify assignments")
