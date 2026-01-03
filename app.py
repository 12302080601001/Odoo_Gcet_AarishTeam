from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask_mail import Mail, Message
from pymongo import MongoClient
from bson.objectid import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
from functools import wraps
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here-change-in-production'
app.config['UPLOAD_FOLDER'] = 'static/uploads'

# Email Configuration
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'mkbharvad534@gmail.com'
app.config['MAIL_PASSWORD'] = 'dwtp fmiq miyl ccvq'
app.config['MAIL_DEFAULT_SENDER'] = 'mkbharvad534@gmail.com'

mail = Mail(app)

# MongoDB Configuration
MONGO_URI = "mongodb+srv://mkbharvad8080:Mkb%408080@cluster0.a82h2.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
client = MongoClient(MONGO_URI)
db = client['hrms_db']

# Ensure upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'profile_pics'), exist_ok=True)

# Custom Jinja Filter for Date Formatting
@app.template_filter('date_format')
def date_format(value, format='%d %b %Y'):
    if value is None:
        return ""
    if isinstance(value, str):
        try:
            # Try to parse ISO format if it's a string
            value = datetime.fromisoformat(value.replace('Z', '+00:00'))
        except:
            return value  # Return as is if parsing fails
    return value.strftime(format)

# Helper function for notifications
def add_notification(user_id, message, type='info'):
    db.notifications.insert_one({
        "user_id": ObjectId(user_id),
        "message": message,
        "type": type,
        "is_read": False,
        "created_at": datetime.utcnow()
    })

# Helper for dot notation in templates
class MongoObject:
    def __init__(self, data):
        if data is None:
            return
        for key, value in data.items():
            if key == '_id':
                setattr(self, 'id', str(value))
            elif isinstance(value, dict):
                setattr(self, key, MongoObject(value))
            elif isinstance(value, list) and len(value) > 0 and isinstance(value[0], dict):
                setattr(self, key, [MongoObject(i) for i in value])
            else:
                setattr(self, key, value)
    
    def __getattr__(self, name):
        return None  # Return None if attribute doesn't exist

# Decorators
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('login'))
        user = db.users.find_one({"_id": ObjectId(session['user_id'])})
        if not user or user.get('role') not in ['HR', 'Administrator']:
            flash('You do not have permission to access this page.', 'danger')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function

def super_admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('login'))
        user = db.users.find_one({"_id": ObjectId(session['user_id'])})
        if not user or user.get('role') != 'Administrator':
            flash('Administrator privileges required for this action.', 'danger')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function

# HR Required decorator (alias for admin_required - allows HR and Administrator)
def hr_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('login'))
        user = db.users.find_one({"_id": ObjectId(session['user_id'])})
        if not user or user.get('role') not in ['HR', 'Administrator']:
            flash('You do not have permission to access this page.', 'danger')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function

# Error Handlers
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def server_error(e):
    return render_template('500.html'), 500

# Routes
@app.route('/')
@app.route('/home')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return render_template('home.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        employee_id = request.form.get('employee_id')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        role = request.form.get('role')
        full_name = request.form.get('full_name')
        
        if password != confirm_password:
            flash('Passwords do not match!', 'danger')
            return redirect(url_for('signup'))
        
        if len(password) < 8:
            flash('Password must be at least 8 characters long!', 'danger')
            return redirect(url_for('signup'))
        
        if db.users.find_one({"email": email}):
            flash('Email already registered!', 'danger')
            return redirect(url_for('signup'))
        
        if db.users.find_one({"employee_id": employee_id}):
            flash('Employee ID already exists!', 'danger')
            return redirect(url_for('signup'))
        
        hashed_password = generate_password_hash(password)
        
        # User document
        user_data = {
            "employee_id": employee_id,
            "email": email,
            "password": hashed_password,
            "role": role,
            "is_verified": True,
            "created_at": datetime.utcnow(),
            "profile": {
                "full_name": full_name,
                "phone": "",
                "address": "",
                "designation": "",
                "department": "",
                "basic_salary": 0.0,
                "allowances": 0.0,
                "deductions": 0.0,
                "net_salary": 0.0,
                "joining_date": datetime.utcnow()
            }
        }
        
        db.users.insert_one(user_data)
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('login'))
    
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        user = db.users.find_one({"email": email})
        
        if user and check_password_hash(user['password'], password):
            session['user_id'] = str(user['_id'])
            session['role'] = user['role']
            session['employee_id'] = user['employee_id']
            flash(f'Welcome back, {user["profile"]["full_name"]}!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid email or password!', 'danger')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    session.clear()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('login'))

# Forgot Password
@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email')
        user = db.users.find_one({"email": email})
        
        if user:
            # In production, send actual email with reset link
            # For now, just show success message
            flash('Password reset link has been sent to your email!', 'success')
        else:
            flash('Email address not found!', 'danger')
        
        return redirect(url_for('forgot_password'))
    
    return render_template('forgot_password.html')

# Contact Us
@app.route('/contact', methods=['GET', 'POST'])
def contact_us():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        subject = request.form.get('subject')
        message = request.form.get('message')
        
        # Save contact message to database
        db.contact_messages.insert_one({
            "name": name,
            "email": email,
            "subject": subject,
            "message": message,
            "created_at": datetime.utcnow(),
            "status": "New"
        })
        
        flash('Thank you for contacting us! We will get back to you soon.', 'success')
        return redirect(url_for('contact_us'))
    
    return render_template('contact.html')

# Terms & Conditions
@app.route('/terms')
def terms():
    return render_template('terms.html')

