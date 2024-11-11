import os
from dotenv import load_dotenv


basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY") or "you can not guess this one"
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    @staticmethod
    def init_app(app):
        pass


class DevConfig(Config):
    SQLALCHEMY_DATABASE_URI = "sqlite:///" + os.path.join(basedir, "dev_db.db")
    # SQLALCHEMY_DATABASE_URI = os.getenv(
    #     "DEV_DATABASE_URL") or "sqlite:///" + os.path.join(basedir, "dev_db.db")
    DEBUG = os.getenv("DEBUG", False)


class TestingConfig(Config):
    SQLALCHEMY_DATABASE_URI = os.getenv("TEST_DATABASE_URL") or "sqlite://"
    WTF_CSRF_ENABLED = False
    TESTING = True


class ProductionConfig(Config):
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DEV_DATABASE_URL") or "sqlite:///" + os.path.join(basedir, "production.sqlite")


config = {
    'development': DevConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevConfig
}
