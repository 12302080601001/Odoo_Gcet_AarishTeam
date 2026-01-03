# HRMS Email & OTP System Implementation Plan

## Phase 1: OTP Verification System

### 1.1 Email Configuration
- Configure SMTP settings for sending emails
- Use Gmail SMTP or other email service
- Store email credentials securely

### 1.2 OTP Generation & Storage
- Generate 6-digit OTP codes
- Store OTPs in database with expiry time (5 minutes)
- Create OTP verification routes

### 1.3 Login/Signup OTP Flow
**Signup:**
1. User enters details → Generate OTP → Send to email
2. User enters OTP → Verify → Create account
3. Send welcome email

**Login:**
1. User enters credentials → Verify password → Generate OTP
2. Send OTP to registered email
3. User enters OTP → Verify → Login successful

## Phase 2: Email Notifications System

### 2.1 Admin Actions → Employee Notifications
- Leave approved/rejected → Email to employee
- Payroll updated → Email to employee
- Project assigned → Email to team members
- Attendance marked → Email to employee
- Performance review added → Email to employee

### 2.2 Employee Actions → HR Notifications
- Leave request submitted → Email to HR/Admin
- Expense claim submitted → Email to HR
- Project update added → Email to HR/Admin
- Document uploaded → Email to HR

### 2.3 System Notifications
- New user signup → Email to Admin
- Password reset request → Email to user
- Account created → Welcome email to user
- Monthly reports → Email to Admin

## Phase 3: Email Templates

### 3.1 Create Professional Email Templates
- OTP verification email
- Welcome email
- Leave approval/rejection email
- Payroll update email
- Project assignment email
- General notification email

## Implementation Steps

### Step 1: Install Required Packages
```bash
pip install Flask-Mail
```

### Step 2: Update app.py
- Add Flask-Mail configuration
- Create email sending functions
- Add OTP generation and verification
- Update all routes to send emails

### Step 3: Create Database Collections
- `otps` collection for storing OTPs
- Add email_verified field to users

### Step 4: Create Email Templates
- HTML email templates
- Professional design with branding

### Step 5: Update Routes
- Modify signup route for OTP
- Modify login route for OTP
- Add email notifications to all actions

## Email Triggers

### Admin Actions
1. Approve/Reject Leave → Email to Employee
2. Update Payroll → Email to Employee
3. Assign Project → Email to Team Members
4. Add Announcement → Email to All Employees
5. Update User Role → Email to User

### Employee Actions
1. Apply Leave → Email to HR/Admin
2. Submit Expense → Email to HR
3. Check In/Out → Email to Employee (confirmation)
4. Update Project → Email to HR/Admin
5. Upload Document → Email to HR

### System Actions
1. New Signup → Email OTP to User
2. Login → Email OTP to User
3. Forgot Password → Email Reset Link
4. Account Created → Welcome Email
5. Password Changed → Confirmation Email

## Security Features
- OTP expires in 5 minutes
- Maximum 3 OTP attempts
- Email verification required for signup
- Rate limiting on OTP requests
- Secure password reset flow

## Testing Checklist
- [ ] OTP email delivery
- [ ] OTP verification
- [ ] Leave notification emails
- [ ] Payroll notification emails
- [ ] Project notification emails
- [ ] Signup/Login flow
- [ ] Email template rendering
- [ ] Error handling

---

**Status:** Ready to implement
**Estimated Time:** 30-45 minutes
**Priority:** High
