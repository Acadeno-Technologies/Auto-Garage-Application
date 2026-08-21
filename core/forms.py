import re
from django import forms
from django.db.models import Q
from django.contrib.auth.models import User
from django.contrib.auth.forms import AuthenticationForm
from .models import (
    UserProfile, RoleCustomization, Customer, Vehicle, JobCard, JobCardPhoto,
    SparePart, PartCategory, Supplier, StockTransaction, JobPartUsage, Invoice,
    AMCPlan, CustomerAMC, AMCServiceSchedule, WhatsAppLog, Expense, GarageSettings
)

COMMON_TYPO_DOMAINS = {
    'gmai.com': 'gmail.com',
    'gamil.com': 'gmail.com',
    'gmial.com': 'gmail.com',
    'gmaill.com': 'gmail.com',
    'gmal.com': 'gmail.com',
    'yaho.com': 'yahoo.com',
    'yahooo.com': 'yahoo.com',
    'hotmai.com': 'hotmail.com',
    'outloo.com': 'outlook.com',
    'outlok.com': 'outlook.com',
    'iclou.com': 'icloud.com',
}

DISALLOWED_FAKE_DOMAINS = {
    'hh.com', 'aa.com', 'bb.com', 'cc.com', 'dd.com', 'ee.com', 'ff.com', 'gg.com',
    'ii.com', 'jj.com', 'kk.com', 'll.com', 'mm.com', 'nn.com', 'oo.com', 'pp.com',
    'qq.com', 'rr.com', 'ss.com', 'tt.com', 'uu.com', 'vv.com', 'ww.com', 'xx.com',
    'yy.com', 'zz.com', '11.com', '22.com', '33.com', 'test.com', 'example.com',
    'asdf.com', 'qwerty.com', 'abc.com', 'xyz.com', 'fake.com', 'temp.com', 'dummy.com',
    '123.com', 'mailinator.com', 'dispostable.com', 'trashmail.com'
}

def validate_and_clean_email(email_str):
    if not email_str:
        return email_str
    email_str = email_str.strip().lower()
    
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(email_pattern, email_str):
        raise forms.ValidationError("Please enter a valid email address (e.g. user@gmail.com).")

    domain = email_str.split('@')[-1]
    if domain in COMMON_TYPO_DOMAINS:
        correct_domain = COMMON_TYPO_DOMAINS[domain]
        raise forms.ValidationError(f"Invalid email domain '@{domain}'. Did you mean '@{correct_domain}'?")

    domain_name = domain.split('.')[0]
    if domain in DISALLOWED_FAKE_DOMAINS or (len(domain_name) <= 2 and len(set(domain_name)) == 1):
        raise forms.ValidationError(f"'{email_str}' is not a valid email address. Please provide a real email address (e.g. name@gmail.com).")

    return email_str

ROLE_CHOICES = [
    ('owner', 'Owner'),
    ('advisor', 'Service Advisor'),
    ('mechanic', 'Mechanic'),
    ('store_manager', 'Store Manager'),
    ('custom', 'Custom Role'),
]

