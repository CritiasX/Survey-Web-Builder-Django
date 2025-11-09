from django.contrib import admin
from django.urls import path
from WebSurvey import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.landingPage, name='landing'),
    path('login/', views.loginPage, name='login'),
    path('about/', views.aboutPage, name='about'),
    path('contact/', views.contactPage, name='contact'),
    path('register/', views.registerPage, name='register'),
    path('dashboard/', views.dashboardPage, name='dashboard'),
    path('logout/', views.logoutPage, name='logout'),
    
    # Survey builder URLs
    path('surveys/', views.survey_list, name='survey_list'),
    path('surveys/create/', views.survey_builder, name='survey_create'),
    path('surveys/<int:survey_id>/edit/', views.survey_builder, name='survey_edit'),
    path('surveys/save/', views.save_survey, name='save_survey'),
    path('surveys/<int:survey_id>/data/', views.get_survey_data, name='get_survey_data'),
    path('surveys/<int:survey_id>/delete/', views.delete_survey, name='delete_survey'),
    
    # Section management URLs
    path('sections/', views.section_list, name='section_list'),
    path('sections/create/', views.create_section, name='create_section'),
    path('sections/<int:section_id>/edit/', views.edit_section, name='edit_section'),
    path('sections/<int:section_id>/delete/', views.delete_section, name='delete_section'),
    path('sections/<int:section_id>/remove-student/<int:user_id>/', views.remove_student_from_section, name='remove_student_from_section'),
]
