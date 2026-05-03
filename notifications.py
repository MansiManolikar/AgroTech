from database import get_db

def create_notification(user_id: int, title: str, message: str, ntype: str = 'info', link: str = None):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO notifications (user_id, title, message, type, link)
        VALUES (%s, %s, %s, %s, %s)
    """, (user_id, title, message, ntype, link))
    conn.commit()
    conn.close()

def notify_all_farmers(title: str, message: str, ntype: str = 'info', link: str = None):
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT id FROM users WHERE role='farmer'")
    farmers = cursor.fetchall()
    for f in farmers:
        cursor.execute("""
            INSERT INTO notifications (user_id, title, message, type, link)
            VALUES (%s, %s, %s, %s, %s)
        """, (f['id'], title, message, ntype, link))
    conn.commit()
    conn.close()

def notify_farmers_by_crop(crop_id: int, title: str, message: str, ntype: str = 'info', link: str = None):
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT DISTINCT u.id FROM users u
        JOIN farms f ON f.user_id = u.id
        WHERE f.crop_id = %s AND u.role = 'farmer'
    """, (crop_id,))
    farmers = cursor.fetchall()
    for f in farmers:
        cursor.execute("""
            INSERT INTO notifications (user_id, title, message, type, link)
            VALUES (%s, %s, %s, %s, %s)
        """, (f['id'], title, message, ntype, link))
    conn.commit()
    conn.close()

def notify_farmers_by_zone(zone_id: int, title: str, message: str, ntype: str = 'info', link: str = None):
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT DISTINCT u.id FROM users u
        JOIN farms f ON f.user_id = u.id
        WHERE f.zone_id = %s AND u.role = 'farmer'
    """, (zone_id,))
    farmers = cursor.fetchall()
    for f in farmers:
        cursor.execute("""
            INSERT INTO notifications (user_id, title, message, type, link)
            VALUES (%s, %s, %s, %s, %s)
        """, (f['id'], title, message, ntype, link))
    conn.commit()
    conn.close()

def get_notifications(user_id: int, limit: int = 20):
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT * FROM notifications
        WHERE user_id = %s
        ORDER BY created_at DESC
        LIMIT %s
    """, (user_id, limit))
    notifs = cursor.fetchall()
    conn.close()
    return notifs

def get_unread_count(user_id: int) -> int:
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT COUNT(*) AS cnt FROM notifications
        WHERE user_id = %s AND is_read = FALSE
    """, (user_id,))
    result = cursor.fetchone()
    conn.close()
    return result['cnt'] if result else 0

def mark_read(notification_id: int, user_id: int):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE notifications SET is_read = TRUE
        WHERE id = %s AND user_id = %s
    """, (notification_id, user_id))
    conn.commit()
    conn.close()

def mark_all_read(user_id: int):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE notifications SET is_read = TRUE
        WHERE user_id = %s AND is_read = FALSE
    """, (user_id,))
    conn.commit()
    conn.close()

def delete_notification(notification_id: int, user_id: int):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        DELETE FROM notifications WHERE id = %s AND user_id = %s
    """, (notification_id, user_id))
    conn.commit()
    conn.close()

def delete_all_notifications(user_id: int):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM notifications WHERE user_id = %s", (user_id,))
    conn.commit()
    conn.close()