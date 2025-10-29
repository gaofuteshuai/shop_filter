import mysql.connector
from config import MYSQL_CONFIG

def add_sneakers():
    conn = None  # 初始化conn，避免未定义的错误
    try:
        # 仅使用MYSQL_CONFIG中的配置，不重复添加charset
        conn = mysql.connector.connect(**MYSQL_CONFIG)
        cursor = conn.cursor()

        # 检查"运动鞋"是否已存在
        cursor.execute("SELECT id FROM products WHERE name = '运动鞋'")
        if cursor.fetchone():
            print("⚠️ 数据已存在：运动鞋")
            return

        # 插入数据：("运动鞋", "服装", 288, 1)
        data = ("运动鞋", "服装", 288, 1, "static/images/10.png")
        cursor.execute(
            "INSERT INTO products (name, category, price, free_shipping, image_url) VALUES (%s, %s, %s, %s, %s)",
            data
        )
        conn.commit()  # 提交事务
        print(f"✅ 已添加：{data}（ID: {cursor.lastrowid}）")

    except Exception as e:
        print(f"❌ 添加失败：{e}")
        if conn:  # 仅在conn成功创建时执行回滚
            conn.rollback()
    finally:
        if conn and conn.is_connected():  # 确保conn已定义且连接有效
            cursor.close()
            conn.close()
            print("✅ 数据库连接已关闭")

if __name__ == "__main__":
    add_sneakers()