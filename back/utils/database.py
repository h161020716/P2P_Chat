import mysql.connector


class Database:
    def __init__(self, config:dict):
        self.conn = mysql.connector.connect(
            host=config['HOST'],
            user=config['USER'],
            password=config['PASSWORD'],
            database=config['DATABASE']
        )
        self.cursor = self.conn.cursor()
        self.create_users_table()

    def create_users_table(self):
        """创建用户表"""
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(50) NOT NULL,
                password VARCHAR(255) NOT NULL,
                phone VARCHAR(15) UNIQUE NOT NULL,
                email VARCHAR(100) UNIQUE NOT NULL,
                id_card VARCHAR(18) UNIQUE NOT NULL,
                profile_picture LONGBLOB
            )
        """)
        self.conn.commit()

    def register_user(self, username, password, phone, email, id_card, profile_picture=None):
        """注册用户"""
        try:
            sql = """
                INSERT INTO users (username, password, phone, email, id_card, profile_picture)
                VALUES (%s, %s, %s, %s, %s, %s)
            """
            self.cursor.execute(sql, (username, password, phone, email, id_card, profile_picture))
            self.conn.commit()
            return True
        except mysql.connector.IntegrityError:
            return False

    def login_user(self, phone, password):
        self.cursor.execute("""
            SELECT username, password, phone, email, id_card FROM users
            WHERE phone = %s AND password = %s
        """, (phone, password))
        return self.cursor.fetchone()

    def update_user_info(self, phone, new_username=None, new_profile_picture=None):
        """更新用户信息"""
        if new_username:
            self.cursor.execute("""
                UPDATE users SET username = %s WHERE phone = %s
            """, (new_username, phone))
        if new_profile_picture:
            self.cursor.execute("""
                UPDATE users SET profile_picture = %s WHERE phone = %s
            """, (new_profile_picture, phone))
        self.conn.commit()
