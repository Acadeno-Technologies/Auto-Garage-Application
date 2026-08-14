from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.http import JsonResponse
from django.contrib.auth import login, logout, authenticate, update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.db.models import Sum, Count, Q
from django.utils import timezone
from datetime import date, timedelta
from decimal import Decimal
from functools import wraps

from .models import (
    UserProfile, RoleCustomization, Customer, Vehicle, JobCard, JobCardPhoto,
    SparePart, PartCategory, Supplier, StockTransaction, JobPartUsage, Invoice,
    AMCPlan, CustomerAMC, AMCServiceSchedule, WhatsAppLog, Expense, GarageSettings
)
from .forms import (
    LoginForm, StaffCreationForm, StaffEditForm, CustomerForm, VehicleForm, JobCardForm, JobCardPhotoForm,
    JobStatusForm, SparePartForm, PartCategoryForm, SupplierForm,
    StockTransactionForm, JobPartUsageForm, InvoiceForm,
    AMCPlanForm, CustomerAMCForm, ExpenseForm, UserProfileUpdateForm, GarageSettingsForm
)


# ─── Role Decorators ────────────────────────────────────────────────────────

def role_required(*roles):
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('login')
            try:
                profile = request.user.profile
                if profile.role in roles or ('mechanic' in roles and profile.role == 'custom') or request.user.is_superuser:
                    return view_func(request, *args, **kwargs)
            except UserProfile.DoesNotExist:
                if request.user.is_superuser:
                    return view_func(request, *args, **kwargs)
            messages.error(request, "You don't have permission to access that page.")
            return redirect('dashboard')
        return wrapper
    return decorator


# ─── Auth Views ──────────────────────────────────────────────────────────────

def landing_page(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    return render(request, 'core/landing.html')


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    form = LoginForm(request, data=request.POST or None)

    if request.method == 'POST':
        if form.is_valid():
            user = form.get_user()
            role_selected = form.cleaned_data.get("role")

            if hasattr(user, "profile"):
                user_role = user.profile.role
                if user_role != role_selected and user_role != 'custom' and role_selected != 'custom' and not (user_role == 'mechanic' and role_selected == 'custom'):
                    messages.error(request, "Incorrect role selected for this account.")
                    return render(request, 'core/login.html', {'form': form})

            login(request, user)
            return redirect('dashboard')
        else:
            messages.error(request, "Invalid username, password, or login credentials. Please try again.")

    return render(request, 'core/login.html', {'form': form})


@login_required
def logout_view(request):
    logout(request)
    return redirect('login')


@login_required
def user_profile(request):
    user = request.user
    profile, _ = UserProfile.objects.get_or_create(user=user)
    garage = GarageSettings.get_settings()

    is_admin_or_owner = user.is_superuser or profile.role == 'owner'

    profile_form = UserProfileUpdateForm(instance=user, user_profile=profile)
    password_form = PasswordChangeForm(user=user)
    garage_form = GarageSettingsForm(instance=garage) if is_admin_or_owner else None

    active_tab = 'profile'

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'update_profile':
            active_tab = 'profile'
            profile_form = UserProfileUpdateForm(request.POST, instance=user, user_profile=profile)
            if profile_form.is_valid():
                profile_form.save()
                profile.phone = profile_form.cleaned_data.get('phone', '')
                profile.save()
                messages.success(request, 'Your profile details have been updated successfully!')
                return redirect('profile')

        elif action == 'update_password':
            active_tab = 'security'
            password_form = PasswordChangeForm(user=user, data=request.POST)
            if password_form.is_valid():
                user = password_form.save()
                update_session_auth_hash(request, user)
                messages.success(request, 'Your password was updated successfully!')
                return redirect('profile')
            else:
                messages.error(request, 'Please correct the password errors below.')

        elif action == 'update_garage' and is_admin_or_owner:
            active_tab = 'garage'
            garage_form = GarageSettingsForm(request.POST, request.FILES, instance=garage)
            if garage_form.is_valid():
                garage_form.save()
                messages.success(request, 'Garage profile and location details updated successfully!')
                return redirect('profile')
            else:
                messages.error(request, 'Please check the form inputs for garage settings.')

    return render(request, 'core/profile.html', {
        'profile_form': profile_form,
        'password_form': password_form,
        'garage_form': garage_form,
        'is_admin_or_owner': is_admin_or_owner,
        'garage': garage,
        'user_profile': profile,
        'active_tab': active_tab,
    })


@login_required
def dashboard(request):
    try:
        role = request.user.profile.role
    except UserProfile.DoesNotExist:
        role = 'owner' if request.user.is_superuser else None

    if role == 'owner' or request.user.is_superuser:
        return redirect('owner_dashboard')
    elif role == 'advisor':
        return redirect('advisor_dashboard')
    elif role in ['mechanic', 'custom']:
        return redirect('mechanic_dashboard')
    elif role == 'store_manager':
        return redirect('store_dashboard')
    return redirect('mechanic_dashboard')


# ─── Owner Dashboard ─────────────────────────────────────────────────────────

@login_required
@role_required('owner')
def owner_dashboard(request):
    today = date.today()
    month_start = today.replace(day=1)

    total_customers = Customer.objects.count()
    total_vehicles = Vehicle.objects.count()
    active_jobs = JobCard.objects.exclude(status__in=['completed', 'delivered']).count()
    completed_jobs = JobCard.objects.filter(status__in=['completed', 'delivered']).count()
    low_stock_parts = SparePart.objects.filter(stock_quantity__lte=models_low_stock()).count()
    pending_invoices = Invoice.objects.filter(status='unpaid').count()
    staff_count = UserProfile.objects.exclude(role='owner').count()

    monthly_revenue = Invoice.objects.filter(
        status='paid', issue_date__gte=month_start
    ).aggregate(total=Sum('amount_paid'))['total'] or 0

    recent_jobs = JobCard.objects.select_related('vehicle__customer', 'mechanic').order_by('-created_at')[:8]
    low_stock_list = SparePart.objects.filter(stock_quantity__lte=5).order_by('stock_quantity')[:5]
    recent_invoices = Invoice.objects.select_related('job_card__vehicle__customer').order_by('-id')[:5]

    mechanics = User.objects.filter(Q(profile__role='mechanic') | Q(profile__role='custom'))
    mechanic_stats = []
    for m in mechanics:
        count = JobCard.objects.filter(mechanic=m, status='completed').count()
        mechanic_stats.append({'mechanic': m, 'completed': count})

    ctx = {
        'total_customers': total_customers,
        'total_vehicles': total_vehicles,
        'active_jobs': active_jobs,
        'completed_jobs': completed_jobs,
        'low_stock_parts': SparePart.objects.filter(stock_quantity__lte=5).count(),
        'pending_invoices': pending_invoices,
        'staff_count': staff_count,
        'monthly_revenue': monthly_revenue,
        'recent_jobs': recent_jobs,
        'low_stock_list': low_stock_list,
        'recent_invoices': recent_invoices,
        'mechanic_stats': mechanic_stats,
    }
    return render(request, 'core/owner_dashboard.html', ctx)


def models_low_stock():
    return 5


# ─── Staff Management ────────────────────────────────────────────────────────

@login_required
@role_required('owner')
def staff_list(request):
    if request.method == 'POST' and 'update_role_names' in request.POST:
        for key in ['advisor', 'mechanic', 'store_manager']:
            val = request.POST.get(f'role_name_{key}', '').strip()
            if val:
                RoleCustomization.objects.update_or_create(
                    role_key=key,
                    defaults={'display_name': val}
                )
        messages.success(request, "Role display names updated successfully.")
        return redirect('staff_list')

    staff = UserProfile.objects.select_related('user').exclude(role='owner')
    custom_roles = {
        'advisor': RoleCustomization.objects.filter(role_key='advisor').first(),
        'mechanic': RoleCustomization.objects.filter(role_key='mechanic').first(),
        'store_manager': RoleCustomization.objects.filter(role_key='store_manager').first(),
    }
    return render(request, 'core/staff_list.html', {
        'staff': staff,
        'custom_roles': custom_roles
    })


@login_required
@role_required('owner')
def staff_create(request):
    form = StaffCreationForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = User.objects.create_user(
            username=form.cleaned_data['username'],
            email=form.cleaned_data['email'],
            password=form.cleaned_data['password'],
            first_name=form.cleaned_data['first_name'],
            last_name=form.cleaned_data['last_name'],
        )
        UserProfile.objects.create(
            user=user,
            role=form.cleaned_data['role'],
            custom_role=form.cleaned_data.get('custom_role', ''),
            phone=form.cleaned_data.get('phone', ''),
        )
        messages.success(request, f"Staff member {user.get_full_name()} created successfully.")
        return redirect('staff_list')
    return render(request, 'core/staff_form.html', {'form': form, 'title': 'Add Staff Member'})


@login_required
@role_required('owner')
def staff_edit(request, pk):
    profile = get_object_or_404(UserProfile, pk=pk)
    user = profile.user
    if request.method == 'POST':
        form = StaffEditForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            profile.role = form.cleaned_data['role']
            profile.custom_role = form.cleaned_data.get('custom_role', '')
            profile.phone = form.cleaned_data.get('phone', '')
            profile.save()
            messages.success(request, f"Staff member {user.get_full_name() or user.username} updated successfully.")
            return redirect('staff_list')
    else:
        form = StaffEditForm(instance=user, initial={
            'role': profile.role,
            'custom_role': profile.custom_role,
            'phone': profile.phone,
        })
    return render(request, 'core/staff_form.html', {'form': form, 'title': f'Edit Staff Member: {user.get_full_name() or user.username}'})


@login_required
@role_required('owner')
def staff_delete(request, pk):
    profile = get_object_or_404(UserProfile, pk=pk)
    if request.method == 'POST':
        profile.user.delete()
        messages.success(request, "Staff member removed.")
        return redirect('staff_list')
    return render(request, 'core/confirm_delete.html', {'obj': profile, 'type': 'Staff Member'})


# ─── Customer Management ──────────────────────────────────────────────────────

@login_required
@role_required('owner', 'advisor')
def customer_list(request):
    q = request.GET.get('q', '')
    customers = Customer.objects.all()
    if q:
        customers = customers.filter(Q(name__icontains=q) | Q(phone__icontains=q))
    return render(request, 'core/customer_list.html', {'customers': customers, 'q': q})


@login_required
@role_required('owner', 'advisor')
def customer_create(request):
    form = CustomerForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        c = form.save(commit=False)
        c.created_by = request.user
        c.save()
        messages.success(request, f"Customer '{c.name}' added.")
        return redirect('customer_list')
    return render(request, 'core/customer_form.html', {'form': form, 'title': 'Add Customer'})


@login_required
@role_required('owner', 'advisor')
def customer_detail(request, pk):
    customer = get_object_or_404(Customer, pk=pk)
    vehicles = customer.vehicles.all()
    return render(request, 'core/customer_detail.html', {'customer': customer, 'vehicles': vehicles})


@login_required
@role_required('owner', 'advisor')
def customer_edit(request, pk):
    customer = get_object_or_404(Customer, pk=pk)
    form = CustomerForm(request.POST or None, instance=customer)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, "Customer updated.")
        return redirect('customer_detail', pk=pk)
    return render(request, 'core/customer_form.html', {'form': form, 'title': 'Edit Customer'})


