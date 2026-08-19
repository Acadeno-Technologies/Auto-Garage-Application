import os
import sys
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

def generate_pdf():
    pdf_filename = "c:/Users/Arathy tp/OneDrive/Documents/auto garage project/autogarage-Project/PROJECT_DOCUMENTATION.pdf"
    doc = SimpleDocTemplate(
        pdf_filename,
        pagesize=letter,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40
    )
    
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontSize=18,
        leading=22,
        textColor=colors.HexColor("#1e293b"),
        spaceAfter=4
    )
    
    subtitle_style = ParagraphStyle(
        'DocSubTitle',
        parent=styles['Normal'],
        fontSize=9.5,
        leading=13,
        textColor=colors.HexColor("#64748b"),
        spaceAfter=12
    )
    
    h1_style = ParagraphStyle(
        'SectionH1',
        parent=styles['Heading2'],
        fontSize=13,
        leading=17,
        textColor=colors.HexColor("#0f172a"),
        spaceBefore=12,
        spaceAfter=6,
        keepWithNext=True
    )

    h2_style = ParagraphStyle(
        'SectionH2',
        parent=styles['Heading3'],
        fontSize=10.5,
        leading=14,
        textColor=colors.HexColor("#2563eb"),
        spaceBefore=8,
        spaceAfter=4,
        keepWithNext=True
    )
    
    body_style = ParagraphStyle(
        'BodyTextCustom',
        parent=styles['BodyText'],
        fontSize=9,
        leading=13,
        textColor=colors.HexColor("#334155"),
        spaceAfter=4
    )

    bullet_style = ParagraphStyle(
        'BulletCustom',
        parent=body_style,
        leftIndent=15,
        firstLineIndent=-10,
        spaceAfter=3
    )
    
    callout_style = ParagraphStyle(
        'CalloutText',
        parent=body_style,
        fontSize=9,
        leading=13,
        textColor=colors.HexColor("#991b1b")
    )

    table_text = ParagraphStyle(
        'TableText',
        parent=body_style,
        fontSize=8.5,
        leading=11,
        textColor=colors.HexColor("#1e293b")
    )

    table_header = ParagraphStyle(
        'TableHeader',
        parent=table_text,
        fontSize=9,
        leading=12,
        textColor=colors.HexColor("#ffffff"),
        fontName="Helvetica-Bold"
    )

    story = []

    # Title Header
    story.append(Paragraph("AutoGarage Project Module Documentation & Status Report", title_style))
    story.append(Paragraph("<b>Date:</b> August 18, 2026 | <b>Project:</b> AutoGarage Workshop Management | <b>Tech Stack:</b> Django, Python, HTML5/CSS3, SQLite", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#cbd5e1"), spaceAfter=10))

    # SECTION 1: ALL COMPLETED MODULES (BY ROLES & FUNCTIONALITIES)
    story.append(Paragraph("1. Overview of Completed Modules & Role Dashboards", h1_style))
    
    # Owner Role
    story.append(Paragraph("A. Owner / Admin Dashboard & Staff Management", h2_style))
    story.append(Paragraph("• <b>Owner KPI Dashboard:</b> Dedicated executive dashboard (<i>/owner/</i>) featuring KPI summary widgets for total monthly revenue, active jobs count, completed jobs count, total registered customers, total vehicles, pending unpaid invoices count, staff count, and low-stock alert badges.", bullet_style))
    story.append(Paragraph("• <b>Revenue & Staff Performance Analytics:</b> Dynamic revenue breakdown charts, mechanic productivity summary tables (tracking total completed jobs & labor revenue per mechanic), recent job cards log, and recent invoices audit trail.", bullet_style))
    story.append(Paragraph("• <b>Staff & Role Customization:</b> Create, edit, and delete staff accounts (Advisor, Mechanic, Store Manager, Custom Role), assign user privileges, set custom role display titles (e.g., Senior Diagnostician), and enforce role-based access control (RBAC).", bullet_style))
    story.append(Paragraph("• <b>Incentives & Expense Calculator:</b> Calculates net workshop profit (Revenue - Overhead Expenses - Parts Used) and individual mechanic commission allocations.", bullet_style))
    story.append(Paragraph("• <b>Garage Settings & Workshop Branding:</b> Dedicated admin settings page (<i>/settings/</i>) to configure Garage Name, Tagline, Phone, Email, Address, GSTIN, and Logo upload for official receipts.", bullet_style))

    # Service Advisor Role
    story.append(Paragraph("B. Service Advisor Operations & Customer CRM", h2_style))
    story.append(Paragraph("• <b>Advisor Operations Dashboard:</b> Dedicated dashboard (<i>/advisor/</i>) showing assigned active jobs, pending vehicle check-ins, customer service queue, and quick actions for rapid Job Card creation.", bullet_style))
    story.append(Paragraph("• <b>Customer CRM & Service History:</b> Complete customer directory, contact info, and linked vehicle repair history.", bullet_style))
    story.append(Paragraph("• <b>Vehicle Registry & Instant Search API:</b> Registry for Make, Model, Year, Plate, VIN, Mileage, Photo upload, and an instant AJAX search lookup API (<i>/api/search-records/</i>) to auto-fill customer and vehicle history when creating job cards.", bullet_style))
    story.append(Paragraph("• <b>Job Card Management & Workflow:</b> Automated job numbering (JC-00001), status workflow (Pending &rarr; In Progress &rarr; Waiting for Parts &rarr; Completed &rarr; Delivered), labor cost entry, progress photo uploads with captions, and automatic Title Case text formatting.", bullet_style))
    story.append(Paragraph("• <b>Invoicing & Billing System:</b> Converts completed Job Cards into tax invoices with automatic computation of spare parts totals, labor charges, pickup/drop fees, 5% GST, AMC discounts, partial payments, and remaining balance due.", bullet_style))

    # Store Manager Role
    story.append(Paragraph("C. Store Manager & Inventory Control", h2_style))
    story.append(Paragraph("• <b>Store Manager Inventory Dashboard:</b> Specialized inventory dashboard (<i>/store/</i>) displaying low stock alert banners, total inventory valuation, category breakdown, supplier activity, and pending parts requests.", bullet_style))
    story.append(Paragraph("• <b>Spare Parts Catalog:</b> Comprehensive stock tracking with part numbers, unit prices, minimum stock warning levels, categories, and supplier references.", bullet_style))
    story.append(Paragraph("• <b>Stock Transactions & Audit:</b> Logs Stock In and Stock Out operations with reference numbers and notes.", bullet_style))
    story.append(Paragraph("• <b>Inventory Export:</b> One-click export of parts list to <b>CSV</b> and <b>PDF</b> report formats.", bullet_style))

    # Mechanic Role
    story.append(Paragraph("D. Mechanic Workbench & My Jobs Dashboard", h2_style))
    story.append(Paragraph("• <b>Mechanic My Jobs Dashboard:</b> Dedicated, clean workbench dashboard (<i>/mechanic/</i>) displaying assigned repair jobs sorted by status (Pending, In Progress, Waiting for Parts).", bullet_style))
    story.append(Paragraph("• <b>Job Detail & Repair Logs:</b> View repair instructions, problem descriptions, assigned vehicle photos, allocated spare parts list, and update repair progress status in real-time.", bullet_style))

    story.append(Spacer(1, 8))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#e2e8f0"), spaceAfter=8))

    # SECTION 2: MODULES IN PROGRESS
    story.append(Paragraph("2. Modules Currently In Progress", h1_style))
    story.append(Paragraph("A. WhatsApp Notification Workflow", h2_style))
    story.append(Paragraph("• Integrated WhatsApp dispatch view (/send-whatsapp/) to send job completion alerts, invoice billing summaries, and AMC reminders with audit logging.", bullet_style))

    story.append(Spacer(1, 8))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#e2e8f0"), spaceAfter=8))

    # SECTION 3: PENDING & OPEN REQUIREMENTS
    story.append(Paragraph("3. What is Pending & Open Requirements", h1_style))
    story.append(Paragraph("A. Pending: Annual Maintenance Contract (AMC) Module Integration", h2_style))
    
    # Callout Box for AMC Challenge
    callout_data = [[
        Paragraph("<b>Key Pending Challenge:</b><br/>"
                  "The basic AMC database models (<i>AMCPlan, CustomerAMC, AMCServiceSchedule</i>) and rudimentary views have been created. However, <b>full business logic integration remains pending due to implementation complexity</b>.", callout_style)
    ]]
    callout_table = Table(callout_data, colWidths=[532])
    callout_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#fef2f2")),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#fca5a5")),
        ('PADDING', (0,0), (-1,-1), 6),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    story.append(callout_table)
    story.append(Spacer(1, 6))

    story.append(Paragraph("<b>Specific Challenges / Missing Logic for AMC:</b>", body_style))
    story.append(Paragraph("1. <b>Job Card Integration:</b> Auto-detecting active AMC contracts during Job Card creation to apply free service vouchers.", bullet_style))
    story.append(Paragraph("2. <b>Service Schedule Tracking:</b> Auto-generating quarterly service visits upon AMC purchase and linking scheduled visits to Job Cards.", bullet_style))
    story.append(Paragraph("3. <b>Invoice Discount Engine:</b> Enforcing AMC discount rules (e.g., 100% off labor, 10% off spare parts) dynamically on billing.", bullet_style))
    story.append(Paragraph("4. <b>Renewal Automation:</b> Automated background reminders for contracts expiring within 30 days.", bullet_style))

    story.append(Spacer(1, 4))
    story.append(Paragraph("B. Additional Set of Pending Requirements", h2_style))
    story.append(Paragraph("1. <b>Mobile Responsiveness & Handheld UI:</b> Full mobile design (collapsible sidebar, responsive table stacks, mobile-friendly forms) is currently pending.", bullet_style))
    story.append(Paragraph("2. <b>Role-Specific Dashboard UI Polish:</b> Custom dashboard widgets for store managers and mechanics.", bullet_style))
    story.append(Paragraph("3. <b>Print-Ready Documents:</b> Clean A4 print stylesheets for Invoices and Job Cards.", bullet_style))

    story.append(Spacer(1, 8))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#e2e8f0"), spaceAfter=8))

    # SECTION 4: ISSUES, BLOCKERS & DELAYS TABLE
    story.append(Paragraph("4. Issues, Blockers & Delays", h1_style))
    
    table_data = [
        [Paragraph("Issue / Blocker", table_header), Paragraph("Category", table_header), Paragraph("Description", table_header), Paragraph("Mitigation Plan", table_header)],
        [
            Paragraph("<b>AMC Workflow Uncertainty</b>", table_text),
            Paragraph("Feature Architecture", table_text),
            Paragraph("Lack of technical design linking CustomerAMC <-> JobCard <-> Invoice.", table_text),
            Paragraph("Define a step-by-step AMC logic plan & discount rule matrix.", table_text)
        ],
        [
            Paragraph("<b>Mobile Responsiveness</b>", table_text),
            Paragraph("UI / UX Layout", table_text),
            Paragraph("Complex tables and multi-column forms stretch on small mobile screens.", table_text),
            Paragraph("Add CSS media queries, card views for tables, and responsive mobile nav.", table_text)
        ],
        [
            Paragraph("<b>Staff Incentive Edge Cases</b>", table_text),
            Paragraph("Business Logic", table_text),
            Paragraph("Uncertainty in profit sharing formula per mechanic vs flat labor %.", table_text),
            Paragraph("Define commission formula (flat labor % vs net profit allocation).", table_text)
        ],
        [
            Paragraph("<b>WhatsApp Gateway Setup</b>", table_text),
            Paragraph("Third-Party API", table_text),
            Paragraph("Templates use wa.me links rather than official direct API endpoints.", table_text),
            Paragraph("Decide between client-side wa.me or official Twilio/Meta API.", table_text)
        ],
        [
            Paragraph("<b>Stock Deduction Safety</b>", table_text),
            Paragraph("Data Integrity", table_text),
            Paragraph("Manual post-completion job part edits can cause stock drift.", table_text),
            Paragraph("Enforce job status lockouts prior to part modifications.", table_text)
        ]
    ]

    blocker_table = Table(table_data, colWidths=[110, 95, 172, 155])
    blocker_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#1e293b")),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#cbd5e1")),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.HexColor("#ffffff"), colors.HexColor("#f8fafc")]),
        ('PADDING', (0,0), (-1,-1), 5),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
    ]))
    story.append(blocker_table)

    doc.build(story)
    print("PDF Generated successfully with detailed role dashboards!")

if __name__ == "__main__":
    generate_pdf()
