from flask import Flask
from flask_mysqldb import MySQL 
from pymongo import MongoClient
from flask_login import LoginManager
from config import config_map
from datetime import datetime

mysql = MySQL()
login_manager = LoginManager()
mongo_db = None

def create_app():
    app = Flask(__name__)

    app.config.from_object(config_map['development'])

    @app.context_processor
    def inject_time():
        return {'now_hour' : datetime.now().hour}
    
    mysql.init_app(app)

    mongo_client = MongoClient(app.config['MONGO_URI'])
    mongo_db = mongo_client[app.config['MONGO_DB']]

    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'

    from app.models.user import load_user
    login_manager.user_loader(load_user)

    from app.routes.auth import auth_bp
    from app.routes.farmer import farmer_bp
    from app.routes.operator import operator_bp
    from app.routes.main import main_bp

    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(farmer_bp, url_prefix='/farmer')
    app.register_blueprint(operator_bp, url_prefix='/operator')
    app.register_blueprint(main_bp)
    
    return app