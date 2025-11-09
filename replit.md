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
- **Employee Management**: CRUD operations, department assignment, document management with expiry tracking, profile image/ID uploads, bulk import/export. Includes comprehensive housing documentation with multi-image upload (HEIC support) and Google Drive links integration.
- **Vehicle Management**: Registration, tracking, handover/return, workshop records, reports, document management (registration, plates, insurance), external safety checks with photo uploads, and automated return system.
- **Attendance System**: Daily tracking, overtime, monthly/weekly reports, Hijri calendar integration, department-based filtering, and enhanced dashboard with dual-calendar display.
- **Smart Attendance System (Future)**: Advanced mobile-based attendance with face recognition (ML Kit), geofencing, mock location detection, real-time verification, shift management, and web-based admin dashboard for multi-location workforce management.
- **Salary Management**: Calculation, processing, allowances/deductions, monthly payroll reports.
- **Department Management**: Organizational structure and hierarchy, with department-based access control across all modules.
- **User Management**: Role-based access control, permission management, multi-tenant authentication/authorization.
- **Report Generation**: PDF and Excel generation with full Arabic support and professional futuristic designs. External safety check PDFs feature modern gradient headers (cyan→purple→indigo), color-coded information cards, decorative separators, and image frames with unique colors (cyan, purple, pink, emerald, blue, violet, rose, amber). Excel employee reports feature a 3-sheet workbook structure (Dashboard, Employee Data, Complete Data) with professional formatting and visual statistics.
- **File Management**: Secure validation, virus scanning, image processing, organized physical storage in `static/uploads/` directory, and enhanced static file serving for uploads. All files (images, PDFs) are stored locally for permanent accessibility.
- **Mobile Device Management**: CRUD operations for devices, IMEI tracking, department/brand/status filtering, Excel import/export, employee assignment.
- **Employee Requests System**: Comprehensive employee request management (invoices, car wash, car inspection, advance payments) with web and mobile app interfaces. Features Google Drive integration for file storage, request tracking, admin approval workflow, and notifications system.
- **Employee Requests API**: RESTful API for Flutter mobile app integration with 13 endpoints including JWT authentication, request CRUD operations, file uploads (images/videos up to 500MB), notifications, and statistics. All files are stored on Google Drive with hierarchical folder structure. API documentation available in EMPLOYEE_REQUESTS_API.md.
- **API**: Comprehensive RESTful API with 25+ endpoints, JWT authentication, search, filtering, and pagination.
- **Integrated Management System**: Unified dashboard connecting all modules, auto-accounting integration, and comprehensive reporting.
- **AI Services**: Advanced AI dashboard with intelligent analytics, predictive modeling, strategic recommendations, employee insights, vehicle fleet optimization, and API integration. Includes an AI-powered financial analysis system with OpenAI GPT-4o integration for smart recommendations and real-time financial insights in Arabic.
- **Chart of Accounts**: Hierarchical tree structure management with automatic default Saudi accounting structure, dedicated account balance pages, and transaction history.
- **Email System**: Comprehensive email sharing with SendGrid integration, local fallback, professional Arabic templates, Excel/PDF attachment support, and a multi-tier delivery system. Features enhanced handover operation emails with simplified subject lines ("عملية تسليم" / "عملية استلام") and optimized message content focused on operation success confirmation.
- **VoiceHub Integration**: Webhook endpoint for real-time call events, database models for call metadata and analysis, management interface with detailed analysis view, and department-based access control. Features include emotional analysis, keyword extraction, and full Arabic conversation transcripts.
- **VoiceHub Knowledge API**: Secure REST endpoints for querying system data (employee, vehicle, department, statistics) with API key authentication, and an interactive setup interface in the VoiceHub Dashboard for agent instructions.
- **Rental Property Management**: Comprehensive system for managing company-rented properties including contract management, payment tracking, property images upload with HEIC support, furnishing inventory, contract expiry alerts, payment reminders, and detailed financial reporting.
- **Google Drive Integration**: Automatic archiving system for vehicle operations to Google Drive. Features hierarchical folder structure (نُظم / [Plate Number] / [Operation Type] / [Date-Time]), automatic upload of PDFs and images for workshop records, handover operations, and safety inspections. Includes admin settings page for Service Account credential management. All uploads are optional and non-blocking, preserving local storage as primary source.

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
- **Authentication**: Flask-Login, Firebase SDK
- **Charting**: Chart.js
- **Mapping**: Fabric.js
- **AI**: OpenAI GPT-4o
- **Voice AI**: VoiceHub
- **Face Recognition (Future)**: Google ML Kit, TensorFlow Lite