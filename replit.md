# نُظم - Arabic Employee Management System

## Overview
نُظم is a comprehensive Arabic employee management system built with Flask, designed for companies in Saudi Arabia. Its primary purpose is to provide complete employee lifecycle management, vehicle tracking, attendance monitoring, and detailed reporting capabilities. The system supports full Arabic language from right-to-left. The business vision is to streamline HR and vehicle fleet operations, offering a localized, efficient solution with strong market potential in the Saudi Arabian business landscape.

## User Preferences
Preferred communication style: Simple, everyday language.

## Recent Changes
- **Landing Page Enhancement (Jan 2025)**: Created comprehensive independent landing page at `/nuzum` route completely separate from main system
- **Demo Page Development**: Enhanced demo page with interactive features, customer testimonials, step-by-step guidance, and trial account access
- **Marketing Features**: Added animated statistics, feature showcases, video placeholders, and professional CTA sections
- **Landing Page Routes**: All landing pages now use `/nuzum/` prefix (features, pricing, contact, demo) with separate layout and navigation
- **Demo Page Video Fix (Aug 2025)**: Replaced generic movie videos with interactive iframe demos showing actual system interfaces for employees, vehicles, attendance, and reports management
- **Marketing Presentation Plan**: Created comprehensive 30-45 minute presentation strategy with detailed slides, visual guidelines, pricing structure, and follow-up strategies for B2B sales
- **Documents Search Enhancement (Aug 2025)**: Added advanced search functionality in documents page allowing search by employee name, employee number, and national ID. Added national ID column to documents table for better employee identification.
- **Financial Analytics System (Aug 2025)**: Replaced demo data with real database analytics. Created comprehensive financial analytics dashboard at `/accounting/analytics/` showing actual employee counts, department statistics, transaction summaries, and account breakdowns. Fixed Employee model attribute issues and template URL routing errors to ensure stable operation with authentic data from the accounting system.
- **AI-Powered Financial Analysis System (Aug 2025)**: Integrated OpenAI GPT-4o for intelligent financial analysis and recommendations. Added comprehensive AI financial analyzer service with smart recommendations, expense pattern analysis, and real-time financial insights. Created interactive AI buttons in auto-accounting interface with modal displays for analysis results. System provides Arabic language financial consulting tailored for Saudi market with focus areas including general analysis, salaries, vehicles, and operational efficiency.
- **Chart of Accounts Tree Structure (Aug 2025)**: Implemented comprehensive chart of accounts management system with hierarchical tree display at `/accounting/chart-of-accounts/`. Added automatic creation of default Saudi accounting structure with main accounts (Assets, Liabilities, Equity, Revenue, Expenses), sub-accounts, and detailed accounts. Created dedicated account balance pages with complete transaction history, parent-child relationships, and balance calculations including sub-accounts. Enhanced user experience with clickable account balance buttons leading to detailed separate pages instead of modal popups.
- **Integrated Management System (Aug 2025)**: Created comprehensive integrated management system with modern professional design. Implemented unified dashboard at `/integrated/dashboard` connecting all modules (employees, vehicles, attendance, accounting). Added automatic accounting integration page at `/integrated/auto-accounting` and comprehensive reporting system at `/integrated/comprehensive-report`. Features include real-time statistics, interactive charts, quick actions, urgent tasks tracking, and mobile-responsive design with modern UI/UX standards.
- **Advanced AI Services Module (Aug 2025)**: Developed comprehensive artificial intelligence services module at `/ai/` with professional integration across the system. Created advanced AI dashboard with intelligent analytics, predictive modeling, and strategic recommendations. Features include employee insights analysis, vehicle fleet optimization, predictive analytics, AI-powered recommendations, smart alerts system, and API integration. Added dedicated AI card to reports page with modern gradient design and seamless navigation to AI services dashboard. System provides intelligent business analysis with fallback systems for offline operation.
- **Complete Email System Integration (Aug 2025)**: Successfully implemented comprehensive email sharing system with SendGrid integration and local fallback storage. Features include professional Arabic email templates with vehicle and operation details, Excel/PDF attachment support, sandbox mode for safe testing, local email queue management at `/email-queue/` route, and multi-tier delivery system (SendGrid primary, Resend secondary, local storage fallback). System resolves sender identity verification through sandbox mode and sink.sendgrid.net domain usage. Email service now fully operational for vehicle operation sharing with real-time delivery confirmation.
- **Department-Based Access Control System (Aug 2025)**: Implemented comprehensive department-based filtering across all system modules. Users with assigned_department_id see only data from their specific department, while admin users (without assigned department) maintain full system access. Applied filtering to employees, vehicles, users, dashboard statistics, vehicle operations (handover, workshop, safety, maintenance), external safety checks, and share links. System ensures complete data isolation between departments for enhanced security and privacy.
- **Static File Serving Enhancement (Aug 2025)**: Enhanced Flask static file serving system to properly handle safety check images and uploaded files. Added dedicated routes for `/static/uploads/` and `/uploads/` with fallback mechanisms for missing files. Fixed image display issues in external safety module by implementing proper file path resolution and backup image handling. System now correctly serves images from both static/uploads and uploads directories with appropriate error handling.
- **Employee-Department Many-to-Many Relationship Fix (Oct 2025)**: Fixed critical issue where employee counts and attendance statistics were inaccurate due to using direct department_id field instead of many-to-many relationship. Updated attendance dashboard (`/attendance-dashboard/`), attendance recording API, and department attendance functions to properly use `department.employees` relationship. System now correctly displays all employees assigned to departments through the `employee_departments` junction table.
- **Attendance Dashboard Enhancements (Oct 2025)**: Significantly improved attendance dashboard with modern UX features. Added dual-calendar date display (Hijri and Gregorian) in page header for better clarity. Implemented department filtering system with checkboxes allowing users to show/hide specific departments in statistics table. Added "Show All" and "Hide All" quick action buttons. Enhanced table design with larger badges, improved progress bars, and better visual hierarchy. All department statistics now accurately reflect many-to-many employee relationships.
- **Professional Excel Employee Reports (Oct 2025)**: Completely redesigned employee Excel export system using openpyxl with world-class professional formatting. Created comprehensive 3-sheet workbook structure: Dashboard (visual statistics with color-coded metrics, department distribution, and job title analytics), Employee Data (11-column essential information with status color coding), and Complete Data (16-column comprehensive data). Applied professional color scheme (#1F4788 titles, #4472C4 headers, #70AD47 accents) with alternating row colors, borders, and automatic column width adjustments. Dashboard displays real-time statistics, percentage distributions, and top categories with emoji icons for enhanced readability.
- **VoiceHub AI Integration (Oct 2025)**: Integrated VoiceHub voice AI platform for intelligent call recording and analysis. Implemented webhook endpoint at `/voicehub/webhook` to receive real-time call events (CallStatusChanged, RecordingsAvailable, AnalysisResultReady). Created comprehensive database models (VoiceHubCall, VoiceHubAnalysis) to store call metadata, recordings, transcripts, sentiment analysis, empathy scores, and resolution status. Built management interface at `/voicehub/dashboard` with call list, detailed analysis view, and employee/department assignment features. System supports automatic emotional analysis, keyword extraction, loyalty indicators, and full conversation transcripts in Arabic. Includes department-based access control and secure webhook verification.
- **VoiceHub Knowledge API (Oct 2025)**: Created comprehensive Knowledge API service at `/voicehub/api/knowledge/` enabling VoiceHub voice assistant to query system data in real-time. Implemented 4 secure REST endpoints: employee search (by name/national ID), vehicle search (by plate number/make), department lookup, and system statistics. Added API key authentication via `X-VoiceHub-API-Key` header using VOICEHUB_API_KEY environment variable. Built interactive setup interface in VoiceHub Dashboard with copyable API URL, toggleable API key display, complete endpoint documentation table, and ready-to-use agent instructions. System enables voice assistant to answer queries about employees (73), vehicles (31), and departments (8) during phone calls, providing seamless Arabic voice experience for system data retrieval.

## System Architecture
### Frontend Architecture
- **Framework**: Flask with Jinja2 templates.
- **Language Support**: Right-to-left (RTL) Arabic interface.
- **Styling**: Bootstrap-based responsive design. Color schemes utilize dark backgrounds (e.g., `#1e3a5c`, `#1a1a1a`) with gradients (linear-gradient) for headers and buttons. UI elements often feature transparent cards with backdrop-filter and glow effects. Icons are larger and clearer, with specific colors for different document types.
- **Forms**: Flask-WTF for secure form handling.
- **JavaScript**: Vanilla JS with Firebase integration for authentication. Includes advanced features like drag-and-drop for file uploads, Canvas API for image compression, and Web Share API for content sharing.

### Backend Architecture
- **Framework**: Flask 3.1.0 with a modular blueprint structure.
- **Architecture Pattern**: Modular Monolith with separated concerns, supporting a multi-tenant architecture. This enables data isolation for multiple companies and a three-tier user hierarchy (System Owner → Company Admin → Employee).
- **Database ORM**: SQLAlchemy 2.0+ with Flask-SQLAlchemy.
- **Authentication**: Flask-Login with Firebase integration and JWT tokens.
- **Session Management**: Flask sessions with CSRF protection.

### Database Architecture
- **Primary**: MySQL (production) with PyMySQL driver.
- **Development**: SQLite for local development.
- **ORM**: SQLAlchemy with declarative base models.
- **Migrations**: Manual schema management.

### Key Features & Design Decisions
- **Employee Management**: Comprehensive CRUD operations, department assignments, document management with expiry tracking, profile image/ID uploads, and bulk import/export from Excel with intelligent field mapping.
- **Vehicle Management**: Registration, tracking, handover/return documentation, workshop maintenance records, and detailed reports. Includes management of vehicle documents (registration, plates, insurance) with secure file uploads, image previews, and sharing capabilities. Integrates with Google Drive for file management. Supports external safety checks with photo uploads and admin review workflow. Automated vehicle return system.
- **Attendance System**: Daily tracking, overtime calculation, monthly/weekly reports, Hijri calendar integration.
- **Salary Management**: Calculation, processing, allowances/deductions, monthly payroll reports. Features smart saving for individual and bulk salary entries, leaving empty fields as NULL.
- **Department Management**: Organizational structure and hierarchy.
- **User Management**: Role-based access control, permission management, and multi-tenant user authentication/authorization.
- **Report Generation**: Supports PDF and Excel generation with full Arabic text support (reshaping, bidirectional processing). Professional report designs with company branding and detailed data.
- **File Management**: Secure validation, virus scanning, image processing (compression, thumbnails), and organized physical file storage.
- **Mobile Device Management**: Full CRUD operations for mobile devices, IMEI tracking, optional phone number support, department/brand/status filtering, Excel import/export, employee assignment with advanced search.
- **API**: Comprehensive RESTful API with 25+ endpoints covering all system features, including JWT authentication, advanced search, filtering, and pagination.

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
- **Authentication/Storage**: Firebase SDK
- **Charting**: Chart.js (for report visualizations)
- **Mapping**: Fabric.js (for damage diagrams)