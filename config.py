import os


class Config:
# Change these values for production
    SECRET_KEY = os.environ.get('SECRET_KEY', 'replace_this_with_a_secure_random_string')
    MYSQL_HOST = os.environ.get('MYSQL_HOST', 'localhost')
    MYSQL_USER = os.environ.get('MYSQL_USER', 'root')
    MYSQL_PASSWORD = os.environ.get('MYSQL_PASSWORD', '')
    MYSQL_DB = os.environ.get('MYSQL_DB', 'library_db')
    JWT_EXP_HOURS = int(os.environ.get('JWT_EXP_HOURS', '2'))