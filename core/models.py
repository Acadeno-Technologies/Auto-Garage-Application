from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import date
from decimal import Decimal


def to_camel_case(text):
    """Convert text to Camel Case (Title Case).
    Example: 'hello world' -> 'Hello World'
    """
    if not text:
        return text
    return ' '.join(word.capitalize() for word in text.split())


class RoleCustomization(models.Model):
    role_key = models.CharField(max_length=50, unique=True)
    display_name = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.role_key} -> {self.display_name}"


class UserProfile(models.Model):
    ROLE_CHOICES = [
        ('owner', 'Owner'),
        ('advisor', 'Service Advisor'),
        ('mechanic', 'Mechanic'),
        ('store_manager', 'Store Manager'),
        ('custom', 'Custom Role'),
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=50, choices=ROLE_CHOICES, default='mechanic')
    custom_role = models.CharField(max_length=50, blank=True, null=True, verbose_name="Custom Role Title")
    phone = models.CharField(max_length=20, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def get_role_display_name(self):
        if self.role == 'custom' and self.custom_role:
            return self.custom_role
        default_names = {
            'owner': 'Owner',
            'advisor': 'Service Advisor',
            'mechanic': 'Mechanic',
            'store_manager': 'Store Manager',
            'custom': 'Custom Role',
        }
        def_name = default_names.get(self.role, self.role.title())
        try:
            rc = RoleCustomization.objects.filter(role_key=self.role).first()
            if rc and rc.display_name.strip():
                return rc.display_name.strip()
        except Exception:
            pass
        return def_name

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} ({self.get_role_display_name()})"


class Customer(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=20, unique=True)
    address = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return self.name


class Vehicle(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='vehicles')
    make = models.CharField(max_length=50)
    model = models.CharField(max_length=50)
    year = models.PositiveIntegerField()
    license_plate = models.CharField(max_length=20, unique=True)
    vin = models.CharField(max_length=50, blank=True)
    color = models.CharField(max_length=30, blank=True)
    mileage = models.PositiveIntegerField(default=0)
    image = models.ImageField(upload_to='vehicles/', null=True, blank=True, verbose_name="Vehicle Photo")

    def __str__(self):
        return f"{self.year} {self.make} {self.model} ({self.license_plate})"


class JobCard(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('waiting_parts', 'Waiting for Parts'),
        ('completed', 'Completed'),
        ('delivered', 'Delivered'),
    ]
    job_number = models.CharField(max_length=20, unique=True, blank=True)
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name='job_cards')
    advisor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='advised_jobs')
    mechanic = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_jobs')
    problem_description = models.TextField()
    repair_instructions = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    estimated_completion_time = models.DateTimeField(null=True, blank=True, verbose_name="Estimated Completion Time")
    labour_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    amc_service = models.ForeignKey('AMCServiceSchedule', on_delete=models.SET_NULL, null=True, blank=True, related_name='job_cards')
    notes = models.TextField(blank=True)

    def save(self, *args, **kwargs):
        if not self.job_number:
            last = JobCard.objects.order_by('-id').first()
            num = (last.id + 1) if last else 1
            self.job_number = f"JC-{num:05d}"
        if self.status == 'completed' and not self.completed_at:
            self.completed_at = timezone.now()
        
        # Apply Camel Case formatting to text fields
        if self.problem_description:
            self.problem_description = to_camel_case(self.problem_description)
        if self.repair_instructions:
            self.repair_instructions = to_camel_case(self.repair_instructions)
        if self.notes:
            self.notes = to_camel_case(self.notes)
        
        super().save(*args, **kwargs)

        # Update AMC service schedule status when job card is completed
        if self.amc_service and self.status in ['completed', 'delivered']:
            if self.amc_service.status != 'completed':
                self.amc_service.status = 'completed'
                self.amc_service.completed_date = date.today()
                self.amc_service.job_card = self
                self.amc_service.save()

    def total_parts_cost(self):
        return sum(u.total_price for u in self.parts_used.all())

    def total_cost(self):
        return self.labour_cost + self.total_parts_cost()

    def __str__(self):
        return f"{self.job_number} - {self.vehicle}"


