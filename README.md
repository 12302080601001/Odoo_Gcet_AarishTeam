
# Human Resource Management System 

A comprehensive, modern HRMS built with Flask, Bootstrap, and SQLite. Features role-based access control, attendance tracking, leave management, and payroll management.

## 🌟 Features

### Authentication & Authorization
- ✅ Secure sign up and sign in
- ✅ Role-based access (Employee / HR Admin)
- ✅ Password hashing with Werkzeug
- ✅ Session management

### Employee Features
- 📊 **Dashboard**: Quick overview of attendance, leave requests, and salary
- 👤 **Profile Management**: View and edit personal information
- ⏰ **Attendance Tracking**: Check-in/check-out functionality with daily/weekly views
- 🏖️ **Leave Management**: Apply for leave (Paid, Sick, Unpaid, Casual)
- 💰 **Payroll View**: Read-only access to salary structure

### Admin/HR Features
- 📈 **Admin Dashboard**: Organization statistics and pending approvals
- 👥 **Employee Management**: View all employees and their details
- ✅ **Leave Approval**: Approve or reject leave requests with comments
- 📅 **Attendance Management**: View attendance records of all employees
- 💵 **Payroll Management**: Update salary structure for employees

## 🚀 Installation & Setup

### Prerequisites
- Python 3.8 or higher
- pip (Python package manager)

### Step 1: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 2: Run the Application
```bash
python app.py
```

The application will:
- Create the SQLite database (`hrms.db`)
- Initialize database tables
- Create a default admin account
- Start the development server on `http://localhost:5000`

### Step 3: Access the Application
Open your browser and navigate to: `http://localhost:5000`

## 🔐 Default Credentials

**Admin Account:**
- Email: `admin@hrms.com`
- Password: `admin123`

**Note:** Please change the default admin password after first login in a production environment.

## 📁 Project Structure

```
HR/
├── app.py                          # Main Flask application
├── requirements.txt                # Python dependencies
├── hrms.db                        # SQLite database (auto-created)
├── templates/                     # HTML templates
│   ├── base.html                 # Base template with navbar
│   ├── login.html                # Login page
│   ├── signup.html               # Registration page
│   ├── employee_dashboard.html   # Employee dashboard
│   ├── admin_dashboard.html      # Admin dashboard
│   ├── profile.html              # Profile view
│   ├── edit_profile.html         # Profile edit form
│   ├── employee_attendance.html  # Employee attendance view
│   ├── admin_attendance.html     # Admin attendance management
│   ├── employee_leave.html       # Employee leave requests
│   ├── admin_leave.html          # Admin leave management
│   ├── apply_leave.html          # Leave application form
│   ├── employee_payroll.html     # Employee payroll view
│   ├── admin_payroll.html        # Admin payroll management
│   ├── employees.html            # Employee list
│   └── employee_detail.html      # Employee detail view
└── static/
    └── uploads/                   # User uploads (auto-created)
```

## 🎨 Design Features

- **Modern Dark Theme**: Sleek dark mode with gradient accents
- **Responsive Design**: Mobile-friendly Bootstrap 5 layout
- **Interactive UI**: Smooth animations and hover effects
- **Glassmorphism**: Modern card designs with backdrop blur
- **Color-Coded Status**: Visual indicators for attendance and leave status
- **Icon Integration**: Font Awesome icons throughout

## 🔧 Technology Stack

- **Backend**: Python Flask 3.0
- **Database**: SQLite with SQLAlchemy ORM
- **Frontend**: HTML5, CSS3, JavaScript
- **CSS Framework**: Bootstrap 5.3
- **Icons**: Font Awesome 6.4
- **Fonts**: Google Fonts (Inter)

## 📋 Database Models

### User
- Employee ID, Email, Password (hashed)
- Role (Employee/HR)
- Email verification status

### EmployeeProfile
- Personal details (name, phone, address, DOB)
- Job details (designation, department, joining date)
- Salary structure (basic, allowances, deductions, net)
- Profile picture and documents

### Attendance
- Date, Check-in/Check-out times
- Status (Present, Absent, Half-day, Leave)
- Remarks

### LeaveRequest
- Leave type (Paid, Sick, Unpaid, Casual)
- Date range (start/end dates)
- Reason and admin comments
- Status (Pending, Approved, Rejected)

## 🔒 Security Features

- Password hashing using Werkzeug
- Session-based authentication
- Role-based access control
- CSRF protection (Flask built-in)
- SQL injection prevention (SQLAlchemy ORM)

## 🎯 Future Enhancements

- 📧 Email notifications for leave approvals
- 📊 Analytics dashboard with charts
- 📄 PDF generation for salary slips
- 📱 Mobile app integration
- 🔔 Real-time notifications
- 📈 Performance reports
- 🗓️ Calendar integration
- 💾 Document management system

## 🐛 Troubleshooting

**Database Issues:**
```bash
# Delete the database and restart
rm hrms.db
python app.py
```

**Port Already in Use:**
```python
# Change port in app.py (last line)
app.run(debug=True, port=5001)
```

## 📝 License

This project is created for educational purposes.

## 👨‍💻 Developer

Built with ❤️ using Flask and Bootstrap

---

**Note**: This is a development version. For production deployment:
1. Change the SECRET_KEY in app.py
2. Use a production-grade database (PostgreSQL/MySQL)
3. Enable HTTPS
4. Set debug=False
5. Use a production WSGI server (Gunicorn/uWSGI)
=======
