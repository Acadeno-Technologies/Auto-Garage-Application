import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'autogarage.settings')
django.setup()

from django.test import Client
from django.contrib.auth.models import User
from core.models import Customer, Vehicle, JobCard

def run_tests():
    print("==========================================")
    print("RUNNING JOB CARD WORKFLOW VERIFICATION TEST")
    print("==========================================")

    # Clean up prior test records for idempotency
    JobCard.objects.filter(problem_description__in=['Brake inspection and oil change', 'Engine noise investigation', 'AC cooling issue', 'Wheel alignment']).delete()
    Customer.objects.filter(phone__in=["9999900001", "9888800002", "9777700003"]).delete()
    Vehicle.objects.filter(license_plate__in=["KA01AB1111", "MH12CD2222", "DL03EF3333", "KA04GH4444"]).delete()

    client = Client()
    # Create or get test user
    user, _ = User.objects.get_or_create(username="test_advisor", defaults={"is_staff": True})
    user.set_password("password123")
    user.save()

    # Login advisor user
    logged_in = client.login(username="test_advisor", password="password123")
    print(f"User login status: {logged_in}")

    # TEST 1 & 8: Existing Customer + Existing Vehicle
    c1, _ = Customer.objects.get_or_create(phone="9999900001", defaults={"name": "Alice Smith"})
    v1, _ = Vehicle.objects.get_or_create(license_plate="KA01AB1111", defaults={"customer": c1, "make": "Toyota", "model": "Corolla", "year": 2022})
    
    post_data_1 = {
        'customer_name': 'Alice Smith',
        'customer_phone': '9999900001',
        'vehicle_number': 'KA01AB1111',
        'vehicle_model': 'Toyota Corolla',
        'vehicle_color': 'White',
        'problem_description': 'Brake inspection and oil change',
        'repair_instructions': 'Replace front brake pads',
        'labour_cost': '500.00',
    }
    response_1 = client.post('/jobs/create/', post_data_1)
    print(f"\n[Test 1] Existing Customer + Existing Vehicle Response Code: {response_1.status_code}")
    assert response_1.status_code == 302, "Expected redirect on successful Job Card creation"
    jc1 = JobCard.objects.filter(vehicle__license_plate='KA01AB1111', problem_description='Brake inspection and oil change').first()
    assert jc1 is not None, "Job Card 1 should exist in DB"
    print(f"✓ Job Card Created: {jc1.job_number} for Vehicle {jc1.vehicle.license_plate} (Customer: {jc1.vehicle.customer.name})")

    # TEST 2: New Customer + New Vehicle
    post_data_2 = {
        'customer_name': 'Bob Marley',
        'customer_phone': '9888800002',
        'vehicle_number': 'MH12CD2222',
        'vehicle_model': 'Honda Civic',
        'vehicle_color': 'Black',
        'problem_description': 'Engine noise investigation',
        'repair_instructions': 'Check timing belt',
        'labour_cost': '1200.00',
    }
    response_2 = client.post('/jobs/create/', post_data_2)
    print(f"\n[Test 2] New Customer + New Vehicle Response Code: {response_2.status_code}")
    assert response_2.status_code == 302
    c2 = Customer.objects.filter(phone="9888800002").first()
    assert c2 is not None and c2.name == "Bob Marley", "New Customer should be created"
    v2 = Vehicle.objects.filter(license_plate="MH12CD2222").first()
    assert v2 is not None and v2.customer == c2, "New Vehicle should be linked to New Customer"
    print(f"✓ New Customer ({c2.name}) and New Vehicle ({v2.license_plate}) created and associated successfully")

    # TEST 3: Existing Customer + New Vehicle
    post_data_3 = {
        'customer_name': 'Alice Smith',
        'customer_phone': '9999900001',
        'vehicle_number': 'DL03EF3333',
        'vehicle_model': 'Hyundai i20',
        'vehicle_color': 'Red',
        'problem_description': 'AC cooling issue',
        'repair_instructions': 'Gas refill',
        'labour_cost': '800.00',
    }
    response_3 = client.post('/jobs/create/', post_data_3)
    print(f"\n[Test 3] Existing Customer + New Vehicle Response Code: {response_3.status_code}")
    assert response_3.status_code == 302
    v3 = Vehicle.objects.filter(license_plate="DL03EF3333").first()
    assert v3 is not None and v3.customer == c1, "New Vehicle should be associated with existing Customer c1"
    print(f"✓ Existing Customer ({c1.name}) associated with new Vehicle ({v3.license_plate})")

    # TEST 4: Invalid Phone Number (Form validation failure)
    post_data_4 = {
        'customer_name': 'Charlie',
        'customer_phone': '123', # Invalid short phone
        'vehicle_number': 'KA04GH4444',
        'vehicle_model': 'Ford EcoSport',
        'problem_description': 'General service',
    }
    response_4 = client.post('/jobs/create/', post_data_4)
    print(f"\n[Test 4] Invalid Phone Number Response Code: {response_4.status_code}")
    assert response_4.status_code == 200 # Re-renders form with error
    print("✓ Form correctly rejected invalid phone number")

    # TEST 5: Invalid Vehicle Number (Form validation failure)
    post_data_5 = {
        'customer_name': 'Charlie',
        'customer_phone': '9777700003',
        'vehicle_number': 'A', # Invalid short vehicle num
        'vehicle_model': 'Ford EcoSport',
        'problem_description': 'General service',
    }
    response_5 = client.post('/jobs/create/', post_data_5)
    print(f"\n[Test 5] Invalid Vehicle Number Response Code: {response_5.status_code}")
    assert response_5.status_code == 200 # Re-renders form with error
    print("✓ Form correctly rejected invalid vehicle number")

    # TEST 6: Existing Vehicle belonging to another customer
    # vehicle DL03EF3333 currently belongs to c1 (Alice). Now Bob creates job card for DL03EF3333.
    post_data_6 = {
        'customer_name': 'Bob Marley',
        'customer_phone': '9888800002', # Bob's phone
        'vehicle_number': 'DL03EF3333',
        'vehicle_model': 'Hyundai i20',
        'vehicle_color': 'Red',
        'problem_description': 'Wheel alignment',
        'labour_cost': '300.00',
    }
    response_6 = client.post('/jobs/create/', post_data_6)
    print(f"\n[Test 6] Existing Vehicle re-association Response Code: {response_6.status_code}")
    assert response_6.status_code == 302
    v3.refresh_from_db()
    assert v3.customer == c2, "Vehicle should be re-associated to Bob Marley"
    print(f"✓ Vehicle ({v3.license_plate}) successfully re-associated from Alice to Bob ({v3.customer.name})")

    # TEST 7: Duplicate Job Card Prevention (rapid resubmission)
    response_7 = client.post('/jobs/create/', post_data_6)
    print(f"\n[Test 7] Duplicate Prevention Response Code: {response_7.status_code}")
    assert response_7.status_code == 302
    jc_count = JobCard.objects.filter(vehicle=v3, problem_description='Wheel alignment').count()
    assert jc_count == 1, f"Expected 1 job card, found {jc_count}"
    print("✓ Duplicate Job Card creation prevented within 15 seconds window")

    # TEST API Search Endpoint
    api_res_phone = client.get('/api/search-records/?phone=9888800002')
    data_phone = api_res_phone.json()
    assert data_phone['customer_found'] == True
    print(f"\n[API Test] Phone Search API returned Customer: {data_phone['customer']['name']} with {len(data_phone['customer']['vehicles'])} vehicle(s)")

    api_res_vehicle = client.get('/api/search-records/?vehicle_number=KA01AB1111')
    data_vehicle = api_res_vehicle.json()
    assert data_vehicle['vehicle_found'] == True
    print(f"[API Test] Vehicle Search API returned Vehicle: {data_vehicle['vehicle']['vehicle_number']} ({data_vehicle['vehicle']['vehicle_model']}) owned by {data_vehicle['vehicle']['customer_name']}")

    print("\n==========================================")
    print("ALL 8 VERIFICATION TESTS PASSED SUCCESSFULLY! 🎉")
    print("==========================================")

if __name__ == '__main__':
    run_tests()
