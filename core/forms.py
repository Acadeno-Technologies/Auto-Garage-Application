from django import forms
from django.db.models import Q
from django.contrib.auth.models import User
from django.contrib.auth.forms import AuthenticationForm
from .models import (
    UserProfile, Customer, Vehicle, JobCard, JobCardPhoto,
    SparePart, PartCategory, Supplier, StockTransaction, JobPartUsage, Invoice,
    AMCPlan, CustomerAMC, AMCServiceSchedule, WhatsAppLog, Expense
)

ROLE_CHOICES = [
    ('owner', 'Owner'),
    ('advisor', 'Service Advisor'),
    ('mechanic', 'Mechanic'),
    ('store_manager', 'Store Manager'),
]

class LoginForm(AuthenticationForm):

    username = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'Username'
        })
    )

    role = forms.ChoiceField(
        choices=ROLE_CHOICES,
        widget=forms.Select(attrs={
            'class': 'form-input'
        })
    )

    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-input',
            'placeholder': 'Password'
        })
    )


class StaffCreationForm(forms.ModelForm):
    first_name = forms.CharField(max_length=50, widget=forms.TextInput(attrs={'class': 'form-input'}))
    last_name = forms.CharField(max_length=50, widget=forms.TextInput(attrs={'class': 'form-input'}))
    username = forms.CharField(max_length=150, widget=forms.TextInput(attrs={'class': 'form-input'}))
    email = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'form-input'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-input'}))
    role = forms.ChoiceField(
        choices=[c for c in UserProfile.ROLE_CHOICES if c[0] != 'owner'],
        widget=forms.Select(attrs={'class': 'form-input', 'id': 'id_role_select'})
    )
    custom_role = forms.CharField(
        max_length=50,
        required=False,
        label="Custom Role Title (Specify if 'Custom Role' is selected)",
        widget=forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'e.g. Senior Electrician, Front Desk, Accountant', 'id': 'id_custom_role_input'})
    )
    phone = forms.CharField(max_length=20, required=False, widget=forms.TextInput(attrs={'class': 'form-input'}))

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'username', 'email']


class StaffEditForm(forms.ModelForm):
    first_name = forms.CharField(max_length=50, widget=forms.TextInput(attrs={'class': 'form-input'}))
    last_name = forms.CharField(max_length=50, widget=forms.TextInput(attrs={'class': 'form-input'}))
    email = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'form-input'}))
    role = forms.ChoiceField(
        choices=[c for c in UserProfile.ROLE_CHOICES if c[0] != 'owner'],
        widget=forms.Select(attrs={'class': 'form-input', 'id': 'id_role_select'})
    )
    custom_role = forms.CharField(
        max_length=50,
        required=False,
        label="Custom Role Title (Specify if 'Custom Role' is selected)",
        widget=forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'e.g. Senior Electrician, Front Desk, Accountant', 'id': 'id_custom_role_input'})
    )
    phone = forms.CharField(max_length=20, required=False, widget=forms.TextInput(attrs={'class': 'form-input'}))

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']


class CustomerForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = ['name', 'email', 'phone', 'address']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-input'}),
            'email': forms.EmailInput(attrs={'class': 'form-input'}),
            'phone': forms.TextInput(attrs={'class': 'form-input'}),
            'address': forms.Textarea(attrs={'class': 'form-input', 'rows': 3}),
        }


class VehicleForm(forms.ModelForm):
    class Meta:
        model = Vehicle
        fields = ['customer', 'make', 'model', 'year', 'license_plate', 'vin', 'color', 'mileage', 'image']
        widgets = {
            'customer': forms.Select(attrs={'class': 'form-input'}),
            'make': forms.TextInput(attrs={'class': 'form-input'}),
            'model': forms.TextInput(attrs={'class': 'form-input'}),
            'year': forms.NumberInput(attrs={'class': 'form-input'}),
            'license_plate': forms.TextInput(attrs={'class': 'form-input'}),
            'vin': forms.TextInput(attrs={'class': 'form-input'}),
            'color': forms.TextInput(attrs={'class': 'form-input'}),
            'mileage': forms.NumberInput(attrs={'class': 'form-input'}),
            'image': forms.FileInput(attrs={'class': 'form-input', 'accept': 'image/*'}),
        }


class MultipleFileInput(forms.FileInput):
    allow_multiple_selected = True

    def __init__(self, attrs=None):
        super().__init__(attrs)
        if attrs and 'multiple' in attrs:
            self.attrs['multiple'] = attrs['multiple']
        else:
            self.attrs['multiple'] = True


