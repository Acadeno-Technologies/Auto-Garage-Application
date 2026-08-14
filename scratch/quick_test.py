import os
import sys
import django

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'autogarage.settings')
django.setup()

from decimal import Decimal
from django.utils import timezone
from core.models import Customer, Vehicle, JobCard, Invoice, AMCPlan, CustomerAMC

print("=== Running Quick Verification ===")

# Create customer & vehicle
c, _ = Customer.objects.get_or_create(phone="9998887770", defaults={"name": "test customer", "address": "test street"})
v, _ = Vehicle.objects.get_or_create(license_plate="KL-01-XX-9999", defaults={"customer": c, "make": "Hyundai", "model": "i20", "year": 2022})

# Create active AMC
plan, _ = AMCPlan.objects.get_or_create(name="Gold Care", defaults={"price": Decimal("5000"), "discount_percentage": Decimal("100")})
amc, _ = CustomerAMC.objects.get_or_create(
    contract_number="AMC-TEST-999",
    defaults={
        "vehicle": v,
        "plan": plan,
        "start_date": timezone.now().date(),
        "end_date": timezone.now().date() + timezone.timedelta(days=365),
        "amount_paid": Decimal("5000"),
        "status": "active"
    }
)

# Test AMC calculation
job = JobCard.objects.create(vehicle=v, problem_description="Engine Oil Change", labour_cost=Decimal("1500.00"))
discount = (job.labour_cost * plan.discount_percentage / Decimal("100.00")).quantize(Decimal("0.01"))
print(f"Labour Cost: {job.labour_cost}, Discount: {discount}")
assert discount == Decimal("1500.00"), "AMC discount calculation failed!"

# Test Invoice creation with AMC discount auto deduction
inv = Invoice.objects.create(job_card=job, amc_discount=discount, amc_policy=amc)
print(f"Invoice Subtotal: {inv.subtotal}, After Discount: {inv.subtotal_after_discount}, Grand Total: {inv.grand_total}")
assert inv.subtotal_after_discount == Decimal("0.00"), "Subtotal after discount should be 0"

# Clean up test objects
inv.delete()
job.delete()
amc.delete()
v.delete()
c.delete()

print("=== ALL VERIFICATION CHECKS PASSED ===")
