from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.db import transaction
from django.utils import timezone
from django.core.paginator import Paginator
from django.db.models import Q, Count
import json
import logging
from collections import Counter
from django.views.decorators.csrf import csrf_exempt
from .models import (
    User,
    Section,
    Survey,
    Question,
    MultipleChoiceOption,
    TrueFalseAnswer,
    EnumerationAnswer,
    QuestionContext,
    StudentResponse,
    QuestionAnswer,
)
from .services import auto_close_due_surveys, parse_due_date

logger = logging.getLogger(__name__)

# Create your views here.


def _get_student_survey_data(user):
    """Return collections used by student survey pages."""
    auto_close_due_surveys()
    section = user.section
    now = timezone.now()

    available_surveys = []
    pending_responses = []
    completed_responses = []
    responses_map = {}

    if section:
        base_surveys = (
            Survey.objects.filter(sections=section, status__in=['published', 'closed'])
            .select_related('teacher')
            .prefetch_related('questions')
            .distinct()
        )
        responses_qs = (
            StudentResponse.objects.filter(
                student=user,
                survey__sections=section,
                survey__status__in=['published', 'closed']
            )
            .select_related('survey', 'survey__teacher')
            .prefetch_related('survey__questions')
            .distinct()
        )

        for response in responses_qs:
            responses_map[response.survey_id] = response
            if response.is_submitted:
                completed_responses.append(response)
            else:
                pending_responses.append(response)

        for survey in base_surveys:
            # Set status flags first
            survey.is_overdue = bool(survey.due_date and survey.due_date < now)
            survey.is_closed = survey.status == 'closed'
            
            response = responses_map.get(survey.id)
            if response and response.is_submitted:
                continue
            survey.student_response = response
            survey.is_draft = bool(response and not response.is_submitted)
            available_surveys.append(survey)

    for response in pending_responses:
        survey = response.survey
        survey.is_overdue = bool(survey.due_date and survey.due_date < now)
        survey.is_closed = survey.status == 'closed'
        response.is_overdue = survey.is_overdue
        response.is_closed = survey.is_closed

    available_active_count = sum(1 for survey in available_surveys if not survey.is_overdue and not survey.is_closed)
    # Count only pending responses that are not closed
    pending_active_count = sum(1 for response in pending_responses if not response.is_overdue and not response.is_closed)

    context = {
        'student_section': section,
        'available_surveys': available_surveys,
        'pending_responses': pending_responses,
        'completed_responses': completed_responses,
        'available_survey_count': available_active_count,
        'pending_survey_count': pending_active_count,
        'completed_survey_count': len(completed_responses),
        'current_time': now,
    }
    return context


def _save_student_answers(response, survey, post_data):
    """Persist the student's answers for each question."""
    for question in survey.questions.all():
        answer, _ = QuestionAnswer.objects.get_or_create(
            response=response,
            question=question
        )
        field_name = f'question_{question.id}'

        if question.question_type in ['multiple_choice', 'likert']:
            option_id = post_data.get(field_name)
            if option_id:
                option = question.options.filter(id=option_id).first()
                answer.selected_option = option
            else:
                answer.selected_option = None
            answer.true_false_answer = None
            answer.text_answer = ''

        elif question.question_type == 'true_false':
            raw_value = post_data.get(field_name)
            if raw_value in ('true', 'false'):
                answer.true_false_answer = (raw_value == 'true')
            else:
                answer.true_false_answer = None
            answer.selected_option = None
            answer.text_answer = ''

        else:
            answer.text_answer = post_data.get(field_name, '').strip()
            answer.selected_option = None
            answer.true_false_answer = None

        answer.save()

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
    auto_close_due_surveys()
    user = request.user
    context = {
        'user': user,
        'role': user.role
    }

    if user.role == 'teacher':
        teacher_surveys = user.surveys.all().prefetch_related('questions', 'responses')
        context.update({
            'teacher_survey_count': teacher_surveys.count(),
            'teacher_response_count': StudentResponse.objects.filter(survey__teacher=user).count(),
            'teacher_surveys': teacher_surveys[:6]
        })
    else:
        context.update(_get_student_survey_data(user))

    return render(request, 'dashboard.html', context)

