# AutoGarage Project Module Documentation & Status Report

**Date:** August 18, 2026  
**Project:** AutoGarage - Workshop & Service Management System  
**Framework:** Django (Python), HTML5/CSS3 (Vanilla Modern Dashboard UI), SQLite Database  

---

## 1. Overview of Completed Modules & Role Dashboards

### A. Owner / Admin Dashboard & Staff Management
- **Owner KPI Analytics Dashboard:** Dedicated executive dashboard (`/owner/`) featuring KPI summary widgets for total monthly revenue, active jobs count, completed jobs count, total registered customers, total vehicles, pending unpaid invoices count, staff count, and low-stock alert badges.
- **Revenue & Staff Performance Analytics:** Dynamic revenue breakdown charts, mechanic productivity summary tables (tracking total completed jobs & labor revenue per mechanic), recent job cards log, and recent invoices audit trail.
- **Staff & Role Customization:** Create, edit, and delete staff accounts (Advisor, Mechanic, Store Manager, Custom Role), assign user privileges, set custom role display titles (e.g., Senior Diagnostician), and enforce role-based access control (RBAC).
- **Incentives & Expense Calculator:** Calculates workshop net profit ($\text{Revenue} - \text{Overhead Expenses} - \text{Parts Used}$) and individual mechanic commission allocations.
- **Garage Settings & Workshop Branding:** Dedicated admin settings page (`/settings/`) to configure Garage Name, Tagline, Phone, Email, Address, GSTIN, and Logo upload for official receipts.

### B. Service Advisor Operations & Customer CRM
- **Advisor Operations Dashboard:** Dedicated dashboard (`/advisor/`) showing assigned active jobs, pending vehicle check-ins, customer service queue, and quick actions for rapid Job Card creation.
- **Customer CRM & Service History:** Complete customer directory, contact info, and linked vehicle repair history.
- **Vehicle Registry & Instant Search API:** Registry for Make, Model, Year, Plate, VIN, Mileage, Photo upload, and an instant AJAX search lookup API (`/api/search-records/`) to auto-fill customer and vehicle history when creating job cards.
- **Job Card Management & Workflow:** Automated job numbering (`JC-00001`), status workflow (`Pending` -> `In Progress` -> `Waiting for Parts` -> `Completed` -> `Delivered`), labor cost entry, progress photo uploads with captions, and automatic Title Case text formatting.
- **Invoicing & Billing System:** Converts completed Job Cards into tax invoices with automatic computation of spare parts totals, labor charges, pickup/drop fees, 5% GST, AMC discounts, partial payments, and remaining balance due.

### C. Store Manager & Inventory Control
- **Store Manager Inventory Dashboard:** Specialized inventory dashboard (`/store/`) displaying low stock alert banners, total inventory valuation, category breakdown, supplier activity, and pending parts requests.
- **Spare Parts Catalog:** Comprehensive stock tracking with part numbers, unit prices, minimum stock warning levels, categories, and supplier references.
- **Stock Transactions & Audit:** Logs Stock In and Stock Out operations with reference numbers and notes.
- **Inventory Export:** One-click export of parts list to **CSV** and **PDF** report formats.

### D. Mechanic Workbench & My Jobs Dashboard
- **Mechanic My Jobs Dashboard:** Dedicated, clean workbench dashboard (`/mechanic/`) displaying assigned repair jobs sorted by status (Pending, In Progress, Waiting for Parts).
- **Job Detail & Repair Logs:** View repair instructions, problem descriptions, assigned vehicle photos, allocated spare parts list, and update repair progress status in real-time.

---

## 2. Modules Currently In Progress

### A. WhatsApp Notification Workflow
- Integrated WhatsApp dispatch view (`/send-whatsapp/`) to send job completion alerts, invoice billing summaries, and AMC reminders with audit logging.

---

## 3. What is Pending & Open Requirements

### A. Pending: Annual Maintenance Contract (AMC) Module Integration
> **Key Pending Challenge:**  
> The basic AMC database models (`AMCPlan`, `CustomerAMC`, `AMCServiceSchedule`) and rudimentary views have been created. However, **full business logic integration remains pending due to implementation complexity**.

**Specific Challenges / Missing Logic for AMC:**
1. **Job Card Integration:** Auto-detecting active AMC contracts during Job Card creation to apply free service vouchers.
2. **Service Schedule Tracking:** Auto-generating quarterly service visits upon AMC purchase and linking scheduled visits to Job Cards.
3. **Invoice Discount Engine:** Enforcing AMC discount rules (e.g., 100% off labor, 10% off spare parts) dynamically on billing.
4. **Renewal Automation:** Automated background reminders for contracts expiring within 30 days.

### B. Additional Set of Pending Requirements
1. **Mobile Responsiveness & Handheld UI:** Full mobile design (collapsible sidebar, responsive table stacks, mobile-friendly forms) is currently pending.
2. **Role-Specific Dashboard UI Polish:** Custom dashboard widgets for store managers and mechanics.
3. **Print-Ready Documents:** Clean A4 print stylesheets for Invoices and Job Cards.

---

## 4. Issues, Blockers & Delays

| Issue / Blocker | Category | Description | Mitigation Plan |
| :--- | :--- | :--- | :--- |
| **AMC Workflow Uncertainty** | **Feature Architecture** | Lack of technical design linking CustomerAMC <-> JobCard <-> Invoice. | Define a step-by-step AMC logic plan & discount rule matrix. |
| **Mobile Responsiveness** | **UI / UX Layout** | Complex tables and multi-column forms stretch on small mobile screens. | Add CSS media queries, card views for tables, and responsive mobile nav. |
| **Staff Incentive Edge Cases** | **Business Logic** | Uncertainty in profit sharing formula per mechanic vs flat labor %. | Define commission formula (flat labor % vs net profit allocation). |
| **WhatsApp Gateway Setup** | **Third-Party API** | Templates use wa.me links rather than official direct API endpoints. | Decide between client-side wa.me or official Twilio/Meta API. |
| **Stock Deduction Safety** | **Data Integrity** | Manual post-completion job part edits can cause stock drift. | Enforce job status lockouts prior to part modifications. |
