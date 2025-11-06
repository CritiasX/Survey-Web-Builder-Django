from django.db import models

# Create your models here.

class User(models.Model):
    user_id = models.AutoField(primary_key=True)
    username = models.CharField('username', max_length=30, unique=True)
    email = models.EmailField('email address', unique=True)
    password_hash = models.CharField('password', max_length=30)
    is_admin = models.BooleanField('admin', default=False)
    if is_admin == False:
        role = models.CharField('role', default='user', max_length=20)
    else:
        role = models.CharField('role', default='admin', max_length=20)
