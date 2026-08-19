import os
import sys
import django

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "autogarage.settings")
django.setup()

from django.contrib.auth.models import User
from core.models import Customer, Supplier, GarageSettings, JobCard

TYPO_MAP = {
    'gmai.com': 'gmail.com',
    'gamil.com': 'gmail.com',
    'gmial.com': 'gmail.com',
    'gmaill.com': 'gmail.com',
    'gmal.com': 'gmail.com',
    'yaho.com': 'yahoo.com',
    'yahooo.com': 'yahoo.com',
    'hotmai.com': 'hotmail.com',
    'outloo.com': 'outlook.com',
    'outlok.com': 'outlook.com',
    'iclou.com': 'icloud.com'
}

def fix_email_str(email):
    if not email:
        return email
    email = email.strip().lower()
    if '@' in email:
        prefix, domain = email.split('@', 1)
        if domain in TYPO_MAP:
            return f"{prefix}@{TYPO_MAP[domain]}"
    return email

def run():
    print("--- Cleaning & Fixing Database Email Records ---")
    
    # 1. Users
    user_count = 0
    for u in User.objects.all():
        old_email = u.email
        new_email = fix_email_str(old_email)
        if old_email != new_email:
            u.email = new_email
            u.save()
            print(f"Fixed User '{u.username}': {old_email} -> {new_email}")
            user_count += 1
            
    # 2. Customers
    cust_count = 0
    for c in Customer.objects.all():
        old_email = c.email
        new_email = fix_email_str(old_email)
        if old_email != new_email:
            c.email = new_email
            c.save()
            print(f"Fixed Customer '{c.name}': {old_email} -> {new_email}")
            cust_count += 1

    # 3. Suppliers
    sup_count = 0
    for s in Supplier.objects.all():
        old_email = s.email
        new_email = fix_email_str(old_email)
        if old_email != new_email:
            s.email = new_email
            s.save()
            print(f"Fixed Supplier '{s.name}': {old_email} -> {new_email}")
            sup_count += 1

    # 4. Garage Settings
    gs_count = 0
    for g in GarageSettings.objects.all():
        old_email = g.email
        new_email = fix_email_str(old_email)
        if old_email != new_email:
            g.email = new_email
            g.save()
            print(f"Fixed GarageSettings '{g.name}': {old_email} -> {new_email}")
            gs_count += 1

    print(f"\nDone! Corrected {user_count} Users, {cust_count} Customers, {sup_count} Suppliers, {gs_count} Garage Settings.")

if __name__ == '__main__':
    run()
