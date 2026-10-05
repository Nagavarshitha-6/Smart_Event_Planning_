# Smart Event Planning Platform with Resource Coordination System
**Institutional Campus Operations & Event Dispatch**  
**Design System Source:** Google Stitch Project `2231770233956563362` (*EventCore Platform*)

---

## 1. Overview
The **Smart Event Planning Platform with Resource Coordination System** is a full-stack enterprise web application built from scratch with Django, MySQL, Bootstrap 5, and Vanilla JavaScript, translating the Google Stitch design system into a functional system for university and campus operations teams.

---

## 2. Technology Stack
- **Backend:** Python 3.10+, Django 4.2 LTS, Django REST Framework, Django ORM
- **Database:** MySQL 8.0 (configured via `.env`), with local SQLite fallback
- **Frontend:** Django Templates, HTML5, CSS3, Bootstrap 5.3, Bootstrap Icons, Material Symbols Outlined, Vanilla JavaScript, Chart.js
- **Typography:** Inter, Poppins, JetBrains Mono (monospaced metrics & codes)
- **Document & Data Export:** `openpyxl` (Excel), `reportlab` (PDF), `Pillow` (Image/Barcode processing)

---

## 3. Project Architecture

```
d:/anigravity_IDE/
├── manage.py
├── requirements.txt
├── .env
├── .env.example
├── .gitignore
├── DESIGN.md
├── README.md
│
├── config/
│   ├── __init__.py          # PyMySQL driver integration
│   ├── settings.py          # Environment-driven settings (MySQL, Auth, Apps)
│   ├── urls.py              # Root routing table & Auth views
│   └── wsgi.py
│
├── accounts/                # Authentication, profiles, password management
├── dashboard/               # Operational telemetry, KPI widgets, turnout charts
├── events/                  # Scheduling core, CRUD, categories
├── registrations/           # Guest lists, ticket generation, duplicate prevention
├── attendance/              # Ticket scanner, badge telemetry, check-in validation
├── vendors/                 # Vendor directory, catering, A/V rigging dispatch
├── resources/               # Assets inventory, scheduling lanes, conflict engine
├── budgets/                 # Financial allocations, ledgers
├── expenses/                # Invoices, expense entries, budget utilization
├── reports/                 # Institutional analytics, Excel & PDF exports
├── notifications/           # Database-backed alerts & dispatch inboxes
│
├── static/
│   ├── css/
│   │   └── style.css        # Stitch design system variables, components & layout
│   ├── js/
│   │   └── main.js          # Mobile drawer toggle, Cmd+K search shortcut
│   └── images/
│       └── logo.svg         # EventCore institutional brand SVG logo
│
└── templates/
    ├── base.html            # Global application shell (Sidebar, Navbar, Alerts)
    ├── registration/
    │   └── login.html       # Stitch-styled login page
    ├── accounts/
    │   ├── profile.html     # Profile & administrative governance
    │   └── change_password.html
    ├── dashboard/
    │   └── index.html       # Operational Dashboard with Chart.js telemetry
    ├── events/
    │   ├── list.html
    │   └── create.html
    ├── registrations/
    │   └── list.html
    ├── attendance/
    │   └── scanner.html
    ├── vendors/
    │   └── list.html
    ├── resources/
    │   ├── list.html
    │   ├── allocations.html
    │   └── conflicts.html
    ├── budgets/
    │   └── list.html
    ├── reports/
    │   └── index.html
    └── notifications/
        └── list.html
```

---

## 4. Configuration & Environment Variables (`.env`)
Database credentials are never hardcoded. Configure your local MySQL credentials in `.env`:

```env
# Database Configuration
# Set DB_ENGINE=mysql for MySQL 8.0, or sqlite3 for local development
DB_ENGINE=mysql
DB_NAME=smartevent_db
DB_USER=root
DB_PASSWORD=your_mysql_password
DB_HOST=127.0.0.1
DB_PORT=3306

# Django Settings
SECRET_KEY=django-insecure-smart-event-planning-platform-dev-key-2026
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
```

---

## 5. Development Server & Verification
- **Dev Server URL:** [http://127.0.0.1:8000/](http://127.0.0.1:8000/)
- **Default Administrative Credentials:**
  - **Username:** `admin`
  - **Password:** `adminpassword123`
  - **Name:** Dr. Sarah Jenkins (Ops Director)
