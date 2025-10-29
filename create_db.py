import mysql.connector
from mysql.connector import errorcode
from config import MYSQL_CONFIG

def init_db():
    try:
        # 1. 连接MySQL服务器（不指定数据库）
        conn = mysql.connector.connect(
            host=MYSQL_CONFIG["host"],
            user=MYSQL_CONFIG["user"],
            password=MYSQL_CONFIG["password"],
            port=MYSQL_CONFIG["port"],
            charset="utf8mb4"  # 强制客户端编码
        )
        cursor = conn.cursor()

        # 2. 创建数据库（指定UTF-8编码）
        db_name = MYSQL_CONFIG["database"]
        cursor.execute(f"""
            CREATE DATABASE IF NOT EXISTS {db_name} 
            DEFAULT CHARACTER SET utf8mb4 
            DEFAULT COLLATE utf8mb4_general_ci
        """)
        print(f"✅ 数据库 {db_name} 创建成功（UTF-8编码）")

        # 3. 切换到创建的数据库
        conn.database = db_name

        # 4. 创建商品表（强制UTF-8编码，与原结构一致）
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS products (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(100) NOT NULL,  # 商品名称
                category VARCHAR(50) NOT NULL,  # 类别
                price INT NOT NULL,  # 价格
                free_shipping TINYINT NOT NULL,  # 1=包邮，0=不包邮
                image_url VARCHAR(255) COMMENT '商品图片路径'  # 新增商品图片路径字段
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        ''')
        print("✅ 表 products 创建成功（支持中文）")
        

        # 5. 清空旧数据并插入初始数据（中文正常显示）
        cursor.execute("TRUNCATE TABLE products")
        data = [
            ("牛仔裤", "服装", 299, 0, "static/images/1.png"),
            ("连衣裙", "服装", 399, 0, "static/images/2.png"),
            ("T恤", "服装", 99, 0, "static/images/3.png"),
            ("饼干", "食品", 19, 1, "static/images/4.png"),
            ("牛奶", "食品", 29, 1, "static/images/5.png"),
            ("巧克力", "食品", 59, 1, "static/images/6.png"),
            ("冰箱", "家电", 2999, 1, "static/images/7.png"),
            ("洗衣机", "家电", 1500, 1, "static/images/8.png"),
            ("笔记本电脑", "家电", 6999, 1, "static/images/9.png")
        ]
        # 执行批量插入（包含image_url字段）
        cursor.executemany('''
            INSERT INTO products 
            (name, category, price, free_shipping, image_url) 
            VALUES (%s, %s, %s, %s, %s)
        ''', data)
        conn.commit()
        print(f"✅ 插入 {len(data)} 条初始数据（中文正常）")

    except mysql.connector.Error as err:
        if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
            print("❌ 错误：用户名或密码不正确")
        else:
            print(f"❌ 初始化失败：{err}")
    finally:
        if 'conn' in locals() and conn.is_connected():
            cursor.close()
            conn.close()

if __name__ == "__main__":
    init_db()