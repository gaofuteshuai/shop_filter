from flask import Flask, render_template, request
import mysql.connector
from config import MYSQL_CONFIG
import gradio as gr
import threading
app = Flask(__name__)

# 连接数据库（使用config中的配置，不重复指定charset）
def get_db_connection():
    try:
        # 直接使用MYSQL_CONFIG，不再额外额外添加charset
        conn = mysql.connector.connect(**MYSQL_CONFIG)
        conn.autocommit = True
        return conn
    except Exception as e:
        print(f"❌ 数据库连接失败：{e}")
        raise

# 首页路由
@app.route('/')
def index():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)  # 返回字典格式
    cursor.execute("SELECT * FROM products")
    products = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('index.html', products=products)

# 筛选结果路由
@app.route('/result', methods=['GET'])
def result():
    categories = request.args.getlist('category')
    price_range = request.args.get('priceRange', '')
    shipping = request.args.get('shipping', '')

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    query = "SELECT * FROM products WHERE 1=1"
    params = []

    # 类别筛选
    if categories:
        placeholders = ", ".join(["%s"] * len(categories))
        query += f" AND category IN ({placeholders})"
        params.extend(categories)

    # 价格筛选
    if price_range == '0-100':
        query += " AND price BETWEEN 0 AND 100"
    elif price_range == '100-500':
        query += " AND price BETWEEN 101 AND 500"
    elif price_range == '500+':
        query += " AND price > 500"

    # 包邮筛选
    if shipping == 'yes':
        query += " AND free_shipping = 1"
    elif shipping == 'no':
        query += " AND free_shipping = 0"

    cursor.execute(query, params)
    results = cursor.fetchall()
    cursor.close()
    conn.close()

    # 生成集合表达式
    expr_parts = []
    if categories:
        expr_parts.append('∪'.join([f'{c}集合' for c in categories]))
    if price_range:
        expr_map = {'0-100':'0-100元','100-500':'100-500元','500+':'500元以上'}
        expr_parts.append(f'{expr_map[price_range]}集合')
    if shipping:
        expr_parts.append('包邮集合' if shipping=='yes' else '非包邮集合')
    expression = ' ∩ '.join(expr_parts) if expr_parts else '全集合'

    return render_template('result.html', results=results, expression=expression)

# Gradio相关功能
def get_all_categories():
    """获取所有商品类别"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT category FROM products")
    categories = [row[0] for row in cursor.fetchall()]
    cursor.close()
    conn.close()
    return categories

def search_products(categories, price_range, free_shipping):
    """Gradio搜索函数 - 处理默认提示值"""
    # 忽略默认提示值（视为不筛选）
    if price_range == "请选择价格范围":
        price_range = ""
    if free_shipping == "请选择是否包邮":
        free_shipping = ""

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    query = "SELECT * FROM products WHERE 1=1"
    params = []

    # 类别筛选
    if categories:
        placeholders = ", ".join(["%s"] * len(categories))
        query += f" AND category IN ({placeholders})"
        params.extend(categories)

    # 价格筛选
    if price_range == '0-100元':
        query += " AND price BETWEEN 0 AND 100"
    elif price_range == '100-500元':
        query += " AND price BETWEEN 101 AND 500"
    elif price_range == '500元以上':
        query += " AND price > 500"

    # 包邮筛选
    if free_shipping == "是":
        query += " AND free_shipping = 1"
    elif free_shipping == "否":
        query += " AND free_shipping = 0"

    cursor.execute(query, params)
    results = cursor.fetchall()
    cursor.close()
    conn.close()

    # 格式化输出结果
    if not results:
        return "没有找到符合条件的商品"
    
    output = []
    for item in results:
        shipping_status = "包邮" if item["free_shipping"] else "不包邮"
        output.append(
            f"ID: {item['id']}\n"
            f"名称: {item['name']}\n"
            f"📷 图片：{image_markdown}\n"  # 显示图片
            f"类别: {item['category']}\n"
            f"价格: {item['price']}元\n"
            f"运费: {shipping_status}\n"
            "-------------------------"
        )
    return "\n".join(output)

def create_gradio_interface():
    """创建Gradio界面 - 用value替代placeholder"""
    categories = get_all_categories()
    with gr.Blocks(title="商品查询系统") as demo:
        gr.Markdown("# 商品信息查询")
        gr.Markdown("### 请选择筛选条件，点击【搜索】查看结果（含商品图片）")
        with gr.Row():
            with gr.Column(scale=1):
                category_checkbox = gr.CheckboxGroup(
                    choices=categories,
                    label="商品类别"
                )
                # 用value设置默认提示文字（替代placeholder）
                price_dropdown = gr.Dropdown(
                    choices=["请选择价格范围", "0-100元", "100-500元", "500元以上"],  # 提示文字作为第一个选项
                    label="价格范围",
                    value="请选择价格范围"  # 默认显示提示
                )
                # 用value设置默认提示文字（替代placeholder）
                shipping_radio = gr.Radio(
                    choices=["请选择是否包邮", "是", "否"],  # 提示文字作为第一个选项
                    label="是否包邮",
                    value="请选择是否包邮"  # 默认显示提示
                )
                search_btn = gr.Button("搜索")
            
            with gr.Column(scale=2):
                result_text = gr.Markdown(
                    label="查询结果",
                )
        
        # 设置点击事件
        search_btn.click(
            fn=search_products,
            inputs=[category_checkbox, price_dropdown, shipping_radio],
            outputs=result_text
        )
    
    return demo

# 生成Gradio实例
gradio_demo = create_gradio_interface()

if __name__ == '__main__':
    # 同时启动Flask和Gradio（Flask在5000端口，Gradio在7860端口）
    import threading
    threading.Thread(target=lambda: app.run(host='127.0.0.1', port=5000, debug=True, use_reloader=False)).start()
    gradio_demo.launch(server_name="127.0.0.1", server_port=7860)