# Document Verification
@app.route('/verify', methods=['GET', 'POST'])
def verify_document():
    if request.method == 'POST':
        doc_id = request.form.get('doc_id')
        # Here you would typically check a database for certificates
        # For now, we'll simulate a valid check
        flash(f'Document {doc_id} is VALID and AUTHENTIC.', 'success')
        return redirect(url_for('verify_document'))
    return render_template('verify.html')

@app.route('/dashboard')
@login_required
def dashboard():
    user_data = db.users.find_one({"_id": ObjectId(session['user_id'])})
    user = MongoObject(user_data)
    
    if user.role in ['HR', 'Administrator']:
        total_employees = db.users.count_documents({"role": "Employee"})
        pending_leaves = db.leave_requests.count_documents({"status": "Pending"})
        now = datetime.now()
        today_midnight = datetime(now.year, now.month, now.day)
        today_attendance = db.attendance.count_documents({"date": today_midnight})
        
        recent_leaves_data = list(db.leave_requests.find().sort("created_at", -1).limit(5))
        recent_leaves = []
        for l in recent_leaves_data:
            # Join with user
            u_data = db.users.find_one({"_id": l['user_id']})
            l['user'] = u_data
            recent_leaves.append(MongoObject(l))
            
        # Get Announcements
        announcements_data = list(db.announcements.find().sort("created_at", -1).limit(3))
        announcements = [MongoObject(a) for a in announcements_data]

        return render_template('admin_dashboard.html', 
                             user=user,
                             total_employees=total_employees,
                             pending_leaves=pending_leaves,
                             today_attendance=today_attendance,
                             recent_leaves=recent_leaves,
                             announcements=announcements)
    else:
        now = datetime.now()
        today_midnight = datetime(now.year, now.month, now.day)
        today_attendance_data = db.attendance.find_one({"user_id": ObjectId(session['user_id']), "date": today_midnight})
        today_attendance = MongoObject(today_attendance_data) if today_attendance_data else None
        
        pending_leaves = db.leave_requests.count_documents({"user_id": ObjectId(session['user_id']), "status": "Pending"})
        
        week_ago = datetime.utcnow() - timedelta(days=7)
        recent_attendance_data = list(db.attendance.find({
            "user_id": ObjectId(session['user_id']),
            "created_at": {"$gte": week_ago}
        }).sort("date", -1))
        recent_attendance = [MongoObject(a) for a in recent_attendance_data]
        
        # Get Announcements
        announcements_data = list(db.announcements.find().sort("created_at", -1).limit(3))
        announcements = [MongoObject(a) for a in announcements_data]

        # Get Notifications
        notifications_data = list(db.notifications.find({"user_id": ObjectId(session['user_id']), "is_read": False}).sort("created_at", -1))
        notifications = [MongoObject(n) for n in notifications_data]

        # Get Assigned Projects
        assigned_projects_data = list(db.projects.find({"team_members": ObjectId(session['user_id'])}).sort("created_at", -1))
        assigned_projects = [MongoObject(p) for p in assigned_projects_data]

        return render_template('employee_dashboard.html',
                             user=user,
                             today_attendance=today_attendance,
                             pending_leaves=pending_leaves,
                             recent_attendance=recent_attendance,
                             announcements=announcements,
                             notifications=notifications,
                             assigned_projects=assigned_projects)

@app.route('/profile')
@login_required
def profile():
    user_data = db.users.find_one({"_id": ObjectId(session['user_id'])})
    return render_template('profile.html', user=MongoObject(user_data))

@app.route('/profile/edit', methods=['GET', 'POST'])
@login_required
def edit_profile():
    user_data = db.users.find_one({"_id": ObjectId(session['user_id'])})
    
    if request.method == 'POST':
        update_data = {}
        if user_data['role'] == 'Employee':
            update_data["profile.phone"] = request.form.get('phone')
            update_data["profile.address"] = request.form.get('address')
        else:
            update_data["profile.full_name"] = request.form.get('full_name')
            update_data["profile.phone"] = request.form.get('phone')
            update_data["profile.address"] = request.form.get('address')
            update_data["profile.designation"] = request.form.get('designation')
            update_data["profile.department"] = request.form.get('department')
        
        db.users.update_one({"_id": ObjectId(session['user_id'])}, {"$set": update_data})
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('profile'))
    
    return render_template('edit_profile.html', user=MongoObject(user_data))

@app.route('/attendance')
@login_required
def attendance():
    user_data = db.users.find_one({"_id": ObjectId(session['user_id'])})
    user = MongoObject(user_data)
    
    if user.role == 'HR':
        employees_data = list(db.users.find({"role": "Employee"}))
        employees = [MongoObject(e) for e in employees_data]
        return render_template('admin_attendance.html', user=user, employees=employees)
    else:
        # Get start of current month
        now = datetime.now()
        month_start = datetime(now.year, now.month, 1)
        
        attendance_records_data = list(db.attendance.find({
            "user_id": ObjectId(session['user_id']),
            "created_at": {"$gte": month_start}
        }).sort("date", -1))
        
        attendance_records = [MongoObject(a) for a in attendance_records_data]
        return render_template('employee_attendance.html', user=user, attendance_records=attendance_records)

@app.route('/attendance/checkin', methods=['POST'])
@login_required
def check_in():
    try:
        now = datetime.now()
        today_midnight = datetime(now.year, now.month, now.day)
        user_id = ObjectId(session['user_id'])
        
        # Check if already checked in today
        existing = db.attendance.find_one({"user_id": user_id, "date": today_midnight})
        if existing:
            flash('You have already checked in today!', 'warning')
            return redirect(url_for('attendance'))
        
        # Create attendance record
        db.attendance.insert_one({
            "user_id": user_id,
            "date": today_midnight,
            "check_in": now,
            "check_in_time": now.strftime('%I:%M %p'),
            "status": 'Present',
            "created_at": now
        })
        
        flash(f'Checked in successfully at {now.strftime("%I:%M %p")}!', 'success')
    except Exception as e:
        flash(f'Error checking in: {str(e)}', 'danger')
    
    return redirect(url_for('attendance'))

