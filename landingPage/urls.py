from django.urls import path
from . import views

app_name = 'landingPage'


urlpatterns = [
    path('', views.landingPage, name='landing'),
    path('login/', views.loginPage, name='login'),
    path('about/', views.aboutPage, name='about'),
    path('contact/', views.contactPage, name='contact'),
]