@login_required
@role_required('owner', 'advisor')
def customer_delete(request, pk):
    customer = get_object_or_404(Customer, pk=pk)
    name = customer.name
    if request.method == 'POST':
        customer.delete()
        messages.success(request, f"Customer '{name}' deleted successfully.")
        return redirect('customer_list')
    return render(request, 'core/confirm_delete.html', {'obj': customer, 'type': 'Customer'})


# ─── Vehicle Management ───────────────────────────────────────────────────────

@login_required
@role_required('owner', 'advisor')
def vehicle_list(request):
    q = request.GET.get('q', '').strip()
    vehicles = Vehicle.objects.select_related('customer').all()
    if q:
        vehicles = vehicles.filter(
            Q(license_plate__icontains=q) |
            Q(make__icontains=q) |
            Q(model__icontains=q) |
            Q(customer__name__icontains=q) |
            Q(customer__phone__icontains=q)
        )
    return render(request, 'core/vehicle_list.html', {'vehicles': vehicles, 'q': q})


@login_required
@role_required('owner', 'advisor')
def vehicle_create(request):
    files = request.FILES.copy() if request.FILES else None
    if files and 'image' in files and (not files['image'] or getattr(files['image'], 'size', 0) == 0):
        del files['image']
    initial = {}
    customer_id = request.GET.get('customer')
    if customer_id:
        initial['customer'] = customer_id
    form = VehicleForm(request.POST or None, files or None, initial=initial)
    if request.method == 'POST' and form.is_valid():
        try:
            vehicle = form.save()
            messages.success(request, f"Vehicle '{vehicle.license_plate}' added successfully.")
            return redirect('vehicle_detail', pk=vehicle.pk)
        except Exception as e:
            messages.warning(request, f"Vehicle details saved, but photo upload encountered an issue: {e}")
            vehicle = form.save(commit=False)
            vehicle.image = None
            vehicle.save()
            return redirect('vehicle_detail', pk=vehicle.pk)
    return render(request, 'core/vehicle_form.html', {'form': form, 'title': 'Add Vehicle'})


@login_required
@role_required('owner', 'advisor')
def vehicle_edit(request, pk):
    vehicle = get_object_or_404(Vehicle, pk=pk)
    files = request.FILES.copy() if request.FILES else None
    if files and 'image' in files and (not files['image'] or getattr(files['image'], 'size', 0) == 0):
        del files['image']
    form = VehicleForm(request.POST or None, files or None, instance=vehicle)
    if request.method == 'POST' and form.is_valid():
        try:
            form.save()
            messages.success(request, f"Vehicle '{vehicle.license_plate}' updated successfully.")
            return redirect('vehicle_detail', pk=pk)
        except Exception as e:
            messages.warning(request, f"Vehicle saved, but photo upload failed: {e}")
            vehicle_obj = form.save(commit=False)
            if 'image' in form.changed_data:
                vehicle_obj.image = vehicle.image
            vehicle_obj.save()
            return redirect('vehicle_detail', pk=pk)
    return render(request, 'core/vehicle_form.html', {'form': form, 'title': 'Edit Vehicle', 'vehicle': vehicle})


@login_required
@role_required('owner', 'advisor')
def vehicle_detail(request, pk):
    vehicle = get_object_or_404(Vehicle, pk=pk)
    jobs = vehicle.job_cards.all().order_by('-created_at')
    return render(request, 'core/vehicle_detail.html', {'vehicle': vehicle, 'jobs': jobs})


@login_required
@role_required('owner', 'advisor')
def vehicle_delete(request, pk):
    vehicle = get_object_or_404(Vehicle, pk=pk)
    plate = vehicle.license_plate
    if request.method == 'POST':
        vehicle.delete()
        messages.success(request, f"Vehicle '{plate}' deleted successfully.")
        return redirect('vehicle_list')
    return render(request, 'core/confirm_delete.html', {'obj': vehicle, 'type': 'Vehicle'})


# ─── Job Card Management ─────────────────────────────────────────────────────