@login_required
def student_available_surveys(request):
    if request.user.role != 'student':
        messages.error(request, 'Only students can access this page.')
        return redirect('dashboard')

    # Get filter parameter - default to 'available' to show open surveys
    filter_type = request.GET.get('filter', 'available')
    
    context = {'user': request.user, 'current_filter': filter_type}
    survey_data = _get_student_survey_data(request.user)
    context.update(survey_data)
    
    # Apply filter to show different surveys based on dropdown selection
    if filter_type == 'available':
        # Show only published surveys that are not closed/overdue
        available_only = [s for s in survey_data['available_surveys'] 
                         if s.status == 'published' and not s.is_overdue and not s.is_closed]
        context['filtered_surveys'] = available_only
        context['filter_title'] = 'Available Surveys'
        context['is_response_list'] = False
    elif filter_type == 'pending':
        # Show only pending responses that are not closed
        pending_only = [r for r in survey_data['pending_responses'] 
                       if not r.is_overdue and not r.is_closed]
        context['filtered_surveys'] = pending_only
        context['filter_title'] = 'Pending Surveys'
        context['is_response_list'] = True
    elif filter_type == 'completed':
        context['filtered_surveys'] = survey_data['completed_responses']
        context['filter_title'] = 'Completed Surveys'
        context['is_response_list'] = True
    elif filter_type == 'closed':
        # Show only closed or overdue surveys
        closed_only = [s for s in survey_data['available_surveys'] 
                      if s.is_overdue or s.is_closed]
        context['filtered_surveys'] = closed_only
        context['filter_title'] = 'Closed Surveys'
        context['is_response_list'] = False
    else:  # 'all'
        # For 'all', show all surveys including open, closed, and those with responses
        all_surveys_list = []
        # Add all available surveys (both open and closed)
        all_surveys_list.extend(survey_data['available_surveys'])
        context['filtered_surveys'] = all_surveys_list
        context['filter_title'] = 'All Surveys'
        context['is_response_list'] = False
    
    return render(request, 'student_available_surveys.html', context)


@login_required
def student_pending_surveys(request):
    """Redirect to unified surveys page with pending filter"""
    return redirect('/student/surveys/?filter=pending')


@login_required
def student_completed_surveys(request):
    """Redirect to unified surveys page with completed filter"""
    return redirect('/student/surveys/?filter=completed')


@login_required
def _old_student_completed_surveys(request):
    if request.user.role != 'student':
        messages.error(request, 'Only students can access this page.')
        return redirect('dashboard')

    context = {'user': request.user}
    context.update(_get_student_survey_data(request.user))
    return render(request, 'student_completed_surveys.html', context)


@login_required
def student_history(request):
    """Display student's response history with ability to view individual responses."""
    if request.user.role != 'student':
        messages.error(request, 'Only students can access this page.')
        return redirect('dashboard')

    context = {'user': request.user}
    context.update(_get_student_survey_data(request.user))
    return render(request, 'student_history.html', context)


@login_required
def student_view_response(request, response_id):
    """Allow a student to review their submitted answers."""
    if request.user.role != 'student':
        messages.error(request, 'Only students can access this page.')
        return redirect('dashboard')

    response = get_object_or_404(
        StudentResponse.objects.select_related('survey', 'survey__teacher'),
        id=response_id,
        student=request.user,
        is_submitted=True
    )

    answers = (
        response.answers
        .select_related('question', 'selected_option')
        .prefetch_related('question__enumeration_answers')
        .order_by('question__order')
    )

    context = {
        'user': request.user,
        'response': response,
        'survey': response.survey,
        'answers': answers,
    }
    return render(request, 'student_view_response.html', context)

def logoutPage(request):
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('landing')


# Survey Builder Views
@login_required
def survey_list(request):
    """List all surveys for the teacher"""
    if request.user.role != 'teacher':
        messages.error(request, 'Only teachers can access this page.')
        return redirect('dashboard')

    auto_close_due_surveys()
    surveys = Survey.objects.filter(teacher=request.user)
    context = {
        'surveys': surveys,
        'user': request.user
    }
    return render(request, 'survey_list.html', context)


