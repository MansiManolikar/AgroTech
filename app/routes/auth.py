from flask import Blueprint, render_template, request, redirect, url_for, flash, session

from flask_login import login_user, logout_user, login_required, current_user

from app.models.user import User

auth_bp = Blueprint('auth', __name__)



@auth_bp.route('/register', methods=['GET', 'POST'])

def register():

    if current_user.is_authenticated:

        return redirect(url_for('main.index'))

    if request.method == 'POST':

        name     = request.form.get('name', '').strip()

        email    = request.form.get('email', '').strip().lower()

        phone    = request.form.get('phone', '').strip()

        password = request.form.get('password', '')

        confirm  = request.form.get('confirm_password', '')

        role     = request.form.get('role', 'farmer')

        language = request.form.get('language', 'en')

        errors = []

        if not name:      errors.append('Name is required.')

        if not email:     errors.append('Email is required.')

        if len(password) < 8: errors.append('Password must be at least 8 characters.')

        if password != confirm: errors.append('Passwords do not match.')

        if role not in ('farmer', 'operator'): errors.append('Invalid role selected.')

        if not errors and User.get_by_email(email):

            errors.append('An account with this email already exists.')

        if errors:

            for e in errors:

                flash(e, 'error')

            return render_template('auth/register.html', form=request.form)

        User.create(name, email, phone, password, role, language)

        flash('Account created successfully! Please log in.', 'success')

        return redirect(url_for('auth.login'))

    return render_template('auth/register.html', form={})



@auth_bp.route('/login', methods=['GET', 'POST'])

def login():

    if current_user.is_authenticated:

        return redirect(url_for('main.index'))

    if request.method == 'POST':

        email    = request.form.get('email', '').strip().lower()

        password = request.form.get('password', '')

        user = User.get_by_email(email)

        if user and User.check_password(password, _get_hash(email)):

            login_user(user, remember=request.form.get('remember') == 'on')

            flash(f'Welcome back, {user.name}!', 'success')

            next_page = request.args.get('next')

            if user.is_operator:

                return redirect(next_page or url_for('operator.dashboard'))

            return redirect(next_page or url_for('farmer.dashboard'))

        flash('Invalid email or password.', 'error')

    return render_template('auth/login.html')



def _get_hash(email):

    """Fetch raw password hash from DB for bcrypt check."""

    from app import mysql

    cur = mysql.connection.cursor()

    cur.execute("SELECT password_hash FROM users WHERE email=%s", (email,))

    row = cur.fetchone()

    cur.close()

    return row['password_hash'] if row else ''



@auth_bp.route('/logout')

@login_required

def logout():

    logout_user()

    flash('You have been logged out.', 'info')

    return redirect(url_for('auth.login'))



@auth_bp.route('/profile', methods=['GET', 'POST'])

@login_required

def profile():

    if request.method == 'POST':

        name       = request.form.get('name', '').strip()

        phone      = request.form.get('phone', '').strip()

        language   = request.form.get('language', 'en')

        notif_sms  = 1 if request.form.get('notif_sms') else 0

        notif_email= 1 if request.form.get('notif_email') else 0

        User.update_profile(current_user.id, name, phone, language, notif_sms, notif_email)

        flash('Profile updated successfully.', 'success')

        return redirect(url_for('auth.profile'))

    return render_template('auth/profile.html')