@login_required
@role_required('owner', 'advisor')
def job_list(request):
    status = request.GET.get('status', '').strip()
    q = request.GET.get('q', '').strip()
    jobs = JobCard.objects.select_related('vehicle__customer', 'mechanic', 'advisor').all()
    if status:
        jobs = jobs.filter(status=status)
    if q:
        jobs = jobs.filter(
            Q(job_number__icontains=q) |
            Q(vehicle__license_plate__icontains=q) |
            Q(vehicle__make__icontains=q) |
            Q(vehicle__model__icontains=q) |
            Q(vehicle__customer__name__icontains=q) |
            Q(vehicle__customer__phone__icontains=q)
        )
    jobs = jobs.order_by('-created_at')
    return render(request, 'core/job_list.html', {'jobs': jobs, 'status_filter': status, 'q': q})


@login_required
def job_search_records(request):
    phone = request.GET.get('phone', '').strip()
    vehicle_number = request.GET.get('vehicle_number', '').strip()
    q = request.GET.get('q', '').strip()

    response_data = {
        'customer_found': False,
        'customer': None,
        'vehicle_found': False,
        'vehicle': None,
        'results': []
    }

    # 1. Customer search by phone
    if phone:
        customer = Customer.objects.filter(phone__iexact=phone).first()
        if not customer:
            # Fallback to icontains if exact phone didn't hit
            customer = Customer.objects.filter(phone__icontains=phone).first()
        
        if customer:
            vehicles_list = [
                {
                    'vehicle_number': v.license_plate,
                    'vehicle_model': f"{v.make} {v.model}".strip(),
                    'vehicle_color': v.color
                }
                for v in customer.vehicles.all()
            ]
            response_data['customer_found'] = True
            response_data['customer'] = {
                'id': customer.pk,
                'name': customer.name,
                'phone': customer.phone,
                'email': customer.email,
                'address': customer.address,
                'vehicles': vehicles_list
            }

    # 2. Vehicle search by vehicle number / license plate
    if vehicle_number:
        v_clean = vehicle_number.replace(" ", "").upper()
        # Require exact match (or full plate matching) to prevent partial populating
        vehicle = Vehicle.objects.filter(license_plate__iexact=v_clean).select_related('customer').first()
        if not vehicle and len(v_clean) >= 6:
            vehicle = Vehicle.objects.filter(license_plate__iexact=vehicle_number).select_related('customer').first()

        if vehicle:
            response_data['vehicle_found'] = True
            response_data['vehicle'] = {
                'id': vehicle.pk,
                'vehicle_number': vehicle.license_plate,
                'vehicle_model': f"{vehicle.make} {vehicle.model}".strip(),
                'vehicle_make': vehicle.make,
                'vehicle_color': vehicle.color,
                'customer_name': vehicle.customer.name,
                'customer_phone': vehicle.customer.phone,
                'customer_email': vehicle.customer.email,
                'customer_address': vehicle.customer.address
            }

    # 3. General query fallback search
    search_query = q or phone or vehicle_number
    if search_query and len(search_query) >= 2:
        vehicles = Vehicle.objects.filter(
            Q(license_plate__icontains=search_query) |
            Q(model__icontains=search_query) |
            Q(make__icontains=search_query) |
            Q(customer__name__icontains=search_query) |
            Q(customer__phone__icontains=search_query)
        ).select_related('customer')[:10]
        
        for v in vehicles:
            response_data['results'].append({
                'customer_name': v.customer.name,
                'customer_phone': v.customer.phone,
                'customer_email': v.customer.email,
                'customer_address': v.customer.address,
                'vehicle_number': v.license_plate,
                'vehicle_model': f"{v.make} {v.model}".strip(),
                'vehicle_color': v.color
            })
            
        if len(response_data['results']) < 5:
            existing_phones = {r['customer_phone'] for r in response_data['results']}
            customers = Customer.objects.filter(
                Q(name__icontains=search_query) | Q(phone__icontains=search_query)
            ).exclude(phone__in=existing_phones)[:5]
            for c in customers:
                response_data['results'].append({
                    'customer_name': c.name,
                    'customer_phone': c.phone,
                    'customer_email': c.email,
                    'customer_address': c.address,
                    'vehicle_number': '',
                    'vehicle_model': '',
                    'vehicle_color': ''
                })

    return JsonResponse(response_data)


@login_required
@role_required('owner', 'advisor')
def job_create(request):
    form = JobCardForm(request.POST or None, request.FILES or None)
    if request.method == 'POST':
        if form.is_valid():
            job = form.save(commit=False)
            c_name = form.cleaned_data['customer_name'].strip().title()
            c_phone = form.cleaned_data['customer_phone'].strip()
            c_email = form.cleaned_data.get('customer_email', '').strip()
            c_address = form.cleaned_data.get('customer_address', '').strip().title()
            v_num = form.cleaned_data['vehicle_number'].strip().upper()
            v_model_raw = form.cleaned_data['vehicle_model'].strip().title()
            v_color = form.cleaned_data.get('vehicle_color', '').strip().title()

            job.problem_description = job.problem_description.title() if job.problem_description else ""
            job.repair_instructions = job.repair_instructions.title() if job.repair_instructions else ""
            job.notes = job.notes.title() if job.notes else ""

            # Find or create customer by phone number (prevent duplicates)
            customer = Customer.objects.filter(phone__iexact=c_phone).first()
            if not customer:
                customer = Customer.objects.create(
                    phone=c_phone,
                    name=c_name,
                    email=c_email,
                    address=c_address,
                    created_by=request.user
                )
            else:
                updated = False
                if c_name and customer.name != c_name:
                    customer.name = c_name
                    updated = True
                if c_email and customer.email != c_email:
                    customer.email = c_email
                    updated = True
                if c_address and customer.address != c_address:
                    customer.address = c_address
                    updated = True
                if updated:
                    customer.save()

            # Split model string into make and model if space separated
            model_parts = v_model_raw.split()
            v_make = model_parts[0] if model_parts else "Vehicle"
            v_model = ' '.join(model_parts[1:]) if len(model_parts) > 1 else v_model_raw

            # Find or create Vehicle by license plate (prevent duplicates)
            vehicle = Vehicle.objects.filter(license_plate__iexact=v_num).first()
            if vehicle:
                # Update customer relationship and vehicle info
                if vehicle.customer != customer:
                    messages.info(request, f"Vehicle '{v_num}' was previously registered under customer '{vehicle.customer.name}'. Re-associated to '{customer.name}'.")
                    vehicle.customer = customer
                if v_make: vehicle.make = v_make
                if v_model: vehicle.model = v_model
                if v_color: vehicle.color = v_color
                vehicle.save()
            else:
                vehicle = Vehicle.objects.create(
                    license_plate=v_num,
                    customer=customer,
                    make=v_make,
                    model=v_model,
                    color=v_color,
                    year=timezone.now().year
                )

            # Prevent duplicate job creation (check active job cards or recent creation)
            recent_cutoff = timezone.now() - timedelta(seconds=60)
            existing_duplicate = JobCard.objects.filter(
                vehicle=vehicle,
                problem_description=job.problem_description
            ).filter(
                Q(status__in=['pending', 'in_progress', 'waiting_parts']) | Q(created_at__gte=recent_cutoff)
            ).first()

            if existing_duplicate:
                messages.warning(request, f"Active Job Card '{existing_duplicate.job_number}' already exists for vehicle '{vehicle.license_plate}' with the same problem description.")
                return redirect('job_detail', pk=existing_duplicate.pk)

            job.vehicle = vehicle
            job.advisor = request.user
            job.save()

            images = request.FILES.getlist('photos')
            for img in images:
                JobCardPhoto.objects.create(job_card=job, image=img)
            
            # Trigger SMS / WhatsApp Notification on Job Card Creation
            est_str = job.estimated_completion_time.strftime('%d %b %Y %H:%M') if job.estimated_completion_time else 'Not specified'
            sms_body = (
                f"Dear {customer.name}, your Job Card {job.job_number} for {job.vehicle.make} {job.vehicle.model} "
                f"({job.vehicle.license_plate}) has been created at Auto Garage. Est. Completion: {est_str}. Status: {job.get_status_display()}."
            )
            WhatsAppLog.objects.create(
                recipient_name=customer.name,
                phone=customer.phone,
                message_type='job_created',
                message_body=sms_body,
                sent_by=request.user
            )
            messages.success(request, f"Job card {job.job_number} created successfully with {len(images)} photo(s). Notification logged for customer ({customer.phone}).")
            return redirect('job_detail', pk=job.pk)
        else:
            messages.error(request, "Please correct the errors in the form before submitting.")
    return render(request, 'core/job_form.html', {'form': form, 'title': 'Create Job Card'})


