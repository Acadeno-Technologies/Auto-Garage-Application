import os
import sys
import django

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "autogarage.settings")
django.setup()

from core.models import Vehicle

def run():
    print("--- Checking and Fixing Duplicate Vehicle VINs in Database ---")
    seen_vins = {}
    fixed_count = 0
    
    vehicles = Vehicle.objects.all().order_by('id')
    for v in vehicles:
        if not v.vin:
            continue
        vin_upper = v.vin.strip().upper()
        if vin_upper in seen_vins:
            first_v = seen_vins[vin_upper]
            print(f"Duplicate VIN found: '{vin_upper}' on Vehicle ID {v.id} ({v.make} {v.model}, Owner: {v.customer.name})")
            print(f"  --> Original Owner: {first_v.customer.name} (Vehicle ID {first_v.id})")
            # Clear or differentiate duplicate sample VIN
            v.vin = f"{vin_upper[:-2]}{v.id:02d}"
            v.save()
            print(f"  --> Updated Vehicle ID {v.id} VIN to '{v.vin}'")
            fixed_count += 1
        else:
            seen_vins[vin_upper] = v
            
    print(f"\nDone! Corrected {fixed_count} duplicate VIN records in database.")

if __name__ == '__main__':
    run()
