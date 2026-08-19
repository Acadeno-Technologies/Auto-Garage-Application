from django.contrib import admin
from .models import (
    UserProfile, Customer, Vehicle, JobCard,
    PartCategory, Supplier, SparePart, StockTransaction, JobPartUsage, Invoice,
    GarageSettings
)

admin.site.register(UserProfile)
admin.site.register(Customer)
admin.site.register(Vehicle)
admin.site.register(JobCard)
admin.site.register(PartCategory)
admin.site.register(Supplier)
admin.site.register(SparePart)
admin.site.register(StockTransaction)
admin.site.register(JobPartUsage)
admin.site.register(Invoice)
admin.site.register(GarageSettings)
