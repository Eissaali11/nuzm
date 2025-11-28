# نُظم - Arabic Employee Management System

## Overview
نُظم is a comprehensive Arabic employee management system built with Flask, designed for companies in Saudi Arabia. Its primary purpose is to provide complete employee lifecycle management, vehicle tracking, attendance monitoring, and detailed reporting capabilities. The system supports full Arabic language from right-to-left. The business vision is to streamline HR and vehicle fleet operations, offering a localized, efficient solution with strong market potential in the Saudi Arabian business landscape.

## User Preferences
Preferred communication style: Simple, everyday language.

## Recent Updates
- **Nov 28, 2025**: Complete File Retention System - Zero File Loss Guarantee:
  - **Root Cause**: Files were being saved to `/tmp/` (system temp directory) which gets auto-deleted, AND temporary files were being deleted after processing
  - **Solution Applied**: 
    - ✅ Changed all temporary file paths from `/tmp/` to `static/.temp` (persistent project folder)
    - ✅ Removed all file deletion logic - no files are deleted after processing
    - ✅ All files retained permanently in their processing directory
    - Applied to: external_safety.py, api_external_safety.py, operations.py
    - All temporary files during image compression/processing now stay in `static/.temp/`
    - All final files stay in `static/uploads/{module}/`
  - **Files Modified**: 
    - external_safety.py: 3 locations - safety checks uploads from managers and driver camera images
    - api_external_safety.py: API endpoint for mobile app image uploads
    - operations.py: ZIP package creation for sharing operations
  - **Impact**: 
    - ✅ Zero file loss - all uploaded files are permanent
    - ✅ All temporary files retained for recovery/debugging
    - ✅ Complete audit trail of all file operations
    - ✅ Users can download/access files anytime
- **Nov 27, 2025**: GPS Performance & Geofence Cleanup Optimization:
  - **GPS 5-Minute Throttling System**: Implemented smart rate limiting to accept location updates every 5 minutes only, reducing server load by 80%. Single employee (HAMED) reduced from 56 requests to ~12 requests per tracking session.
  - **Smart Caching**: Automatic skip of location data if distance change < 100 meters (100m minimum distance threshold)
  - **Detailed Logging**: Added comprehensive logging (📍 CACHED, ⏳ Throttled, ✅ SAVED) for real-time GPS monitoring
  - **Geofence Event Cleanup**: Automated scheduled deletion of geofence events and sessions older than 24 hours, running every 24 hours via APScheduler
  - **Foreign Key Management**: Implemented safe deletion by first disconnecting FK constraints before removing old session/event records
  - **Data Retention**: Reduced location data retention from 48 hours to 14 hours to save storage
- **Nov 25, 2025**: Vehicle Accident Reporting System:
  - Implemented comprehensive accident reporting API for Flutter mobile app integration
  - Added support for uploading driver ID card, driver license, accident report (PDF/image), and multiple accident photos
  - Created approval workflow system (pending → under_review → approved/rejected) for operations management
  - Extended VehicleAccident model with review_status, driver_phone, latitude/longitude tracking, and Absher phone number
  - Added VehicleAccidentImage model for storing multiple accident photos
  - Created API endpoint `/api/v1/accident-reports/submit` with JWT authentication
  - Automatic image compression (1920x1920, 85% quality) and HEIC support
  - File size limit: 50MB per file, organized storage in `static/uploads/accidents/{accident_id}/`
  - Operations management routes for reviewing/approving accident reports
  - **Professional PDF Export**: Implemented comprehensive accident report PDF generation with FPDF2 library featuring:
    - Full Arabic text support with Cairo font and proper RTL rendering
    - Professional layout with vehicle info, driver details, accident data, and review information
    - Smart document handling: PDF files displayed as clickable links with icons, images embedded inline
    - Includes all accident photos (up to 3 per page) with proper formatting
    - Automatic filename generation: `accident_report_{id}_{plate}_{date}.pdf`
    - Error handling with safe fallbacks for missing or corrupted files
    - PDF export button on accident details page with audit logging
  - Complete API documentation in `API_ACCIDENT_REPORTS.md` with Flutter/Dart examples
  - Bulk delete functionality with select-all checkbox, dynamic count, and automatic file cleanup