@app.route('/attendance/checkout', methods=['POST'])
@login_required
def check_out():
    try:
        now = datetime.now()
        today_midnight = datetime(now.year, now.month, now.day)
        user_id = ObjectId(session['user_id'])
        
        record = db.attendance.find_one({"user_id": user_id, "date": today_midnight})
        if not record:
            flash('Please check in first!', 'warning')
            return redirect(url_for('attendance'))
        
        if record.get('check_out'):
            flash('You have already checked out today!', 'warning')
            return redirect(url_for('attendance'))
        
        # Calculate work duration
        check_in_time = record['check_in']
        duration = now - check_in_time
        hours = duration.total_seconds() / 3600
        
        db.attendance.update_one(
            {"_id": record['_id']},
            {"$set": {
                "check_out": now,
                "check_out_time": now.strftime('%I:%M %p'),
                "work_hours": round(hours, 2)
            }}
        )
        
        flash(f'Checked out successfully at {now.strftime("%I:%M %p")}! Total work hours: {round(hours, 2)}h', 'success')
    except Exception as e:
        flash(f'Error checking out: {str(e)}', 'danger')
    
    return redirect(url_for('attendance'))

@app.route('/api/attendance/<string:emp_id>')
@admin_required
def api_get_attendance(emp_id):
    # Get current month records
    now = datetime.now()
    month_start = datetime(now.year, now.month, 1)
    
    records = list(db.attendance.find({
        "user_id": ObjectId(emp_id),
        "created_at": {"$gte": month_start}
    }).sort("date", -1))
    
    # Format for JSON
    result = []
    for r in records:
        result.append({
            "date": r['date'].strftime('%Y-%m-%d'),
            "check_in": r['check_in'].strftime('%I:%M %p') if r.get('check_in') else '-',
            "check_out": r['check_out'].strftime('%I:%M %p') if r.get('check_out') else '-',
            "status": r['status'],
            "remarks": r.get('remarks', '-')
        })
    return jsonify(result)

@app.route('/leave')
@login_required
def leave():
    user_data = db.users.find_one({"_id": ObjectId(session['user_id'])})
    user = MongoObject(user_data)
    
    if user.role == 'HR':
        leave_requests_data = list(db.leave_requests.find().sort("created_at", -1))
        leave_requests = []
        for l in leave_requests_data:
            u_data = db.users.find_one({"_id": l['user_id']})
            l['user'] = u_data
            leave_requests.append(MongoObject(l))
        return render_template('admin_leave.html', user=user, leave_requests=leave_requests)
    else:
        leave_requests_data = list(db.leave_requests.find({"user_id": ObjectId(session['user_id'])}).sort("created_at", -1))
        leave_requests = [MongoObject(l) for l in leave_requests_data]
        return render_template('employee_leave.html', user=user, leave_requests=leave_requests)

@app.route('/leave/apply', methods=['GET', 'POST'])
@login_required
def apply_leave():
    user_data = db.users.find_one({"_id": ObjectId(session['user_id'])})
    
    if request.method == 'POST':
        leave_type = request.form.get('leave_type')
        start_date = datetime.strptime(request.form.get('start_date'), '%Y-%m-%d')
        end_date = datetime.strptime(request.form.get('end_date'), '%Y-%m-%d')
        reason = request.form.get('reason')
        
        db.leave_requests.insert_one({
            "user_id": ObjectId(session['user_id']),
            "leave_type": leave_type,
            "start_date": start_date,
            "end_date": end_date,
            "reason": reason,
            "status": 'Pending',
            "created_at": datetime.utcnow()
        })
        
        flash('Leave request submitted successfully!', 'success')
        return redirect(url_for('leave'))
    
    return render_template('apply_leave.html', user=MongoObject(user_data))

@app.route('/leave/approve/<string:leave_id>', methods=['POST'])
@admin_required
def approve_leave(leave_id):
    leave_request = db.leave_requests.find_one({"_id": ObjectId(leave_id)})
    if not leave_request:
        flash('Leave request not found!', 'danger')
        return redirect(url_for('leave'))
        
    db.leave_requests.update_one(
        {"_id": ObjectId(leave_id)},
        {"$set": {
            "status": 'Approved',
            "admin_comment": request.form.get('comment', ''),
            "updated_at": datetime.utcnow()
        }}
    )
    
    # Add Notification for Employee
    add_notification(leave_request['user_id'], f"Your leave request for {leave_request['start_date'].strftime('%d %b')} has been Approved.", "success")
    
    # Mark attendance as leave
    curr = leave_request['start_date']
    while curr <= leave_request['end_date']:
        date_str = curr.strftime('%Y-%m-%d')
        if not db.attendance.find_one({"user_id": leave_request['user_id'], "date": curr.strftime('%Y-%m-%d')}):
            db.attendance.insert_one({
                "user_id": leave_request['user_id'],
                "date": curr,
                "status": 'Leave',
                "remarks": f"{leave_request['leave_type']} Leave",
                "created_at": datetime.utcnow()
            })
        curr += timedelta(days=1)
    
    flash('Leave request approved!', 'success')
    return redirect(url_for('leave'))

