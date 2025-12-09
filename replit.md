# نُظم - Arabic Employee Management System

## Overview
نُظم is a comprehensive Arabic employee management system built with Flask, designed for companies in Saudi Arabia. Its primary purpose is to provide complete employee lifecycle management, vehicle tracking, attendance monitoring, and detailed reporting capabilities. The system supports full Arabic language from right-to-left. The business vision is to streamline HR and vehicle fleet operations, offering a localized, efficient solution with strong market potential in the Saudi Arabian business landscape.

## User Preferences
Preferred communication style: Simple, everyday language.

## System Architecture
### Frontend Architecture
- **Framework**: Flask with Jinja2 templates, supporting right-to-left (RTL) Arabic.
- **Styling**: Bootstrap-based responsive design with dark color schemes, gradients, transparent cards, and glow effects. Larger, clearer icons are used.
- **Forms**: Flask-WTF for secure handling.
- **JavaScript**: Vanilla JS with Firebase integration, including drag-and-drop, Canvas API for image compression, and Web Share API.
- **Dashboard Design**: Professional analytical dashboards with gradient headers, metric cards, interactive charts (Chart.js), and responsive grids.

### Backend Architecture
- **Framework**: Flask 3.1.0 with a modular blueprint structure.
- **Architecture Pattern**: Modular Monolith with separated concerns, multi-tenant architecture, and a three-tier user hierarchy (System Owner → Company Admin → Employee).
- **Database ORM**: SQLAlchemy 2.0+ with Flask-SQLAlchemy.
- **Authentication**: Flask-Login with Firebase and JWT tokens.
- **Session Management**: Flask sessions with CSRF protection.

### Database Architecture
- **Primary**: MySQL (production).
- **Development**: SQLite.
- **ORM**: SQLAlchemy.

### Key Features & Design Decisions
- **Employee Management**: CRUD, document management with expiry tracking, profile image/ID uploads, bulk import/export, comprehensive housing documentation with multi-image upload (HEIC support) and Google Drive links integration.
- **Vehicle Management**: Registration, tracking, handover/return, workshop records, reports, document management, external safety checks, automated return system, and a comprehensive accident reporting system with mobile app integration, review workflow, and multi-file upload support.
- **Attendance System**: Daily tracking, overtime, monthly/weekly reports, Hijri calendar integration, department-based filtering, enhanced dashboard with dual-calendar display, and comprehensive geofence session tracking with real-time analytics.
- **GPS Employee Tracking**: Real-time location tracking with high-precision interactive maps using Leaflet 1.9.4. Features include intelligent road-based route drawing via OSRM API, directional arrows, dual-layer maps, enhanced route lines, zoom levels up to 20, metric scale display, auto-fitting bounds, speed-based color coding, and seamless 24-hour movement history visualization.
- **Smart Attendance System (Future)**: Mobile-based attendance with face recognition (ML Kit), geofencing, mock location detection, real-time verification, shift management, and web-based admin dashboard.
- **Salary Management**: Calculation, processing, allowances/deductions, monthly payroll reports.
- **Department Management**: Organizational structure and hierarchy, with department-based access control.
- **User Management**: Role-based access control, permission management, multi-tenant authentication/authorization.
- **Report Generation**: PDF and Excel generation with full Arabic support and professional designs.
- **File Management**: ✅ **Unified Storage System** - Secure validation, image processing, organized physical storage in `static/uploads/`, enhanced static file serving. **Permanent local storage** ensures zero loss. Files are automatically uploaded to `static/uploads/` with atomic writes and persistent disk storage. System supports all file types (images, PDF, documents). Fallback to local storage if external services unavailable. **1,193+ files, 232+ MB stored securely**.
- **Mobile Device Management**: CRUD for devices, IMEI tracking, department/brand/status filtering, Excel import/export, employee assignment.
- **Employee Requests System**: Comprehensive request management (invoices, car wash, car inspection, advance payments) with web and mobile app interfaces. Features Google Drive integration, request tracking, admin approval workflow, and notifications. Includes a RESTful API for Flutter mobile app integration with 13 endpoints.
- **API**: Comprehensive RESTful API with 25+ endpoints, JWT authentication, search, filtering, and pagination. Includes secure external endpoints for employee profiles and verification.
- **Integrated Management System**: Unified dashboard connecting all modules, auto-accounting integration, and comprehensive reporting.
- **AI Services**: Advanced AI dashboard with intelligent analytics, predictive modeling, strategic recommendations, employee insights, vehicle fleet optimization, and API integration. Includes an AI-powered financial analysis system with OpenAI GPT-4o integration.
- **Chart of Accounts**: Hierarchical tree structure management with automatic default Saudi accounting structure, dedicated account balance pages, and transaction history.
- **Email System**: Comprehensive email sharing with SendGrid integration, local fallback, professional Arabic templates, Excel/PDF attachment support, and a multi-tier delivery system.
- **VoiceHub Integration**: Webhook endpoint for real-time call events, database models for call metadata and analysis, management interface with detailed analysis view, and department-based access control. Includes VoiceHub Knowledge API.
- **Rental Property Management**: System for managing company-rented properties including contract management, payment tracking, property images upload, furnishing inventory, contract expiry alerts, payment reminders, and detailed financial reporting.
- **File Storage**: ✅ **Local Storage Only** - All files are permanently stored locally in `static/uploads/` with atomic writes and persistent disk storage. System supports all file types (images, PDF, documents). **1,193+ files, 232+ MB stored securely**. Google Drive integration was removed due to Service Account limitations with personal Google accounts (no storage quota for non-Workspace accounts).
- **Power BI Dashboard**: ✅ **Embedded Professional Analytics Dashboard** - Integrated Power BI-style dashboard with real-time charts (Chart.js) showing attendance summaries, department-based attendance rates, document completion status, vehicle status, and operations overview. Features include:
  - **Professional Excel Export**: Multi-sheet Excel reports with formatted headers, conditional coloring (green/yellow/red for status), Arabic RTL support, and professional styling matching the dashboard design
  - **Smart Insights**: AI-powered recommendations and alerts based on data analysis
  - **KPI Cards**: Real-time key performance indicators with trend indicators
  - **Sidebar Integration**: Quick access link under Reports section with BI badge
  - **Date/Department Filtering**: Interactive filters for customized analysis
  - Access at `/powerbi/`