import json

@login_required
def job_detail(request, pk):
    job = get_object_or_404(JobCard, pk=pk)
    parts_used = job.parts_used.select_related('part').all()
    photos = job.photos.all().order_by('-uploaded_at')
    part_form = JobPartUsageForm()
    photo_form = JobCardPhotoForm()
    status_choices = JobCard.STATUS_CHOICES
    part_prices_json = json.dumps({str(p.pk): str(p.unit_price) for p in SparePart.objects.all()})
    return render(request, 'core/job_detail.html', {
        'job': job, 'parts_used': parts_used, 'photos': photos,
        'part_form': part_form, 'photo_form': photo_form,
        'status_choices': status_choices,
        'part_prices_json': part_prices_json
    })


@login_required
@role_required('owner', 'advisor', 'mechanic')
def job_add_photo(request, pk):
    job = get_object_or_404(JobCard, pk=pk)
    if request.method == 'POST':
        photo_form = JobCardPhotoForm(request.POST, request.FILES)
        if photo_form.is_valid():
            photo = photo_form.save(commit=False)
            photo.job_card = job
            photo.save()
            messages.success(request, "Photo uploaded successfully.")
        else:
            messages.error(request, "Failed to upload photo. Please check the file.")
    return redirect('job_detail', pk=pk)


@login_required
@role_required('owner', 'advisor')
def job_delete_photo(request, pk, photo_pk):
    job = get_object_or_404(JobCard, pk=pk)
    photo = get_object_or_404(JobCardPhoto, pk=photo_pk, job_card=job)
    photo.image.delete(save=False)
    photo.delete()
    messages.success(request, "Photo removed.")
    return redirect('job_detail', pk=pk)


@login_required
@role_required('owner', 'advisor', 'mechanic')
def job_update_status(request, pk):
    job = get_object_or_404(JobCard, pk=pk)

    # Check for instant inline quick status change from job_detail page
    if request.method == 'POST' and 'quick_status' in request.POST:
        new_status = request.POST.get('quick_status', '').strip()
        if new_status in dict(JobCard.STATUS_CHOICES):
            job.status = new_status
            job.save()
            customer = job.vehicle.customer
            status_disp = job.get_status_display()

            if job.status == 'completed':
                sms_body = (
                    f"Dear {customer.name}, great news! Your vehicle {job.vehicle.make} {job.vehicle.model} "
                    f"({job.vehicle.license_plate}) service (Job Card {job.job_number}) is COMPLETED and ready for pickup! "
                    f"Total Cost: ₹{job.total_cost():.2f}."
                )
            else:
                sms_body = (
                    f"Dear {customer.name}, update on your Job Card {job.job_number} for {job.vehicle.make} {job.vehicle.model}: "
                    f"Status updated to '{status_disp}'."
                )
            WhatsAppLog.objects.create(
                recipient_name=customer.name,
                phone=customer.phone,
                message_type=f"job_status_{job.status}",
                message_body=sms_body,
                sent_by=request.user
            )
            messages.success(request, f"Status updated to '{status_disp}'. Opening WhatsApp to notify customer ({customer.phone})...")
            wa_redirect_url = reverse('send_whatsapp') + f"?type=job_status&job_id={job.pk}&phone={customer.phone}&name={customer.name}"
            return redirect(wa_redirect_url)

    form = JobStatusForm(request.POST or None, request.FILES or None, instance=job)
    if request.method == 'POST' and form.is_valid():
        updated_job = form.save(commit=False)
        
        # Save customer and vehicle changes
        c_name = form.cleaned_data.get('customer_name', '').strip().title()
        c_phone = form.cleaned_data.get('customer_phone', '').strip()
        c_email = form.cleaned_data.get('customer_email', '').strip()
        c_address = form.cleaned_data.get('customer_address', '').strip().title()
        v_num = form.cleaned_data.get('vehicle_number', '').strip().upper()
        v_model_raw = form.cleaned_data.get('vehicle_model', '').strip().title()
        v_color = form.cleaned_data.get('vehicle_color', '').strip().title()

        updated_job.problem_description = updated_job.problem_description.title() if updated_job.problem_description else ""
        updated_job.repair_instructions = updated_job.repair_instructions.title() if updated_job.repair_instructions else ""
        updated_job.notes = updated_job.notes.title() if updated_job.notes else ""

        if c_name and c_phone and updated_job.vehicle:
            cust = updated_job.vehicle.customer
            cust.name = c_name
            cust.phone = c_phone
            if c_email: cust.email = c_email
            if c_address: cust.address = c_address
            cust.save()

            model_parts = v_model_raw.split()
            v_make = model_parts[0] if model_parts else "Vehicle"
            v_model = ' '.join(model_parts[1:]) if len(model_parts) > 1 else v_model_raw

            v = updated_job.vehicle
            v.license_plate = v_num
            v.make = v_make
            v.model = v_model
            v.color = v_color
            v.save()

        updated_job.save()

        images = request.FILES.getlist('photos')
        for img in images:
            JobCardPhoto.objects.create(job_card=updated_job, image=img)

        customer = updated_job.vehicle.customer
        status_disp = updated_job.get_status_display()
        
        # Trigger SMS Notification on Job Card Status Update
        if updated_job.status == 'completed':
            sms_body = (
                f"Dear {customer.name}, great news! Your vehicle {updated_job.vehicle.make} {updated_job.vehicle.model} "
                f"({updated_job.vehicle.license_plate}) service (Job Card {updated_job.job_number}) is COMPLETED and ready for pickup! "
                f"Total Cost: ₹{updated_job.total_cost():.2f}."
            )
        else:
            sms_body = (
                f"Dear {customer.name}, update on your Job Card {updated_job.job_number} for {updated_job.vehicle.make} {updated_job.vehicle.model}: "
                f"Status updated to '{status_disp}'."
            )
        
        WhatsAppLog.objects.create(
            recipient_name=customer.name,
            phone=customer.phone,
            message_type=f"job_status_{updated_job.status}",
            message_body=sms_body,
            sent_by=request.user
        )
        messages.success(request, f"Job card '{updated_job.job_number}' updated successfully. SMS notification sent to customer ({customer.phone}).")
        return redirect('job_detail', pk=pk)
    return render(request, 'core/job_form.html', {'form': form, 'title': 'Update Job Card & Status', 'job': job})


@login_required
@role_required('owner', 'advisor')
def job_delete(request, pk):
    job = get_object_or_404(JobCard, pk=pk)
    if request.method == 'POST':
        job_num = job.job_number
        job.delete()
        messages.success(request, f"Job card '{job_num}' deleted successfully.")
        return redirect('job_list')
    return redirect('job_detail', pk=pk)


@login_required
@role_required('owner', 'advisor')
def job_add_part(request, pk):
    job = get_object_or_404(JobCard, pk=pk)
    if request.method == 'POST':
        form = JobPartUsageForm(request.POST)
        if form.is_valid():
            usage = form.save(commit=False)
            usage.job_card = job
            if not usage.unit_price:
                usage.unit_price = usage.part.unit_price
            usage.save()
            # Deduct from stock
            part = usage.part
            part.stock_quantity = max(0, part.stock_quantity - usage.quantity)
            part.save()
            messages.success(request, f"Part '{part.name}' added to job (₹{usage.unit_price} each).")
    return redirect('job_detail', pk=pk)