@app.route('/leave/reject/<string:leave_id>', methods=['POST'])
@admin_required
def reject_leave(leave_id):
    leave_request = db.leave_requests.find_one({"_id": ObjectId(leave_id)})
    db.leave_requests.update_one(
        {"_id": ObjectId(leave_id)},
        {"$set": {
            "status": 'Rejected',
            "admin_comment": request.form.get('comment', ''),
            "updated_at": datetime.utcnow()
        }}
    )
    
    # Add Notification for Employee
    add_notification(leave_request['user_id'], f"Your leave request for {leave_request['start_date'].strftime('%d %b')} has been Rejected.", "danger")
    
    flash('Leave request rejected!', 'info')
    return redirect(url_for('leave'))

# New Features Routes
@app.route('/announcements/add', methods=['POST'])
@admin_required
def add_announcement():
    title = request.form.get('title')
    content = request.form.get('content')
    
    db.announcements.insert_one({
        "title": title,
        "content": content,
        "created_at": datetime.utcnow()
    })
    
    flash('Announcement posted successfully!', 'success')
    return redirect(url_for('dashboard'))

@app.route('/notifications/read/<string:notif_id>', methods=['POST'])
@login_required
def read_notification(notif_id):
    db.notifications.update_one(
        {"_id": ObjectId(notif_id)},
        {"$set": {"is_read": True}}
    )
    return jsonify({"status": "success"})

@app.route('/profile/upload_pic', methods=['POST'])
@login_required
def upload_profile_pic():
    if 'profile_pic' not in request.files:
        flash('No file part', 'danger')
        return redirect(url_for('profile'))
    
    file = request.files['profile_pic']
    if file.filename == '':
        flash('No selected file', 'danger')
        return redirect(url_for('profile'))
    
    if file:
        filename = f"{session['user_id']}_{datetime.now().strftime('%Y%m%d%H%M%S')}.jpg"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], 'profile_pics', filename)
        file.save(filepath)
        
        db.users.update_one(
            {"_id": ObjectId(session['user_id'])},
            {"$set": {"profile.profile_picture": filename}}
        )
        
        flash('Profile picture updated!', 'success')
    
    return redirect(url_for('profile'))

@app.route('/holidays')
@login_required
def holidays():
    user = MongoObject(db.users.find_one({"_id": ObjectId(session['user_id'])}))
    holidays_data = list(db.holidays.find().sort("date", 1))
    holidays_list = [MongoObject(h) for h in holidays_data]
    return render_template('holidays.html', user=user, holidays=holidays_list, now=datetime.now())

@app.route('/holidays/add', methods=['POST'])
@admin_required
def add_holiday():
    name = request.form.get('name')
    date = datetime.strptime(request.form.get('date'), '%Y-%m-%d')
    db.holidays.insert_one({
        "name": name,
        "date": date,
        "created_at": datetime.utcnow()
    })
    flash('Holiday added successfully!', 'success')
    return redirect(url_for('holidays'))

# Expense Management
@app.route('/expenses')
@login_required
def expenses():
    user = MongoObject(db.users.find_one({"_id": ObjectId(session['user_id'])}))
    if user.role == 'HR':
        expenses_data = list(db.expenses.find().sort("created_at", -1))
        expenses_list = []
        for e in expenses_data:
            u = db.users.find_one({"_id": e['user_id']})
            e['user'] = u
            expenses_list.append(MongoObject(e))
        return render_template('admin_expenses.html', user=user, expenses=expenses_list)
    else:
        expenses_data = list(db.expenses.find({"user_id": ObjectId(session['user_id'])}).sort("created_at", -1))
        expenses_list = [MongoObject(e) for e in expenses_data]
        return render_template('employee_expenses.html', user=user, expenses=expenses_list)

@app.route('/expenses/apply', methods=['POST'])
@login_required
def apply_expense():
    amount = float(request.form.get('amount'))
    category = request.form.get('category')
    description = request.form.get('description')
    
    db.expenses.insert_one({
        "user_id": ObjectId(session['user_id']),
        "amount": amount,
        "category": category,
        "description": description,
        "status": 'Pending',
        "created_at": datetime.utcnow()
    })
    
    add_notification(session['user_id'], f"Expense claim for ₹{amount} submitted.", "info")
    flash('Expense claim submitted successfully!', 'success')
    return redirect(url_for('expenses'))

@app.route('/expenses/action/<string:expense_id>/<string:action>', methods=['POST'])
@admin_required
def expense_action(expense_id, action):
    status = 'Approved' if action == 'approve' else 'Rejected'
    comment = request.form.get('comment', '')
    
    expense = db.expenses.find_one({"_id": ObjectId(expense_id)})
    db.expenses.update_one(
        {"_id": ObjectId(expense_id)},
        {"$set": {"status": status, "admin_comment": comment, "updated_at": datetime.utcnow()}}
    )
    
    add_notification(expense['user_id'], f"Your expense claim for ₹{expense['amount']} has been {status}.", "success" if action == 'approve' else "danger")
    flash(f'Expense {status.lower()} successfully!', 'success')
    return redirect(url_for('expenses'))

# Performance Management
@app.route('/performance')
@login_required
def performance():
    user = MongoObject(db.users.find_one({"_id": ObjectId(session['user_id'])}))
    if user.role in ['HR', 'Administrator']:
        employees_data = list(db.users.find({"role": "Employee"}))
        employees = [MongoObject(e) for e in employees_data]
        return render_template('admin_performance.html', user=user, employees=employees)
    else:
        reviews_data = list(db.performance_reviews.find({"user_id": ObjectId(session['user_id'])}).sort("review_date", -1))
        reviews = [MongoObject(r) for r in reviews_data]
        return render_template('employee_performance.html', user=user, reviews=reviews)

