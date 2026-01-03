# HRMS - Complete OTP & Email Notification Implementation

## Summary
This document contains all the code needed to implement:
1. OTP verification for login and signup
2. Comprehensive email notifications for all actions
3. Professional email templates

## Current Status
✅ Flask-Mail is already configured in app.py
✅ Email credentials are set up
✅ MongoDB is connected

## What Needs to Be Done

### 1. Add OTP and Email Helper Functions to app.py

Add these functions after line 54 in app.py (after add_notification function):

```python
# OTP Generation and Verification
import random
import string

def generate_otp():
    """Generate a 6-digit OTP"""
    return ''.join(random.choices(string.digits, k=6))

def store_otp(email, otp):
    """Store OTP in database with 5-minute expiry"""
    db.otps.delete_many({"email": email})  # Remove old OTPs
    db.otps.insert_one({
        "email": email,
        "otp": otp,
        "created_at": datetime.utcnow(),
        "expires_at": datetime.utcnow() + timedelta(minutes=5),
        "attempts": 0
    })

def verify_otp(email, otp):
    """Verify OTP and check expiry"""
    otp_record = db.otps.find_one({"email": email})
    
    if not otp_record:
        return False, "OTP not found. Please request a new one."
    
    if otp_record['attempts'] >= 3:
        db.otps.delete_one({"_id": otp_record['_id']})
        return False, "Maximum attempts exceeded. Please request a new OTP."
    
    if datetime.utcnow() > otp_record['expires_at']:
        db.otps.delete_one({"_id": otp_record['_id']})
        return False, "OTP expired. Please request a new one."
    
    if otp_record['otp'] != otp:
        db.otps.update_one(
            {"_id": otp_record['_id']},
            {"$inc": {"attempts": 1}}
        )
        return False, "Invalid OTP. Please try again."
    
    # OTP is valid, delete it
    db.otps.delete_one({"_id": otp_record['_id']})
    return True, "OTP verified successfully!"

# Email Sending Functions
def send_email(to_email, subject, body_html):
    """Send email using Flask-Mail"""
    try:
        msg = Message(subject=subject,
                     recipients=[to_email],
                     html=body_html)
        mail.send(msg)
        return True
    except Exception as e:
        print(f"Error sending email: {str(e)}")
        return False

def send_otp_email(email, otp, purpose="verification"):
    """Send OTP email"""
    subject = f"HRMS - Your OTP Code: {otp}"
    body = f"""
    <html>
    <body style="font-family: Arial; max-width: 600px; margin: 0 auto; padding: 20px;">
        <div style="background: linear-gradient(135deg, #6366f1, #8b5cf6); padding: 30px; text-align: center; color: white; border-radius: 10px 10px 0 0;">
            <h1>🔐 HRMS Verification</h1>
        </div>
        <div style="padding: 30px; background: white; border: 1px solid #e5e7eb; border-top: none; border-radius: 0 0 10px 10px;">
            <h2>Your One-Time Password</h2>
            <p>Use this OTP for {purpose}:</p>
            <div style="background: #f8f9ff; border: 2px dashed #6366f1; padding: 20px; text-align: center; margin: 20px 0; border-radius: 10px;">
                <h1 style="color: #6366f1; letter-spacing: 8px; margin: 0;">{otp}</h1>
            </div>
            <p style="color: #64748b;">This OTP will expire in <strong>5 minutes</strong>.</p>
            <p style="color: #ef4444; font-size: 14px;">⚠️ If you didn't request this, please ignore this email.</p>
        </div>
        <div style="text-align: center; padding: 20px; color: #6c757d; font-size: 12px;">
            <p>© 2026 HRMS. All rights reserved.</p>
        </div>
    </body>
    </html>
    """
    return send_email(email, subject, body)

def send_notification_email(to_email, subject, message):
    """Send notification email"""
    body = f"""
    <html>
    <body style="font-family: Arial; max-width: 600px; margin: 0 auto; padding: 20px;">
        <div style="background: linear-gradient(135deg, #6366f1, #8b5cf6); padding: 30px; text-align: center; color: white; border-radius: 10px 10px 0 0;">
            <h1>📧 HRMS Notification</h1>
        </div>
        <div style="padding: 30px; background: white; border: 1px solid #e5e7eb; border-top: none; border-radius: 0 0 10px 10px;">
            <h2>{subject}</h2>
            <div style="background: #f8f9ff; border-left: 4px solid #6366f1; padding: 20px; margin: 20px 0;">
                <p style="margin: 0;">{message}</p>
            </div>
            <p style="color: #64748b; font-size: 14px;">Time: {datetime.now().strftime('%d %b %Y, %I:%M %p')}</p>
        </div>
        <div style="text-align: center; padding: 20px; color: #6c757d; font-size: 12px;">
            <p>© 2026 HRMS. All rights reserved.</p>
        </div>
    </body>
    </html>
    """
    return send_email(to_email, subject, body)
```

