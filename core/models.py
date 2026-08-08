from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from decimal import Decimal


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
        d = dict(self.ROLE_CHOICES)
        return d.get(self.role, self.role.title())

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} ({self.get_role_display_name()})"


class Customer(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=20)
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
    notes = models.TextField(blank=True)

    def save(self, *args, **kwargs):
        if not self.job_number:
            last = JobCard.objects.order_by('-id').first()
            num = (last.id + 1) if last else 1
            self.job_number = f"JC-{num:05d}"
        if self.status == 'completed' and not self.completed_at:
            self.completed_at = timezone.now()
        super().save(*args, **kwargs)

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
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    payment_method = models.CharField(max_length=50, blank=True)
    notes = models.TextField(blank=True)

    def save(self, *args, **kwargs):
        if not self.invoice_number:
            last = Invoice.objects.order_by('-id').first()
            num = (last.id + 1) if last else 1
            self.invoice_number = f"INV-{num:05d}"
        super().save(*args, **kwargs)

    @property
    def subtotal(self):
        return self.job_card.total_cost()

    @property
    def total_amount(self):
        if self.is_pickup_service and self.pickup_charge:
            return self.subtotal + self.pickup_charge
        return self.subtotal

    @property
    def balance_due(self):
        return self.grand_total - self.amount_paid

    @property
    def tax_amount(self):
        return self.total_amount * Decimal('0.05')

    @property
    def grand_total(self):
        return self.total_amount + self.tax_amount

    def __str__(self):
        return f"{self.invoice_number} - {self.job_card.vehicle.customer.name}"


class AMCPlan(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    duration_months = models.PositiveIntegerField(default=12)
    services_included = models.PositiveIntegerField(default=4)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.duration_months} Months / {self.services_included} Services)"


class CustomerAMC(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('expired', 'Expired'),
        ('cancelled', 'Cancelled'),
    ]
    contract_number = models.CharField(max_length=30, unique=True, blank=True)
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name='amc_contracts')
    plan = models.ForeignKey(AMCPlan, on_delete=models.PROTECT)
    start_date = models.DateField(default=timezone.now)
    end_date = models.DateField()
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='active')
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.contract_number:
            last = CustomerAMC.objects.order_by('-id').first()
            num = (last.id + 1) if last else 1
            self.contract_number = f"AMC-{num:05d}"
        super().save(*args, **kwargs)

    @property
    def is_expiring_soon(self):
        if self.status != 'active':
            return False
        days_left = (self.end_date - date.today()).days
        return 0 <= days_left <= 30

    def __str__(self):
        return f"{self.contract_number} - {self.vehicle}"


class AMCServiceSchedule(models.Model):
    STATUS_CHOICES = [
        ('scheduled', 'Scheduled'),
        ('completed', 'Completed'),
        ('overdue', 'Overdue'),
        ('cancelled', 'Cancelled'),
    ]
    amc = models.ForeignKey(CustomerAMC, on_delete=models.CASCADE, related_name='schedules')
    service_number = models.PositiveIntegerField()
    scheduled_date = models.DateField()
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='scheduled')
    job_card = models.ForeignKey(JobCard, on_delete=models.SET_NULL, null=True, blank=True, related_name='amc_service')
    notes = models.TextField(blank=True)

    @property
    def is_due_soon(self):
        if self.status != 'scheduled':
            return False
        days = (self.scheduled_date - date.today()).days
        return -7 <= days <= 7

    def __str__(self):
        return f"Service #{self.service_number} for {self.amc.contract_number}"


class WhatsAppLog(models.Model):
    recipient_name = models.CharField(max_length=100)
    phone = models.CharField(max_length=20)
    message_type = models.CharField(max_length=50) # service_completion, amc_reminder, amc_renewal
    message_body = models.TextField()
    sent_at = models.DateTimeField(auto_now_add=True)
    sent_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return f"{self.message_type} to {self.recipient_name} ({self.sent_at.strftime('%Y-%m-%d %H:%M')})"

