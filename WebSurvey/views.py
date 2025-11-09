from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from .models import User, Section

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
    context = {
        'user': request.user,
        'role': request.user.role
    }
    return render(request, 'dashboard.html', context)

def logoutPage(request):
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('landing')