- **Departments Management Dashboard**: ✅ **Professional Departments & Positions Dashboard** - Comprehensive management interface for all organizational divisions featuring:
  - **Department Cards**: Visual cards for each department with employee count, manager info, and quick action buttons
  - **Analytics View**: Detailed analysis of departments and job positions with interactive charts and statistics
  - **Real-time Statistics**: KPI metrics showing total departments, employees, active staff, and position counts
  - **Job Position Analysis**: Comprehensive table showing position names, employee counts, department distribution, and percentages
  - **Interactive Charts**: Bar charts for department distribution and doughnut charts for position prevalence
  - **Employee Status Breakdown**: Visual representation of active, on-leave, and inactive employees
  - **Responsive Design**: Beautiful gradient-based UI with professional styling matching system theme
  - Access at `/departments/` (main) and `/departments/analytics` (detailed analysis)

## External Dependencies
- **Web Framework**: Flask 3.1.0
- **Database ORM**: SQLAlchemy 2.0.40
- **MySQL Driver**: PyMySQL 1.1.1
- **User Management**: Flask-Login 0.6.3
- **Form Handling**: Flask-WTF 1.2.2
- **Arabic Text Processing**: arabic-reshaper 3.0.0, python-bidi 0.6.6
- **Hijri Calendar**: hijri-converter 2.3.1
- **PDF Generation**: reportlab 4.3.1, weasyprint 65.1, fpdf 1.7.2
- **Data Manipulation**: pandas 2.2.3
- **Excel Handling**: openpyxl 3.1.5
- **Image Processing**: Pillow 11.2.1
- **SMS Notifications**: twilio 9.5.2
- **Email Services**: sendgrid 6.11.0
- **Authentication**: Firebase SDK
- **Charting**: Chart.js
- **Mapping**: Leaflet 1.9.4, OSRM API
- **AI**: OpenAI GPT-4o
- **Voice AI**: VoiceHub
- **Face Recognition (Future)**: Google ML Kit, TensorFlow Lite