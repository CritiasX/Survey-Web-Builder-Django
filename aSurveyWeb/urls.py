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
]
