from django.template.loader import get_template
import sys

templates = ['reuseable/header.html','loginPage.html','registerPage.html','landingPage.html']
for t in templates:
    try:
        get_template(t)
        print(t, 'OK')
    except Exception as e:
        print(t, 'ERROR', type(e).__name__)
        print(str(e))
        sys.exit(1)
print('ALL_TEMPLATES_LOADED')