@login_required
@role_required('owner', 'advisor', 'mechanic')
def job_update_part_qty(request, pk, usage_pk, action):
    job = get_object_or_404(JobCard, pk=pk)
    usage = get_object_or_404(JobPartUsage, pk=usage_pk, job_card=job)
    part = usage.part

    if action == 'increase':
        if part.stock_quantity >= 1:
            usage.quantity += 1
            usage.save()
            part.stock_quantity -= 1
            part.save()
            messages.success(request, f"Increased quantity of '{part.name}' to {usage.quantity}.")
        else:
            messages.error(request, f"Cannot increase. Insufficient stock for '{part.name}' (Available stock: {part.stock_quantity}).")

    elif action == 'decrease':
        if usage.quantity > 1:
            usage.quantity -= 1
            usage.save()
            part.stock_quantity += 1
            part.save()
            messages.success(request, f"Decreased quantity of '{part.name}' to {usage.quantity}.")
        else:
            # Quantity goes down to 0 -> delete usage & restore stock
            part.stock_quantity += usage.quantity
            part.save()
            usage.delete()
            messages.success(request, f"Removed '{part.name}' from job card.")

    elif action == 'delete' or request.method == 'POST':
        part.stock_quantity += usage.quantity
        part.save()
        usage.delete()
        messages.success(request, f"Removed '{part.name}' from job card.")

    return redirect('job_detail', pk=pk)


# ─── Mechanic Dashboard ───────────────────────────────────────────────────────

@login_required
@role_required('mechanic')
def mechanic_dashboard(request):
    my_jobs = JobCard.objects.filter(
        mechanic=request.user
    ).select_related('vehicle__customer').order_by('-created_at')

    active = my_jobs.exclude(status__in=['completed', 'delivered'])
    completed = my_jobs.filter(status__in=['completed', 'delivered'])
    ctx = {
        'active_jobs': active,
        'completed_jobs': completed,
        'total_completed': completed.count(),
    }
    return render(request, 'core/mechanic_dashboard.html', ctx)


# ─── Advisor Dashboard ────────────────────────────────────────────────────────

@login_required
@role_required('advisor')
def advisor_dashboard(request):
    my_jobs = JobCard.objects.filter(
        advisor=request.user
    ).select_related('vehicle__customer', 'mechanic').order_by('-created_at')

    pending = my_jobs.filter(status='pending').count()
    in_progress = my_jobs.filter(status='in_progress').count()
    completed = my_jobs.filter(status='completed').count()
    recent_customers = Customer.objects.filter(created_by=request.user).order_by('-created_at')[:5]

    ctx = {
        'my_jobs': my_jobs[:10],
        'pending': pending,
        'in_progress': in_progress,
        'completed': completed,
        'recent_customers': recent_customers,
    }
    return render(request, 'core/advisor_dashboard.html', ctx)


# ─── Store Dashboard ──────────────────────────────────────────────────────────

@login_required
@role_required('store_manager')
def store_dashboard(request):
    total_parts = SparePart.objects.count()
    low_stock = SparePart.objects.filter(stock_quantity__lte=5)
    total_categories = PartCategory.objects.count()
    total_suppliers = Supplier.objects.count()
    recent_transactions = StockTransaction.objects.select_related('part').order_by('-created_at')[:10]

    ctx = {
        'total_parts': total_parts,
        'low_stock_count': low_stock.count(),
        'low_stock_parts': low_stock[:5],
        'total_categories': total_categories,
        'total_suppliers': total_suppliers,
        'recent_transactions': recent_transactions,
    }
    return render(request, 'core/store_dashboard.html', ctx)


# ─── Spare Parts ──────────────────────────────────────────────────────────────

@login_required
@role_required('owner', 'store_manager')
def parts_list(request):
    q = request.GET.get('q', '').strip()
    cat_id = request.GET.get('category', '').strip()
    active_tab = request.GET.get('tab', 'parts').strip().lower()
    if active_tab not in ['parts', 'categories', 'suppliers']:
        active_tab = 'parts'

    all_parts = SparePart.objects.select_related('category', 'supplier').all()
    parts = all_parts
    if q:
        parts = parts.filter(
            Q(name__icontains=q) |
            Q(part_number__icontains=q) |
            Q(category__name__icontains=q) |
            Q(supplier__name__icontains=q)
        )
    if cat_id:
        parts = parts.filter(category_id=cat_id)

    categories = PartCategory.objects.annotate(parts_count=Count('sparepart')).all()
    suppliers = Supplier.objects.annotate(parts_count=Count('sparepart')).all()

    if q:
        categories = categories.filter(Q(name__icontains=q) | Q(description__icontains=q))
        suppliers = suppliers.filter(
            Q(name__icontains=q) |
            Q(contact_person__icontains=q) |
            Q(phone__icontains=q) |
            Q(email__icontains=q)
        )

    total_parts_count = all_parts.count()
    low_stock_count = sum(1 for p in all_parts if p.is_low_stock)
    total_categories_count = PartCategory.objects.count()
    total_suppliers_count = Supplier.objects.count()

    return render(request, 'core/parts_list.html', {
        'parts': parts,
        'q': q,
        'selected_category': cat_id,
        'categories': categories,
        'suppliers': suppliers,
        'total_parts_count': total_parts_count,
        'low_stock_count': low_stock_count,
        'total_categories_count': total_categories_count,
        'total_suppliers_count': total_suppliers_count,
        'active_tab': active_tab,
    })


@login_required
@role_required('owner', 'store_manager')
def part_delete(request, pk):
    part = get_object_or_404(SparePart, pk=pk)
    if request.method == 'POST':
        name = part.name
        part.delete()
        messages.success(request, f"Spare part '{name}' deleted.")
    return redirect('parts_list')


@login_required
@role_required('owner', 'store_manager')
def parts_export_csv(request):
    import csv
    from django.http import HttpResponse
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="inventory_parts_export.csv"'
    writer = csv.writer(response)
    writer.writerow(['Name', 'Part Number', 'Category', 'Unit Price', 'Stock Quantity', 'Minimum Stock', 'Supplier'])
    for p in SparePart.objects.select_related('category', 'supplier').all():
        writer.writerow([
            p.name, p.part_number, p.category.name if p.category else '',
            p.unit_price, p.stock_quantity, p.minimum_stock,
            p.supplier.name if p.supplier else ''
        ])
    return response


@login_required
@role_required('owner', 'store_manager')
def parts_export_pdf(request):
    q = request.GET.get('q', '').strip()
    cat_id = request.GET.get('category', '').strip()

    all_parts = SparePart.objects.select_related('category', 'supplier').all()
    parts = all_parts
    if q:
        parts = parts.filter(Q(name__icontains=q) | Q(part_number__icontains=q) | Q(category__name__icontains=q))
    if cat_id:
        parts = parts.filter(category_id=cat_id)

    from django.utils import timezone
    return render(request, 'core/parts_pdf.html', {
        'parts': parts,
        'generated_at': timezone.now()
    })


@login_required
@role_required('owner', 'store_manager')
def part_create(request):
    form = SparePartForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, "Spare part added.")
        return redirect('parts_list')
    return render(request, 'core/part_form.html', {'form': form, 'title': 'Add Spare Part'})


@login_required
@role_required('owner', 'store_manager')
def part_edit(request, pk):
    part = get_object_or_404(SparePart, pk=pk)
    form = SparePartForm(request.POST or None, instance=part)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, "Part updated.")
        return redirect('parts_list')
    return render(request, 'core/part_form.html', {'form': form, 'title': 'Edit Spare Part'})