@app.route('/performance/add', methods=['POST'])
@admin_required
def add_performance_review():
    emp_id = request.form.get('employee_id')
    rating = int(request.form.get('rating'))
    feedback = request.form.get('feedback')
    
    db.performance_reviews.insert_one({
        "user_id": ObjectId(emp_id),
        "rating": rating,
        "feedback": feedback,
        "review_date": datetime.utcnow(),
        "reviewer_id": ObjectId(session['user_id'])
    })
    
    add_notification(emp_id, "A new performance review has been posted for you.", "success")
    flash('Performance review added!', 'success')
    return redirect(url_for('performance'))

@app.route('/analytics')
@admin_required
def analytics():
    user = MongoObject(db.users.find_one({"_id": ObjectId(session['user_id'])}))
    
    # 1. Department Distribution (Doughnut)
    dept_stats = list(db.users.aggregate([
        {"$match": {"role": "Employee"}},
        {"$group": {"_id": "$profile.department", "count": {"$sum": 1}}}
    ]))
    
    # 2. Salary Analytics (Bar)
    salary_stats = list(db.users.aggregate([
        {"$match": {"role": "Employee"}},
        {"$group": {
            "_id": "$profile.department", 
            "total": {"$sum": "$profile.net_salary"},
            "avg": {"$avg": "$profile.net_salary"}
        }}
    ]))
    
    # 3. Attendance Trends (Line - Last 7 Days)
    seven_days_ago = datetime.utcnow() - timedelta(days=7)
    attendance_stats = list(db.attendance.aggregate([
        {"$match": {"created_at": {"$gte": seven_days_ago}, "status": "Present"}},
        {"$group": {
            "_id": {"$dateToString": {"format": "%Y-%m-%d", "date": "$date"}},
            "count": {"$sum": 1}
        }},
        {"$sort": {"_id": 1}}
    ]))
    
    # 4. Expense Distribution (Pie)
    expense_stats = list(db.expenses.aggregate([
        {"$group": {"_id": "$category", "total": {"$sum": "$amount"}}}
    ]))
    
    # 5. Performance Distribution (Polar Area)
    performance_stats = list(db.performance_reviews.aggregate([
        {"$group": {"_id": "$rating", "count": {"$sum": 1}}},
        {"$sort": {"_id": 1}}
    ]))

    # Summary Metrics
    total_staff = db.users.count_documents({"role": "Employee"})
    total_payroll = sum(s['total'] for s in salary_stats)
    pending_tasks = db.leave_requests.count_documents({"status": "Pending"}) + \
                    db.expenses.count_documents({"status": "Pending"})
    
    return render_template('admin_analytics.html', 
                         user=user, 
                         dept_stats=dept_stats, 
                         salary_stats=salary_stats,
                         attendance_stats=attendance_stats,
                         expense_stats=expense_stats,
                         performance_stats=performance_stats,
                         total_staff=total_staff,
                         total_payroll=total_payroll,
                         pending_tasks=pending_tasks)

@app.route('/employees')
@admin_required
def employees():
    user_data = db.users.find_one({"_id": ObjectId(session['user_id'])})
    all_employees_data = list(db.users.find({"role": "Employee"}))
    all_employees = [MongoObject(e) for e in all_employees_data]
    return render_template('employees.html', user=MongoObject(user_data), employees=all_employees)

@app.route('/employee/<string:employee_id>')
@admin_required
def employee_detail(employee_id):
    user_data = db.users.find_one({"_id": ObjectId(session['user_id'])})
    employee_data = db.users.find_one({"_id": ObjectId(employee_id)})
    if not employee_data:
        flash('Employee not found!', 'danger')
        return redirect(url_for('employees'))
        
    now = datetime.now()
    month_start = datetime(now.year, now.month, 1)
    
    attendance_count = db.attendance.count_documents({
        "user_id": ObjectId(employee_id),
        "created_at": {"$gte": month_start},
        "status": "Present"
    })
    
    leave_count = db.leave_requests.count_documents({
        "user_id": ObjectId(employee_id),
        "status": "Approved"
    })
    
    return render_template('employee_detail.html', 
                         user=MongoObject(user_data), 
                         employee=MongoObject(employee_data),
                         attendance_count=attendance_count,
                         leave_count=leave_count)

@app.route('/payroll')
@login_required
def payroll():
    user_data = db.users.find_one({"_id": ObjectId(session['user_id'])})
    user = MongoObject(user_data)
    current_month = datetime.now().strftime('%B %Y')
    
    if user.role == 'HR':
        employees_data = list(db.users.find({"role": "Employee"}))
        employees = [MongoObject(e) for e in employees_data]
        return render_template('admin_payroll.html', user=user, employees=employees)
    else:
        # Generate a unique verification code for the current month
        # This code is based on user_id and current month/year for security
        import hashlib
        verify_secret = f"{user.id}-{current_month}-HRMS-SECRET"
        verify_code = hashlib.sha256(verify_secret.encode()).hexdigest()[:12].upper()
        
        return render_template('employee_payroll.html', 
                             user=user, 
                             current_month=current_month,
                             verify_code=verify_code)

@app.route('/payroll/verify/<code>')
def verify_payroll(code):
    # Public route to verify if a payroll code is valid
    return render_template('payroll_verify.html', 
                         code=code, 
                         status="Verified", 
                         now=datetime.now())

@app.route('/payroll/update/<string:employee_id>', methods=['POST'])
@admin_required
def update_payroll(employee_id):
    basic = float(request.form.get('basic_salary', 0))
    allow = float(request.form.get('allowances', 0))
    deduc = float(request.form.get('deductions', 0))
    net = basic + allow - deduc
    
    db.users.update_one(
        {"_id": ObjectId(employee_id)},
        {"$set": {
            "profile.basic_salary": basic,
            "profile.allowances": allow,
            "profile.deductions": deduc,
            "profile.net_salary": net
        }}
    )
    
    flash('Payroll updated successfully!', 'success')
    return redirect(url_for('payroll'))