@login_required
def survey_builder(request, survey_id=None):
    """Survey builder page - create or edit survey"""
    if request.user.role != 'teacher':
        messages.error(request, 'Only teachers can access this page.')
        return redirect('dashboard')

    auto_close_due_surveys()
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
        try:
            raw = request.body.decode('utf-8') if request.body else '{}'
            data = json.loads(raw or '{}')
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error in save_survey: {e}")
            return JsonResponse({'success': False, 'message': f'Invalid JSON: {e}'}, status=400)

        survey_id = data.get('survey_id') or data.get('id')
        questions_provided = isinstance(data.get('questions'), list)

        logger.info(f"Saving survey - ID: {survey_id}, Questions provided: {questions_provided}, Questions count: {len(data.get('questions', []))}")

        with transaction.atomic():
            # Create or update survey
            if survey_id:
                survey = get_object_or_404(Survey, id=survey_id, teacher=request.user)
            else:
                survey = Survey(teacher=request.user)

            survey.title = data.get('title') or 'Untitled Survey'
            survey.description = data.get('description') or ''
            survey.status = data.get('status') or 'draft'

            # Time limit may come as string or null
            time_limit = data.get('time_limit')
            if time_limit in ("", None, "None"):
                survey.time_limit = None
            else:
                try:
                    survey.time_limit = int(time_limit)
                except (TypeError, ValueError):
                    survey.time_limit = None

            survey.due_date = parse_due_date(data.get('due_date'))
            survey.save()

            # Handle sections (ids may be strings)
            section_ids = data.get('sections') or []
            if section_ids:
                try:
                    section_ids_int = [int(sid) for sid in section_ids]
                except (TypeError, ValueError):
                    section_ids_int = []
                survey.sections.set(Section.objects.filter(id__in=section_ids_int, teacher=request.user))
            else:
                survey.sections.clear()

            if questions_provided:
                # When editing an existing survey, clear previous questions first
                if survey.pk:
                    survey.questions.all().delete()

                questions_data = data.get('questions') or []
                logger.info(f"Processing {len(questions_data)} questions")

                for idx, q_data in enumerate(questions_data):
                    try:
                        q_type = q_data.get('type') or q_data.get('question_type')
                        q_text = q_data.get('text') or q_data.get('question_text') or ''
                        if not q_type:
                            logger.warning(f"Question {idx} has no type, skipping")
                            continue

                        # Text elements (heading, subheading, paragraph) don't need points/required
                        is_text_element = q_type in ['heading', 'subheading', 'paragraph']

                        base_kwargs = {
                            'survey': survey,
                            'question_type': q_type,
                            'question_text': q_text,
                            'order': idx,
                        }

                        # Only add points and required for actual questions, not text elements
                        if not is_text_element:
                            base_kwargs['points'] = 0  # points removed for survey mode
                            base_kwargs['required'] = bool(q_data.get('required', True))
                        else:
                            base_kwargs['points'] = 0  # Text elements have no points
                            base_kwargs['required'] = False  # Text elements are not required

                        question = Question.objects.create(**base_kwargs)
                        logger.debug(f"Created question {idx}: {q_type} - {q_text[:50] if q_text else 'no text'}")

                        # Handle nested items for headings
                        if q_type == 'heading':
                            nested_items = q_data.get('nested_items', [])
                            if nested_items:
                                logger.debug(f"Processing {len(nested_items)} nested items for heading")
                                for nested_idx, nested_item in enumerate(nested_items):
                                    try:
                                        nested_type = nested_item.get('type')
                                        nested_text = nested_item.get('text', '')
                                        if nested_type in ['subheading', 'paragraph']:
                                            # Create nested text element as a separate question with a special marker
                                            Question.objects.create(
                                                survey=survey,
                                                question_type=nested_type,
                                                question_text=nested_text,
                                                points=0,
                                                order=idx + 0.001 * (nested_idx + 1),  # Fractional order to maintain nesting
                                                required=False,
                                            )
                                    except Exception as nested_error:
                                        logger.error(f"Error saving nested item: {nested_error}")

                        # Only process question-specific data for actual questions
                        if not is_text_element:
                            if q_type in ['multiple_choice', 'likert']:
                                options = q_data.get('options') or []
                                if not options:
                                    logger.warning(f"{q_type} question {idx} has no options")
                                for opt_idx, option in enumerate(options):
                                    MultipleChoiceOption.objects.create(
                                        question=question,
                                        option_text=option.get('text', ''),
                                        is_correct=bool(option.get('is_correct') or option.get('correct')) if q_type == 'multiple_choice' else False,
                                        order=opt_idx,
                                    )

                            elif q_type == 'true_false':
                                TrueFalseAnswer.objects.create(
                                    question=question,
                                    is_true=bool(q_data.get('correct_answer', True)),
                                )

                            elif q_type == 'enumeration':
                                answers = q_data.get('answers') or []
                                if not answers:
                                    logger.warning(f"Enumeration question {idx} has no answers")
                                for ans_idx, answer in enumerate(answers):
                                    EnumerationAnswer.objects.create(
                                        question=question,
                                        answer_text=str(answer),
                                        order=ans_idx,
                                    )

                        # Save context items (code snippets and images)
                        context_items = q_data.get('context_items', [])
                        if context_items:
                            logger.debug(f"Saving {len(context_items)} context items for question {idx}")
                            for ctx_item in context_items:
                                try:
                                    QuestionContext.objects.create(
                                        question=question,
                                        context_type=ctx_item.get('type', 'code_snippet'),
                                        content=ctx_item.get('content', ''),
                                        language=ctx_item.get('language', ''),
                                        order=ctx_item.get('order', 0)
                                    )
                                except Exception as ctx_error:
                                    logger.error(f"Error saving context item: {ctx_error}")

                    except Exception as q_error:
                        logger.error(f"Error processing question {idx} (type: {q_type if 'q_type' in locals() else 'unknown'}): {q_error}")
                        import traceback
                        logger.error(traceback.format_exc())
                        # Continue processing other questions instead of failing entire save
                        continue

                # Safely recalculate total points
                try:
                    survey.calculate_total_points()
                except Exception as calc_error:
                    logger.warning(f"Could not calculate total points: {calc_error}")
                    pass

            return JsonResponse({
                'success': True,
                'message': 'Survey saved successfully!',
                'survey_id': survey.id,
            })

    except Exception as e:
        import traceback
        error_traceback = traceback.format_exc()
        logger.error(f"Error saving survey: {e}\n{error_traceback}")
        return JsonResponse({'success': False, 'message': f'Error saving survey: {str(e)}'}, status=500)


