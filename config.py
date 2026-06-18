import os
from dotenv import load_dotenv

load_dotenv()


def _database_uri():
    url = os.environ.get('DATABASE_URL', 'sqlite:///exam_portal.db')
    # Managed Postgres providers (Render, Heroku, etc.) hand out 'postgres://',
    # but SQLAlchemy 2.x requires the 'postgresql://' scheme.
    if url.startswith('postgres://'):
        url = url.replace('postgres://', 'postgresql://', 1)
    return url


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-change-in-production')
    SQLALCHEMY_DATABASE_URI = _database_uri()
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # Recycle pooled connections so managed Postgres doesn't drop idle ones.
    SQLALCHEMY_ENGINE_OPTIONS = {'pool_pre_ping': True, 'pool_recycle': 280}
    ANTHROPIC_API_KEY = os.environ.get('ANTHROPIC_API_KEY', '')
    GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', '')