def get_customized_role_choices(include_owner=False):
    default_labels = [
        ('owner', 'Owner'),
        ('advisor', 'Service Advisor'),
        ('mechanic', 'Mechanic'),
        ('store_manager', 'Store Manager'),
        ('custom', 'Custom Role'),
    ]
    try:
        customizations = {rc.role_key: rc.display_name for rc in RoleCustomization.objects.all() if rc.display_name.strip()}
    except Exception:
        customizations = {}

    choices = []
    for key, default_label in default_labels:
        if not include_owner and key == 'owner':
            continue
        label = customizations.get(key, default_label)
        choices.append((key, label))
    return choices


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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['role'].choices = get_customized_role_choices(include_owner=True)


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
    phone = forms.CharField(max_length=20, required=False, widget=forms.TextInput(attrs={'class': 'form-input', 'maxlength': '20', 'placeholder': '10-digit Phone Number'}))

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'username', 'email']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['role'].choices = get_customized_role_choices(include_owner=False)

    def clean_email(self):
        return validate_and_clean_email(self.cleaned_data.get('email'))

    def clean_first_name(self):
        val = self.cleaned_data.get('first_name', '').strip()
        return val.title() if val else val

    def clean_last_name(self):
        val = self.cleaned_data.get('last_name', '').strip()
        return val.title() if val else val

    def clean_phone(self):
        phone = self.cleaned_data.get('phone', '').strip()
        if phone:
            cleaned_digits = ''.join(c for c in phone if c.isdigit())
            if len(cleaned_digits) != 10:
                raise forms.ValidationError("Please enter a valid 10-digit phone number.")
            return cleaned_digits
        return phone


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
    phone = forms.CharField(max_length=20, required=False, widget=forms.TextInput(attrs={'class': 'form-input', 'maxlength': '20', 'placeholder': '10-digit Phone Number'}))

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['role'].choices = get_customized_role_choices(include_owner=False)

    def clean_email(self):
        return validate_and_clean_email(self.cleaned_data.get('email'))

    def clean_first_name(self):
        val = self.cleaned_data.get('first_name', '').strip()
        return val.title() if val else val

    def clean_last_name(self):
        val = self.cleaned_data.get('last_name', '').strip()
        return val.title() if val else val

    def clean_phone(self):
        phone = self.cleaned_data.get('phone', '').strip()
        if phone:
            cleaned_digits = ''.join(c for c in phone if c.isdigit())
            if len(cleaned_digits) != 10:
                raise forms.ValidationError("Please enter a valid 10-digit phone number.")
            return cleaned_digits
        return phone


class CustomerForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = ['name', 'email', 'phone', 'address']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Customer Name'}),
            'email': forms.EmailInput(attrs={'class': 'form-input', 'placeholder': 'customer@example.com'}),
            'phone': forms.TextInput(attrs={'class': 'form-input', 'maxlength': '20', 'placeholder': '10-digit Phone Number'}),
            'address': forms.Textarea(attrs={'class': 'form-input', 'rows': 3, 'placeholder': 'Customer Address'}),
        }

    def clean_email(self):
        return validate_and_clean_email(self.cleaned_data.get('email'))

    def clean_name(self):
        val = self.cleaned_data.get('name', '').strip()
        return val.title() if val else val

    def clean_phone(self):
        phone = self.cleaned_data.get('phone', '').strip()
        cleaned_digits = ''.join(c for c in phone if c.isdigit())
        if len(cleaned_digits) != 10:
            raise forms.ValidationError("Please enter a valid 10-digit phone number.")
        
        qs = Customer.objects.filter(phone=cleaned_digits)
        if self.instance and self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError("Phone number already exists.")
        return cleaned_digits


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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['customer'].label_from_instance = lambda obj: f"{obj.name} ({obj.phone})" if obj.phone else obj.name

    def clean_license_plate(self):
        plate = self.cleaned_data.get('license_plate', '').strip().upper()
        if plate:
            qs = Vehicle.objects.filter(license_plate__iexact=plate)
            if self.instance and self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                existing = qs.first()
                raise forms.ValidationError(f"Vehicle with license plate '{plate}' is already registered to customer '{existing.customer.name}'.")
        return plate

    def clean_vin(self):
        vin = self.cleaned_data.get('vin', '').strip().upper()
        if vin:
            qs = Vehicle.objects.filter(vin__iexact=vin)
            if self.instance and self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                existing = qs.first()
                raise forms.ValidationError(f"VIN '{vin}' is already registered to another vehicle ({existing.make} {existing.model} - Owner: {existing.customer.name}). Each vehicle must have a unique VIN.")
        return vin


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
        widget=forms.TextInput(attrs={'class': 'form-input', 'maxlength': '20', 'placeholder': '10-digit Phone Number (e.g. 9876543210)'}),
        label='Customer Phone Number',
        required=True
    )
    customer_email = forms.EmailField(
        widget=forms.EmailInput(attrs={'class': 'form-input', 'placeholder': 'customer@example.com'}),
        label='Customer Email',
        required=False
    )
    customer_address = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-input', 'rows': 2, 'placeholder': 'Customer Address'}),
        label='Customer Address',
        required=False
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
            self.initial['customer_email'] = v.customer.email
            self.initial['customer_address'] = v.customer.address
            self.initial['vehicle_number'] = v.license_plate
            self.initial['vehicle_model'] = f"{v.make} {v.model}".strip()
            self.initial['vehicle_color'] = v.color

        if self.instance and self.instance.estimated_completion_time:
            self.initial['estimated_completion_time'] = self.instance.estimated_completion_time.strftime('%Y-%m-%dT%H:%M')

    def clean_customer_email(self):
        return validate_and_clean_email(self.cleaned_data.get('customer_email'))

    def clean_customer_phone(self):
        phone = self.cleaned_data.get('customer_phone', '').strip()
        cleaned_phone = ''.join(c for c in phone if c.isdigit())
        if len(cleaned_phone) != 10:
            raise forms.ValidationError("Please enter a valid 10-digit phone number.")
        return cleaned_phone

    def clean_vehicle_number(self):
        vehicle_num = self.cleaned_data.get('vehicle_number', '').strip().upper()
        if not vehicle_num or len(vehicle_num) < 3:
            raise forms.ValidationError("Please enter a valid vehicle registration number.")
        return vehicle_num


