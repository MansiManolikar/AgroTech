from flask import Blueprint, render_template, session, redirect, url_for

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
   return render_template('index.html')

@main_bp.route('/dashboard')
def dashboard_redirect():
   if 'user_id' not in session:
       return redirect(url_for('auth.login'))
   if session.get('role') == 'operator':
       return redirect(url_for('operator.dashboard'))
   return redirect(url_for('farmer.dashboard'))