class JobCardPhoto(models.Model):
    job_card = models.ForeignKey(JobCard, on_delete=models.CASCADE, related_name='photos')
    image = models.ImageField(upload_to='job_photos/')
    caption = models.CharField(max_length=255, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Photo for {self.job_card.job_number} ({self.uploaded_at.strftime('%Y-%m-%d %H:%M')})"


class PartCategory(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "Part Categories"


class Supplier(models.Model):
    name = models.CharField(max_length=100)
    contact_person = models.CharField(max_length=100, blank=True)
    phone = models.CharField(max_length=20)
    email = models.EmailField(blank=True)
    address = models.TextField(blank=True)

    def __str__(self):
        return self.name


class SparePart(models.Model):
    name = models.CharField(max_length=150)
    part_number = models.CharField(max_length=50, unique=True)
    category = models.ForeignKey(PartCategory, on_delete=models.SET_NULL, null=True)
    supplier = models.ForeignKey(Supplier, on_delete=models.SET_NULL, null=True, blank=True)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    stock_quantity = models.PositiveIntegerField(default=0)
    minimum_stock = models.PositiveIntegerField(default=5)
    location = models.CharField(max_length=50, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def is_low_stock(self):
        return self.stock_quantity <= self.minimum_stock

    def __str__(self):
        return f"{self.name} ({self.part_number})"


class StockTransaction(models.Model):
    TYPE_CHOICES = [
        ('in', 'Stock In'),
        ('out', 'Stock Out'),
    ]
    part = models.ForeignKey(SparePart, on_delete=models.CASCADE, related_name='transactions')
    transaction_type = models.CharField(max_length=5, choices=TYPE_CHOICES)
    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    reference = models.CharField(max_length=100, blank=True)
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.get_transaction_type_display()} - {self.part.name} x{self.quantity}"


class JobPartUsage(models.Model):
    job_card = models.ForeignKey(JobCard, on_delete=models.CASCADE, related_name='parts_used')
    part = models.ForeignKey(SparePart, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)

    @property
    def total_price(self):
        return self.quantity * self.unit_price

    def __str__(self):
        return f"{self.part.name} x{self.quantity} for {self.job_card.job_number}"


class Invoice(models.Model):
    STATUS_CHOICES = [
        ('unpaid', 'Unpaid'),
        ('paid', 'Paid'),
        ('partial', 'Partial'),
    ]
    invoice_number = models.CharField(max_length=20, unique=True, blank=True)
    job_card = models.OneToOneField(JobCard, on_delete=models.CASCADE, related_name='invoice')
    issue_date = models.DateField(auto_now_add=True)
    due_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='unpaid')
    is_pickup_service = models.BooleanField(default=False, verbose_name="Vehicle Pickup & Drop Service")
    pickup_charge = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'), verbose_name="Pickup & Drop Charge")
    amc_discount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'), verbose_name="AMC Discount Amount")
    amc_policy = models.ForeignKey('CustomerAMC', null=True, blank=True, on_delete=models.SET_NULL, related_name='invoices')
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    payment_method = models.CharField(max_length=50, blank=True)
    notes = models.TextField(blank=True)

    def save(self, *args, **kwargs):
        if not self.invoice_number:
            last = Invoice.objects.order_by('-id').first()
            num = (last.id + 1) if last else 1
            self.invoice_number = f"INV-{num:05d}"
        
        paid = self.amount_paid or Decimal('0.00')
        gt = self.grand_total
        if gt <= Decimal('0.00') or paid >= gt:
            self.status = 'paid'
        elif paid > Decimal('0.00'):
            self.status = 'partial'
        else:
            self.status = 'unpaid'
        super().save(*args, **kwargs)

    @property
    def subtotal(self):
        return self.job_card.total_cost()

    @property
    def subtotal_after_discount(self):
        return max(Decimal('0.00'), self.subtotal - self.amc_discount)

    @property
    def total_amount(self):
        if self.is_pickup_service and self.pickup_charge:
            return self.subtotal_after_discount + self.pickup_charge
        return self.subtotal_after_discount

    @property
    def tax_amount(self):
        return (self.total_amount * Decimal('0.05')).quantize(Decimal('0.01'))

    @property
    def grand_total(self):
        return self.total_amount + self.tax_amount

    @property
    def balance_due(self):
        return max(Decimal('0.00'), self.grand_total - (self.amount_paid or Decimal('0.00')))

    def __str__(self):
        return f"{self.invoice_number} - {self.job_card.vehicle.customer.name}"


class AMCPlan(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    duration_months = models.PositiveIntegerField(default=12)
    services_included = models.PositiveIntegerField(default=4)
    service_interval_months = models.PositiveIntegerField(default=3, verbose_name="Service Interval (Months)")
    discount_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('100.00'), verbose_name="Labour/Service Discount %")
    is_active = models.BooleanField(default=True, verbose_name="Is Active Plan")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} (₹{self.price:,.0f} | {self.duration_months} Months / {self.services_included} Services)"


class CustomerAMC(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('expired', 'Expired'),
        ('cancelled', 'Cancelled'),
    ]
    contract_number = models.CharField(max_length=30, unique=True, blank=True)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='amc_contracts', null=True, blank=True)
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name='amc_contracts')
    plan = models.ForeignKey(AMCPlan, on_delete=models.PROTECT)
    previous_contract = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='renewals')
    start_date = models.DateField(default=timezone.now)
    end_date = models.DateField()
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='active')
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if self.vehicle and self.vehicle.customer:
            self.customer = self.vehicle.customer
        if not self.contract_number:
            year = timezone.now().year
            last = CustomerAMC.objects.order_by('-id').first()
            num = (last.id + 1) if last else 1
            self.contract_number = f"AMC-{year}-{num:04d}"
        super().save(*args, **kwargs)

    @property
    def amount_payable(self):
        return self.plan.price if self.plan else Decimal('0.00')

    @property
    def balance_amount(self):
        return max(Decimal('0.00'), self.amount_payable - (self.amount_paid or Decimal('0.00')))

    @property
    def payment_status(self):
        paid = self.amount_paid or Decimal('0.00')
        payable = self.amount_payable
        if paid >= payable and payable > Decimal('0.00'):
            return 'paid'
        elif paid > Decimal('0.00'):
            return 'partially_paid'
        return 'unpaid'

    @property
    def computed_status(self):
        if self.status == 'cancelled':
            return 'cancelled'
        today = date.today()
        if today > self.end_date:
            return 'expired'
        days_left = (self.end_date - today).days
        if 0 <= days_left <= 30:
            return 'expiring_soon'
        return 'active'

    @property
    def is_expiring_soon(self):
        return self.computed_status == 'expiring_soon'

    @property
    def total_services(self):
        return self.plan.services_included if self.plan else 0

    @property
    def used_services(self):
        return self.schedules.filter(status='completed').count()

    @property
    def remaining_services(self):
        return max(0, self.total_services - self.used_services)

    def __str__(self):
        return f"{self.contract_number} - {self.vehicle.make} {self.vehicle.model} ({self.vehicle.license_plate})"