@login_required
@role_required('owner', 'store_manager')
def stock_transaction(request):
    form = StockTransactionForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        tx = form.save(commit=False)
        tx.created_by = request.user
        if not tx.unit_price:
            tx.unit_price = tx.part.unit_price
        tx.save()
        # Update stock
        part = tx.part
        if tx.transaction_type == 'in':
            part.stock_quantity += tx.quantity
        else:
            part.stock_quantity = max(0, part.stock_quantity - tx.quantity)
        part.save()
        messages.success(request, f"Stock transaction recorded for '{part.name}'.")
        return redirect('parts_list')

    import json
    part_prices = {p.id: float(p.unit_price) for p in SparePart.objects.all()}
    return render(request, 'core/stock_form.html', {
        'form': form,
        'title': 'Stock Transaction',
        'part_prices_json': json.dumps(part_prices)
    })


# ─── Categories & Suppliers ───────────────────────────────────────────────────

@login_required
@role_required('owner', 'store_manager')
def category_list(request):
    return redirect('/parts/?tab=categories')


@login_required
@role_required('owner', 'store_manager')
def category_create(request):
    form = PartCategoryForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, "Category created.")
        return redirect('/parts/?tab=categories')
    return render(request, 'core/category_form.html', {'form': form, 'title': 'Add Category'})


@login_required
@role_required('owner', 'store_manager')
def category_edit(request, pk):
    cat = get_object_or_404(PartCategory, pk=pk)
    form = PartCategoryForm(request.POST or None, instance=cat)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, "Category updated.")
        return redirect('/parts/?tab=categories')
    return render(request, 'core/category_form.html', {'form': form, 'title': 'Edit Category'})


@login_required
@role_required('owner', 'store_manager')
def category_delete(request, pk):
    cat = get_object_or_404(PartCategory, pk=pk)
    if request.method == 'POST':
        name = cat.name
        cat.delete()
        messages.success(request, f"Category '{name}' deleted.")
    return redirect('/parts/?tab=categories')


@login_required
@role_required('owner', 'store_manager')
def supplier_list(request):
    return redirect('/parts/?tab=suppliers')


@login_required
@role_required('owner', 'store_manager')
def supplier_create(request):
    form = SupplierForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, "Supplier created.")
        return redirect('/parts/?tab=suppliers')
    return render(request, 'core/supplier_form.html', {'form': form, 'title': 'Add Supplier'})


@login_required
@role_required('owner', 'store_manager')
def supplier_edit(request, pk):
    sup = get_object_or_404(Supplier, pk=pk)
    form = SupplierForm(request.POST or None, instance=sup)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, "Supplier updated.")
        return redirect('/parts/?tab=suppliers')
    return render(request, 'core/supplier_form.html', {'form': form, 'title': 'Edit Supplier'})


@login_required
@role_required('owner', 'store_manager')
def supplier_delete(request, pk):
    sup = get_object_or_404(Supplier, pk=pk)
    if request.method == 'POST':
        name = sup.name
        sup.delete()
        messages.success(request, f"Supplier '{name}' deleted.")
    return redirect('/parts/?tab=suppliers')


# ─── Billing / Invoices ───────────────────────────────────────────────────────

@login_required
@role_required('owner', 'advisor')
def invoice_list(request):
    q = request.GET.get('q', '').strip()
    invoices = Invoice.objects.select_related('job_card__vehicle__customer').order_by('-id')
    if q:
        invoices = invoices.filter(
            Q(invoice_number__icontains=q) |
            Q(job_card__job_number__icontains=q) |
            Q(job_card__vehicle__customer__name__icontains=q) |
            Q(job_card__vehicle__customer__phone__icontains=q) |
            Q(job_card__vehicle__license_plate__icontains=q)
        )
    return render(request, 'core/invoice_list.html', {'invoices': invoices, 'q': q})


@login_required
@role_required('owner', 'advisor')
def invoice_create(request, job_pk=None):
    if not job_pk and request.GET.get('job_id'):
        try:
            job_pk = int(request.GET.get('job_id'))
        except (ValueError, TypeError):
            pass

    if job_pk:
        job = get_object_or_404(JobCard.objects.select_related('vehicle__customer', 'mechanic', 'advisor'), pk=job_pk)
        if hasattr(job, 'invoice'):
            messages.info(request, f"Invoice already exists for Job Card {job.job_number}.")
            return redirect('invoice_detail', pk=job.invoice.pk)
        
        parts_used = job.parts_used.select_related('part').all()
        parts_total = sum(p.total_price for p in parts_used)

        active_amc = CustomerAMC.objects.filter(
            vehicle=job.vehicle,
            status='active',
            start_date__lte=timezone.now().date(),
            end_date__gte=timezone.now().date()
        ).select_related('plan').first()

        calculated_amc_discount = Decimal('0.00')
        if active_amc:
            discount_pct = getattr(active_amc.plan, 'discount_percentage', Decimal('100.00')) or Decimal('100.00')
            calculated_amc_discount = (job.labour_cost * discount_pct / Decimal('100.00')).quantize(Decimal('0.01'))

        if request.method != 'POST':
            initial_data = {}
            if active_amc:
                initial_data['amc_discount'] = calculated_amc_discount
            form = InvoiceForm(initial=initial_data)
        else:
            form = InvoiceForm(request.POST)

        if request.method == 'POST' and form.is_valid():
            inv = form.save(commit=False)
            inv.job_card = job
            if active_amc and not inv.amc_policy:
                inv.amc_policy = active_amc
            inv.save()
            messages.success(request, f"Invoice {inv.invoice_number} created successfully for Job Card {job.job_number}.")
            return redirect('invoice_detail', pk=inv.pk)
        
        return render(request, 'core/invoice_form.html', {
            'form': form,
            'job': job,
            'parts_used': parts_used,
            'parts_total': parts_total,
            'active_amc': active_amc,
            'calculated_amc_discount': calculated_amc_discount,
            'title': f'Create Invoice for {job.job_number}'
        })

    # Step 1: Select Job Card workflow
    q = request.GET.get('q', '').strip()
    available_jobs = JobCard.objects.filter(invoice__isnull=True).select_related('vehicle__customer', 'mechanic').order_by('-created_at')
    if q:
        available_jobs = available_jobs.filter(
            Q(job_number__icontains=q) |
            Q(vehicle__license_plate__icontains=q) |
            Q(vehicle__make__icontains=q) |
            Q(vehicle__model__icontains=q) |
            Q(vehicle__customer__name__icontains=q) |
            Q(vehicle__customer__phone__icontains=q)
        )

    return render(request, 'core/invoice_form.html', {
        'available_jobs': available_jobs,
        'q': q,
        'title': 'Create Invoice'
    })


@login_required
def invoice_detail(request, pk):
    invoice = get_object_or_404(Invoice.objects.select_related('job_card__vehicle__customer', 'amc_policy__plan'), pk=pk)
    active_amc = invoice.amc_policy or CustomerAMC.objects.filter(
        vehicle=invoice.job_card.vehicle,
        status='active',
        start_date__lte=timezone.now().date(),
        end_date__gte=timezone.now().date()
    ).select_related('plan').first()
    return render(request, 'core/invoice_detail.html', {'invoice': invoice, 'active_amc': active_amc})


@login_required
@role_required('owner', 'advisor')
def invoice_edit(request, pk):
    invoice = get_object_or_404(Invoice, pk=pk)
    active_amc = invoice.amc_policy or CustomerAMC.objects.filter(
        vehicle=invoice.job_card.vehicle,
        status='active',
        start_date__lte=timezone.now().date(),
        end_date__gte=timezone.now().date()
    ).select_related('plan').first()

    form = InvoiceForm(request.POST or None, instance=invoice)
    if request.method == 'POST' and form.is_valid():
        inv = form.save(commit=False)
        if active_amc and not inv.amc_policy:
            inv.amc_policy = active_amc
        inv.save()
        messages.success(request, "Invoice updated.")
        return redirect('invoice_detail', pk=pk)
    return render(request, 'core/invoice_form.html', {
        'form': form, 'job': invoice.job_card, 'invoice': invoice, 'active_amc': active_amc, 'title': 'Edit Invoice'
    })


# ─── Reports ──────────────────────────────────────────────────────────────────

