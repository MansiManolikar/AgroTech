class Config:
    SECRET_KEY = 'super123'

    MYSQL_HOST = 'localhost'
    MYSQL_PORT = 3306
    MYSQL_USER= 'root'
    MYSQL_PASSWORD = 'root'
    MYSQL_DB = 'irrigation_portal'
    MYSQL_CURSORCLASS = 'DictCursor'

    MONGO_URI = 'mongodb://localhost:27017/'
    MONGO_DB = 'irrigation_portal_mongo'

class DevelopmentConfig(Config):
    DEBUG = True

class ProductionConfig(Config):
    DEBUG = False

config_map = {
    'development' : DevelopmentConfig,
    'production' : ProductionConfig,
    'default' : DevelopmentConfig,
}