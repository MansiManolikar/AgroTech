from flask import Blueprint, render_template, request, redirect, url_for, session, flash, current_app
from flask_mail import Mail, Message
from database import get_db, hash_password
from helpers import log_action
import datetime
import random

auth_bp = Blueprint('auth', __name__)

# Login 
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')

        if not email or not password:
            flash('Please fill all fields', 'error')
            return render_template('auth/login.html')

        conn = get_db()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE email=%s", (email,))
        user = cursor.fetchone()
        conn.close()

        if user and user['password'] == hash_password(password):
            session['user_id'] = user['id']
            session['user_name'] = user['name']
            session['role'] = user['role']
            session['email'] = user['email']

            log_action(user['id'], 'login', f"User {user['email']} logged in")

            if user['role'] == 'operator':
                return redirect(url_for('operator.dashboard'))
            return redirect(url_for('farmer.dashboard'))
        else:
            flash('Invalid email or password', 'error')

    return render_template('auth/login.html')

# Register 
@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        phone = request.form.get('phone', '').strip()

        if not all([name, email, password]):
            flash('Please fill all required fields', 'error')
            return render_template('auth/register.html')

        conn = get_db()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id FROM users WHERE email=%s", (email,))
        existing = cursor.fetchone()

        if existing:
            flash('Email already registered', 'error')
            conn.close()
            return render_template('auth/register.html')

        cursor.execute("""
            INSERT INTO users (name, email, password, role, phone)
            VALUES (%s, %s, %s, %s, %s)
        """, (name, email, hash_password(password), 'farmer', phone))

        conn.commit()
        conn.close()

        try:
            from notifications import create_notification
            conn_op = get_db()
            cur_op = conn_op.cursor(dictionary=True)
            cur_op.execute("SELECT id FROM users WHERE role='operator'")
            operators = cur_op.fetchall()
            conn_op.close()
            for op in operators:
                create_notification(
                    user_id=op['id'],
                    title=f'👨‍🌾 New Farmer Registered: {name}',
                    message=f'A new farmer "{name}" ({email}) has registered on the platform.',
                    ntype='info',
                    link='/operator/farmers'
                )
        except Exception:
            pass

        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/register.html')

# Logout 
@auth_bp.route('/logout')
def logout():
    user_id = session.get('user_id')
    if user_id:
        log_action(user_id, 'logout', 'User logged out')
    session.clear()
    return redirect(url_for('main.index'))

# Forgot Password 
@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()

        if not email:
            flash('Please enter your email address.', 'error')
            return render_template('auth/forgot_password.html')

        conn = get_db()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
        user = cursor.fetchone()

        if user:
            otp = str(random.randint(100000, 999999))
            expires_at = datetime.datetime.now() + datetime.timedelta(minutes=5)

            cursor.execute(
                "UPDATE password_reset_tokens SET used = TRUE WHERE user_id = %s AND used = FALSE",
                (user['id'],)
            )
            cursor.execute(
                "INSERT INTO password_reset_tokens (user_id, token, expires_at) VALUES (%s, %s, %s)",
                (user['id'], otp, expires_at)
            )
            conn.commit()

            try:
                mail = current_app.extensions['mail']
                msg = Message(
                    subject='🌾 AgriTech — Your Password Reset OTP',
                    recipients=[email]
                )
                msg.html = f"""
                <div style="font-family:Arial,sans-serif;max-width:520px;margin:auto;border:1px solid #e0e0e0;border-radius:12px;overflow:hidden;">
                  <div style="background:linear-gradient(135deg,#2e7d32,#66bb6a);padding:32px;text-align:center;">
                    <h1 style="color:#fff;margin:0;font-size:24px;">🌾 AgriTech Portal</h1>
                    <p style="color:rgba(255,255,255,0.85);margin:8px 0 0;">Password Reset OTP</p>
                  </div>
                  <div style="padding:32px;">
                    <p style="font-size:15px;color:#333;">Hello <strong>{user['name']}</strong>,</p>
                    <p style="font-size:14px;color:#555;line-height:1.6;">
                      Use the OTP below to reset your AgriTech password.
                      This code is valid for <strong>5 minutes only</strong>.
                    </p>
                    <div style="text-align:center;margin:32px 0;">
                      <div style="display:inline-block;background:#f1f8e9;border:2px dashed #66bb6a;border-radius:12px;padding:20px 40px;">
                        <div style="font-size:11px;color:#888;font-weight:600;letter-spacing:2px;margin-bottom:8px;">YOUR OTP</div>
                        <div style="font-size:42px;font-weight:800;letter-spacing:10px;color:#2e7d32;">{otp}</div>
                      </div>
                    </div>
                    <p style="font-size:13px;color:#888;line-height:1.6;text-align:center;">
                      ⏱️ Expires in <strong>5 minutes</strong>. Do not share this OTP with anyone.
                    </p>
                    <p style="font-size:13px;color:#aaa;line-height:1.6;">
                      If you didn't request this, you can safely ignore this email.
                    </p>
                    <hr style="border:none;border-top:1px solid #eee;margin:24px 0;">
                    <p style="font-size:12px;color:#aaa;text-align:center;">
                      AgriTech Smart Irrigation Portal &nbsp;|&nbsp; Do not reply to this email
                    </p>
                  </div>
                </div>
                """
                mail.send(msg)
                log_action(user['id'], 'forgot_password', f'OTP sent to {email}')

            except Exception as e:
                conn.close()
                flash('Failed to send OTP. Please check mail configuration.', 'error')
                return render_template('auth/forgot_password.html')

        conn.close()
        session['reset_email'] = email
        flash('If that email is registered, an OTP has been sent. Check your inbox.', 'success')
        return redirect(url_for('auth.verify_otp'))

    return render_template('auth/forgot_password.html')

