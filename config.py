import os
from os import environ
from dotenv import load_dotenv

GOOGLE_CLIENT_ID=os.environ.get("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET=os.environ.get("GOOGLE_CLIENT_SECRET")

class Config(object):
    DEBUG = False
    TESTING = False

class DevelopmentConfig(Config):
    SECRET_KEY=os.environ.get("SECRET_KEY")

config = {
    'development': DevelopmentConfig,
    'testing': DevelopmentConfig,
    'production': DevelopmentConfig
}
