from django.urls import path
from . import views

urlpatterns = [
    # Auth
    path('', views.landing_page, name='landing'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),

    # Role dashboards
    path('owner/', views.owner_dashboard, name='owner_dashboard'),
    path('advisor/', views.advisor_dashboard, name='advisor_dashboard'),
    path('mechanic/', views.mechanic_dashboard, name='mechanic_dashboard'),
    path('store/', views.store_dashboard, name='store_dashboard'),

    # Staff
    path('staff/', views.staff_list, name='staff_list'),
    path('staff/add/', views.staff_create, name='staff_create'),
    path('staff/<int:pk>/edit/', views.staff_edit, name='staff_edit'),
    path('staff/<int:pk>/delete/', views.staff_delete, name='staff_delete'),

    # Customers
    path('customers/', views.customer_list, name='customer_list'),
    path('customers/add/', views.customer_create, name='customer_create'),
    path('customers/<int:pk>/', views.customer_detail, name='customer_detail'),
    path('customers/<int:pk>/edit/', views.customer_edit, name='customer_edit'),

    # Vehicles
    path('vehicles/', views.vehicle_list, name='vehicle_list'),
    path('vehicles/add/', views.vehicle_create, name='vehicle_create'),
    path('vehicles/<int:pk>/', views.vehicle_detail, name='vehicle_detail'),
    path('vehicles/<int:pk>/edit/', views.vehicle_edit, name='vehicle_edit'),

    # Job Cards
    path('jobs/', views.job_list, name='job_list'),
    path('jobs/create/', views.job_create, name='job_create'),
    path('api/search-records/', views.job_search_records, name='job_search_records'),
    path('jobs/<int:pk>/', views.job_detail, name='job_detail'),
    path('jobs/<int:pk>/status/', views.job_update_status, name='job_update_status'),
    path('jobs/<int:pk>/add-part/', views.job_add_part, name='job_add_part'),
    path('jobs/<int:pk>/add-photo/', views.job_add_photo, name='job_add_photo'),
    path('jobs/<int:pk>/photo/<int:photo_pk>/delete/', views.job_delete_photo, name='job_delete_photo'),

    # Spare Parts
    path('parts/', views.parts_list, name='parts_list'),
    path('parts/add/', views.part_create, name='part_create'),
    path('parts/<int:pk>/edit/', views.part_edit, name='part_edit'),
    path('parts/stock/', views.stock_transaction, name='stock_transaction'),

    # Categories & Suppliers
    path('categories/', views.category_list, name='category_list'),
    path('categories/add/', views.category_create, name='category_create'),
    path('suppliers/', views.supplier_list, name='supplier_list'),
    path('suppliers/add/', views.supplier_create, name='supplier_create'),

    # Invoices
    path('invoices/', views.invoice_list, name='invoice_list'),
    path('invoices/create/<int:job_pk>/', views.invoice_create, name='invoice_create'),
    path('invoices/<int:pk>/', views.invoice_detail, name='invoice_detail'),
    path('invoices/<int:pk>/edit/', views.invoice_edit, name='invoice_edit'),

    # Reports & Incentives (Admin Only)
    path('reports/', views.reports, name='reports'),
    path('incentives/', views.incentive_calculator, name='incentive_calculator'),

    # AMC Management
    path('amc/', views.amc_list, name='amc_list'),
    path('amc/plans/add/', views.amc_plan_create, name='amc_plan_create'),
    path('amc/add/', views.amc_create, name='amc_create'),
    path('amc/<int:pk>/', views.amc_detail, name='amc_detail'),

    # WhatsApp Notifications
    path('send-whatsapp/', views.send_whatsapp_view, name='send_whatsapp'),
]