- **Nov 19, 2025**: Performance optimization and data integrity fixes:
  - Added database indexes on critical fields (Employee.status, Document.expiry_date, Attendance.date, composite index on employee_id+recorded_at) to improve query performance
  - Fixed department employee count display issue by correcting employee status values from Arabic "يعمل" to standardized "active"
  - Updated get_department_employees API endpoint to strictly filter by status='active' for consistent results
  - All departments now display accurate employee counts (e.g., FLOW department correctly shows 20/20 employees)
- **Nov 16, 2025**: Added Google Search Console verification files to resolve "deceptive site" warning. Files created in multiple locations (root, static folder, Flask route). Requires deployment/publish to take effect on live domain.

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
- **Employee Management**: CRUD, document management with expiry tracking, profile image/ID uploads, bulk import/export. Includes comprehensive housing documentation with multi-image upload (HEIC support) and Google Drive links integration.
- **Vehicle Management**: Registration, tracking, handover/return, workshop records, reports, document management, external safety checks, and automated return system. Includes comprehensive accident reporting system with mobile app integration, review workflow, and multi-file upload support (ID card, license, accident report PDF/image, accident photos).
- **Attendance System**: Daily tracking, overtime, monthly/weekly reports, Hijri calendar integration, department-based filtering, and enhanced dashboard with dual-calendar display. Includes comprehensive geofence session tracking with real-time analytics.
- **GPS Employee Tracking**: Real-time location tracking with high-precision interactive maps using Leaflet 1.9.4. Features include intelligent road-based route drawing via OSRM API, directional arrows, dual-layer maps, enhanced route lines, zoom levels up to 20, metric scale display, auto-fitting bounds, speed-based color coding, and seamless 24-hour movement history visualization.
- **Smart Attendance System (Future)**: Mobile-based attendance with face recognition (ML Kit), geofencing, mock location detection, real-time verification, shift management, and web-based admin dashboard.
- **Salary Management**: Calculation, processing, allowances/deductions, monthly payroll reports.
- **Department Management**: Organizational structure and hierarchy, with department-based access control.
- **User Management**: Role-based access control, permission management, multi-tenant authentication/authorization.
- **Report Generation**: PDF and Excel generation with full Arabic support and professional designs.
- **File Management**: Secure validation, virus scanning, image processing, organized physical storage in `static/uploads/`, and enhanced static file serving.
- **Mobile Device Management**: CRUD for devices, IMEI tracking, department/brand/status filtering, Excel import/export, employee assignment.
- **Employee Requests System**: Comprehensive request management (invoices, car wash, car inspection, advance payments) with web and mobile app interfaces. Features Google Drive integration, request tracking, admin approval workflow, and notifications. Includes a RESTful API for Flutter mobile app integration with 13 endpoints.
- **API**: Comprehensive RESTful API with 25+ endpoints, JWT authentication, search, filtering, and pagination. Includes secure external endpoints for employee profiles and verification.
- **Integrated Management System**: Unified dashboard connecting all modules, auto-accounting integration, and comprehensive reporting.
- **AI Services**: Advanced AI dashboard with intelligent analytics, predictive modeling, strategic recommendations, employee insights, vehicle fleet optimization, and API integration. Includes an AI-powered financial analysis system with OpenAI GPT-4o integration.
- **Chart of Accounts**: Hierarchical tree structure management with automatic default Saudi accounting structure, dedicated account balance pages, and transaction history.
- **Email System**: Comprehensive email sharing with SendGrid integration, local fallback, professional Arabic templates, Excel/PDF attachment support, and a multi-tier delivery system.
- **VoiceHub Integration**: Webhook endpoint for real-time call events, database models for call metadata and analysis, management interface with detailed analysis view, and department-based access control. Includes VoiceHub Knowledge API.
- **Rental Property Management**: System for managing company-rented properties including contract management, payment tracking, property images upload, furnishing inventory, contract expiry alerts, payment reminders, and detailed financial reporting.
- **Google Drive Integration**: Automatic archiving system for vehicle operations and employee requests to Google Drive. Features hierarchical folder structure and automatic upload of PDFs and images. All uploads are optional and non-blocking, preserving local storage as primary source.
- **Google Drive Browser**: Unified browser for all files across all modules, displaying both Google Drive uploads and local-only files. Features comprehensive dashboard with real-time statistics, advanced filtering, responsive RTL table with pagination, status badges, local file links, retry functionality, and direct links to Google Drive folders.

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