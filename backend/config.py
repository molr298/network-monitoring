import json
import os
from sqlalchemy import select, insert, update
from database import engine, email_config_table

CONFIG_FILE = os.path.join(os.path.dirname(__file__), 'config.json')

DEFAULT_CONFIG = {
    "email": {
        "smtp_host": "",
        "smtp_port": 587,
        "smtp_user": "",
        "smtp_password": "",
        "recipients": ""
    }
}

def load_config():
    if not os.path.exists(CONFIG_FILE):
        save_config(DEFAULT_CONFIG)
        return DEFAULT_CONFIG
    
    try:
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    except (IOError, json.JSONDecodeError):
        return DEFAULT_CONFIG

def save_config(config_data):
    try:
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config_data, f, indent=4)
    except IOError as e:
        print(f"Error saving config: {e}")

# --- DB helper functions ---

def _db_get_email_config():
    with engine.begin() as conn:
        row = conn.execute(select(email_config_table)).mappings().first()
    if row:
        return {
            "smtp_host": row["smtp_host"] or "",
            "smtp_port": row["smtp_port"] or 587,
            "smtp_user": row["smtp_user"] or "",
            "smtp_password": row["smtp_password"] or "",
            "recipients": row["recipients"] or "",
        }
    return DEFAULT_CONFIG["email"]


def _db_save_email_config(email_config: dict):
    with engine.begin() as conn:
        existing = conn.execute(select(email_config_table.c.id)).scalar_one_or_none()
        if existing:
            stmt = (
                update(email_config_table)
                .where(email_config_table.c.id == existing)
                .values(**email_config)
            )
        else:
            stmt = insert(email_config_table).values(id=1, **email_config)
        conn.execute(stmt)

# --- Public API ---

def get_email_config():
    """Return email config, preferring DB storage; fallback to file for backward compatibility."""
    try:
        return _db_get_email_config()
    except Exception:
        # DB may not be ready yet; fallback
        return load_config().get('email', DEFAULT_CONFIG['email'])

def save_email_config(email_config):
    """Persist email config to DB (and file for redundancy)."""
    try:
        _db_save_email_config(email_config)
    except Exception as exc:
        print(f"Failed to save email config to DB: {exc}")
    # update legacy file as well for compatibility
    config = load_config()
    config['email'] = email_config
    save_config(config)
