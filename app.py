from flask import Flask
from database import init_db, init_notifications_table
from mongo_weather_seed import init_weather_mongo
from routes.auth import auth_bp
from routes.farmer import farmer_bp
from routes.operator import operator_bp
from routes.main import main_bp
from routes.notifications_route import notif_bp

app = Flask(__name__)
app.secret_key = 'agritech-secret-key-2024'

init_db()
init_notifications_table()
weather_mongo_ok, weather_mongo_msg = init_weather_mongo()
print(f"[WeatherMongo] {weather_mongo_msg}")

app.register_blueprint(main_bp)
app.register_blueprint(notif_bp)
app.register_blueprint(auth_bp, url_prefix='/auth')
app.register_blueprint(farmer_bp, url_prefix='/farmer')
app.register_blueprint(operator_bp, url_prefix='/operator')

if __name__ == '__main__':
    app.run(debug=True)