from django.test import Client
c=Client()
r=c.get('/register/')
text = r.content.decode('utf-8')
with open('tools/register_preview.html','w', encoding='utf-8') as f:
    f.write(text)
print('WROTE tools/register_preview.html, len=', len(text))

