from flask import Blueprint, render_template, request, redirect, url_for, session, jsonify
from notifications import (get_notifications, get_unread_count, delete_notification, delete_all_notifications)

notif_bp = Blueprint('notif', __name__)

def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated

@notif_bp.route('/notifications')
@login_required
def notifications_page():
    user_id = session['user_id']
    notifs  = get_notifications(user_id, limit=50)
    unread  = get_unread_count(user_id)
    return render_template('notifications.html', notifications=notifs, unread_count=unread)

@notif_bp.route('/notifications/mark-read/<int:notif_id>', methods=['POST'])
@login_required
def mark_one_read(notif_id):
    delete_notification(notif_id, session['user_id'])
    return redirect(request.referrer or url_for('notif.notifications_page'))

@notif_bp.route('/notifications/mark-all-read', methods=['POST'])
@login_required
def mark_all():
    delete_all_notifications(session['user_id'])
    return redirect(url_for('notif.notifications_page'))

@notif_bp.route('/notifications/delete/<int:notif_id>', methods=['POST'])
@login_required
def delete_one(notif_id):
    delete_notification(notif_id, session['user_id'])
    return redirect(request.referrer or url_for('notif.notifications_page'))

@notif_bp.route('/notifications/unread-count')
@login_required
def unread_count():
    return jsonify({'count': get_unread_count(session['user_id'])})

@notif_bp.route('/notifications/preview')
@login_required
def preview():
    notifs = get_notifications(session['user_id'], limit=5)
    result = []
    for n in notifs:
        result.append({
            'id':       n['id'],
            'title':    n['title'],
            'message':  n['message'],
            'type':     n['type'],
            'is_read':  n['is_read'],
            'link':     n['link'],
            'created_at': n['created_at'].strftime('%d %b, %I:%M %p') if n['created_at'] else '',
        })
    return jsonify({'notifications': result, 'unread': get_unread_count(session['user_id'])})