@app.route('/super/users')
@super_admin_required
def manage_users():
    user = MongoObject(db.users.find_one({"_id": ObjectId(session['user_id'])}))
    all_users_data = list(db.users.find().sort("created_at", -1))
    all_users = [MongoObject(u) for u in all_users_data]
    return render_template('super_user_management.html', user=user, members=all_users)

@app.route('/super/user/role/<string:uid>', methods=['POST'])
@super_admin_required
def update_user_role(uid):
    new_role = request.form.get('role')
    if uid == session['user_id']:
        flash('You cannot change your own role!', 'danger')
        return redirect(url_for('manage_users'))
    
    db.users.update_one(
        {"_id": ObjectId(uid)},
        {"$set": {"role": new_role}}
    )
    flash('User role updated successfully.', 'success')
    return redirect(url_for('manage_users'))

@app.route('/super/user/delete/<string:uid>', methods=['POST'])
@super_admin_required
def delete_user(uid):
    if uid == session['user_id']:
        flash('You cannot delete your own account!', 'danger')
        return redirect(url_for('manage_users'))
    
    target = db.users.find_one({"_id": ObjectId(uid)})
    if not target:
        flash('User not found!', 'danger')
        return redirect(url_for('manage_users'))
    
    # Cascade delete associated data
    db.attendance.delete_many({"user_id": ObjectId(uid)})
    db.leave_requests.delete_many({"user_id": ObjectId(uid)})
    db.expenses.delete_many({"user_id": ObjectId(uid)})
    db.performance_reviews.delete_many({"user_id": ObjectId(uid)})
    db.notifications.delete_many({"user_id": ObjectId(uid)})
    
    # Delete user
    db.users.delete_one({"_id": ObjectId(uid)})
    
    flash(f'User {target["profile"]["full_name"]} and all associated data have been removed.', 'success')
    return redirect(url_for('manage_users'))

# ==================== NEW FEATURES ====================

# Clients Management
@app.route('/clients')
@admin_required
def clients():
    user = MongoObject(db.users.find_one({"_id": ObjectId(session['user_id'])}))
    clients_data = list(db.clients.find().sort("created_at", -1))
    clients_list = [MongoObject(c) for c in clients_data]
    return render_template('clients.html', user=user, clients=clients_list)

@app.route('/clients/add', methods=['POST'])
@admin_required
def add_client():
    name = request.form.get('name')
    email = request.form.get('email')
    phone = request.form.get('phone')
    company = request.form.get('company')
    address = request.form.get('address')
    
    db.clients.insert_one({
        "name": name,
        "email": email,
        "phone": phone,
        "company": company,
        "address": address,
        "status": "Active",
        "created_at": datetime.utcnow()
    })
    
    flash('Client added successfully!', 'success')
    return redirect(url_for('clients'))

@app.route('/clients/update/<string:client_id>', methods=['POST'])
@admin_required
def update_client(client_id):
    name = request.form.get('name')
    email = request.form.get('email')
    phone = request.form.get('phone')
    company = request.form.get('company')
    address = request.form.get('address')
    
    db.clients.update_one(
        {"_id": ObjectId(client_id)},
        {"$set": {
            "name": name,
            "email": email,
            "phone": phone,
            "company": company,
            "address": address
        }}
    )
    
    flash('Client updated successfully!', 'success')
    return redirect(url_for('clients'))

@app.route('/clients/delete/<string:client_id>', methods=['POST'])
@admin_required
def delete_client(client_id):
    db.clients.delete_one({"_id": ObjectId(client_id)})
    flash('Client deleted successfully!', 'success')
    return redirect(url_for('clients'))

# Projects Management
@app.route('/projects')
@login_required
def projects():
    user = MongoObject(db.users.find_one({"_id": ObjectId(session['user_id'])}))
    
    # If employee, show only their assigned projects
    if user.role == 'Employee':
        projects_data = list(db.projects.find({"team_members": ObjectId(session['user_id'])}).sort("created_at", -1))
        projects_list = []
        for p in projects_data:
            # Get client info
            if p.get('client_id'):
                client = db.clients.find_one({"_id": p['client_id']})
                p['client'] = client
            # Get team members
            if p.get('team_members'):
                team = []
                for member_id in p['team_members']:
                    member = db.users.find_one({"_id": member_id})
                    if member:
                        team.append(member)
                p['team'] = team
            # Get work updates for this project
            updates = list(db.project_updates.find({"project_id": p['_id'], "user_id": ObjectId(session['user_id'])}).sort("created_at", -1).limit(5))
            p['my_updates'] = updates
            projects_list.append(MongoObject(p))
        return render_template('employee_projects.html', user=user, projects=projects_list)
    
    # Admin/HR view
    projects_data = list(db.projects.find().sort("created_at", -1))
    projects_list = []
    for p in projects_data:
        # Get client info
        if p.get('client_id'):
            client = db.clients.find_one({"_id": p['client_id']})
            p['client'] = client
        # Get team members
        if p.get('team_members'):
            team = []
            for member_id in p['team_members']:
                member = db.users.find_one({"_id": member_id})
                if member:
                    team.append(member)
            p['team'] = team
        projects_list.append(MongoObject(p))
    
    clients_data = list(db.clients.find({"status": "Active"}))
    clients_list = [MongoObject(c) for c in clients_data]
    
    employees_data = list(db.users.find({"role": "Employee"}))
    employees_list = [MongoObject(e) for e in employees_data]
    
    return render_template('projects.html', user=user, projects=projects_list, clients=clients_list, employees=employees_list)

