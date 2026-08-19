import os
import sys
import django

sys.path.append('.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'autogarage.settings')
django.setup()

from django.contrib.auth.models import User
from core.models import (
    Customer, Vehicle, Supplier, SparePart, PartCategory,
    GarageSettings, Expense, JobCard
)

def fix_casing():
    print("Converting existing data formatting...")

    # 1. Users / Staff Names
    users_updated = 0
    for u in User.objects.all():
        changed = False
        if u.first_name and u.first_name != u.first_name.title():
            u.first_name = u.first_name.title()
            changed = True
        if u.last_name and u.last_name != u.last_name.title():
            u.last_name = u.last_name.title()
            changed = True
        if changed:
            u.save()
            users_updated += 1
    print(f"Updated {users_updated} User / Staff names.")

    # 2. Customers
    cust_updated = 0
    for c in Customer.objects.all():
        changed = False
        if c.name and c.name != c.name.title():
            c.name = c.name.title()
            changed = True
        if c.address and c.address != c.address.title():
            c.address = c.address.title()
            changed = True
        if changed:
            c.save()
            cust_updated += 1
    print(f"Updated {cust_updated} Customers.")

    # 3. Vehicles
    veh_updated = 0
    for v in Vehicle.objects.all():
        changed = False
        if v.make and v.make != v.make.title():
            v.make = v.make.title()
            changed = True
        if v.model and v.model != v.model.title():
            v.model = v.model.title()
            changed = True
        if v.color and v.color != v.color.title():
            v.color = v.color.title()
            changed = True
        if v.license_plate and v.license_plate != v.license_plate.upper():
            v.license_plate = v.license_plate.upper()
            changed = True
        if v.vin and v.vin != v.vin.upper():
            v.vin = v.vin.upper()
            changed = True
        if changed:
            v.save()
            veh_updated += 1
    print(f"Updated {veh_updated} Vehicles.")

    # 4. Suppliers
    sup_updated = 0
    for s in Supplier.objects.all():
        changed = False
        if s.name and s.name != s.name.title():
            s.name = s.name.title()
            changed = True
        if s.contact_person and s.contact_person != s.contact_person.title():
            s.contact_person = s.contact_person.title()
            changed = True
        if changed:
            s.save()
            sup_updated += 1
    print(f"Updated {sup_updated} Suppliers.")

    # 5. Spare Parts
    part_updated = 0
    for p in SparePart.objects.all():
        changed = False
        if p.name and p.name != p.name.title():
            p.name = p.name.title()
            changed = True
        if p.part_number and p.part_number != p.part_number.upper():
            p.part_number = p.part_number.upper()
            changed = True
        if changed:
            p.save()
            part_updated += 1
    print(f"Updated {part_updated} Spare Parts.")

    # 6. Part Categories
    cat_updated = 0
    for cat in PartCategory.objects.all():
        if cat.name and cat.name != cat.name.title():
            cat.name = cat.name.title()
            cat.save()
            cat_updated += 1
    print(f"Updated {cat_updated} Part Categories.")

    # 7. Garage Settings
    gs = GarageSettings.objects.first()
    if gs:
        if gs.name: gs.name = gs.name.title()
        if gs.tagline: gs.tagline = gs.tagline.title()
        if gs.city: gs.city = gs.city.title()
        if gs.state: gs.state = gs.state.title()
        if gs.gst_number: gs.gst_number = gs.gst_number.upper()
        gs.save()
        print("Updated Garage Settings branding details.")

    # 8. Expenses
    exp_updated = 0
    for e in Expense.objects.all():
        if e.title and e.title != e.title.title():
            e.title = e.title.title()
            e.save()
            exp_updated += 1
    print(f"Updated {exp_updated} Expenses.")

    print("\n✅ All existing data formatting updated successfully!")

if __name__ == '__main__':
    fix_casing()