# Verify OTP 
@auth_bp.route('/verify-otp', methods=['GET', 'POST'])
def verify_otp():
    email = session.get('reset_email')
    if not email:
        flash('Session expired. Please start again.', 'error')
        return redirect(url_for('auth.forgot_password'))

    if request.method == 'POST':
        digits = [request.form.get(f'd{i}', '').strip() for i in range(1, 7)]
        entered_otp = ''.join(digits)

        if len(entered_otp) != 6 or not entered_otp.isdigit():
            flash('Please enter all 6 OTP digits.', 'error')
            return render_template('auth/verify_otp.html', email=email)

        conn = get_db()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
        user = cursor.fetchone()

        if not user:
            conn.close()
            flash('Invalid session. Please start again.', 'error')
            return redirect(url_for('auth.forgot_password'))

        # Valid OTP: matches, not used, not expired
        cursor.execute("""
            SELECT * FROM password_reset_tokens
            WHERE user_id = %s AND token = %s AND used = FALSE AND expires_at > NOW()
        """, (user['id'], entered_otp))
        token_row = cursor.fetchone()

        if not token_row:
            cursor.execute("""
                SELECT * FROM password_reset_tokens
                WHERE user_id = %s AND token = %s AND used = FALSE
            """, (user['id'], entered_otp))
            expired = cursor.fetchone()
            conn.close()
            if expired:
                flash('OTP has expired. Please request a new one.', 'error')
                return redirect(url_for('auth.forgot_password'))
            flash('Incorrect OTP. Please try again.', 'error')
            return render_template('auth/verify_otp.html', email=email)

        cursor.execute("UPDATE password_reset_tokens SET used = TRUE WHERE id = %s", (token_row['id'],))
        conn.commit()
        conn.close()

        session['otp_verified'] = True
        return redirect(url_for('auth.reset_password'))

    return render_template('auth/verify_otp.html', email=email)

# Reset Password 
@auth_bp.route('/reset-password', methods=['GET', 'POST'])
def reset_password():
    email = session.get('reset_email')
    verified = session.get('otp_verified')

    if not email or not verified:
        flash('Unauthorized. Please start over.', 'error')
        return redirect(url_for('auth.forgot_password'))

    if request.method == 'POST':
        password = request.form.get('password', '')
        confirm = request.form.get('confirm_password', '')

        if len(password) < 6:
            flash('Password must be at least 6 characters.', 'error')
            return render_template('auth/reset_password.html')

        if password != confirm:
            flash('Passwords do not match.', 'error')
            return render_template('auth/reset_password.html')

        conn = get_db()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
        user = cursor.fetchone()

        if not user:
            conn.close()
            flash('User not found. Please start again.', 'error')
            return redirect(url_for('auth.forgot_password'))

        cursor.execute("UPDATE users SET password = %s WHERE email = %s", (hash_password(password), email))
        conn.commit()
        log_action(user['id'], 'reset_password', 'Password reset via OTP')
        conn.close()

        session.pop('reset_email', None)
        session.pop('otp_verified', None)

        flash('Password reset successfully! Please log in.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/reset_password.html')