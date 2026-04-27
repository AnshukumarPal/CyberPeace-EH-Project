# ================================================================
#  Nexus HR — config.py
#  All configuration is read from environment variables.
#  Use python-dotenv to load a local .env file in development.
# ================================================================

import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    # ── security ─────────────────────────────────────────────
    SECRET_KEY: str = os.environ.get('SECRET_KEY', '')
    if not SECRET_KEY:
        raise RuntimeError(
            "SECRET_KEY is not set. "
            "Copy .env.example → .env and set a strong random value.\n"
            "  python -c \"import secrets; print(secrets.token_hex(32))\""
        )

    SESSION_COOKIE_HTTPONLY: bool = True   # block JS from reading the cookie
    SESSION_COOKIE_SAMESITE: str  = 'Lax' # CSRF mitigation

    # ── database ─────────────────────────────────────────────
    DB_PATH: str = os.environ.get(
        'DB_PATH',
        os.path.join(os.path.dirname(__file__), 'nexus.db')
    )


class DevelopmentConfig(Config):
    DEBUG: bool = True
    SESSION_COOKIE_SECURE: bool = False   # http is fine locally


class ProductionConfig(Config):
    DEBUG: bool = False
    SESSION_COOKIE_SECURE: bool = True    # HTTPS only


# Map FLASK_ENV → config class
_configs = {
    'development': DevelopmentConfig,
    'production':  ProductionConfig,
}

def get_config() -> type:
    env = os.environ.get('FLASK_ENV', 'development').lower()
    cfg = _configs.get(env)
    if cfg is None:
        raise RuntimeError(f"Unknown FLASK_ENV value: '{env}'. Use 'development' or 'production'.")
    return cfg