@app.route('/projects/add', methods=['POST'])
@admin_required
def add_project():
    name = request.form.get('name')
    client_id = request.form.get('client_id')
    description = request.form.get('description')
    budget = float(request.form.get('budget', 0))
    start_date = datetime.strptime(request.form.get('start_date'), '%Y-%m-%d')
    end_date = datetime.strptime(request.form.get('end_date'), '%Y-%m-%d')
    team_members = request.form.getlist('team_members[]')
    
    db.projects.insert_one({
        "name": name,
        "client_id": ObjectId(client_id) if client_id else None,
        "description": description,
        "budget": budget,
        "start_date": start_date,
        "end_date": end_date,
        "team_members": [ObjectId(tid) for tid in team_members],
        "status": "In Progress",
        "progress": 0,
        "created_at": datetime.utcnow()
    })
    
    flash('Project created successfully!', 'success')
    return redirect(url_for('projects'))

@app.route('/projects/update/<string:project_id>', methods=['POST'])
@admin_required
def update_project_status(project_id):
    try:
        status = request.form.get('status')
        progress = int(request.form.get('progress', 0))
        
        db.projects.update_one(
            {"_id": ObjectId(project_id)},
            {"$set": {"status": status, "progress": progress, "updated_at": datetime.utcnow()}}
        )
        
        flash('Project updated successfully!', 'success')
    except Exception as e:
        flash(f'Error updating project: {str(e)}', 'danger')
    
    return redirect(url_for('projects'))

# Employee Project Update
@app.route('/projects/add-update/<string:project_id>', methods=['POST'])
@login_required
def add_project_update(project_id):
    try:
        project = db.projects.find_one({"_id": ObjectId(project_id)})
        if not project:
            flash('Project not found!', 'danger')
            return redirect(url_for('projects'))
        
        # Check if user is part of the project team
        if ObjectId(session['user_id']) not in project.get('team_members', []):
            flash('You are not authorized to update this project!', 'danger')
            return redirect(url_for('projects'))
        
        update_text = request.form.get('update_text')
        hours_worked = float(request.form.get('hours_worked', 0))
        
        db.project_updates.insert_one({
            "project_id": ObjectId(project_id),
            "user_id": ObjectId(session['user_id']),
            "update_text": update_text,
            "hours_worked": hours_worked,
            "created_at": datetime.utcnow()
        })
        
        # Notify admin
        user = db.users.find_one({"_id": ObjectId(session['user_id'])})
        admins = db.users.find({"role": {"$in": ["HR", "Administrator"]}})
        for admin in admins:
            add_notification(str(admin['_id']), f"{user['profile']['full_name']} added an update to {project['name']}", "info")
        
        flash('Work update added successfully!', 'success')
    except Exception as e:
        flash(f'Error adding update: {str(e)}', 'danger')
    
    return redirect(url_for('projects'))

# Policies Management
@app.route('/policies')
@login_required
def policies():
    user = MongoObject(db.users.find_one({"_id": ObjectId(session['user_id'])}))
    policies_data = list(db.policies.find().sort("created_at", -1))
    policies_list = [MongoObject(p) for p in policies_data]
    return render_template('policies.html', user=user, policies=policies_list)

@app.route('/policies/add', methods=['POST'])
@admin_required
def add_policy():
    title = request.form.get('title')
    category = request.form.get('category')
    content = request.form.get('content')
    
    db.policies.insert_one({
        "title": title,
        "category": category,
        "content": content,
        "effective_date": datetime.utcnow(),
        "created_at": datetime.utcnow()
    })
    
    flash('Policy added successfully!', 'success')
    return redirect(url_for('policies'))

# Reports
@app.route('/reports')
@admin_required
def reports():
    user = MongoObject(db.users.find_one({"_id": ObjectId(session['user_id'])}))
    
    # Generate various reports
    total_employees = db.users.count_documents({"role": "Employee"})
    total_projects = db.projects.count_documents({})
    total_clients = db.clients.count_documents({})
    
    # Attendance Report
    now = datetime.now()
    month_start = datetime(now.year, now.month, 1)
    attendance_report = db.attendance.count_documents({
        "created_at": {"$gte": month_start},
        "status": "Present"
    })
    
    # Leave Report
    leave_report = list(db.leave_requests.aggregate([
        {"$group": {"_id": "$status", "count": {"$sum": 1}}}
    ]))
    
    # Expense Report
    expense_report = list(db.expenses.aggregate([
        {"$group": {"_id": "$status", "total": {"$sum": "$amount"}}}
    ]))
    
    # Payroll Report
    payroll_total = list(db.users.aggregate([
        {"$match": {"role": "Employee"}},
        {"$group": {"_id": None, "total": {"$sum": "$profile.net_salary"}}}
    ]))
    
    return render_template('reports.html', 
                         user=user,
                         total_employees=total_employees,
                         total_projects=total_projects,
                         total_clients=total_clients,
                         attendance_report=attendance_report,
                         leave_report=leave_report,
                         expense_report=expense_report,
                         payroll_total=payroll_total[0]['total'] if payroll_total else 0)

