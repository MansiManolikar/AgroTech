# import bcrypt
# from flask_login import UserMixin
# from app import mysql

# class User(UserMixin):
#     def __init__(self, data):
#         self.id = data['id']
#         self.name = data['name']
#         self.email = data['email']
#         self.phone = data.get('phone')
#         self.role = data.get('role', 'farmer')
#         self.language = data.get('language', 'en')
#         self.active = data.get('is_active', 1)

#     def get_id(self):
#         return str(self.id)

#     @property
#     def is_farmer(self):
#         return self.role == 'farmer'

#     @property
#     def is_operator(self):
#         return self.role == 'operator'

#     @property
#     def is_active(self):
#         return bool(self.active)

#     @staticmethod
#     def hash_password(password):
#         return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

#     @staticmethod
#     def check_password(password, hashed):
#         return bcrypt.checkpw(password.encode(), hashed.encode())

#     @staticmethod
#     def get_by_id(user_id):
#         cur = mysql.connection.cursor()
#         cur.execute("select * from users where id=%s and is_active=1", (user_id,))
#         row = cur.fetchone()
#         cur.close()
#         return User(row) if row else None

#     @staticmethod
#     def get_by_email(email):
#         cur = mysql.connection.cursor()
#         cur.execute("select * from users where email=%s and is_active=1", (email,))
#         row = cur.fetchone()
#         cur.close()
#         return User(row) if row else None

#     @staticmethod
#     def create(name, email, phone, password, role='farmer', language='en'):
#         hashed = User.hash_password(password)

#         cur = mysql.connection.cursor()
#         cur.execute("insert into users(name, email, phone, password_hash, role, language) values(%s, %s, %s, %s, %s, %s)", (name, email, phone, hashed, role, language))
#         mysql.connection.commit()
#         user_id = cur.lastrowid
#         cur.close()
#         return user_id

#     @staticmethod
#     def update_profile(user_id, name, phone, language):
#         cur = mysql.connection.cursor()
#         cur.execute("update users set name=%s, phone=%s, language=%s where id=%s", (name, phone, language, user_id))
#         mysql.connection.commit()
#         cur.close()

# def load_user(user_id):
#     return User.get_by_id(int(user_id))

import bcrypt

from flask_login import UserMixin

from app import mysql

class User(UserMixin):

    def __init__(self, data: dict):

        self.id       = data['id']

        self.name     = data['name']

        self.email    = data['email']

        self.phone    = data.get('phone')

        self.role     = data['role']

        self.language = data.get('language', 'en')

        self.is_active_flag = data.get('is_active', 1)

    def get_id(self):

        return str(self.id)

    @property

    def is_farmer(self):

        return self.role == 'farmer'

    @property

    def is_operator(self):

        return self.role == 'operator'

    # ------------------------------------------------------------------ #

    # Static helpers

    # ------------------------------------------------------------------ #

    @staticmethod

    def hash_password(plain: str) -> str:

        return bcrypt.hashpw(plain.encode(), bcrypt.gensalt()).decode()

    @staticmethod

    def check_password(plain: str, hashed: str) -> bool:

        return bcrypt.checkpw(plain.encode(), hashed.encode())

    @staticmethod

    def get_by_id(user_id: int):

        cur = mysql.connection.cursor()

        cur.execute("SELECT * FROM users WHERE id = %s AND is_active = 1", (user_id,))

        row = cur.fetchone()

        cur.close()

        return User(row) if row else None

    @staticmethod

    def get_by_email(email: str):

        cur = mysql.connection.cursor()

        cur.execute("SELECT * FROM users WHERE email = %s AND is_active = 1", (email,))

        row = cur.fetchone()

        cur.close()

        return User(row) if row else None

    @staticmethod

    def create(name, email, phone, password, role='farmer', language='en'):

        hashed = User.hash_password(password)

        cur = mysql.connection.cursor()

        cur.execute(

            """INSERT INTO users (name, email, phone, password_hash, role, language)

               VALUES (%s, %s, %s, %s, %s, %s)""",

            (name, email, phone, hashed, role, language)

        )

        mysql.connection.commit()

        uid = cur.lastrowid

        cur.close()

        return uid

    @staticmethod

    def update_profile(user_id, name, phone, language, notif_sms, notif_email):

        cur = mysql.connection.cursor()

        cur.execute(

            """UPDATE users SET name=%s, phone=%s, language=%s,

               notif_sms=%s, notif_email=%s WHERE id=%s""",

            (name, phone, language, notif_sms, notif_email, user_id)

        )

        mysql.connection.commit()

        cur.close()



def load_user(user_id):

    return User.get_by_id(int(user_id))