class AMCServiceSchedule(models.Model):
    STATUS_CHOICES = [
        ('upcoming', 'Upcoming'),
        ('due', 'Due'),
        ('completed', 'Completed'),
        ('overdue', 'Overdue'),
        ('cancelled', 'Cancelled'),
    ]
    amc = models.ForeignKey(CustomerAMC, on_delete=models.CASCADE, related_name='schedules')
    service_number = models.PositiveIntegerField()
    scheduled_date = models.DateField()
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='upcoming')
    completed_date = models.DateField(null=True, blank=True)
    job_card = models.ForeignKey(JobCard, on_delete=models.SET_NULL, null=True, blank=True, related_name='amc_schedules')
    notes = models.TextField(blank=True)

    @property
    def computed_status(self):
        if self.status == 'completed':
            return 'completed'
        if self.status == 'cancelled':
            return 'cancelled'
        today = date.today()
        if self.scheduled_date < today:
            return 'overdue'
        if self.scheduled_date == today:
            return 'due'
        return 'upcoming'

    @property
    def is_due_soon(self):
        if self.status in ['completed', 'cancelled']:
            return False
        days = (self.scheduled_date - date.today()).days
        return -15 <= days <= 15

    def __str__(self):
        return f"Service #{self.service_number} for {self.amc.contract_number} (Due: {self.scheduled_date})"


class WhatsAppLog(models.Model):
    recipient_name = models.CharField(max_length=100)
    phone = models.CharField(max_length=20)
    message_type = models.CharField(max_length=50) # service_completion, amc_reminder, amc_renewal
    message_body = models.TextField()
    sent_at = models.DateTimeField(auto_now_add=True)
    sent_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return f"{self.message_type} to {self.recipient_name} ({self.sent_at.strftime('%Y-%m-%d %H:%M')})"


class Expense(models.Model):
    CATEGORY_CHOICES = [
        ('utilities', 'Electricity & Utilities'),
        ('rent', 'Garage Rent'),
        ('tools', 'Tools & Equipment'),
        ('salary', 'Staff Salary / Advance'),
        ('parts_purchase', 'Parts Purchase'),
        ('other', 'Other Expenses'),
    ]
    title = models.CharField(max_length=150)
    category = models.CharField(max_length=30, choices=CATEGORY_CHOICES, default='other')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    expense_date = models.DateField(default=timezone.now)
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} - ₹{self.amount} ({self.expense_date})"


class GarageSettings(models.Model):
    name = models.CharField(max_length=150, default="Krishna Auto Care", verbose_name="Garage / Workshop Name")
    tagline = models.CharField(max_length=200, default="Precision Workshop", blank=True, verbose_name="Tagline / Subtitle")
    phone = models.CharField(max_length=30, default="+91 98765 43210", blank=True, verbose_name="Contact Phone")
    email = models.EmailField(default="info@krishnaautocare.com", blank=True, verbose_name="Contact Email")
    address = models.TextField(default="Main Road, Near Bus Stand", blank=True, verbose_name="Street Address")
    city = models.CharField(max_length=100, default="Kochi", blank=True, verbose_name="City / Place")
    state = models.CharField(max_length=100, default="Kerala", blank=True, verbose_name="State")
    pincode = models.CharField(max_length=20, default="682001", blank=True, verbose_name="Pincode / Zip")
    gst_number = models.CharField(max_length=50, blank=True, verbose_name="GST / Tax ID Number")
    logo = models.ImageField(upload_to='garage/', null=True, blank=True, verbose_name="Garage Logo")
    updated_at = models.DateTimeField(auto_now=True)

    @classmethod
    def get_settings(cls):
        settings_obj, _ = cls.objects.get_or_create(
            id=1,
            defaults={
                'name': 'Krishna Auto Care',
                'tagline': 'Precision Workshop',
                'phone': '+91 98765 43210',
                'email': 'info@krishnaautocare.com',
                'address': 'Main Road, Near Bus Stand',
                'city': 'Kochi',
                'state': 'Kerala',
                'pincode': '682001'
            }
        )
        return settings_obj

    def __str__(self):
        return f"Garage Settings ({self.name})"


