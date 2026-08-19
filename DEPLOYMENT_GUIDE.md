# 🚀 Auto Garage Application — Vercel & Neon PostgreSQL Deployment Guide

**Prepared for:** Team Lead & DevOps Administrator  
**Project:** Auto Garage Management System (Krishna Auto Care)  
**Stack:** Django 6.1, Vercel Serverless Functions, Neon Serverless PostgreSQL, Cloudinary (Media)

---

## 📌 1. Architectural Overview

* **Hosting & Compute:** [Vercel](https://vercel.com/) (Serverless Python Runtime via `api/index.py` and `vercel.json`).
* **Production Database:** [Neon PostgreSQL](https://neon.tech/) (Fully managed serverless Postgres with SSL support).
* **Static Assets:** Managed via `whitenoise` (Compressed Manifest Static Files Storage).
* **Media & Uploads:** Integrated with `cloudinary` & `django-cloudinary-storage` for invoice/vehicle image hosting.

---

## 🛠️ 2. Prerequisites for Deployment

Before deploying, ensure you have access to:
1. **GitHub Repository Access:** Admin permissions on the GitHub repository.
2. **Vercel Account:** Team or Individual Vercel Account linked to GitHub.
3. **Neon Tech Account:** Access to [Neon Console](https://console.neon.tech/) to provision the Postgres DB.

---

## 🗄️ 3. Step 1: Provisioning Neon PostgreSQL

1. Log into your [Neon Console](https://console.neon.tech/).
2. Click **Create Project** $\rightarrow$ Project Name: `autogarage-prod-db`.
3. In the **Connection Details** dashboard:
   * Select **PostgreSQL** string.
   * Copy the full connection string. It will follow this format:
     ```text
     postgres://<user>:<password>@<ep-hostname>.neon.tech/neondb?sslmode=require
     ```

---

## ⚙️ 4. Step 2: Vercel Project Setup

1. Log into [Vercel](https://vercel.com/) and click **Add New...** $\rightarrow$ **Project**.
2. Import the GitHub repository created for the Auto Garage application.
3. In the **Build and Output Settings** configuration:
   * **Framework Preset:** `Other`
   * **Build Command:** `bash build.sh`
   * **Output Directory:** `staticfiles`
   * **Install Command:** `pip install -r requirements.txt`

---

## 🔑 5. Step 3: Required Environment Variables in Vercel

Navigate to **Project Settings** $\rightarrow$ **Environment Variables** in Vercel and add the following keys:

| Environment Variable | Recommended Value / Description | Required |
| :--- | :--- | :---: |
| `DATABASE_URL` | `postgres://<user>:<password>@<ep-hostname>.neon.tech/neondb?sslmode=require` | **YES** |
| `SECRET_KEY` | *(Generate a secure 50+ character random string)* | **YES** |
| `USE_LOCAL_DB` | `False` | **YES** |
| `CLOUDINARY_CLOUD_NAME` | *(Your Cloudinary Cloud Name)* | Optional |
| `CLOUDINARY_API_KEY` | *(Your Cloudinary API Key)* | Optional |
| `CLOUDINARY_API_SECRET` | *(Your Cloudinary API Secret)* | Optional |

> ⚠️ **Important:** Ensure `USE_LOCAL_DB` is explicitly set to `False` in Vercel so Django connects to the Neon PostgreSQL database instead of the local SQLite database.

---

## ⚡ 6. Step 4: Running Database Migrations & Initial Setup

Once the Vercel deployment finishes, run the database migrations and create the initial **Superuser / Owner Account** on Neon.

Execute the following commands from a local terminal connected to your repository:

### For Windows PowerShell:
```powershell
# Set temporary connection parameters to Neon PostgreSQL
$env:DATABASE_URL="postgres://<user>:<password>@<ep-hostname>.neon.tech/neondb?sslmode=require"
$env:USE_LOCAL_DB="False"

# Run migrations against Neon PostgreSQL
.\env\Scripts\python.exe manage.py migrate

# Create initial Superuser/Owner Account
.\env\Scripts\python.exe manage.py createsuperuser
```

### For Linux / macOS Terminal:
```bash
export DATABASE_URL="postgres://<user>:<password>@<ep-hostname>.neon.tech/neondb?sslmode=require"
export USE_LOCAL_DB="False"

python manage.py migrate
python manage.py createsuperuser
```

---

## 🔍 7. Step 5: Post-Deployment Verification Checklist

- [ ] **Public Landing Page:** Visit `https://your-app.vercel.app/` — verify the homepage loads smoothly.
- [ ] **Owner Portal Login:** Visit `https://your-app.vercel.app/login/` and log in with your Superuser account.
- [ ] **Staff & Role Management:** Navigate to `Staff Management` and test role creation (Service Advisor, Mechanic, Store Manager).
- [ ] **Job Cards & Invoices:** Verify creating a Job Card and generating an Invoice PDF.
- [ ] **Workshop Settings:** Upload workshop branding/logo in `Garage Settings`.

---

## 📞 Technical Support & Troubleshooting

* **Build Errors on Vercel:** Verify `build.sh` has executable permissions and `requirements.txt` includes `dj-database-url` & `psycopg2-binary`.
* **Database Connection Issues:** Ensure `sslmode=require` is appended to the `DATABASE_URL` string in Vercel environment variables.
