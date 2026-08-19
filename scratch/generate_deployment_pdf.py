import os
import sys
from reportlab.lib.pagesizes import letter
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, HRFlowable, KeepTogether
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

def create_deployment_pdf(pdf_path):
    doc = SimpleDocTemplate(
        pdf_path,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )

    styles = getSampleStyleSheet()

    # Custom Color Palette
    PRIMARY_RED = colors.HexColor("#e11d48")
    DARK_NAVY = colors.HexColor("#0f172a")
    SLATE_DARK = colors.HexColor("#1e293b")
    SLATE_MUTED = colors.HexColor("#64748b")
    LIGHT_BG = colors.HexColor("#f8fafc")
    BORDER_COLOR = colors.HexColor("#cbd5e1")
    CODE_BG = colors.HexColor("#1e293b")

    # Typography Styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=20,
        leading=24,
        textColor=colors.white,
        spaceAfter=6
    )

    subtitle_style = ParagraphStyle(
        'DocSubTitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#f1f5f9")
    )

    h1_style = ParagraphStyle(
        'CustomH1',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=13,
        leading=17,
        textColor=DARK_NAVY,
        spaceBefore=14,
        spaceAfter=6
    )

    h2_style = ParagraphStyle(
        'CustomH2',
        parent=styles['Heading3'],
        fontName='Helvetica-Bold',
        fontSize=11,
        leading=15,
        textColor=PRIMARY_RED,
        spaceBefore=10,
        spaceAfter=4
    )

    body_style = ParagraphStyle(
        'CustomBody',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9.5,
        leading=14,
        textColor=SLATE_DARK,
        spaceAfter=6
    )

    bullet_style = ParagraphStyle(
        'CustomBullet',
        parent=body_style,
        leftIndent=15,
        spaceAfter=4
    )

    code_style = ParagraphStyle(
        'CodeStyle',
        parent=styles['Normal'],
        fontName='Courier',
        fontSize=8.5,
        leading=12,
        textColor=colors.HexColor("#f8fafc"),
        backColor=CODE_BG,
        borderColor=DARK_NAVY,
        borderWidth=1,
        borderPadding=8,
        spaceBefore=6,
        spaceAfter=8,
        borderRadius=4
    )

    table_header_style = ParagraphStyle(
        'TableHeader',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9,
        leading=12,
        textColor=colors.white
    )

    table_cell_style = ParagraphStyle(
        'TableCell',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=12,
        textColor=SLATE_DARK
    )

    story = []

    # 1. Header Banner
    header_data = [
        [
            Paragraph("🚀 Auto Garage Application — Vercel & Neon Deployment Guide", title_style),
        ],
        [
            Paragraph("<b>Prepared for:</b> Team Lead & DevOps Administrator &nbsp;|&nbsp; <b>Stack:</b> Django 6.1, Vercel Serverless, Neon PostgreSQL, Cloudinary", subtitle_style),
        ]
    ]

    header_table = Table(header_data, colWidths=[540])
    header_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), DARK_NAVY),
        ('PADDING', (0,0), (-1,-1), 12),
        ('BOTTOMPADDING', (0,-1), (-1,-1), 12),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 12))

    # 2. Section 1: Overview
    story.append(Paragraph("1. Architectural Overview", h1_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=PRIMARY_RED, spaceAfter=8))
    
    arch_points = [
        "<b>Hosting & Compute:</b> Vercel (Serverless Python Runtime via <code>api/index.py</code> and <code>vercel.json</code>).",
        "<b>Production Database:</b> Neon PostgreSQL (Fully managed serverless Postgres with SSL connection support).",
        "<b>Static Assets:</b> Managed via <code>whitenoise</code> (Compressed Manifest Static Files Storage).",
        "<b>Media & Uploads:</b> Integrated with <code>cloudinary</code> & <code>django-cloudinary-storage</code> for invoice/vehicle images."
    ]
    for pt in arch_points:
        story.append(Paragraph(f"• {pt}", bullet_style))
    
    story.append(Spacer(1, 8))

    # 3. Section 2: Prerequisites
    story.append(Paragraph("2. Prerequisites for Deployment", h1_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=PRIMARY_RED, spaceAfter=8))
    prereqs = [
        "<b>GitHub Access:</b> Push/Admin access to the repository.",
        "<b>Vercel Account:</b> Team or Individual Vercel Account linked to GitHub.",
        "<b>Neon Console:</b> Access to <font color='#e11d48'><u>console.neon.tech</u></font> to provision the Postgres DB."
    ]
    for p in prereqs:
        story.append(Paragraph(f"• {p}", bullet_style))

    story.append(Spacer(1, 8))

    # 4. Section 3: Provisioning Neon
    story.append(Paragraph("3. Provisioning Neon PostgreSQL", h1_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=PRIMARY_RED, spaceAfter=8))
    story.append(Paragraph("1. Log into your Neon Console and click <b>Create Project</b> (e.g. <i>autogarage-prod-db</i>).", body_style))
    story.append(Paragraph("2. In the <b>Connection Details</b> dashboard, select <b>PostgreSQL</b> and copy your connection string:", body_style))
    story.append(Paragraph("postgres://&lt;user&gt;:&lt;password&gt;@&lt;ep-hostname&gt;.neon.tech/neondb?sslmode=require", code_style))

    story.append(Spacer(1, 8))

    # 5. Section 4: Vercel Setup & Environment Variables
    story.append(Paragraph("4. Vercel Project Setup & Environment Variables", h1_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=PRIMARY_RED, spaceAfter=8))
    story.append(Paragraph("Import the GitHub repository into Vercel (Framework Preset: <b>Other</b>, Build Command: <b>bash build.sh</b>, Output Directory: <b>staticfiles</b>).", body_style))
    story.append(Paragraph("Add the following <b>Environment Variables</b> in Vercel Settings:", body_style))

    env_table_data = [
        [
            Paragraph("Environment Variable", table_header_style),
            Paragraph("Value / Description", table_header_style),
            Paragraph("Required", table_header_style)
        ],
        [
            Paragraph("<b>DATABASE_URL</b>", table_cell_style),
            Paragraph("postgres://&lt;user&gt;:&lt;pass&gt;@&lt;ep-host&gt;.neon.tech/neondb?sslmode=require", table_cell_style),
            Paragraph("<b>YES</b>", table_cell_style)
        ],
        [
            Paragraph("<b>SECRET_KEY</b>", table_cell_style),
            Paragraph("Secure random string (50+ characters)", table_cell_style),
            Paragraph("<b>YES</b>", table_cell_style)
        ],
        [
            Paragraph("<b>USE_LOCAL_DB</b>", table_cell_style),
            Paragraph("<code>False</code>", table_cell_style),
            Paragraph("<b>YES</b>", table_cell_style)
        ],
        [
            Paragraph("<b>CLOUDINARY_*</b>", table_cell_style),
            Paragraph("CLOUDINARY_CLOUD_NAME, API_KEY, API_SECRET", table_cell_style),
            Paragraph("Optional", table_cell_style)
        ]
    ]

    env_table = Table(env_table_data, colWidths=[130, 320, 90])
    env_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), DARK_NAVY),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('GRID', (0,0), (-1,-1), 0.5, BORDER_COLOR),
        ('BACKGROUND', (0,1), (-1,1), LIGHT_BG),
        ('BACKGROUND', (0,3), (-1,3), LIGHT_BG),
        ('PADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(env_table)

    story.append(Spacer(1, 10))

    # 6. Section 5: Migrations & Superuser
    story.append(Paragraph("5. Database Migrations & Initial Owner Setup", h1_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=PRIMARY_RED, spaceAfter=8))
    story.append(Paragraph("Run migrations and create the initial Superuser account on Neon from your terminal:", body_style))

    cmd_text = (
        "<b># Windows PowerShell:</b><br/>"
        "$env:DATABASE_URL=\"postgres://&lt;user&gt;:&lt;pass&gt;@&lt;ep-host&gt;.neon.tech/neondb?sslmode=require\"<br/>"
        "$env:USE_LOCAL_DB=\"False\"<br/>"
        ".\\env\\Scripts\\python.exe manage.py migrate<br/>"
        ".\\env\\Scripts\\python.exe manage.py createsuperuser<br/><br/>"
        "<b># Linux / macOS:</b><br/>"
        "export DATABASE_URL=\"postgres://&lt;user&gt;:&lt;pass&gt;@&lt;ep-host&gt;.neon.tech/neondb?sslmode=require\"<br/>"
        "export USE_LOCAL_DB=\"False\"<br/>"
        "python manage.py migrate<br/>"
        "python manage.py createsuperuser"
    )
    story.append(Paragraph(cmd_text, code_style))

    story.append(Spacer(1, 8))

    # 7. Section 6: Checklist
    story.append(Paragraph("6. Post-Deployment Verification Checklist", h1_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=PRIMARY_RED, spaceAfter=8))

    chk_list = [
        "[✓] <b>Public Landing Page:</b> Visit <code>https://your-app.vercel.app/</code> — verify homepage loads cleanly.",
        "[✓] <b>Owner Portal Login:</b> Visit <code>/login/</code> and log in with your Superuser account.",
        "[✓] <b>Staff & Role Management:</b> Test staff registration (Service Advisor, Mechanic, Store Manager).",
        "[✓] <b>Job Cards & Invoices:</b> Verify creating a Job Card and generating an Invoice PDF.",
        "[✓] <b>Workshop Settings:</b> Upload workshop branding/logo in Garage Settings."
    ]
    for c in chk_list:
        story.append(Paragraph(c, bullet_style))

    doc.build(story)
    print(f"Generated deployment PDF: {pdf_path}")

if __name__ == '__main__':
    pdf_path = os.path.abspath("DEPLOYMENT_GUIDE.pdf")
    create_deployment_pdf(pdf_path)