@login_required
@role_required('owner')
def reports(request):
    today = date.today()
    month_start = today.replace(day=1)

    # Daily revenue
    daily_rev = Invoice.objects.filter(
        status='paid', issue_date=today
    ).aggregate(t=Sum('amount_paid'))['t'] or 0

    # Monthly revenue
    monthly_rev = Invoice.objects.filter(
        status='paid', issue_date__gte=month_start
    ).aggregate(t=Sum('amount_paid'))['t'] or 0

    # Pending jobs
    pending_jobs = JobCard.objects.exclude(status__in=['completed', 'delivered'])

    # Inventory value
    parts = SparePart.objects.all()
    inv_value = sum(p.unit_price * p.stock_quantity for p in parts)

    # Mechanic performance
    mechanics = User.objects.filter(profile__role='mechanic')
    perf = []
    for m in mechanics:
        total = JobCard.objects.filter(mechanic=m).count()
        done = JobCard.objects.filter(mechanic=m, status='completed').count()
        perf.append({'mechanic': m, 'total': total, 'completed': done})

    ctx = {
        'daily_revenue': daily_rev,
        'monthly_revenue': monthly_rev,
        'pending_jobs': pending_jobs,
        'inventory_value': inv_value,
        'mechanic_performance': perf,
        'low_stock': SparePart.objects.filter(stock_quantity__lte=5),
    }
    return render(request, 'core/reports.html', ctx)


@login_required
@role_required('owner')
def incentive_calculator(request):
    """
    Admin-only view for Incentive Calculation based on Bill Amount minus Expenses.
    """
    period = request.GET.get('period', 'this_month')
    rate_str = request.GET.get('rate', '10')
    from decimal import Decimal
    try:
        incentive_rate = Decimal(rate_str)
    except:
        incentive_rate = Decimal('10')

    today = date.today()
    if period == 'this_month':
        start_date = today.replace(day=1)
        end_date = today
    elif period == 'last_month':
        first_this_month = today.replace(day=1)
        end_date = first_this_month - timedelta(days=1)
        start_date = end_date.replace(day=1)
    else:
        start_date = None
        end_date = None

    # Bill Amount (Total Invoices Paid)
    invoices = Invoice.objects.filter(status='paid')
    if start_date and end_date:
        invoices = invoices.filter(issue_date__range=[start_date, end_date])
    
    total_bill_amount = invoices.aggregate(t=Sum('amount_paid'))['t'] or Decimal('0.00')

    # Overhead Expenses
    expenses_qs = Expense.objects.all()
    if start_date and end_date:
        expenses_qs = expenses_qs.filter(expense_date__range=[start_date, end_date])
    
    overhead_expenses = expenses_qs.aggregate(t=Sum('amount'))['t'] or Decimal('0.00')

    # Parts Used Expenses
    parts_usages = JobPartUsage.objects.all()
    if start_date and end_date:
        parts_usages = parts_usages.filter(job_card__created_at__date__range=[start_date, end_date])
    
    parts_expenses = sum(u.total_price for u in parts_usages)

    total_expenses = overhead_expenses + parts_expenses
    net_profit = total_bill_amount - total_expenses
    total_incentive_pool = max(Decimal('0.00'), net_profit * (incentive_rate / Decimal('100')))

    # Mechanic Breakdown
    mechanics = User.objects.filter(profile__role='mechanic')
    mechanic_breakdown = []
    for m in mechanics:
        m_jobs = JobCard.objects.filter(mechanic=m, status='completed')
        if start_date and end_date:
            m_jobs = m_jobs.filter(created_at__date__range=[start_date, end_date])
        
        m_labour = sum(j.labour_cost for j in m_jobs)
        m_parts_cost = sum(j.total_parts_cost() for j in m_jobs)
        m_net_profit = max(Decimal('0.00'), m_labour - m_parts_cost)
        m_incentive = m_net_profit * (incentive_rate / Decimal('100'))

        mechanic_breakdown.append({
            'mechanic': m,
            'completed_jobs': m_jobs.count(),
            'labour_revenue': m_labour,
            'parts_cost': m_parts_cost,
            'net_profit': m_net_profit,
            'incentive': m_incentive,
        })

    # Expense Form handling
    expense_form = ExpenseForm(request.POST or None)
    if request.method == 'POST' and 'add_expense' in request.POST and expense_form.is_valid():
        exp = expense_form.save(commit=False)
        exp.created_by = request.user
        exp.save()
        messages.success(request, f"Expense '{exp.title}' of ₹{exp.amount} added successfully.")
        return redirect('incentive_calculator')

    context = {
        'period': period,
        'rate': incentive_rate,
        'total_bill_amount': total_bill_amount,
        'overhead_expenses': overhead_expenses,
        'parts_expenses': parts_expenses,
        'total_expenses': total_expenses,
        'net_profit': net_profit,
        'total_incentive_pool': total_incentive_pool,
        'mechanic_breakdown': mechanic_breakdown,
        'expenses_list': expenses_qs.order_by('-expense_date')[:15],
        'expense_form': expense_form,
    }
    return render(request, 'core/incentive_calculator.html', context)


@login_required
@role_required('owner')
def expense_delete(request, pk):
    exp = get_object_or_404(Expense, pk=pk)
    if request.method == 'POST':
        title = exp.title
        exp.delete()
        messages.success(request, f"Expense '{title}' removed.")
        return redirect('incentive_calculator')
    return render(request, 'core/confirm_delete.html', {'obj': exp, 'type': 'Workshop Expense'})


# ─── AMC Management ───────────────────────────────────────────────────────────

@login_required
@role_required('owner', 'advisor')
def amc_list(request):
    amcs = CustomerAMC.objects.select_related('vehicle__customer', 'plan').all().order_by('-created_at')
    plans = AMCPlan.objects.all()
    
    # Upcoming services in next 15 days or overdue
    today = date.today()
    upcoming_services = AMCServiceSchedule.objects.filter(
        status='scheduled',
        scheduled_date__lte=today + timedelta(days=15)
    ).select_related('amc__vehicle__customer').order_by('scheduled_date')

    return render(request, 'core/amc_list.html', {
        'amcs': amcs,
        'plans': plans,
        'upcoming_services': upcoming_services
    })


@login_required
@role_required('owner', 'advisor')
def amc_plan_create(request):
    form = AMCPlanForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, "AMC Plan created successfully.")
        return redirect('amc_list')
    return render(request, 'core/amc_plan_form.html', {'form': form, 'title': 'Create AMC Plan'})


@login_required
@role_required('owner', 'advisor')
def amc_create(request):
    form = CustomerAMCForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        amc = form.save(commit=False)
        start = amc.start_date
        plan = amc.plan
        
        # Calculate end date
        end = start + timedelta(days=plan.duration_months * 30)
        amc.end_date = end
        amc.save()

        # Generate service schedule
        interval_days = (plan.duration_months * 30) // plan.services_included
        for i in range(1, plan.services_included + 1):
            scheduled_d = start + timedelta(days=interval_days * i)
            AMCServiceSchedule.objects.create(
                amc=amc,
                service_number=i,
                scheduled_date=scheduled_d,
                status='scheduled'
            )

        messages.success(request, f"AMC Contract {amc.contract_number} created with {plan.services_included} scheduled services.")
        return redirect('amc_detail', pk=amc.pk)
    return render(request, 'core/amc_form.html', {'form': form, 'title': 'Create Customer AMC'})


@login_required
def amc_detail(request, pk):
    amc = get_object_or_404(CustomerAMC, pk=pk)
    schedules = amc.schedules.all().order_by('service_number')
    return render(request, 'core/amc_detail.html', {'amc': amc, 'schedules': schedules})


# ─── WhatsApp Integration ──────────────────────────────────────────────────────

