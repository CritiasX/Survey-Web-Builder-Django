import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'aSurveyWeb.settings')
django.setup()
from django.urls import reverse

print('landing ->', reverse('landingPage:landing'))
print('about   ->', reverse('landingPage:about'))
print('contact ->', reverse('landingPage:contact'))
print('login   ->', reverse('landingPage:login'))

