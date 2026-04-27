# config.py — safe to commit
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-fallback-key')
    DB_PATH    = os.environ.get('DB_PATH', 'nexus.db')
    DEBUG      = os.environ.get('DEBUG', 'false').lower() == 'true'

def get_config():
    return Config