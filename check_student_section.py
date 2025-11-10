import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'aSurveyWeb.settings')
django.setup()

from WebSurvey.models import User, Section, Survey

print("="*50)
print("CHECKING STUDENT CONFIGURATION")
print("="*50)

# Check student
try:
    student = User.objects.get(username='student1')
    print(f"\n✓ Student found: {student.username}")
    print(f"  Section: {student.section if student.section else 'NOT ASSIGNED'}")
except User.DoesNotExist:
    print("\n✗ Student 'student1' not found")
    exit()

# Check available sections
sections = Section.objects.all()
print(f"\n📚 Available Sections ({sections.count()}):")
if sections.exists():
    for section in sections:
        print(f"  - {section.name} (Teacher: {section.teacher.username}, ID: {section.id})")
        print(f"    Students: {section.students.count()}")
else:
    print("  No sections available")

# Check surveys
surveys = Survey.objects.all()
print(f"\n📋 Available Surveys ({surveys.count()}):")
if surveys.exists():
    for survey in surveys:
        print(f"\n  - {survey.title}")
        print(f"    Status: {survey.status}")
        print(f"    Assigned Sections: {survey.assigned_sections.count()}")
        for section in survey.assigned_sections.all():
            print(f"      • {section.name}")
        print(f"    Start Date: {survey.start_date if survey.start_date else 'Not set'}")
        print(f"    End Date: {survey.end_date if survey.end_date else 'Not set'}")
else:
    print("  No surveys available")

# If student has no section but sections exist, assign to first one
if not student.section and sections.exists():
    first_section = sections.first()
    print(f"\n⚠️  Assigning student to section: {first_section.name}")
    student.section = first_section
    student.save()
    print("✓ Student section updated!")

print("\n" + "="*50)
