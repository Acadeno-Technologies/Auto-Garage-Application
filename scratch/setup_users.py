import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'autogarage.settings')
django.setup()

from django.contrib.auth.models import User
from core.models import UserProfile

# Create Owner / Admin user
username = "admin"
password = "admin135"
email = "admin@autogarage.com"

user, created = User.objects.get_or_create(username=username, defaults={'email': email, 'is_staff': True, 'is_superuser': True})
if created or not user.check_password(password):
    user.set_password(password)
    user.save()

profile, p_created = UserProfile.objects.get_or_create(user=user, defaults={'role': 'owner'})
if profile.role != 'owner':
    profile.role = 'owner'
    profile.save()

print(f"SUCCESS: User '{username}' with password '{password}' and role '{profile.role}' created/updated successfully.")