@login_required
@require_http_methods(["GET"])
def get_survey_data(request, survey_id):
    """AJAX endpoint to get survey data for editing"""
    if request.user.role != 'teacher':
        return JsonResponse({'success': False, 'message': 'Unauthorized'}, status=403)

    try:
        auto_close_due_surveys()
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

            if question.question_type in ['multiple_choice', 'likert']:
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
            
            # Include context items
            if hasattr(question, 'context_items'):
                q_data['context_items'] = [
                    {
                        'type': ctx.context_type,
                        'content': ctx.content,
                        'language': ctx.language,
                        'order': ctx.order
                    }
                    for ctx in question.context_items.all()
                ]

            questions_data.append(q_data)

        survey_data = {
            'id': survey.id,
            'title': survey.title,
            'description': survey.description,
            'status': survey.status,
            'time_limit': survey.time_limit,
            'due_date': survey.due_date.isoformat() if survey.due_date else None,
            'sections': list(survey.sections.values_list('id', flat=True)),
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
def take_survey(request, survey_id):
    """Allow a student to answer a survey assigned to their section."""
    if request.user.role != 'student':
        messages.error(request, 'Only students can access this page.')
        return redirect('dashboard')

    auto_close_due_surveys()
    survey = get_object_or_404(
        Survey.objects.select_related('teacher')
        .prefetch_related('questions__options', 'questions__enumeration_answers', 'questions__context_items'),
        id=survey_id,
        status__in=['published', 'closed']
    )
    section = request.user.section

    if not section or not survey.sections.filter(id=section.id).exists():
        messages.error(request, 'This survey is not assigned to your section.')
        return redirect('student_available_surveys')

    if survey.status == 'closed':
        messages.error(request, 'This survey is already closed.')
        return redirect('student_available_surveys')

    response = StudentResponse.objects.filter(survey=survey, student=request.user).select_related('survey').first()
    if response and response.is_submitted:
        messages.info(request, 'You have already submitted this survey.')
        return redirect('student_completed_surveys')

    if request.method == 'POST':
        response, _ = StudentResponse.objects.get_or_create(
            survey=survey,
            student=request.user,
            defaults={'is_submitted': False}
        )
        action = request.POST.get('action', 'draft')
        _save_student_answers(response, survey, request.POST)

        if action == 'submit':
            missing_required = []
            for question in survey.questions.all():
                if not question.required:
                    continue
                answer = response.answers.filter(question=question).first()
                if not answer:
                    missing_required.append(question)
                    continue

                if question.question_type in ['multiple_choice', 'likert']:
                    if not answer.selected_option_id:
                        missing_required.append(question)
                elif question.question_type == 'true_false':
                    if answer.true_false_answer is None:
                        missing_required.append(question)
                else:
                    if not answer.text_answer.strip():
                        missing_required.append(question)

            if missing_required:
                messages.error(request, 'Please answer all required questions before submitting.')
                return redirect('take_survey', survey_id=survey.id)

            response.is_submitted = True
            response.submitted_at = timezone.now()
            response.save(update_fields=['is_submitted', 'submitted_at'])
            messages.success(request, 'Survey submitted successfully!')
            return redirect('student_completed_surveys')
        else:
            response.is_submitted = False
            response.submitted_at = None
            response.save(update_fields=['is_submitted', 'submitted_at'])
            messages.success(request, 'Draft saved.')
            return redirect('student_pending_surveys')

    answer_map = {}
    if response:
        for answer in response.answers.select_related('selected_option'):
            answer_map[answer.question_id] = answer

    questions = list(survey.questions.all())
    for question in questions:
        question.existing_answer = answer_map.get(question.id)

    context = {
        'user': request.user,
        'survey': survey,
        'student_section': section,
        'response': response,
        'questions': questions,
    }
    return render(request, 'student_take_survey.html', context)


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
    
@login_required
def response_management(request):
    """Table of student submissions with search + date filter + section filter + pagination"""
    teacher = request.user

    search_query = request.GET.get("search", "")
    date_filter = request.GET.get("date", "")
    section_filter = request.GET.get("section", "")

    # Explicit ordering fixes pagination warning
    responses = StudentResponse.objects.filter(
        survey__teacher=teacher,
        is_submitted=True
    ).select_related("student", "survey", "student__section").order_by('-submitted_at')

    if search_query:
        responses = responses.filter(
            Q(student__username__icontains=search_query) |
            Q(student__first_name__icontains=search_query) |
            Q(student__last_name__icontains=search_query) |
            Q(survey__title__icontains=search_query)
        )

    if date_filter:
        responses = responses.filter(submitted_at__date=date_filter)
    
    if section_filter:
        responses = responses.filter(student__section_id=section_filter)

    paginator = Paginator(responses, 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)
    
    # Get unique surveys with responses for analytics dropdown
    surveys_with_responses = Survey.objects.filter(
        teacher=teacher,
        responses__is_submitted=True
    ).distinct().order_by('-created_at')
    
    # Get all sections for this teacher
    sections = Section.objects.filter(teacher=teacher).order_by('name')

    return render(request, "responses.html", {
        "page_obj": page_obj,
        "search_query": search_query,
        "date_filter": date_filter,
        "section_filter": section_filter,
        "surveys_with_responses": surveys_with_responses,
        "sections": sections,
    })


def response_detail(request, pk):
    response = get_object_or_404(StudentResponse, pk=pk)
    answers = QuestionAnswer.objects.filter(response=response).order_by('question__order')
    
    context = {
        'response': response,
        'answers': answers
    }
    return render(request, 'response_detail.html', context)


@login_required
@login_required
def survey_analytics(request, survey_id):
    """Analytics page with pie charts, bar charts, and word clouds using Chart.js"""
    survey = get_object_or_404(Survey, id=survey_id, teacher=request.user)
    
    # Get all submitted responses for this survey
    responses = StudentResponse.objects.filter(
        survey=survey,
        is_submitted=True
    ).select_related('student')
    
    # Get all questions for this survey
    questions = survey.questions.all().prefetch_related(
        'options',
        'true_false_answer',
        'enumeration_answers'
    )
    
    charts_data = []
    
    for question in questions:
        chart_info = {
            'question_text': question.question_text,
            'type': question.question_type,
            'data': {}
        }
        
        # Get all answers for this question
        answers = QuestionAnswer.objects.filter(
            question=question,
            response__in=responses
        )
        
        if question.question_type in ['multiple_choice', 'likert']:
            # Prepare data for pie chart and bar chart
            labels = []
            values = []
            for option in question.options.all():
                count = answers.filter(selected_option=option).count()
                labels.append(option.option_text)
                values.append(count)
            
            if sum(values) > 0:
                chart_info['data'] = {
                    'labels': labels,
                    'values': values
                }
        
        elif question.question_type == 'true_false':
            # Prepare data for true/false pie chart
            true_count = answers.filter(true_false_answer=True).count()
            false_count = answers.filter(true_false_answer=False).count()
            
            if true_count + false_count > 0:
                chart_info['data'] = {
                    'labels': ['True', 'False'],
                    'values': [true_count, false_count]
                }
        
        elif question.question_type == 'essay':
            # Prepare word frequency data for word cloud
            text_answers = answers.exclude(text_answer='').values_list('text_answer', flat=True)
            
            if text_answers:
                # Combine all text and count word frequencies
                combined_text = ' '.join(text_answers).lower()
                words = combined_text.split()
                # Filter out common words
                stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 
                             'of', 'with', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
                             'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
                             'should', 'may', 'might', 'must', 'can', 'this', 'that', 'these', 'those'}
                words = [w for w in words if w not in stop_words and len(w) > 2]
                word_freq = Counter(words)
                top_words = word_freq.most_common(50)
                
                chart_info['data'] = {
                    'words': [{'text': word, 'size': count} for word, count in top_words],
                    'total_responses': len(text_answers)
                }
        
        elif question.question_type == 'enumeration':
            # Prepare word frequency data for enumeration
            text_answers = answers.exclude(text_answer='').values_list('text_answer', flat=True)
            
            if text_answers:
                combined_text = ' '.join(text_answers).lower()
                words = combined_text.split()
                stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
                             'of', 'with', 'is', 'are', 'was', 'were', 'be', 'been', 'being'}
                words = [w for w in words if w not in stop_words and len(w) > 2]
                word_freq = Counter(words)
                top_words = word_freq.most_common(50)
                
                chart_info['data'] = {
                    'words': [{'text': word, 'size': count} for word, count in top_words],
                    'total_responses': len(text_answers)
                }
        
        if chart_info['data']:
            charts_data.append(chart_info)
    
    context = {
        'survey': survey,
        'charts_data': json.dumps(charts_data),
        'total_responses': responses.count(),
    }
    
    return render(request, 'survey_analytics.html', context)


@login_required
def overall_analytics(request):
    """Simple overall analytics page showing combined data from all surveys with pagination"""
    if request.user.role != 'teacher':
        messages.error(request, "Access denied. Teacher account required.")
        return redirect('dashboard')
    
    teacher = request.user
    
    # Get all surveys and responses
    total_surveys = Survey.objects.filter(teacher=teacher).count()
    total_responses = StudentResponse.objects.filter(
        survey__teacher=teacher,
        is_submitted=True
    ).count()
    
    # Get surveys with their response counts
    surveys = Survey.objects.filter(teacher=teacher).annotate(
        response_count=Count('responses', filter=Q(responses__is_submitted=True))
    ).order_by('-created_at')
    
    # Paginate surveys
    paginator = Paginator(surveys, 10)  # 10 surveys per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'total_surveys': total_surveys,
        'total_responses': total_responses,
        'page_obj': page_obj,
    }
    
    return render(request, 'overall_analytics.html', context)
