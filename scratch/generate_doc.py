import sys
import os
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether, HRFlowable
)
from reportlab.pdfgen import canvas

class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count):
        self.saveState()
        self.setFont("Helvetica", 9)
        self.setFillColor(colors.HexColor("#64748b"))
        
        # Header (pages > 1)
        if self._pageNumber > 1:
            self.drawString(54, 750, "Krishna Auto Care — System Documentation & Role Functionalities")
            self.setStrokeColor(colors.HexColor("#cbd5e1"))
            self.setLineWidth(0.5)
            self.line(54, 742, 558, 742)
            
        # Footer (all pages)
        page_str = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(558, 36, page_str)
        self.drawString(54, 36, "Confidential • Krishna Auto Care Precision Workshop Management System")
        self.setStrokeColor(colors.HexColor("#cbd5e1"))
        self.setLineWidth(0.5)
        self.line(54, 48, 558, 48)
        
        self.restoreState()

def build_pdf(filename="Krishna_Auto_Care_System_Documentation.pdf"):
    doc = SimpleDocTemplate(
        filename,
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=54,
        bottomMargin=54
    )
    
    styles = getSampleStyleSheet()
    
    PRIMARY = colors.HexColor("#0f172a")     # Slate 900
    SECONDARY = colors.HexColor("#2563eb")   # Blue 600
    ACCENT = colors.HexColor("#0284c7")      # Sky 600
    TEAL = colors.HexColor("#0d9488")        # Teal 600
    SUCCESS = colors.HexColor("#16a34a")     # Green 600
    WARNING = colors.HexColor("#ea580c")     # Orange 600
    DARK_TEXT = colors.HexColor("#1e293b")   # Slate 800
    LIGHT_BG = colors.HexColor("#f8fafc")    # Slate 50
    BORDER_COLOR = colors.HexColor("#cbd5e1")# Slate 300

    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=22,
        leading=26,
        textColor=PRIMARY,
        spaceAfter=4
    )

    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=11,
        leading=15,
        textColor=colors.HexColor("#64748b"),
        spaceAfter=12
    )

    h1_style = ParagraphStyle(
        'Heading1_Custom',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=14,
        leading=18,
        textColor=PRIMARY,
        spaceBefore=14,
        spaceAfter=6,
        keepWithNext=True
    )

    h2_style = ParagraphStyle(
        'Heading2_Custom',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=11,
        leading=15,
        textColor=SECONDARY,
        spaceBefore=10,
        spaceAfter=4,
        keepWithNext=True
    )

    h3_style = ParagraphStyle(
        'Heading3_Custom',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=10,
        leading=14,
        textColor=TEAL,
        spaceBefore=6,
        spaceAfter=3,
        keepWithNext=True
    )

    body_style = ParagraphStyle(
        'Body_Custom',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=13,
        textColor=DARK_TEXT,
        spaceAfter=5
    )

    bullet_style = ParagraphStyle(
        'Bullet_Custom',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=13,
        textColor=DARK_TEXT,
        leftIndent=14,
        firstLineIndent=-10,
        spaceAfter=3
    )

    table_header_style = ParagraphStyle(
        'TableHeader',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8.5,
        leading=11,
        textColor=colors.white,
        alignment=0
    )

    table_cell_style = ParagraphStyle(
        'TableCell',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8,
        leading=11,
        textColor=DARK_TEXT
    )

    badge_style = ParagraphStyle(
        'BadgeCell',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8.5,
        leading=11,
        textColor=SECONDARY
    )

    story = []

    # Title Banner
    story.append(Paragraph("Krishna Auto Care Precision Workshop", title_style))
    story.append(Paragraph("Full System Documentation & Detailed Role Functionality Guide", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=SECONDARY, spaceBefore=0, spaceAfter=12))

    # Executive Summary Box
    summary_html = (
        "<b>System Architecture Overview:</b> Krishna Auto Care is a specialized web management platform "
        "designed for automotive workshops. It connects garage owners, service advisors, and mechanics in a unified workflow. "
        "Key capabilities include job card lifecycle management, automated dynamic WhatsApp customer notifications, "
        "invoice generation with vehicle pickup/drop charges, cloud photo storage (Cloudinary), AMC contracts, spare parts inventory tracking, "
        "and an admin-only Incentive & Net Profit Calculator."
    )
    summary_table = Table([[Paragraph(summary_html, body_style)]], colWidths=[504])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#f0f9ff")),
        ('BORDER', (0,0), (-1,-1), 1, colors.HexColor("#bae6fd")),
        ('PADDING', (0,0), (-1,-1), 8),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    story.append(summary_table)
    story.append(Spacer(1, 10))

    # SECTION 1: ROLE MATRIX
    story.append(Paragraph("1. User Roles & Permission Matrix Overview", h1_style))
    
    matrix_data = [
        [
            Paragraph("System Role", table_header_style),
            Paragraph("Primary Responsibility", table_header_style),
            Paragraph("Access Scope", table_header_style),
            Paragraph("Key Modules", table_header_style)
        ],
        [
            Paragraph("Garage Owner / Admin (<code>owner</code>)", badge_style),
            Paragraph("Overall Garage Operations, Financial Governance, Staff Management", table_cell_style),
            Paragraph("Full Read & Write across all system modules, financial reports, and settings.", table_cell_style),
            Paragraph("All Modules + Owner Dashboard, Net Profit Calculator, Expense Logger, Staff Manager", table_cell_style)
        ],
        [
            Paragraph("Service Advisor (<code>advisor</code>)", badge_style),
            Paragraph("Customer Service, Vehicle Intake, Job Cards, Billing & Invoicing", table_cell_style),
            Paragraph("Operational Read & Write for front-desk activities. Cannot view profit/incentive pool.", table_cell_style),
            Paragraph("Advisor Dashboard, Vehicles, Job Cards, Invoices, WhatsApp Updates, AMC Contracts", table_cell_style)
        ],
        [
            Paragraph("Mechanic / Technician (<code>mechanic</code>)", badge_style),
            Paragraph("Vehicle Repair Execution, Status Logging, Parts Usage Tracking", table_cell_style),
            Paragraph("Restricted to assigned jobs only. Cannot access financial or customer billing data.", table_cell_style),
            Paragraph("Mechanic Dashboard, My Job Cards, Status Logger, Labour & Parts Log", table_cell_style)
        ],
        [
            Paragraph("Custom Staff Roles", badge_style),
            Paragraph("Specialized Job Titles (e.g. Senior Electrician, Quality Inspector)", table_cell_style),
            Paragraph("Custom designation labels configured under Staff Management by Admin.", table_cell_style),
            Paragraph("Configured per staff profile", table_cell_style)
        ]
    ]

    matrix_table = Table(matrix_data, colWidths=[100, 110, 154, 140])
    matrix_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), PRIMARY),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('GRID', (0,0), (-1,-1), 0.5, BORDER_COLOR),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, LIGHT_BG]),
        ('PADDING', (0,0), (-1,-1), 5),
    ]))
    story.append(matrix_table)
    story.append(Spacer(1, 10))

    # SECTION 2: GRANULAR ROLE FUNCTIONALITIES
    story.append(Paragraph("2. Detailed Functionalities by Role", h1_style))

    # 2.1 Owner
    story.append(Paragraph("👑 Garage Owner / Admin (Role: owner)", h2_style))
    owner_features = [
        "<b>Executive Owner Dashboard:</b> Live KPI view displaying active jobs, completed jobs, monthly revenue, pending customer invoices, total customers, vehicles, and low-stock spare part alerts.",
        "<b>Staff Account Management & Custom Roles:</b> Create new staff login credentials, update staff roles, and assign custom designations (e.g., <i>Senior Technician</i>, <i>Diagnostic Specialist</i>, <i>Parts Officer</i>).",
        "<b>Incentive & Net Profit Calculator (Exclusive Access):</b> Calculate actual garage net profit using <code>Net Profit = Paid Invoices – Total Expenses</code>. Dynamically adjust incentive percentages (5%, 10%, 15%, 20%) to view live pool distributions.",
        "<b>Per-Mechanic Performance Breakdown:</b> Track completed jobs, billed labor, parts cost, net profit contribution, and calculated incentive payouts per mechanic.",
        "<b>Workshop Expense Logger:</b> Record overhead operating expenses (Rent 🏠, Utilities ⚡, Tools 🛠️, Staff Advances 💼, Parts Purchase ⚙️) with complete audit and deletion options.",
        "<b>Financial Reports & Analytics:</b> View date-range revenue summaries, expense breakdowns, and labor vs. parts profitability reports.",
        "<b>Inventory & Supplier Management:</b> Full authority to manage spare parts inventory, safety stock thresholds, unit costs, pricing, and supplier records.",
        "<b>Customer & Vehicle Master Directory:</b> Access, edit, or remove customer records, vehicle profiles, and service histories."
    ]
    for feat in owner_features:
        story.append(Paragraph(f"• {feat}", bullet_style))

    story.append(Spacer(1, 6))

    # 2.2 Service Advisor
    story.append(Paragraph("📋 Service Advisor (Role: advisor)", h2_style))
    advisor_features = [
        "<b>Service Advisor Dashboard:</b> Real-time view of daily vehicle intake, active job cards, pending customer bills, and search tools.",
        "<b>Customer & Vehicle Registration:</b> Register new customers and vehicles (license plate, VIN, make, model, year, color, mileage). Upload vehicle photos directly to Cloudinary CDN.",
        "<b>Job Card Creation & Lifecycle Management:</b> Open new job cards, record customer problem descriptions, document initial vehicle condition, and assign primary mechanics.",
        "<b>Dynamic WhatsApp Customer Updates:</b> Send status-specific WhatsApp notifications with 1 click directly from the job card (e.g., <i>WAITING FOR PARTS 🛠️</i>, <i>IN PROGRESS 🔧</i>, <i>COMPLETED 🎉</i>, <i>DELIVERED 🚘</i>).",
        "<b>Invoice Generation & Billing:</b> Convert completed job cards into customer invoices. Automatically sums labor charges, parts used, and GST taxes.",
        "<b>Vehicle Pickup & Drop Charge Option:</b> Dynamic toggle to add custom vehicle pickup and drop-off charges directly to invoices.",
        "<b>Payment Collection Tracking:</b> Record invoice payment statuses (Unpaid, Partially Paid, Paid) and generate printable PDF invoices for customers.",
        "<b>Annual Maintenance Contracts (AMC):</b> Enroll customer vehicles in AMC plans (Silver, Gold, Platinum), track validity dates, and record free service benefits."
    ]
    for feat in advisor_features:
        story.append(Paragraph(f"• {feat}", bullet_style))

    story.append(Spacer(1, 6))

    # 2.3 Mechanic
    story.append(Paragraph("🔧 Mechanic / Technician (Role: mechanic)", h2_style))
    mechanic_features = [
        "<b>Personalized Mechanic Dashboard:</b> Clean workspace displaying exclusively job cards assigned to that specific mechanic.",
        "<b>Job Execution & Status Logging:</b> Update real-time job status (<i>In Progress</i>, <i>Waiting for Parts</i>, <i>Completed</i>) so advisors and owners can track progress.",
        "<b>Labour & Time Logger:</b> Log labour hours worked and specific repair actions performed on vehicles.",
        "<b>Spare Parts Usage Logger:</b> Record spare parts and consumables used from inventory during vehicle repair.",
        "<b>Performance Contribution:</b> Completed jobs automatically feed into the admin incentive calculator to generate monthly performance rewards."
    ]
    for feat in mechanic_features:
        story.append(Paragraph(f"• {feat}", bullet_style))

    story.append(Spacer(1, 6))

    # 2.4 Custom Roles
    story.append(Paragraph("🏷️ Custom Staff Roles & Specializations", h2_style))
    custom_role_features = [
        "<b>Flexible Workshop Designations:</b> Admins can assign custom titles (e.g. <i>Master Electrician</i>, <i>Denter & Painter</i>, <i>AC Service Specialist</i>, <i>Quality Inspector</i>) without breaking system permissions.",
        "<b>Role Display Alignment:</b> Custom titles appear cleanly across Staff Directory listings, Job Cards, and Customer Invoices."
    ]
    for feat in custom_role_features:
        story.append(Paragraph(f"• {feat}", bullet_style))

    story.append(Spacer(1, 10))

    # SECTION 3: SYSTEM MODULES & TECHNICAL SUMMARY
    story.append(Paragraph("3. Technical Architecture & Environment", h1_style))
    
    tech_data = [
        [Paragraph("Component", table_header_style), Paragraph("Technology / Library", table_header_style), Paragraph("Implementation Details", table_header_style)],
        [Paragraph("Backend Core", badge_style), Paragraph("Django 5.x / Python 3.14", table_cell_style), Paragraph("MVC architecture, ORM models, custom authentication backend, and RBAC decorators.", table_cell_style)],
        [Paragraph("Database", badge_style), Paragraph("PostgreSQL / SQLite", table_cell_style), Paragraph("Relational data schema for Users, Profiles, Customers, Vehicles, JobCards, Invoices, Expenses, and AMCs.", table_cell_style)],
        [Paragraph("Cloud Storage", badge_style), Paragraph("Cloudinary CDN", table_cell_style), Paragraph("Persistent image storage (`django-cloudinary-storage`) solving Vercel read-only filesystem limits.", table_cell_style)],
        [Paragraph("Frontend UI", badge_style), Paragraph("Vanilla CSS, Glassmorphism, SVG Icons", table_cell_style), Paragraph("Responsive layout, HSL color tokens, inline SVG icons, and mobile-friendly touch cards.", table_cell_style)],
        [Paragraph("Deployment", badge_style), Paragraph("Vercel Serverless (WSGI)", table_cell_style), Paragraph("Automated CI/CD deployment pipeline synced with GitHub <code>main</code> branch.", table_cell_style)]
    ]

    tech_table = Table(tech_data, colWidths=[100, 140, 264])
    tech_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), PRIMARY),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('GRID', (0,0), (-1,-1), 0.5, BORDER_COLOR),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, LIGHT_BG]),
        ('PADDING', (0,0), (-1,-1), 5),
    ]))
    story.append(tech_table)

    # Build PDF
    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"Comprehensive PDF generated successfully: {filename}")

if __name__ == "__main__":
    build_pdf()