### 2. Email Notifications for All Actions

Add these email calls to existing routes:

#### Leave Approval (in approve_leave route):
```python
# Send email to employee
employee = db.users.find_one({"_id": leave['user_id']})
send_notification_email(
    employee['email'],
    "Leave Request Approved ✅",
    f"Your {leave['leave_type']} leave request from {leave['start_date'].strftime('%d %b')} to {leave['end_date'].strftime('%d %b')} has been approved."
)
```

#### Leave Rejection (in reject_leave route):
```python
# Send email to employee
employee = db.users.find_one({"_id": leave['user_id']})
send_notification_email(
    employee['email'],
    "Leave Request Rejected ❌",
    f"Your {leave['leave_type']} leave request has been rejected. Reason: {comment}"
)
```

#### Leave Application (in apply_leave route):
```python
# Send email to all HR/Admins
admins = db.users.find({"role": {"$in": ["HR", "Administrator"]}})
for admin in admins:
    send_notification_email(
        admin['email'],
        "New Leave Request 📋",
        f"{user['profile']['full_name']} has requested {leave_type} leave from {start_date.strftime('%d %b')} to {end_date.strftime('%d %b')}."
    )
```

#### Payroll Update (in update_payroll route):
```python
# Send email to employee
employee = db.users.find_one({"_id": ObjectId(employee_id)})
send_notification_email(
    employee['email'],
    "Payroll Updated 💰",
    f"Your payroll has been updated. New net salary: ₹{net_salary:,.0f}"
)
```

#### Project Assignment (in add_project route):
```python
# Send email to team members
for member_id in team_members:
    member = db.users.find_one({"_id": ObjectId(member_id)})
    if member:
        send_notification_email(
            member['email'],
            "New Project Assignment 📊",
            f"You have been assigned to project: {name}. Start date: {start_date.strftime('%d %b %Y')}"
        )
```

### 3. OTP Routes to Add

Add these new routes to app.py:

```python
@app.route('/verify-otp', methods=['GET', 'POST'])
def verify_otp_page():
    if request.method == 'POST':
        email = session.get('pending_email')
        otp = request.form.get('otp')
        
        if not email:
            flash('Session expired. Please try again.', 'danger')
            return redirect(url_for('signup'))
        
        success, message = verify_otp(email, otp)
        
        if success:
            # Complete signup
            pending_user = session.get('pending_user')
            if pending_user:
                db.users.insert_one(pending_user)
                send_notification_email(
                    email,
                    "Welcome to HRMS! 🎉",
                    f"Welcome {pending_user['profile']['full_name']}! Your account has been created successfully."
                )
                session.pop('pending_email', None)
                session.pop('pending_user', None)
                flash('Account created successfully! Please login.', 'success')
                return redirect(url_for('login'))
        else:
            flash(message, 'danger')
    
    return render_template('verify_otp.html')

@app.route('/resend-otp', methods=['POST'])
def resend_otp():
    email = session.get('pending_email')
    if email:
        otp = generate_otp()
        store_otp(email, otp)
        send_otp_email(email, otp, "account verification")
        flash('New OTP sent to your email!', 'success')
    return redirect(url_for('verify_otp_page'))
```

