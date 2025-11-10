from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from .models import User, Section, Survey, Question, MultipleChoiceOption, TrueFalseAnswer, EnumerationAnswer
import json

# Create your views here.

def landingPage(request):
    return render(request,'landingPage.html' )

def aboutPage(request):
    return render(request,'aboutUs.html' )

def contactPage(request):
    return render(request,'contactsPage.html' )

def loginPage(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)

        # Handle AJAX request
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            if user is not None:
                login(request, user)
                return JsonResponse({
                    'success': True,
                    'message': f'Welcome back, {user.username}!',
                    'redirect_url': '/dashboard/'
                })
            else:
                return JsonResponse({
                    'success': False,
                    'message': 'Invalid username or password'
                })

        # Handle regular form submission (fallback)
        if user is not None:
            login(request, user)
            messages.success(request, f'Welcome back, {user.username}!')
            return redirect('dashboard')
        else:
            messages.error(request, 'Invalid username or password')

    return render(request,'loginPage.html' )

def registerPage(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    sections = Section.objects.all()

    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        password_confirm = request.POST.get('password_confirm')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        role = request.POST.get('role')
        section_id = request.POST.get('section')  # may be empty

        # resolve section if provided
        section_obj = None
        if section_id:
            try:
                section_obj = Section.objects.get(id=section_id)
            except Section.DoesNotExist:
                section_obj = None

        # Handle AJAX request
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            if password != password_confirm:
                return JsonResponse({
                    'success': False,
                    'message': 'Passwords do not match'
                })
            elif User.objects.filter(username=username).exists():
                return JsonResponse({
                    'success': False,
                    'message': 'Username already exists'
                })
            elif User.objects.filter(email=email).exists():
                return JsonResponse({
                    'success': False,
                    'message': 'Email already registered'
                })
            else:
                try:
                    user = User.objects.create_user(
                        username=username,
                        email=email,
                        password=password,
                        first_name=first_name,
                        last_name=last_name,
                        role=role
                    )
                    # assign section for students
                    if role == 'student' and section_obj:
                        user.section = section_obj
                        user.save(update_fields=['section'])

                    return JsonResponse({
                        'success': True,
                        'message': 'Account created successfully! Redirecting to login...',
                        'redirect_url': '/login/'
                    })
                except Exception as e:
                    return JsonResponse({
                        'success': False,
                        'message': f'Registration failed: {str(e)}'
                    })

        # Handle regular form submission (fallback)
        if password != password_confirm:
            messages.error(request, 'Passwords do not match')
        elif User.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists')
        elif User.objects.filter(email=email).exists():
            messages.error(request, 'Email already registered')
        else:
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name,
                role=role
            )
            if role == 'student' and section_obj:
                user.section = section_obj
                user.save(update_fields=['section'])

            messages.success(request, 'Account created successfully! Please login.')
            return redirect('login')

    return render(request,'registerPage.html', {'sections': sections})

@login_required
def dashboardPage(request):
    user = request.user
    context = {
        'user': user,
        'role': user.role
    }
    
    if user.role == 'student':
        # Get available surveys for student
        if user.section:
            now = timezone.now()
            available_surveys = Survey.objects.filter(
                assigned_sections=user.section,
                status='published'
            ).filter(
                Q(start_date__lte=now) | Q(start_date__isnull=True)
            ).filter(
                Q(end_date__gte=now) | Q(end_date__isnull=True)
            ).distinct()
            
            # Get student's responses
            from .models import StudentResponse
            completed_surveys = StudentResponse.objects.filter(
                student=user,
                is_submitted=True
            ).count()
            
            # Pending surveys (available but not completed)
            completed_survey_ids = StudentResponse.objects.filter(
                student=user,
                is_submitted=True
            ).values_list('survey_id', flat=True)
            
            pending_surveys = available_surveys.exclude(id__in=completed_survey_ids)
            
            context.update({
                'available_surveys': available_surveys,
                'available_count': available_surveys.count(),
                'completed_count': completed_surveys,
                'pending_count': pending_surveys.count(),
                'recent_surveys': available_surveys[:5]
            })
        else:
            context.update({
                'available_surveys': [],
                'available_count': 0,
                'completed_count': 0,
                'pending_count': 0,
                'recent_surveys': []
            })
    
    elif user.role == 'teacher':
        # Get teacher's surveys
        surveys = Survey.objects.filter(teacher=user)
        from .models import StudentResponse
        total_responses = StudentResponse.objects.filter(survey__teacher=user).count()
        
        context.update({
            'total_surveys': surveys.count(),
            'total_responses': total_responses,
            'recent_surveys': surveys[:5]
        })
    
    return render(request, 'dashboard.html', context)

