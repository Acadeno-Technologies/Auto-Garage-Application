import os
import sys
import django
from datetime import date, timedelta
from decimal import Decimal

# Set up Django environment
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'autogarage.settings')
django.setup()

from core.models import Customer, Vehicle, AMCPlan, CustomerAMC, AMCServiceSchedule, JobCard, Invoice
from core.forms import AMCPlanForm, CustomerAMCForm
from core.views import add_months

def run_test():
    print("==================================================")
    print("STARTING COMPLETE AMC WORKFLOW AUTOMATED TEST")
    print("==================================================")

    # 1. Create AMC Plan
    plan, created = AMCPlan.objects.get_or_create(
        name="Basic AMC Test",
        defaults={
            'description': "Annual scheduled maintenance package test",
            'price': Decimal('2500.00'),
            'duration_months': 12,
            'services_included': 4,
            'service_interval_months': 3,
            'discount_percentage': Decimal('100.00'),
            'is_active': True
        }
    )
    print(f"[OK] Step 1: AMC Plan Created -> {plan}")

    # 2. Create Customer
    customer, created = Customer.objects.get_or_create(
        phone="9988776655",
        defaults={
            'name': "Rahul Kumar Test",
            'email': "rahul.test@gmail.com",
            'address': "Kochi, Kerala"
        }
    )
    print(f"[OK] Step 2: Customer Created -> {customer.name} ({customer.phone})")

    # 3. Create Two Vehicles
    v1, _ = Vehicle.objects.get_or_create(
        license_plate="KL-11-AB-1234",
        defaults={
            'customer': customer,
            'make': "Honda",
            'model': "City",
            'year': 2022,
            'color': "White"
        }
    )
    v2, _ = Vehicle.objects.get_or_create(
        license_plate="KL-11-CD-5678",
        defaults={
            'customer': customer,
            'make': "Hyundai",
            'model': "Creta",
            'year': 2023,
            'color': "Black"
        }
    )
    print(f"[OK] Step 3: Vehicles Created -> {v1.license_plate} (Honda City) & {v2.license_plate} (Hyundai Creta)")

    # Clean up previous test AMCs for clean state
    CustomerAMC.objects.filter(vehicle__in=[v1, v2]).delete()

    # 4. Create AMC for Honda City (KL-11-AB-1234)
    start_d = date(2026, 8, 19)
    end_d = add_months(start_d, plan.duration_months) - timedelta(days=1)
    
    amc1 = CustomerAMC.objects.create(
        vehicle=v1,
        plan=plan,
        start_date=start_d,
        end_date=end_d,
        amount_paid=Decimal('2500.00'),
        status='active'
    )
    # Generate 4 scheduled services
    for i in range(1, plan.services_included + 1):
        sched_d = start_d if i == 1 else add_months(start_d, plan.service_interval_months * (i - 1))
        AMCServiceSchedule.objects.create(
            amc=amc1,
            service_number=i,
            scheduled_date=sched_d,
            status='upcoming'
        )
    print(f"[OK] Step 4: AMC Contract Created for Honda City -> {amc1.contract_number} (Valid: {amc1.start_date} to {amc1.end_date})")

    # 5. Verify Honda City has AMC & Hyundai Creta has NO AMC
    v1_has_amc = CustomerAMC.objects.filter(vehicle=v1, status='active').exists()
    v2_has_amc = CustomerAMC.objects.filter(vehicle=v2, status='active').exists()
    assert v1_has_amc is True, "Honda City should have an active AMC!"
    assert v2_has_amc is False, "Hyundai Creta should NOT have an active AMC!"
    print(f"[OK] Step 5: AMC Status Verified: Honda City (Active: {v1_has_amc}), Hyundai Creta (Active: {v2_has_amc})")

    # 6. Verify Service Schedules
    schedules = amc1.schedules.order_by('service_number')
    print("[OK] Step 6: Generated Service Schedules:")
    for s in schedules:
        print(f"   - Service #{s.service_number} -> Due: {s.scheduled_date} (Status: {s.computed_status})")
    assert schedules.count() == 4, "Should generate 4 scheduled services!"

    # 7. Create Job Card for Honda City & Attach AMC Service #1
    svc1 = schedules.first()
    jc1 = JobCard.objects.create(
        vehicle=v1,
        problem_description="Periodic Engine Oil Service",
        status='pending',
        labour_cost=Decimal('500.00'),
        amc_service=svc1
    )
    print(f"[OK] Step 7: Job Card Created -> {jc1.job_number} for {v1.license_plate} attached to AMC Service #1")

    # Before completion: Service #1 is NOT completed yet, used_services = 0
    assert amc1.used_services == 0, "Used services should be 0 before completing job card!"
    assert amc1.remaining_services == 4, "Remaining services should be 4 before completing job card!"
    print(f"[OK] Step 7.1: Pre-completion usage verified -> Used: {amc1.used_services}, Remaining: {amc1.remaining_services}")

    # 8. Mark Job Card 1 as Completed
    jc1.status = 'completed'
    jc1.save()
    amc1.refresh_from_db()
    svc1.refresh_from_db()

    assert svc1.status == 'completed', "AMC Service #1 status should be updated to completed!"
    assert amc1.used_services == 1, "Used services should be 1 after completing job card!"
    assert amc1.remaining_services == 3, "Remaining services should be 3 after completing job card!"
    print(f"[OK] Step 8: Post-completion usage verified -> Used: {amc1.used_services}, Remaining: {amc1.remaining_services}, Service #1 Status: {svc1.status}")

    # 9. Test Overlapping AMC Contract Prevention
    form = CustomerAMCForm(data={
        'vehicle': v1.id,
        'plan': plan.id,
        'start_date': '2026-10-15', # overlaps with 2026-08-19 to 2027-08-18
        'amount_paid': '2500.00'
    })
    is_valid = form.is_valid()
    assert is_valid is False, "Overlapping contract form submission should fail validation!"
    print(f"[OK] Step 9: Overlapping AMC Contract Prevention Verified -> Form Rejected with error: {form.non_field_errors()}")

    # 10. Test Renewal
    old_end = amc1.end_date
    new_start = old_end + timedelta(days=1)
    new_end = add_months(new_start, plan.duration_months) - timedelta(days=1)

    renewed_amc = CustomerAMC.objects.create(
        vehicle=v1,
        plan=plan,
        previous_contract=amc1,
        start_date=new_start,
        end_date=new_end,
        amount_paid=Decimal('2500.00'),
        status='active'
    )
    for i in range(1, plan.services_included + 1):
        sched_d = new_start if i == 1 else add_months(new_start, plan.service_interval_months * (i - 1))
        AMCServiceSchedule.objects.create(
            amc=renewed_amc,
            service_number=i,
            scheduled_date=sched_d,
            status='upcoming'
        )
    print(f"[OK] Step 10: Renewal Contract Created -> {renewed_amc.contract_number} (Previous: {renewed_amc.previous_contract.contract_number})")
    assert amc1.schedules.filter(status='completed').count() == 1, "Old contract service history must remain intact!"
    print(f"✓ Step 10.1: Old Contract Service History Retained -> {amc1.schedules.filter(status='completed').count()} Completed")

    print("==================================================")
    print("ALL 10 VERIFICATION STEPS PASSED SUCCESSFULLY!")
    print("==================================================")

if __name__ == '__main__':
    run_test()