class JobCardPhotoForm(forms.ModelForm):
    class Meta:
        model = JobCardPhoto
        fields = ['image', 'caption']
        widgets = {
            'image': forms.FileInput(attrs={'class': 'form-input', 'accept': 'image/*'}),
            'caption': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Optional photo caption/notes'}),
        }


class JobStatusForm(forms.ModelForm):
    customer_name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Customer Name'}),
        label='Customer Name',
        required=True
    )
    customer_phone = forms.CharField(
        max_length=20,
        widget=forms.TextInput(attrs={'class': 'form-input', 'maxlength': '20', 'placeholder': '10-digit Phone Number'}),
        label='Customer Phone Number',
        required=True
    )

    def clean_customer_email(self):
        return validate_and_clean_email(self.cleaned_data.get('customer_email'))

    def clean_customer_phone(self):
        phone = self.cleaned_data.get('customer_phone', '').strip()
        cleaned_phone = ''.join(c for c in phone if c.isdigit())
        if len(cleaned_phone) != 10:
            raise forms.ValidationError("Please enter a valid 10-digit phone number.")
        return cleaned_phone
    customer_email = forms.EmailField(
        widget=forms.EmailInput(attrs={'class': 'form-input', 'placeholder': 'customer@example.com'}),
        label='Customer Email',
        required=False
    )
    customer_address = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-input', 'rows': 2, 'placeholder': 'Customer Address'}),
        label='Customer Address',
        required=False
    )
    vehicle_number = forms.CharField(
        max_length=20,
        widget=forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'e.g. KA-01-AB-1234'}),
        label='Vehicle Number',
        required=True
    )
    vehicle_model = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'e.g. Toyota Corolla'}),
        label='Vehicle Model',
        required=True
    )
    vehicle_color = forms.CharField(
        max_length=50,
        widget=forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'e.g. Black / Red'}),
        label='Vehicle Colour',
        required=False
    )

    class Meta:
        model = JobCard
        fields = ['status', 'mechanic', 'problem_description', 'labour_cost', 'estimated_completion_time', 'repair_instructions', 'notes']
        widgets = {
            'status': forms.Select(attrs={'class': 'form-input'}),
            'mechanic': forms.Select(attrs={'class': 'form-input'}),
            'problem_description': forms.Textarea(attrs={'class': 'form-input', 'rows': 3}),
            'labour_cost': forms.NumberInput(attrs={'class': 'form-input', 'step': '0.01'}),
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

        if self.instance and self.instance.pk and getattr(self.instance, 'vehicle', None):
            v = self.instance.vehicle
            self.initial['customer_name'] = v.customer.name
            self.initial['customer_phone'] = v.customer.phone
            self.initial['customer_email'] = v.customer.email
            self.initial['customer_address'] = v.customer.address
            self.initial['vehicle_number'] = v.license_plate
            self.initial['vehicle_model'] = f"{v.make} {v.model}".strip()
            self.initial['vehicle_color'] = v.color

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
            'phone': forms.TextInput(attrs={'class': 'form-input', 'maxlength': '20', 'placeholder': '10-digit Phone Number'}),
            'email': forms.EmailInput(attrs={'class': 'form-input'}),
            'address': forms.Textarea(attrs={'class': 'form-input', 'rows': 2}),
        }

    def clean_email(self):
        return validate_and_clean_email(self.cleaned_data.get('email'))

    def clean_phone(self):
        phone = self.cleaned_data.get('phone', '').strip()
        if phone:
            cleaned_digits = ''.join(c for c in phone if c.isdigit())
            if len(cleaned_digits) != 10:
                raise forms.ValidationError("Please enter a valid 10-digit phone number.")
            return cleaned_digits
        return phone