@login_required
def send_whatsapp_view(request):
    msg_type = request.GET.get('type')
    recipient_phone = request.GET.get('phone', '').replace(' ', '').replace('-', '')
    recipient_name = request.GET.get('name', 'Customer')
    
    if not recipient_phone:
        messages.error(request, "Invalid recipient phone number.")
        return redirect('dashboard')

    # Format phone with country code default (assuming India +91 if length 10)
    if len(recipient_phone) == 10:
        clean_phone = '91' + recipient_phone
    else:
        clean_phone = recipient_phone.lstrip('+')

    message_text = ""

    if msg_type == 'job_created':
        job_id = request.GET.get('job_id')
        job = get_object_or_404(JobCard, pk=job_id)
        est_str = job.estimated_completion_time.strftime('%d %b %Y %H:%M') if job.estimated_completion_time else 'Not specified'
        message_text = (
            f"🚗 *Auto Garage - Job Card Created*\n\n"
            f"Dear *{recipient_name}*,\n\n"
            f"Your vehicle *{job.vehicle.make} {job.vehicle.model}* ({job.vehicle.license_plate}) has been registered for service.\n\n"
            f"📋 *Job Card:* {job.job_number}\n"
            f"⏱️ *Est. Completion:* {est_str}\n"
            f"📌 *Status:* {job.get_status_display()}\n\n"
            f"We will notify you once the work is completed! Thank you for choosing Auto Garage! 🚘"
        )
    elif msg_type in ['job_completed', 'job_status']:
        job_id = request.GET.get('job_id')
        job = get_object_or_404(JobCard, pk=job_id)
        status_disp = job.get_status_display()
        if job.status == 'completed':
            cost = job.total_cost()
            message_text = (
                f"🚗 *Auto Garage Service Update*\n\n"
                f"Dear *{recipient_name}*,\n\n"
                f"Good news! Your vehicle *{job.vehicle.make} {job.vehicle.model}* ({job.vehicle.license_plate}) service is *COMPLETED* and ready for pickup! 🎉\n\n"
                f"📋 *Job Card:* {job.job_number}\n"
                f"💰 *Total Amount:* ₹{cost:.2f}\n\n"
                f"Thank you for choosing Auto Garage! Drive safe! 🚘✨"
            )
        elif job.status == 'delivered':
            message_text = (
                f"🚗 *Auto Garage Service Update*\n\n"
                f"Dear *{recipient_name}*,\n\n"
                f"Your vehicle *{job.vehicle.make} {job.vehicle.model}* ({job.vehicle.license_plate}) service is *DELIVERED*! 🚘\n\n"
                f"📋 *Job Card:* {job.job_number}\n\n"
                f"Thank you for choosing Auto Garage! Have a great drive! ✨"
            )
        elif job.status == 'waiting_parts':
            message_text = (
                f"🚗 *Auto Garage Service Update*\n\n"
                f"Dear *{recipient_name}*,\n\n"
                f"Update on your vehicle *{job.vehicle.make} {job.vehicle.model}* ({job.vehicle.license_plate}):\n\n"
                f"📋 *Job Card:* {job.job_number}\n"
                f"📌 *Status:* *WAITING FOR PARTS* 🛠️\n\n"
                f"We are waiting for required spare parts and will resume work as soon as they arrive. Thank you for your patience! 🚘"
            )
        elif job.status == 'in_progress':
            message_text = (
                f"🚗 *Auto Garage Service Update*\n\n"
                f"Dear *{recipient_name}*,\n\n"
                f"Update on your vehicle *{job.vehicle.make} {job.vehicle.model}* ({job.vehicle.license_plate}):\n\n"
                f"📋 *Job Card:* {job.job_number}\n"
                f"📌 *Status:* *IN PROGRESS* 🔧\n\n"
                f"Our team is actively working on your vehicle service."
            )
        else:
            message_text = (
                f"🚗 *Auto Garage Service Update*\n\n"
                f"Dear *{recipient_name}*,\n\n"
                f"Update on your vehicle *{job.vehicle.make} {job.vehicle.model}* ({job.vehicle.license_plate}):\n\n"
                f"📋 *Job Card:* {job.job_number}\n"
                f"📌 *Status:* *{status_disp.upper()}*\n\n"
                f"We will notify you as soon as the status changes. Thank you for your patience! 🚘"
            )
    elif msg_type in ['invoice_share', 'invoice']:
        invoice_id = request.GET.get('invoice_id')
        invoice = get_object_or_404(Invoice, pk=invoice_id)
        job = invoice.job_card
        customer = job.vehicle.customer
        
        lines = [
            f"🧾 *Krishna Auto Care - Tax Invoice #{invoice.invoice_number}*",
            f"",
            f"Dear *{customer.name}*,",
            f"Here is the invoice summary for your vehicle *{job.vehicle.make} {job.vehicle.model}* ({job.vehicle.license_plate}):",
            f"",
            f"📋 *Job Card:* {job.job_number}",
            f"📅 *Invoice Date:* {invoice.issue_date.strftime('%d %b %Y')}",
            f"🔧 *Labour Charges:* ₹{job.labour_cost:.2f}",
            f"⚙️ *Parts Charges:* ₹{job.total_parts_cost():.2f}"
        ]
        if invoice.amc_discount > 0:
            lines.append(f"🛡️ *AMC Policy Discount:* -₹{invoice.amc_discount:.2f}")
        if invoice.is_pickup_service and invoice.pickup_charge:
            lines.append(f"🚚 *Pickup & Drop Charge:* ₹{invoice.pickup_charge:.2f}")
        
        lines.extend([
            f"📊 *Tax (GST 5%):* ₹{invoice.tax_amount:.2f}",
            f"💰 *Grand Total:* ₹{invoice.grand_total:.2f}",
            f"💳 *Status:* *{invoice.get_status_display().upper()}*",
            f"💵 *Amount Paid:* ₹{invoice.amount_paid:.2f}",
            f"🚨 *Balance Due:* ₹{invoice.balance_due:.2f}",
            f"",
            f"Thank you for choosing Krishna Auto Care! 🚘✨"
        ])
        message_text = "\n".join(lines)
    elif msg_type == 'amc_reminder':
        schedule_id = request.GET.get('schedule_id')
        schedule = get_object_or_404(AMCServiceSchedule, pk=schedule_id)
        message_text = (
            f"🛠️ *Auto Garage - AMC Service Due Reminder*\n\n"
            f"Dear *{recipient_name}*,\n\n"
            f"This is a friendly reminder that your AMC Service #{schedule.service_number} for vehicle *{schedule.amc.vehicle.make} {schedule.amc.vehicle.model}* ({schedule.amc.vehicle.license_plate}) is due on *{schedule.scheduled_date}*.\n\n"
            f"📜 *AMC Contract:* {schedule.amc.contract_number}\n\n"
            f"Please reply or call us to book your convenient service slot! 🚘"
        )
    elif msg_type == 'amc_renewal':
        amc_id = request.GET.get('amc_id')
        amc = get_object_or_404(CustomerAMC, pk=amc_id)
        message_text = (
            f"📋 *Auto Garage - AMC Renewal Reminder*\n\n"
            f"Dear *{recipient_name}*,\n\n"
            f"Your Annual Maintenance Contract (*{amc.contract_number}*) for *{amc.vehicle.make} {amc.vehicle.model}* ({amc.vehicle.license_plate}) expires on *{amc.end_date}*.\n\n"
            f"Renew today to continue enjoying priority service and special discounts!\n"
            f"Contact us to extend your coverage. 🚗"
        )

    import urllib.parse
    encoded_text = urllib.parse.quote(message_text)
    wa_url = f"https://api.whatsapp.com/send?phone={clean_phone}&text={encoded_text}"

    # Log WhatsApp dispatch
    WhatsAppLog.objects.create(
        recipient_name=recipient_name,
        phone=recipient_phone,
        message_type=msg_type or 'custom',
        message_body=message_text,
        sent_by=request.user
    )

    return redirect(wa_url)