def logoutPage(request):
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('landing')


@login_required
def pending_surveys(request):
    """Show pending surveys for students (surveys they haven't completed yet)"""
    if request.user.role != 'student':
        messages.error(request, 'Only students can access this page.')
        return redirect('dashboard')
    
    user = request.user
    
    if user.section:
        now = timezone.now()
        # Get all available surveys
        available_surveys = Survey.objects.filter(
            assigned_sections=user.section,
            status='published'
        ).filter(
            Q(start_date__lte=now) | Q(start_date__isnull=True)
        ).filter(
            Q(end_date__gte=now) | Q(end_date__isnull=True)
        ).distinct()
        
        # Get completed survey IDs
        from .models import StudentResponse
        completed_survey_ids = StudentResponse.objects.filter(
            student=user,
            is_submitted=True
        ).values_list('survey_id', flat=True)
        
        # Pending = available but not completed
        pending_surveys_list = available_surveys.exclude(id__in=completed_survey_ids)
        
        context = {
            'pending_surveys': pending_surveys_list,
            'pending_count': pending_surveys_list.count(),
            'user': user
        }
    else:
        context = {
            'pending_surveys': [],
            'pending_count': 0,
            'user': user
        }
    
    return render(request, 'pending_surveys.html', context)


# Survey Builder Views
@login_required
def survey_list(request):
    """List surveys based on user role"""
    user = request.user
    
    if user.role == 'teacher':
        # Teachers see all their surveys
        surveys = Survey.objects.filter(teacher=user)
    elif user.role == 'student':
        # Students see only surveys assigned to their section
        if user.section:
            now = timezone.now()
            surveys = Survey.objects.filter(
                assigned_sections=user.section,
                status='published'
            ).filter(
                # If start_date is set, must be started. If not set, show it
                Q(start_date__lte=now) | Q(start_date__isnull=True)
            ).filter(
                # If end_date is set, must not be ended. If not set, show it
                Q(end_date__gte=now) | Q(end_date__isnull=True)
            ).distinct()
        else:
            surveys = Survey.objects.none()
    else:
        surveys = Survey.objects.none()
    
    context = {
        'surveys': surveys,
        'user': user
    }
    return render(request, 'survey_list.html', context)


@login_required
def survey_builder(request, survey_id=None):
    """Survey builder page - create or edit survey"""
    if request.user.role != 'teacher':
        messages.error(request, 'Only teachers can access this page.')
        return redirect('dashboard')

    survey = None
    if survey_id:
        survey = get_object_or_404(Survey, id=survey_id, teacher=request.user)

    sections = Section.objects.filter(teacher=request.user)

    context = {
        'survey': survey,
        'sections': sections,
        'user': request.user
    }
    return render(request, 'survey_builder.html', context)


@login_required
@require_http_methods(["POST"])
def save_survey(request):
    """AJAX endpoint to save survey with questions"""
    if request.user.role != 'teacher':
        return JsonResponse({'success': False, 'message': 'Unauthorized'}, status=403)

    try:
        data = json.loads(request.body)
        survey_id = data.get('survey_id')

        with transaction.atomic():
            # Create or update survey
            if survey_id:
                survey = get_object_or_404(Survey, id=survey_id, teacher=request.user)
            else:
                survey = Survey(teacher=request.user)

            survey.title = data.get('title', 'Untitled Survey')
            survey.description = data.get('description', '')
            survey.status = data.get('status', 'draft')
            survey.time_limit = data.get('time_limit')
            survey.due_date = data.get('due_date')
            survey.start_date = data.get('start_date')
            survey.end_date = data.get('end_date')
            survey.save()

            # Handle sections - save to assigned_sections for student visibility
            section_ids = data.get('sections', [])
            if section_ids:
                survey.sections.set(Section.objects.filter(id__in=section_ids, teacher=request.user))
                # Also set assigned_sections so students can see the survey
                survey.assigned_sections.set(Section.objects.filter(id__in=section_ids, teacher=request.user))
            else:
                # Clear assigned sections if none selected
                survey.assigned_sections.clear()

            # Delete existing questions if updating
            if survey_id:
                survey.questions.all().delete()

            # Create questions
            questions_data = data.get('questions', [])
            for idx, q_data in enumerate(questions_data):
                question = Question.objects.create(
                    survey=survey,
                    question_type=q_data['type'],
                    question_text=q_data['text'],
                    points=q_data.get('points', 1),
                    order=idx,
                    required=q_data.get('required', True)
                )

                # Handle question type specific data
                if q_data['type'] == 'multiple_choice':
                    for opt_idx, option in enumerate(q_data.get('options', [])):
                        MultipleChoiceOption.objects.create(
                            question=question,
                            option_text=option['text'],
                            is_correct=option.get('is_correct', False),
                            order=opt_idx
                        )

                elif q_data['type'] == 'true_false':
                    TrueFalseAnswer.objects.create(
                        question=question,
                        is_true=q_data.get('correct_answer', True)
                    )

                elif q_data['type'] == 'enumeration':
                    for ans_idx, answer in enumerate(q_data.get('answers', [])):
                        EnumerationAnswer.objects.create(
                            question=question,
                            answer_text=answer,
                            order=ans_idx
                        )

            # Calculate total points
            survey.calculate_total_points()

            return JsonResponse({
                'success': True,
                'message': 'Survey saved successfully!',
                'survey_id': survey.id
            })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error saving survey: {str(e)}'
        }, status=500)