@app.route('/reports/export-csv')
@admin_required
def export_reports_csv():
    import csv
    from io import StringIO
    from flask import make_response
    
    try:
        # Create CSV in memory
        si = StringIO()
        writer = csv.writer(si)
        
        # Write headers
        writer.writerow(['Report Type', 'Metric', 'Value'])
        
        # Employee data
        total_employees = db.users.count_documents({"role": "Employee"})
        writer.writerow(['Employees', 'Total Staff', total_employees])
        
        # Projects data
        total_projects = db.projects.count_documents({})
        writer.writerow(['Projects', 'Active Projects', total_projects])
        
        # Clients data
        total_clients = db.clients.count_documents({})
        writer.writerow(['Clients', 'Total Clients', total_clients])
        
        # Attendance data
        now = datetime.now()
        month_start = datetime(now.year, now.month, 1)
        attendance_count = db.attendance.count_documents({
            "created_at": {"$gte": month_start},
            "status": "Present"
        })
        writer.writerow(['Attendance', 'This Month', attendance_count])
        
        # Leave data
        leave_report = list(db.leave_requests.aggregate([
            {"$group": {"_id": "$status", "count": {"$sum": 1}}}
        ]))
        for item in leave_report:
            writer.writerow(['Leave Requests', item['_id'], item['count']])
        
        # Create response
        output = make_response(si.getvalue())
        output.headers["Content-Disposition"] = "attachment; filename=hrms_reports.csv"
        output.headers["Content-type"] = "text/csv"
        return output
    except Exception as e:
        flash(f'Error exporting CSV: {str(e)}', 'danger')
        return redirect(url_for('reports'))

# Settings
@app.route('/settings')
@login_required
def settings():
    user = MongoObject(db.users.find_one({"_id": ObjectId(session['user_id'])}))
    return render_template('settings.html', user=user)

@app.route('/settings/update', methods=['POST'])
@login_required
def update_settings():
    # Update user preferences
    theme = request.form.get('theme', 'light')
    notifications = request.form.get('notifications') == 'on'
    email_alerts = request.form.get('email_alerts') == 'on'
    
    db.users.update_one(
        {"_id": ObjectId(session['user_id'])},
        {"$set": {
            "settings.theme": theme,
            "settings.notifications": notifications,
            "settings.email_alerts": email_alerts
        }}
    )
    
    flash('Settings updated successfully!', 'success')
    return redirect(url_for('settings'))

# Email System Routes
@app.route('/email')
@login_required
@hr_required
def email_system():
    employees = list(db.users.find({"role": {"$in": ["Employee", "HR"]}}))
    email_logs = list(db.email_logs.find({"sender_id": ObjectId(session['user_id'])}).sort("sent_at", -1).limit(10))
    return render_template('email_system.html', employees=employees, email_logs=email_logs)

@app.route('/email/send', methods=['POST'])
@admin_required
def send_email():
    try:
        recipients = request.form.getlist('recipients[]')
        subject = request.form.get('subject')
        body = request.form.get('body')
        attach_report = request.form.get('attach_report')
        
        # Get recipient emails
        recipient_emails = []
        for emp_id in recipients:
            emp = db.users.find_one({"_id": ObjectId(emp_id)})
            if emp and emp.get('email'):
                recipient_emails.append(emp['email'])
        
        if not recipient_emails:
            flash('No valid recipients found!', 'warning')
            return redirect(url_for('email_system'))
        
        # Create email message
        msg = Message(subject=subject,
                     recipients=recipient_emails)
        msg.body = body
        msg.html = f"""
        <html>
            <body style="font-family: Arial, sans-serif; padding: 20px; background: #f8f9ff;">
                <div style="max-width: 600px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 4px 20px rgba(99,102,241,0.1);">
                    <h2 style="color: #6366f1; margin-bottom: 20px;">HRMS Notification</h2>
                    <div style="color: #64748b; line-height: 1.6;">
                        {body.replace(chr(10), '<br>')}
                    </div>
                    <hr style="margin: 30px 0; border: none; border-top: 1px solid #e2e8f0;">
                    <p style="color: #94a3b8; font-size: 12px; text-align: center;">
                        This is an automated message from HRMS. Please do not reply to this email.
                    </p>
                </div>
            </body>
        </html>
        """
        
        # Send email
        mail.send(msg)
        
        # Log email in database
        db.email_logs.insert_one({
            "sender_id": ObjectId(session['user_id']),
            "recipients": [ObjectId(r) for r in recipients],
            "subject": subject,
            "body": body,
            "sent_at": datetime.utcnow(),
            "status": "Sent"
        })
        
        flash(f'Email sent successfully to {len(recipient_emails)} recipient(s)!', 'success')
    except Exception as e:
        flash(f'Failed to send email: {str(e)}', 'danger')
    
    return redirect(url_for('email_system'))


# Initialize database (Default Roles)
def init_db():
    # 1. Standard HR Admin
    admin = db.users.find_one({"email": 'admin@hrms.com'})
    if not admin:
        user_data = {
            "employee_id": "HR001",
            "email": "admin@hrms.com",
            "password": generate_password_hash("admin123"),
            "role": "HR",
            "is_verified": True,
            "created_at": datetime.utcnow(),
            "profile": {
                "full_name": "HR Administrator",
                "phone": "",
                "address": "",
                "designation": "HR Manager",
                "department": "Human Resources",
                "basic_salary": 50000.0,
                "allowances": 10000.0,
                "deductions": 2000.0,
                "net_salary": 58000.0,
                "joining_date": datetime.utcnow()
            }
        }
        db.users.insert_one(user_data)
        print("Default HR created: admin@hrms.com / admin123")

    # 2. Super Administrator
    super_admin = db.users.find_one({"role": 'Administrator'})
    if not super_admin:
        s_data = {
            "employee_id": "SAD001",
            "email": "root@hrms.com",
            "password": generate_password_hash("root123"),
            "role": "Administrator",
            "is_verified": True,
            "created_at": datetime.utcnow(),
            "profile": {
                "full_name": "System Administrator",
                "designation": "Chief IT Officer",
                "department": "Management",
                "joining_date": datetime.utcnow()
            }
        }
        db.users.insert_one(s_data)
        print("Super Admin created: root@hrms.com / root123")

if __name__ == '__main__':
    init_db()
    app.run(debug=True, port=5000)
