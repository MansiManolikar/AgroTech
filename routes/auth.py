from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from database import get_db, hash_password
from helpers import log_action
import re

auth_bp = Blueprint('auth', __name__)

SECURITY_QUESTIONS = [
    "What is the name of your primary school?",
    "What is your favourite food?",
    "What is the name of your first pet?",
    "What is your mother's maiden name?",
]

def _valid_name(v):
    return bool(v) and len(v) >= 3 and bool(re.match(r'^[A-Za-z\s]+$', v))
def _valid_email(v):
    return bool(v) and bool(re.match(r'^[^\s@]+@[^\s@]+\.[^\s@]+$', v))
def _valid_phone(v):
    return bool(v) and bool(re.match(r'^[6-9]\d{9}$', v))
def _valid_password(v):
    return bool(v) and len(v) >= 6
def _prepare_security_question(email):
    email = (email or '').strip().lower()
    if not _valid_email(email):
        return False

    conn   = get_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT id, security_question FROM users WHERE email=%s", (email,))
    user = cursor.fetchone()
    conn.close()

    if not user or not user.get('security_question'):
        return False

    session['reset_email']    = email
    session['reset_question'] = user['security_question']
    return True

# Login
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email    = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')

        if not _valid_email(email):
            flash('Enter a valid email address.', 'error')
            return render_template('auth/login.html')
        if not password:
            flash('Password is required.', 'error')
            return render_template('auth/login.html')

        conn   = get_db()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE email=%s", (email,))
        user = cursor.fetchone()
        conn.close()

        if user and user['password'] == hash_password(password):
            session['user_id']   = user['id']
            session['user_name'] = user['name']
            session['role']      = user['role']
            session['email']     = user['email']
            log_action(user['id'], 'login', f"User {user['email']} logged in")
            if user['role'] == 'operator':
                return redirect(url_for('operator.dashboard'))
            return redirect(url_for('farmer.dashboard'))
        else:
            flash('Invalid email or password.', 'error')

    return render_template('auth/login.html')


#Register 
@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name     = request.form.get('name', '').strip()
        email    = request.form.get('email', '').strip().lower()
        phone    = request.form.get('phone', '').strip()
        password = request.form.get('password', '')
        confirm  = request.form.get('confirm_password', '')
        sec_q    = request.form.get('security_question', '').strip()
        sec_a    = request.form.get('security_answer', '').strip().lower()

        errors = []
        if not _valid_name(name):
            errors.append('Full name must be at least 3 characters (letters and spaces only).')
        if not _valid_email(email):
            errors.append('Enter a valid email address.')
        if not _valid_phone(phone):
            errors.append('Enter a valid 10-digit mobile number starting with 6-9.')
        if not _valid_password(password):
            errors.append('Password must be at least 6 characters.')
        if password != confirm:
            errors.append('Passwords do not match.')
        if sec_q not in SECURITY_QUESTIONS:
            errors.append('Please select a valid security question.')
        if len(sec_a) < 2:
            errors.append('Security answer must be at least 2 characters.')

        if errors:
            for e in errors:
                flash(e, 'error')
            return render_template('auth/register.html', questions=SECURITY_QUESTIONS, form_data=request.form)

        conn   = get_db()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id FROM users WHERE email=%s", (email,))
        if cursor.fetchone():
            flash('This email is already registered.', 'error')
            conn.close()
            return render_template('auth/register.html', questions=SECURITY_QUESTIONS, form_data=request.form)

        cursor.execute("""
            INSERT INTO users (name, email, password, role, phone, security_question, security_answer)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (name, email, hash_password(password), 'farmer', phone, sec_q, sec_a))
        conn.commit()
        conn.close()

        try:
            from notifications import create_notification
            conn_op = get_db()
            cur_op  = conn_op.cursor(dictionary=True)
            cur_op.execute("SELECT id FROM users WHERE role='operator'")
            for op in cur_op.fetchall():
                create_notification(
                    user_id=op['id'],
                    title=f'New Farmer Registered: {name}',
                    message=f'A new farmer "{name}" ({email}) has registered.',
                    ntype='info',
                    link='/operator/farmers'
                )
            conn_op.close()
        except Exception:
            pass

        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/register.html', questions=SECURITY_QUESTIONS, form_data={})


# Logout 
@auth_bp.route('/logout')
def logout():
    user_id = session.get('user_id')
    if user_id:
        log_action(user_id, 'logout', 'User logged out')
    session.clear()
    return redirect(url_for('main.index'))


# Forgot Password Step 1: Enter email 
# Forgot Password Step 2: Answer security question 
@auth_bp.route('/verify-security-question', methods=['GET', 'POST'])
def verify_security_question():
    email_from_query = request.args.get('email')
    if email_from_query:
        if not _prepare_security_question(email_from_query):
            flash('No account found with a security question for that email.', 'error')
            return redirect(url_for('auth.login'))
        return redirect(url_for('auth.verify_security_question'))

    email    = session.get('reset_email')
    question = session.get('reset_question')

    if not email or not question:
        flash('Enter your email first, then click Forgot password.', 'error')
        return redirect(url_for('auth.login'))

    if request.method == 'POST':
        answer = request.form.get('security_answer', '').strip().lower()

        if len(answer) < 2:
            flash('Please enter your security answer.', 'error')
            return render_template('auth/verify_security_question.html', question=question)

        conn   = get_db()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id, security_answer FROM users WHERE email=%s", (email,))
        user = cursor.fetchone()
        conn.close()

        if not user or user['security_answer'] != answer:
            flash('Incorrect answer. Please try again.', 'error')
            return render_template('auth/verify_security_question.html', question=question)

        log_action(user['id'], 'security_question_verified', f'Passed for {email}')
        session['sec_verified'] = True
        return redirect(url_for('auth.reset_password'))

    return render_template('auth/verify_security_question.html', question=question)


# Forgot Password Step 3: Set new password 
@auth_bp.route('/reset-password', methods=['GET', 'POST'])
def reset_password():
    email    = session.get('reset_email')
    verified = session.get('sec_verified')

    if not email or not verified:
        flash('Unauthorized. Please start over.', 'error')
        return redirect(url_for('auth.login'))

    if request.method == 'POST':
        password = request.form.get('password', '')
        confirm  = request.form.get('confirm_password', '')

        errors = []
        if not _valid_password(password):
            errors.append('Password must be at least 6 characters.')
        if password != confirm:
            errors.append('Passwords do not match.')
        if errors:
            for e in errors:
                flash(e, 'error')
            return render_template('auth/reset_passwod.html')

        conn   = get_db()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id FROM users WHERE email=%s", (email,))
        user = cursor.fetchone()
        if not user:
            conn.close()
            flash('User not found. Please start again.', 'error')
            return redirect(url_for('auth.login'))

        cursor.execute("UPDATE users SET password=%s WHERE email=%s",
                       (hash_password(password), email))
        conn.commit()
        log_action(user['id'], 'reset_password', 'Password reset via security question')
        conn.close()

        session.pop('reset_email',    None)
        session.pop('reset_question', None)
        session.pop('sec_verified',   None)

        flash('Password reset successfully! Please log in.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/reset_passwod.html')