@login_required
@require_http_methods(["GET"])
def get_survey_data(request, survey_id):
    """AJAX endpoint to get survey data for editing"""
    if request.user.role != 'teacher':
        return JsonResponse({'success': False, 'message': 'Unauthorized'}, status=403)

    try:
        survey = get_object_or_404(Survey, id=survey_id, teacher=request.user)

        questions_data = []
        for question in survey.questions.all():
            q_data = {
                'id': question.id,
                'type': question.question_type,
                'text': question.question_text,
                'points': question.points,
                'required': question.required,
                'order': question.order
            }

            if question.question_type == 'multiple_choice':
                q_data['options'] = [
                    {
                        'text': opt.option_text,
                        'is_correct': opt.is_correct
                    }
                    for opt in question.options.all()
                ]

            elif question.question_type == 'true_false':
                if hasattr(question, 'true_false_answer'):
                    q_data['correct_answer'] = question.true_false_answer.is_true

            elif question.question_type == 'enumeration':
                q_data['answers'] = [
                    ans.answer_text for ans in question.enumeration_answers.all()
                ]

            questions_data.append(q_data)

        survey_data = {
            'id': survey.id,
            'title': survey.title,
            'description': survey.description,
            'status': survey.status,
            'time_limit': survey.time_limit,
            'due_date': survey.due_date.isoformat() if survey.due_date else None,
            'start_date': survey.start_date.isoformat() if survey.start_date else None,
            'end_date': survey.end_date.isoformat() if survey.end_date else None,
            'sections': list(survey.assigned_sections.values_list('id', flat=True)),
            'questions': questions_data,
            'total_points': survey.total_points
        }

        return JsonResponse({
            'success': True,
            'survey': survey_data
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error loading survey: {str(e)}'
        }, status=500)


@login_required
@require_http_methods(["POST"])
def delete_survey(request, survey_id):
    """Delete a survey"""
    if request.user.role != 'teacher':
        return JsonResponse({'success': False, 'message': 'Unauthorized'}, status=403)

    try:
        survey = get_object_or_404(Survey, id=survey_id, teacher=request.user)
        survey.delete()

        return JsonResponse({
            'success': True,
            'message': 'Survey deleted successfully!'
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error deleting survey: {str(e)}'
        }, status=500)


@login_required
def assign_survey_to_sections(request, survey_id):
    """Assign survey to specific sections (teacher only)"""
    if request.user.role != 'teacher':
        messages.error(request, 'Only teachers can assign surveys.')
        return redirect('survey_list')
    
    survey = get_object_or_404(Survey, id=survey_id, teacher=request.user)
    
    if request.method == 'POST':
        section_ids = request.POST.getlist('sections')
        survey.assigned_sections.clear()
        
        for section_id in section_ids:
            try:
                section = Section.objects.get(id=section_id, teacher=request.user)
                survey.assigned_sections.add(section)
            except Section.DoesNotExist:
                pass
        
        messages.success(request, f'Survey "{survey.title}" assigned to selected sections.')
        return redirect('survey_list')
    
    # GET request - show assignment form
    teacher_sections = Section.objects.filter(teacher=request.user)
    assigned_section_ids = survey.assigned_sections.values_list('id', flat=True)
    
    context = {
        'survey': survey,
        'sections': teacher_sections,
        'assigned_section_ids': list(assigned_section_ids),
        'user': request.user
    }
    return render(request, 'assign_survey.html', context)


