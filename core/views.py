from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.db.models import Sum, Count, Q
from django.utils import timezone
from datetime import date, timedelta
from functools import wraps

from .models import (
    UserProfile, Customer, Vehicle, JobCard, JobCardPhoto,
    SparePart, PartCategory, Supplier, StockTransaction, JobPartUsage, Invoice,
    AMCPlan, CustomerAMC, AMCServiceSchedule, WhatsAppLog, Expense
)
from .forms import (
    LoginForm, StaffCreationForm, StaffEditForm, CustomerForm, VehicleForm, JobCardForm, JobCardPhotoForm,
    JobStatusForm, SparePartForm, PartCategoryForm, SupplierForm,
    StockTransactionForm, JobPartUsageForm, InvoiceForm,
    AMCPlanForm, CustomerAMCForm, ExpenseForm
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
                if profile.role in roles or request.user.is_superuser:
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

    if request.method == 'POST' and form.is_valid():
        user = form.get_user()
        role_selected = form.cleaned_data.get("role")

        if hasattr(user, "profile"):
            if user.profile.role != role_selected:
                messages.error(request, "Incorrect role selected.")
                return render(request, 'core/login.html', {'form': form})

        login(request, user)
        return redirect('dashboard')

    return render(request, 'core/login.html', {'form': form})


@login_required
def logout_view(request):
    logout(request)
    return redirect('login')


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
    elif role == 'mechanic':
        return redirect('mechanic_dashboard')
    elif role == 'store_manager':
        return redirect('store_dashboard')
    return render(request, 'core/dashboard_base.html')


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

    mechanics = User.objects.filter(profile__role='mechanic')
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
    staff = UserProfile.objects.select_related('user').exclude(role='owner')
    return render(request, 'core/staff_list.html', {'staff': staff})


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


# ─── Vehicle Management ───────────────────────────────────────────────────────

@login_required
@role_required('owner', 'advisor')
def vehicle_list(request):
    vehicles = Vehicle.objects.select_related('customer').all()
    return render(request, 'core/vehicle_list.html', {'vehicles': vehicles})


@login_required
@role_required('owner', 'advisor')
def vehicle_create(request):
    files = request.FILES.copy() if request.FILES else None
    if files and 'image' in files and (not files['image'] or getattr(files['image'], 'size', 0) == 0):
        del files['image']
    form = VehicleForm(request.POST or None, files or None)
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


# ─── Job Card Management ─────────────────────────────────────────────────────

@login_required
@role_required('owner', 'advisor')
def job_list(request):
    status = request.GET.get('status', '')
    jobs = JobCard.objects.select_related('vehicle__customer', 'mechanic', 'advisor').all()
    if status:
        jobs = jobs.filter(status=status)
    jobs = jobs.order_by('-created_at')
    return render(request, 'core/job_list.html', {'jobs': jobs, 'status_filter': status})


@login_required
def job_search_records(request):
    q = request.GET.get('q', '').strip()
    results = []
    if len(q) >= 2:
        vehicles = Vehicle.objects.filter(
            Q(license_plate__icontains=q) |
            Q(model__icontains=q) |
            Q(make__icontains=q) |
            Q(customer__name__icontains=q) |
            Q(customer__phone__icontains=q)
        ).select_related('customer')[:10]
        
        for v in vehicles:
            results.append({
                'customer_name': v.customer.name,
                'customer_phone': v.customer.phone,
                'vehicle_number': v.license_plate,
                'vehicle_model': f"{v.make} {v.model}".strip(),
                'vehicle_color': v.color
            })
            
        if len(results) < 5:
            existing_phones = {r['customer_phone'] for r in results}
            customers = Customer.objects.filter(
                Q(name__icontains=q) | Q(phone__icontains=q)
            ).exclude(phone__in=existing_phones)[:5]
            for c in customers:
                results.append({
                    'customer_name': c.name,
                    'customer_phone': c.phone,
                    'vehicle_number': '',
                    'vehicle_model': '',
                    'vehicle_color': ''
                })
                
    return JsonResponse({'results': results})


@login_required
@role_required('owner', 'advisor')
def job_create(request):
    form = JobCardForm(request.POST or None, request.FILES or None)
    if request.method == 'POST' and form.is_valid():
        job = form.save(commit=False)
        c_name = form.cleaned_data['customer_name'].strip()
        c_phone = form.cleaned_data['customer_phone'].strip()
        v_num = form.cleaned_data['vehicle_number'].strip().upper()
        v_model_raw = form.cleaned_data['vehicle_model'].strip()
        v_color = form.cleaned_data.get('vehicle_color', '').strip()

        # Find or create customer by phone number
        customer, _ = Customer.objects.get_or_create(
            phone=c_phone,
            defaults={'name': c_name, 'created_by': request.user}
        )
        if customer.name != c_name:
            customer.name = c_name
            customer.save()

        # Split model string into make and model if space separated
        model_parts = v_model_raw.split()
        v_make = model_parts[0] if model_parts else "Vehicle"
        v_model = ' '.join(model_parts[1:]) if len(model_parts) > 1 else v_model_raw

        # Get or create Vehicle record dynamically
        vehicle, _ = Vehicle.objects.get_or_create(
            license_plate=v_num,
            defaults={
                'customer': customer,
                'make': v_make,
                'model': v_model,
                'color': v_color,
                'year': timezone.now().year
            }
        )
        # Update vehicle details if existing
        vehicle.customer = customer
        if v_make: vehicle.make = v_make
        if v_model: vehicle.model = v_model
        if v_color: vehicle.color = v_color
        vehicle.save()

        job.vehicle = vehicle
        job.advisor = request.user
        job.save()

        images = request.FILES.getlist('photos')
        for img in images:
            JobCardPhoto.objects.create(job_card=job, image=img)
        
        # Trigger SMS Notification on Job Card Creation
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
        messages.success(request, f"Job card {job.job_number} created with {len(images)} photo(s). SMS notification sent to customer ({customer.phone}).")
        return redirect('job_detail', pk=job.pk)
    return render(request, 'core/job_form.html', {'form': form, 'title': 'Create Job Card'})


@login_required
def job_detail(request, pk):
    job = get_object_or_404(JobCard, pk=pk)
    parts_used = job.parts_used.select_related('part').all()
    photos = job.photos.all().order_by('-uploaded_at')
    part_form = JobPartUsageForm()
    photo_form = JobCardPhotoForm()
    return render(request, 'core/job_detail.html', {
        'job': job, 'parts_used': parts_used, 'photos': photos,
        'part_form': part_form, 'photo_form': photo_form
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
    form = JobStatusForm(request.POST or None, instance=job)
    if request.method == 'POST' and form.is_valid():
        updated_job = form.save(commit=False)
        
        # Save customer and vehicle changes
        c_name = form.cleaned_data.get('customer_name', '').strip()
        c_phone = form.cleaned_data.get('customer_phone', '').strip()
        v_num = form.cleaned_data.get('vehicle_number', '').strip().upper()
        v_model_raw = form.cleaned_data.get('vehicle_model', '').strip()
        v_color = form.cleaned_data.get('vehicle_color', '').strip()

        if c_name and c_phone and updated_job.vehicle:
            cust = updated_job.vehicle.customer
            cust.name = c_name
            cust.phone = c_phone
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
        customer = updated_job.vehicle.customer
        status_disp = updated_job.get_status_display()
        
        # Trigger SMS Notification on Job Card Status Update
        if updated_job.status == 'completed':
            sms_body = (
                f"Dear {customer.name}, great news! Your vehicle {updated_job.vehicle.make} {updated_job.vehicle.model} "
                f"({updated_job.vehicle.license_plate}) service (Job Card {updated_job.job_number}) is COMPLETED and ready for pickup! "
                f"Total Cost: ${updated_job.total_cost():.2f}."
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
def job_add_part(request, pk):
    job = get_object_or_404(JobCard, pk=pk)
    if request.method == 'POST':
        form = JobPartUsageForm(request.POST)
        if form.is_valid():
            usage = form.save(commit=False)
            usage.job_card = job
            usage.save()
            # Deduct from stock
            part = usage.part
            part.stock_quantity = max(0, part.stock_quantity - usage.quantity)
            part.save()
            messages.success(request, f"Part '{part.name}' added to job.")
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
    q = request.GET.get('q', '')
    parts = SparePart.objects.select_related('category', 'supplier').all()
    if q:
        parts = parts.filter(Q(name__icontains=q) | Q(part_number__icontains=q))
    return render(request, 'core/parts_list.html', {'parts': parts, 'q': q})


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
        tx.save()
        # Update stock
        part = tx.part
        if tx.transaction_type == 'in':
            part.stock_quantity += tx.quantity
        else:
            part.stock_quantity = max(0, part.stock_quantity - tx.quantity)
        part.save()
        messages.success(request, "Stock transaction recorded.")
        return redirect('store_dashboard')
    return render(request, 'core/stock_form.html', {'form': form, 'title': 'Stock Transaction'})


# ─── Categories & Suppliers ───────────────────────────────────────────────────

@login_required
@role_required('owner', 'store_manager')
def category_list(request):
    cats = PartCategory.objects.all()
    return render(request, 'core/category_list.html', {'categories': cats})


@login_required
@role_required('owner', 'store_manager')
def category_create(request):
    form = PartCategoryForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, "Category created.")
        return redirect('category_list')
    return render(request, 'core/category_form.html', {'form': form, 'title': 'Add Category'})


@login_required
@role_required('owner', 'store_manager')
def supplier_list(request):
    suppliers = Supplier.objects.all()
    return render(request, 'core/supplier_list.html', {'suppliers': suppliers})


@login_required
@role_required('owner', 'store_manager')
def supplier_create(request):
    form = SupplierForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, "Supplier added.")
        return redirect('supplier_list')
    return render(request, 'core/supplier_form.html', {'form': form, 'title': 'Add Supplier'})


# ─── Billing / Invoices ───────────────────────────────────────────────────────

@login_required
@role_required('owner', 'advisor')
def invoice_list(request):
    invoices = Invoice.objects.select_related('job_card__vehicle__customer').order_by('-id')
    return render(request, 'core/invoice_list.html', {'invoices': invoices})


@login_required
@role_required('owner', 'advisor')
def invoice_create(request, job_pk):
    job = get_object_or_404(JobCard, pk=job_pk)
    if hasattr(job, 'invoice'):
        return redirect('invoice_detail', pk=job.invoice.pk)
    form = InvoiceForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        inv = form.save(commit=False)
        inv.job_card = job
        inv.save()
        messages.success(request, f"Invoice {inv.invoice_number} created.")
        return redirect('invoice_detail', pk=inv.pk)
    return render(request, 'core/invoice_form.html', {'form': form, 'job': job, 'title': 'Create Invoice'})


@login_required
def invoice_detail(request, pk):
    invoice = get_object_or_404(Invoice, pk=pk)
    return render(request, 'core/invoice_detail.html', {'invoice': invoice})


@login_required
@role_required('owner', 'advisor')
def invoice_edit(request, pk):
    invoice = get_object_or_404(Invoice, pk=pk)
    form = InvoiceForm(request.POST or None, instance=invoice)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, "Invoice updated.")
        return redirect('invoice_detail', pk=pk)
    return render(request, 'core/invoice_form.html', {
        'form': form, 'job': invoice.job_card, 'title': 'Edit Invoice'
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