class MultipleFileField(forms.FileField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("widget", MultipleFileInput(attrs={'class': 'form-input', 'accept': 'image/*'}))
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        single_file_clean = super().clean
        if isinstance(data, (list, tuple)):
            result = [single_file_clean(d, initial) for d in data]
        else:
            result = single_file_clean(data, initial)
        return result


class JobCardForm(forms.ModelForm):
    customer_name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Customer Name'}),
        label='Customer Name',
        required=True
    )
    customer_phone = forms.CharField(
        max_length=20,
        widget=forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Customer Phone Number (e.g. 9876543210)'}),
        label='Customer Phone Number',
        required=True
    )
    vehicle_number = forms.CharField(
        max_length=20,
        widget=forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'e.g. KA-01-AB-1234'}),
        label='Vehicle Number',
        required=True
    )
    vehicle_model = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'e.g. Toyota Corolla / Honda City'}),
        label='Vehicle Model',
        required=True
    )
    vehicle_color = forms.CharField(
        max_length=50,
        widget=forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'e.g. Black / Silver / Red'}),
        label='Vehicle Colour',
        required=False
    )
    photos = MultipleFileField(
        required=False,
        help_text='Upload vehicle/inspection photos (JPEG, PNG). Select multiple files if needed.'
    )

    class Meta:
        model = JobCard
        fields = ['mechanic', 'problem_description', 'repair_instructions', 'estimated_completion_time', 'labour_cost', 'notes']
        widgets = {
            'mechanic': forms.Select(attrs={'class': 'form-input'}),
            'problem_description': forms.Textarea(attrs={'class': 'form-input', 'rows': 4}),
            'repair_instructions': forms.Textarea(attrs={'class': 'form-input', 'rows': 3}),
            'estimated_completion_time': forms.DateTimeInput(attrs={'class': 'form-input', 'type': 'datetime-local'}),
            'labour_cost': forms.NumberInput(attrs={'class': 'form-input', 'step': '0.01'}),
            'notes': forms.Textarea(attrs={'class': 'form-input', 'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        mechanics = User.objects.filter(profile__role='mechanic')
        if not mechanics.exists():
            mechanics = User.objects.exclude(profile__role='owner').exclude(is_superuser=True)
        self.fields['mechanic'].queryset = mechanics
        self.fields['mechanic'].required = False
        
        if self.instance and self.instance.pk and getattr(self.instance, 'vehicle', None):
            v = self.instance.vehicle
            self.initial['customer_name'] = v.customer.name
            self.initial['customer_phone'] = v.customer.phone
            self.initial['vehicle_number'] = v.license_plate
            self.initial['vehicle_model'] = f"{v.make} {v.model}".strip()
            self.initial['vehicle_color'] = v.color

        if self.instance and self.instance.estimated_completion_time:
            self.initial['estimated_completion_time'] = self.instance.estimated_completion_time.strftime('%Y-%m-%dT%H:%M')


class JobCardPhotoForm(forms.ModelForm):
    class Meta:
        model = JobCardPhoto
        fields = ['image', 'caption']
        widgets = {
            'image': forms.FileInput(attrs={'class': 'form-input', 'accept': 'image/*'}),
            'caption': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Optional photo caption/notes'}),
        }


class JobStatusForm(forms.ModelForm):
    class Meta:
        model = JobCard
        fields = ['status', 'mechanic', 'estimated_completion_time', 'repair_instructions', 'notes']
        widgets = {
            'status': forms.Select(attrs={'class': 'form-input'}),
            'mechanic': forms.Select(attrs={'class': 'form-input'}),
            'estimated_completion_time': forms.DateTimeInput(attrs={'class': 'form-input', 'type': 'datetime-local'}),
            'repair_instructions': forms.Textarea(attrs={'class': 'form-input', 'rows': 3}),
            'notes': forms.Textarea(attrs={'class': 'form-input', 'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        mechanics = User.objects.filter(profile__role='mechanic')
        if not mechanics.exists():
            mechanics = User.objects.exclude(profile__role='owner').exclude(is_superuser=True)
        self.fields['mechanic'].queryset = mechanics
        self.fields['mechanic'].required = False
        self.fields['mechanic'].label = "Assign Mechanic"
        if self.instance and self.instance.estimated_completion_time:
            self.initial['estimated_completion_time'] = self.instance.estimated_completion_time.strftime('%Y-%m-%dT%H:%M')


class SparePartForm(forms.ModelForm):
    class Meta:
        model = SparePart
        fields = ['name', 'part_number', 'category', 'supplier', 'unit_price', 'stock_quantity', 'minimum_stock', 'location']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-input'}),
            'part_number': forms.TextInput(attrs={'class': 'form-input'}),
            'category': forms.Select(attrs={'class': 'form-input'}),
            'supplier': forms.Select(attrs={'class': 'form-input'}),
            'unit_price': forms.NumberInput(attrs={'class': 'form-input', 'step': '0.01'}),
            'stock_quantity': forms.NumberInput(attrs={'class': 'form-input'}),
            'minimum_stock': forms.NumberInput(attrs={'class': 'form-input'}),
            'location': forms.TextInput(attrs={'class': 'form-input'}),
        }


class PartCategoryForm(forms.ModelForm):
    class Meta:
        model = PartCategory
        fields = ['name', 'description']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-input'}),
            'description': forms.Textarea(attrs={'class': 'form-input', 'rows': 2}),
        }


class SupplierForm(forms.ModelForm):
    class Meta:
        model = Supplier
        fields = ['name', 'contact_person', 'phone', 'email', 'address']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-input'}),
            'contact_person': forms.TextInput(attrs={'class': 'form-input'}),
            'phone': forms.TextInput(attrs={'class': 'form-input'}),
            'email': forms.EmailInput(attrs={'class': 'form-input'}),
            'address': forms.Textarea(attrs={'class': 'form-input', 'rows': 2}),
        }


class StockTransactionForm(forms.ModelForm):
    class Meta:
        model = StockTransaction
        fields = ['part', 'transaction_type', 'quantity', 'unit_price', 'reference', 'notes']
        widgets = {
            'part': forms.Select(attrs={'class': 'form-input'}),
            'transaction_type': forms.Select(attrs={'class': 'form-input'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-input'}),
            'unit_price': forms.NumberInput(attrs={'class': 'form-input', 'step': '0.01'}),
            'reference': forms.TextInput(attrs={'class': 'form-input'}),
            'notes': forms.Textarea(attrs={'class': 'form-input', 'rows': 2}),
        }


class JobPartUsageForm(forms.ModelForm):
    class Meta:
        model = JobPartUsage
        fields = ['part', 'quantity', 'unit_price']
        widgets = {
            'part': forms.Select(attrs={'class': 'form-input'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-input'}),
            'unit_price': forms.NumberInput(attrs={'class': 'form-input', 'step': '0.01'}),
        }


class InvoiceForm(forms.ModelForm):
    class Meta:
        model = Invoice
        fields = ['status', 'is_pickup_service', 'pickup_charge', 'amount_paid', 'payment_method', 'due_date', 'notes']
        widgets = {
            'status': forms.Select(attrs={'class': 'form-input'}),
            'is_pickup_service': forms.CheckboxInput(attrs={'class': 'form-checkbox', 'id': 'id_is_pickup_service', 'style': 'width:18px; height:18px; accent-color:var(--primary); cursor:pointer;'}),
            'pickup_charge': forms.NumberInput(attrs={'class': 'form-input', 'step': '0.01', 'id': 'id_pickup_charge', 'placeholder': 'e.g. 250.00'}),
            'amount_paid': forms.NumberInput(attrs={'class': 'form-input', 'step': '0.01'}),
            'payment_method': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'e.g. UPI, Cash, Card'}),
            'due_date': forms.DateInput(attrs={'class': 'form-input', 'type': 'date'}),
            'notes': forms.Textarea(attrs={'class': 'form-input', 'rows': 2}),
        }


class AMCPlanForm(forms.ModelForm):
    class Meta:
        model = AMCPlan
        fields = ['name', 'description', 'price', 'duration_months', 'services_included']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-input'}),
            'description': forms.Textarea(attrs={'class': 'form-input', 'rows': 3}),
            'price': forms.NumberInput(attrs={'class': 'form-input', 'step': '0.01'}),
            'duration_months': forms.NumberInput(attrs={'class': 'form-input'}),
            'services_included': forms.NumberInput(attrs={'class': 'form-input'}),
        }


class CustomerAMCForm(forms.ModelForm):
    class Meta:
        model = CustomerAMC
        fields = ['vehicle', 'plan', 'start_date', 'amount_paid', 'notes']
        widgets = {
            'vehicle': forms.Select(attrs={'class': 'form-input'}),
            'plan': forms.Select(attrs={'class': 'form-input'}),
            'start_date': forms.DateInput(attrs={'class': 'form-input', 'type': 'date'}),
            'amount_paid': forms.NumberInput(attrs={'class': 'form-input', 'step': '0.01'}),
            'notes': forms.Textarea(attrs={'class': 'form-input', 'rows': 2}),
        }


class ExpenseForm(forms.ModelForm):
    class Meta:
        model = Expense
        fields = ['title', 'category', 'amount', 'expense_date', 'notes']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'e.g. Electricity Bill, Shop Rent, Tools'}),
            'category': forms.Select(attrs={'class': 'form-input'}),
            'amount': forms.NumberInput(attrs={'class': 'form-input', 'step': '0.01', 'placeholder': 'Amount in ₹'}),
            'expense_date': forms.DateInput(attrs={'class': 'form-input', 'type': 'date'}),
            'notes': forms.Textarea(attrs={'class': 'form-input', 'rows': 2, 'placeholder': 'Optional details'}),
        }