# Section Management Views
@login_required
def section_list(request):
    """List all sections for the teacher"""
    if request.user.role != 'teacher':
        messages.error(request, 'Only teachers can access this page.')
        return redirect('dashboard')

    sections = Section.objects.filter(teacher=request.user)
    context = {
        'sections': sections,
        'user': request.user
    }
    return render(request, 'section_list.html', context)


@login_required
@require_http_methods(["POST"])
def create_section(request):
    """Create a new section"""
    if request.user.role != 'teacher':
        return JsonResponse({'success': False, 'message': 'Unauthorized'}, status=403)

    try:
        name = ''
        # Try to parse JSON body when content-type indicates JSON
        try:
            if request.content_type and 'application/json' in request.content_type:
                raw = request.body.decode('utf-8') if request.body else '{}'
                data = json.loads(raw or '{}')
                name = (data.get('name') or '').strip()
            else:
                # Fallback: attempt to parse JSON anyway, then fallback to POST
                try:
                    raw = request.body.decode('utf-8') if request.body else '{}'
                    data = json.loads(raw or '{}')
                    name = (data.get('name') or '').strip()
                except Exception:
                    name = (request.POST.get('name') or '').strip()
        except Exception:
            name = (request.POST.get('name') or '').strip()

        if not name:
            return JsonResponse({'success': False, 'message': 'Section name is required'})

        # Check if section name already exists for this teacher
        if Section.objects.filter(teacher=request.user, name=name).exists():
            return JsonResponse({'success': False, 'message': 'A section with this name already exists'})

        section = Section.objects.create(teacher=request.user, name=name)

        return JsonResponse({
            'success': True,
            'message': 'Section created successfully!',
            'section': {
                'id': section.id,
                'name': section.name,
                'student_count': section.students.count()
            }
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error creating section: {str(e)}'
        }, status=500)


@login_required
@require_http_methods(["POST"])
def edit_section(request, section_id):
    """Edit a section"""
    if request.user.role != 'teacher':
        return JsonResponse({'success': False, 'message': 'Unauthorized'}, status=403)

    try:
        section = get_object_or_404(Section, id=section_id, teacher=request.user)

        name = ''
        try:
            if request.content_type and 'application/json' in request.content_type:
                raw = request.body.decode('utf-8') if request.body else '{}'
                data = json.loads(raw or '{}')
                name = (data.get('name') or '').strip()
            else:
                try:
                    raw = request.body.decode('utf-8') if request.body else '{}'
                    data = json.loads(raw or '{}')
                    name = (data.get('name') or '').strip()
                except Exception:
                    name = (request.POST.get('name') or '').strip()
        except Exception:
            name = (request.POST.get('name') or '').strip()

        if not name:
            return JsonResponse({'success': False, 'message': 'Section name is required'})

        # Check if section name already exists for this teacher (excluding current section)
        if Section.objects.filter(teacher=request.user, name=name).exclude(id=section_id).exists():
            return JsonResponse({'success': False, 'message': 'A section with this name already exists'})

        section.name = name
        section.save()

        return JsonResponse({
            'success': True,
            'message': 'Section updated successfully!',
            'section': {
                'id': section.id,
                'name': section.name,
                'student_count': section.students.count()
            }
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error updating section: {str(e)}'
        }, status=500)


@login_required
@require_http_methods(["POST"])
def delete_section(request, section_id):
    """Delete a section"""
    if request.user.role != 'teacher':
        return JsonResponse({'success': False, 'message': 'Unauthorized'}, status=403)

    try:
        section = get_object_or_404(Section, id=section_id, teacher=request.user)
        section_name = section.name
        section.delete()

        return JsonResponse({
            'success': True,
            'message': f'Section "{section_name}" deleted successfully!'
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error deleting section: {str(e)}'
        }, status=500)


@login_required
@require_http_methods(["POST"])
def remove_student_from_section(request, section_id, user_id):
    """Unassign a student from a section (teacher only)"""
    if request.user.role != 'teacher':
        return JsonResponse({'success': False, 'message': 'Unauthorized'}, status=403)

    try:
        section = get_object_or_404(Section, id=section_id, teacher=request.user)
        student = get_object_or_404(User, id=user_id)

        # Verify student is assigned to this section
        if student.section_id != section.id:
            return JsonResponse({'success': False, 'message': 'Student is not in this section'})

        # Unassign student
        student.section = None
        student.save(update_fields=['section'])

        return JsonResponse({'success': True, 'message': f'Student {student.username} removed from section {section.name}'})

    except Exception as e:
        return JsonResponse({'success': False, 'message': f'Error removing student: {str(e)}'}, status=500)
