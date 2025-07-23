# Flask Inventory Management System with DaisyUI

A comprehensive multi-role inventory management system built with Flask and DaisyUI for managing delivery challans (DCs), DG sets, materials, and stock movements.

## Features Implemented

### 🔐 Authentication & Authorization
- ✅ Role-based login system with Flask-Login
- ✅ Multi-role support: SUPER_ADMIN, ADMIN, OFFICE, STORE, SERVICE_ENTRY
- ✅ Session management and security
- ✅ Password hashing with bcrypt
- ✅ CSRF protection with Flask-WTF

### 🗃️ Database Models
- ✅ Complete SQLAlchemy models for all entities
- ✅ User management with role-based access
- ✅ Site and sub-site management
- ✅ Material categories and inventory items
- ✅ DG set details and specifications
- ✅ Delivery challan workflow
- ✅ Inventory movements tracking
- ✅ Service logs for maintenance
- ✅ Audit logs for compliance

### 🎨 Modern UI with DaisyUI
- ✅ Responsive design with TailwindCSS + DaisyUI
- ✅ Role-based navigation menus
- ✅ Dashboard with statistics and quick actions
- ✅ Theme switching (Light, Dark, Cupcake, Cyberpunk)
- ✅ Toast notification system
- ✅ Sidebar navigation with collapsible sections

### 📊 Dashboard Features
- ✅ Admin dashboard with system overview
- ✅ Statistics cards for key metrics
- ✅ Recent activities display
- ✅ User role distribution
- ✅ Quick action buttons
- ✅ Low stock alerts

## Sample Data

The system comes pre-populated with:
- **5 Users** across all roles (admin/admin123, store/store123, etc.)
- **3 Sites** with sub-locations (Mumbai, Delhi, Bangalore)
- **19 Materials** across 6 categories
- **5 DG Sets** with complete specifications
- **Sample DCs** in various workflow states
- **Initial inventory** with stock levels

## Installation & Setup

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Initialize Database**
   ```bash
   python database/init_data.py
   ```

3. **Run Application**
   ```bash
   python app.py
   ```

4. **Access System**
   - URL: http://localhost:5000
   - Admin Login: admin / admin123
   - Store Login: store / store123
   - Office Login: office / office123

## Technology Stack

### Backend
- **Flask 2.3+** - Python web framework
- **SQLAlchemy** - ORM for database operations
- **Flask-Login** - User session management
- **Flask-Mail** - Email notifications
- **Flask-WTF** - Form handling and CSRF protection
- **bcrypt** - Password hashing
- **PyOTP** - OTP generation and verification

### Frontend
- **DaisyUI 4.0+** - Modern UI components
- **TailwindCSS** - Utility-first CSS framework
- **Font Awesome** - Icon library
- **Vanilla JavaScript** - Frontend interactions

### Database
- **SQLite** (development) / **MySQL** (production)
- Complete schema with proper relationships
- Indexes for performance optimization