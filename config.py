import os

class Config:
    """Base Configuration."""
    SECRET_KEY = os.environ.get('SECRET_KEY', 'a_super_secret_key')
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'another_super_secret_key')
    
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'postgresql://postgres:harsha1234@db.gsgzjdeyqngjixyjqkrr.supabase.co:5432/postgres')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # --- NEW: Database Connection Pool Settings ---
    # These settings help manage connections that might be closed by the database server.
    SQLALCHEMY_POOL_RECYCLE = 280  # Recycle connections after 280 seconds
    SQLALCHEMY_POOL_TIMEOUT = 20   # Timeout for getting a connection from the pool
    SQLALCHEMY_POOL_PRE_PING = True # Checks if a connection is alive before using it