### 4. Update Signup Route

Replace the signup route with:

```python
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        full_name = request.form.get('full_name')
        employee_id = request.form.get('employee_id')
        email = request.form.get('email')
        password = request.form.get('password')
        role = request.form.get('role', 'Employee')
        
        # Check if user exists
        if db.users.find_one({"email": email}):
            flash('Email already registered!', 'danger')
            return redirect(url_for('signup'))
        
        # Generate OTP
        otp = generate_otp()
        store_otp(email, otp)
        
        # Store user data in session
        session['pending_email'] = email
        session['pending_user'] = {
            "employee_id": employee_id,
            "email": email,
            "password": generate_password_hash(password),
            "role": role,
            "profile": {
                "full_name": full_name,
                "department": "",
                "designation": "",
                "basic_salary": 0,
                "allowances": 0,
                "deductions": 0,
                "net_salary": 0
            },
            "created_at": datetime.utcnow()
        }
        
        # Send OTP email
        send_otp_email(email, otp, "account verification")
        flash(f'OTP sent to {email}. Please verify to complete registration.', 'info')
        return redirect(url_for('verify_otp_page'))
    
    return render_template('signup.html')
```

### 5. Create verify_otp.html Template

Create this file in templates folder:

```html
{% extends "base.html" %}
{% block title %}Verify OTP - HRMS{% endblock %}
{% block content %}
<div class="container mt-5">
    <div class="row justify-content-center">
        <div class="col-md-5">
            <div class="card shadow">
                <div class="card-body p-5">
                    <div class="text-center mb-4">
                        <i class="fas fa-shield-alt fa-3x text-primary"></i>
                        <h2 class="mt-3">Verify OTP</h2>
                        <p class="text-muted">Enter the 6-digit code sent to your email</p>
                    </div>
                    
                    <form method="POST">
                        <div class="mb-4">
                            <input type="text" name="otp" class="form-control form-control-lg text-center" 
                                   placeholder="000000" maxlength="6" required autofocus
                                   style="letter-spacing: 10px; font-size: 24px;">
                        </div>
                        
                        <button type="submit" class="btn btn-primary w-100 mb-3">
                            <i class="fas fa-check me-2"></i>Verify OTP
                        </button>
                    </form>
                    
                    <form method="POST" action="{{ url_for('resend_otp') }}" class="text-center">
                        <button type="submit" class="btn btn-link">
                            <i class="fas fa-redo me-1"></i>Resend OTP
                        </button>
                    </form>
                </div>
            </div>
        </div>
    </div>
</div>
{% endblock %}
```

## Implementation Checklist

- [ ] Add OTP helper functions to app.py
- [ ] Add email sending functions to app.py
- [ ] Update signup route for OTP
- [ ] Add verify_otp_page route
- [ ] Add resend_otp route
- [ ] Create verify_otp.html template
- [ ] Add email notifications to approve_leave
- [ ] Add email notifications to reject_leave
- [ ] Add email notifications to apply_leave
- [ ] Add email notifications to update_payroll
- [ ] Add email notifications to add_project
- [ ] Add email notifications to check_in/check_out
- [ ] Test OTP flow
- [ ] Test email delivery

## Testing

1. **Test OTP Signup:**
   - Go to signup page
   - Enter details
   - Check email for OTP
   - Enter OTP
   - Verify account created

2. **Test Email Notifications:**
   - Apply for leave → HR should get email
   - Approve leave → Employee should get email
   - Update payroll → Employee should get email

## Notes

- OTP expires in 5 minutes
- Maximum 3 attempts per OTP
- All emails use professional HTML templates
- Email credentials are already configured
- MongoDB otps collection will be created automatically

---

**Status:** Ready to implement
**Priority:** High
**Estimated Time:** 1-2 hours for full implementation
