import user

def get_db_connection():
    return user.connect(
        host='localhost',
        user='your_mysql_user',        # e.g., 'root'
        password='your_mysql_password',
        database='testdb',
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor
    )