class StockTransactionForm(forms.ModelForm):
    class Meta:
        model = StockTransaction
        fields = ['part', 'transaction_type', 'quantity', 'unit_price', 'reference', 'notes']
        widgets = {
            'part': forms.Select(attrs={'class': 'form-input'}),
            'transaction_type': forms.Select(attrs={'class': 'form-input'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-input', 'value': 1}),
            'unit_price': forms.NumberInput(attrs={'class': 'form-input', 'step': '0.01', 'placeholder': 'Auto-filled from part price'}),
            'reference': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'e.g. PO-001 / Invoice #'}),
            'notes': forms.Textarea(attrs={'class': 'form-input', 'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['unit_price'].required = False
        self.fields['unit_price'].label = "Unit Price (₹) - Auto-filled"


class JobPartUsageForm(forms.ModelForm):
    class Meta:
        model = JobPartUsage
        fields = ['part', 'quantity', 'unit_price']
        widgets = {
            'part': forms.Select(attrs={'class': 'form-input'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-input', 'value': 1}),
            'unit_price': forms.NumberInput(attrs={'class': 'form-input', 'step': '0.01', 'placeholder': 'Auto-filled from inventory'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['unit_price'].required = False
        self.fields['unit_price'].label = "Unit Price (₹) - Optional"


class InvoiceForm(forms.ModelForm):
    class Meta:
        model = Invoice
        fields = ['status', 'amc_discount', 'is_pickup_service', 'pickup_charge', 'amount_paid', 'payment_method', 'due_date', 'notes']
        widgets = {
            'status': forms.Select(attrs={'class': 'form-input'}),
            'amc_discount': forms.NumberInput(attrs={'class': 'form-input', 'step': '0.01', 'id': 'id_amc_discount', 'placeholder': 'Auto-calculated AMC discount'}),
            'is_pickup_service': forms.CheckboxInput(attrs={'class': 'form-checkbox', 'id': 'id_is_pickup_service', 'style': 'width:18px; height:18px; accent-color:var(--primary); cursor:pointer;'}),
            'pickup_charge': forms.NumberInput(attrs={'class': 'form-input', 'step': '0.01', 'id': 'id_pickup_charge', 'placeholder': 'e.g. 250.00'}),
            'amount_paid': forms.NumberInput(attrs={'class': 'form-input', 'step': '0.01'}),
            'payment_method': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'e.g. UPI, Cash, Card'}),
            'due_date': forms.DateInput(attrs={'class': 'form-input', 'type': 'date'}),
            'notes': forms.Textarea(attrs={'class': 'form-input', 'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        self.max_allowed_amc_discount = kwargs.pop('max_allowed_amc_discount', None)
        super().__init__(*args, **kwargs)
        self.fields['pickup_charge'].required = False
        self.fields['amc_discount'].required = False

    def clean_amc_discount(self):
        amount = self.cleaned_data.get('amc_discount')
        if amount is None or amount < 0:
            raise forms.ValidationError("AMC Discount cannot be negative.")
        if self.max_allowed_amc_discount is not None and amount > self.max_allowed_amc_discount:
            raise forms.ValidationError(
                f"AMC Discount (₹{amount:.2f}) cannot exceed the eligible AMC discount of ₹{self.max_allowed_amc_discount:.2f}."
            )
        return amount

    def clean_amount_paid(self):
        amount = self.cleaned_data.get('amount_paid')
        if amount is None or amount < 0:
            raise forms.ValidationError("Amount Paid cannot be negative.")
        return amount


class AMCPlanForm(forms.ModelForm):
    class Meta:
        model = AMCPlan
        fields = ['name', 'description', 'price', 'duration_months', 'services_included', 'service_interval_months', 'discount_percentage', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'e.g. Basic AMC / Premium Care'}),
            'description': forms.Textarea(attrs={'class': 'form-input', 'rows': 3, 'placeholder': 'Plan details and coverage description'}),
            'price': forms.NumberInput(attrs={'class': 'form-input', 'step': '0.01', 'placeholder': 'Price in ₹'}),
            'duration_months': forms.NumberInput(attrs={'class': 'form-input', 'placeholder': 'e.g. 12'}),
            'services_included': forms.NumberInput(attrs={'class': 'form-input', 'placeholder': 'e.g. 4'}),
            'service_interval_months': forms.NumberInput(attrs={'class': 'form-input', 'placeholder': 'e.g. 3'}),
            'discount_percentage': forms.NumberInput(attrs={'class': 'form-input', 'step': '0.01', 'placeholder': 'Labour/Service Discount % (0 - 100)'}),
            'is_active': forms.CheckboxInput(attrs={'style': 'width:auto;'}),
        }

    def clean_duration_months(self):
        val = self.cleaned_data.get('duration_months')
        if not val or val <= 0:
            raise forms.ValidationError("Duration must be greater than 0 months.")
        return val

    def clean_services_included(self):
        val = self.cleaned_data.get('services_included')
        if not val or val <= 0:
            raise forms.ValidationError("Services included must be greater than 0.")
        return val

    def clean_service_interval_months(self):
        val = self.cleaned_data.get('service_interval_months')
        if not val or val <= 0:
            raise forms.ValidationError("Service interval must be greater than 0 months.")
        return val

    def clean_price(self):
        val = self.cleaned_data.get('price')
        if val is None or val < 0:
            raise forms.ValidationError("Price cannot be negative.")
        return val

    def clean_discount_percentage(self):
        val = self.cleaned_data.get('discount_percentage')
        if val is None or val < 0 or val > 100:
            raise forms.ValidationError("Discount percentage must be between 0% and 100%.")
        return val


class CustomerAMCForm(forms.ModelForm):
    class Meta:
        model = CustomerAMC
        fields = ['vehicle', 'plan', 'start_date', 'amount_paid', 'notes']
        widgets = {
            'vehicle': forms.Select(attrs={'class': 'form-input'}),
            'plan': forms.Select(attrs={'class': 'form-input'}),
            'start_date': forms.DateInput(attrs={'class': 'form-input', 'type': 'date'}),
            'amount_paid': forms.NumberInput(attrs={'class': 'form-input', 'step': '0.01', 'placeholder': 'Amount Paid'}),
            'notes': forms.Textarea(attrs={'class': 'form-input', 'rows': 2, 'placeholder': 'Optional contract notes'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['plan'].queryset = AMCPlan.objects.filter(is_active=True)
        # Custom display for vehicles in dropdown
        self.fields['vehicle'].label_from_instance = lambda v: f"{v.license_plate} | {v.make} {v.model} | {v.customer.name}"

    def clean_amount_paid(self):
        amount = self.cleaned_data.get('amount_paid')
        if amount is None or amount < 0:
            raise forms.ValidationError("Amount paid cannot be negative.")
        plan = self.cleaned_data.get('plan')
        if plan and amount > plan.price:
            raise forms.ValidationError(f"Amount paid (₹{amount}) cannot exceed the plan price (₹{plan.price}).")
        return amount

    def clean(self):
        cleaned_data = super().clean()
        vehicle = cleaned_data.get('vehicle')
        plan = cleaned_data.get('plan')
        start_date = cleaned_data.get('start_date')

        if vehicle and plan and start_date:
            import calendar
            from datetime import date
            # Calculate end date automatically
            month = start_date.month - 1 + plan.duration_months
            year = start_date.year + month // 12
            month = month % 12 + 1
            day = min(start_date.day, calendar.monthrange(year, month)[1])
            end_date = date(year, month, day)

            # Check for overlapping active contracts for this vehicle
            qs = CustomerAMC.objects.filter(
                vehicle=vehicle,
                status='active',
                start_date__lte=end_date,
                end_date__gte=start_date
            )
            if self.instance and self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)

            if qs.exists():
                existing = qs.first()
                raise forms.ValidationError(
                    f"This vehicle already has an active AMC contract ({existing.contract_number}) "
                    f"covering the period {existing.start_date.strftime('%d-%m-%Y')} to {existing.end_date.strftime('%d-%m-%Y')}."
                )
        return cleaned_data


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


class UserProfileUpdateForm(forms.ModelForm):
    first_name = forms.CharField(max_length=50, widget=forms.TextInput(attrs={'class': 'form-input'}))
    last_name = forms.CharField(max_length=50, required=False, widget=forms.TextInput(attrs={'class': 'form-input'}))
    email = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'form-input'}))
    phone = forms.CharField(max_length=20, required=False, widget=forms.TextInput(attrs={'class': 'form-input', 'maxlength': '20', 'placeholder': '10-digit Phone Number'}))

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']

    def __init__(self, *args, **kwargs):
        user_profile = kwargs.pop('user_profile', None)
        super().__init__(*args, **kwargs)
        if user_profile:
            self.fields['phone'].initial = user_profile.phone

    def clean_email(self):
        return validate_and_clean_email(self.cleaned_data.get('email'))

    def clean_phone(self):
        phone = self.cleaned_data.get('phone', '').strip()
        if phone:
            cleaned_digits = ''.join(c for c in phone if c.isdigit())
            if len(cleaned_digits) != 10:
                raise forms.ValidationError("Please enter a valid 10-digit phone number.")
            return cleaned_digits
        return phone


class GarageSettingsForm(forms.ModelForm):
    class Meta:
        model = GarageSettings
        fields = ['name', 'tagline', 'phone', 'email', 'address', 'city', 'state', 'pincode', 'gst_number', 'logo']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'e.g. Krishna Auto Care'}),
            'tagline': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'e.g. Multi-Brand Precision Car Clinic'}),
            'phone': forms.TextInput(attrs={'class': 'form-input', 'maxlength': '20', 'placeholder': '10-digit Phone Number'}),
            'email': forms.EmailInput(attrs={'class': 'form-input', 'placeholder': 'info@krishnaautocare.com'}),
            'address': forms.Textarea(attrs={'class': 'form-input', 'rows': 2, 'placeholder': 'Street Address / Landmark'}),
            'city': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'City / Location'}),
            'state': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'State'}),
            'pincode': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Pincode'}),
            'gst_number': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'GSTIN / Registration Number'}),
            'logo': forms.FileInput(attrs={'class': 'form-input', 'accept': 'image/*'}),
        }

    def clean_email(self):
        return validate_and_clean_email(self.cleaned_data.get('email'))

    def clean_phone(self):
        phone = self.cleaned_data.get('phone', '').strip()
        if phone:
            cleaned_digits = ''.join(c for c in phone if c.isdigit())
            if len(cleaned_digits) != 10:
                raise forms.ValidationError("Please enter a valid 10-digit phone number.")
            return cleaned_digits
        return phone


