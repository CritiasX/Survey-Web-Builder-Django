from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone

# Create your models here.

class Section(models.Model):
    name = models.CharField(max_length=150)
    teacher = models.ForeignKey('User', on_delete=models.CASCADE, related_name='sections')

    def __str__(self):
        return f"{self.name} ({self.teacher.username})"

class User(AbstractUser):
    ROLE_CHOICES = [
        ('student', 'Student'),
        ('teacher', 'Teacher'),
    ]

    role = models.CharField('role', max_length=20, choices=ROLE_CHOICES, default='student')
    # optional section association for students
    section = models.ForeignKey(Section, null=True, blank=True, on_delete=models.SET_NULL, related_name='students')

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"


class Survey(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('published', 'Published'),
        ('closed', 'Closed'),
    ]

    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    teacher = models.ForeignKey(User, on_delete=models.CASCADE, related_name='surveys')
    sections = models.ManyToManyField(Section, blank=True, related_name='surveys')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    total_points = models.IntegerField(default=0)
    time_limit = models.IntegerField(null=True, blank=True, help_text="Time limit in minutes")
    due_date = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    def calculate_total_points(self):
        """Calculate total points from all questions"""
        total = sum(question.points for question in self.questions.all())
        self.total_points = total
        self.save(update_fields=['total_points'])
        return total


class Question(models.Model):
    QUESTION_TYPES = [
        ('multiple_choice', 'Multiple Choice'),
        ('likert', 'Likert Scale'),
        ('true_false', 'True or False'),
        ('essay', 'Short Text'),
        ('enumeration', 'Enumeration'),
        ('heading', 'Heading'),
        ('subheading', 'Subheading'),
        ('paragraph', 'Paragraph'),
    ]

    survey = models.ForeignKey(Survey, on_delete=models.CASCADE, related_name='questions')
    question_type = models.CharField(max_length=20, choices=QUESTION_TYPES)
    question_text = models.TextField()
    points = models.IntegerField(default=1)
    order = models.IntegerField(default=0)
    required = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.survey.title} - Q{self.order}: {self.question_text[:50]}"


class QuestionContext(models.Model):
    """Context items (code snippets, images) for questions"""
    CONTEXT_TYPES = [
        ('code_snippet', 'Code Snippet'),
        ('image', 'Image'),
    ]

    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='context_items')
    context_type = models.CharField(max_length=20, choices=CONTEXT_TYPES)
    content = models.TextField()  # Code text or base64 image data
    language = models.CharField(max_length=50, blank=True, null=True)  # For code snippets
    order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.question} - {self.context_type} #{self.order}"


class MultipleChoiceOption(models.Model):
    """Options for multiple choice questions"""
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='options')
    option_text = models.CharField(max_length=255)
    is_correct = models.BooleanField(default=False)
    order = models.IntegerField(default=0)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return self.option_text


class TrueFalseAnswer(models.Model):
    """Correct answer for true/false questions"""
    question = models.OneToOneField(Question, on_delete=models.CASCADE, related_name='true_false_answer')
    is_true = models.BooleanField()

    def __str__(self):
        return "True" if self.is_true else "False"


class EnumerationAnswer(models.Model):
    """Correct answers for enumeration questions"""
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='enumeration_answers')
    answer_text = models.CharField(max_length=255)
    order = models.IntegerField(default=0)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return self.answer_text


class StudentResponse(models.Model):
    """Student's response to a survey"""
    survey = models.ForeignKey(Survey, on_delete=models.CASCADE, related_name='responses')
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='survey_responses')
    started_at = models.DateTimeField(auto_now_add=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    score = models.FloatField(null=True, blank=True)
    is_submitted = models.BooleanField(default=False)

    class Meta:
        unique_together = ['survey', 'student']

    def __str__(self):
        return f"{self.student.username} - {self.survey.title}"


class QuestionAnswer(models.Model):
    """Individual answer to a question"""
    response = models.ForeignKey(StudentResponse, on_delete=models.CASCADE, related_name='answers')
    question = models.ForeignKey(Question, on_delete=models.CASCADE)

    # For multiple choice
    selected_option = models.ForeignKey(MultipleChoiceOption, null=True, blank=True, on_delete=models.SET_NULL)

    # For true/false
    true_false_answer = models.BooleanField(null=True, blank=True)

    # For essay and enumeration
    text_answer = models.TextField(blank=True)

    # For scoring
    points_earned = models.FloatField(default=0)
    is_correct = models.BooleanField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.response.student.username} - Q{self.question.order}"
