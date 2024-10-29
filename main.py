from flask import Flask, request
from flask_cors import CORS
from threading import Thread
import os, json, requests
import pymysql
from dotenv import load_dotenv
from datetime import datetime, timezone

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)

product_token = os.getenv("product_token")
product_id = os.getenv("product_id")
current_host = os.getenv("current_host")

def get_utc_timestamp():
    """Get current UTC timestamp"""
    return datetime.now(timezone.utc)


def send_message():
    pass



def updatewebhook():
    base_url = "https://api.maytapi.com"

    phone_id = "59094"

    url = f"{base_url}/api/{product_id}/{phone_id}/config"

    payload = json.dumps({"webhook": f"{current_host}/webhook", "ack_delivery": False})
    headers = {'Content-Type': 'application/json', 'x-maytapi-key': product_token}

    response = requests.request("POST", url, headers=headers, data=payload).json()
    print(response)


def sendmessage(phone_payload, text):
    base_url = "https://api.maytapi.com"
    product_id = phone_payload['product_id']
    phone_id = phone_payload['phone_id']

    url = f"{base_url}/api/{product_id}/{phone_id}/sendMessage"

    payload = {"to_number": phone_payload['conversation'],"type": "text","message": text, "reply_to" : phone_payload['message']['id'], "skip_filter":True}
    payload = json.dumps(payload)
    headers = {
            'x-maytapi-key': product_token,
            'Content-Type': 'application/json'
        }

    response = requests.request("POST", url, headers=headers, data=payload)

def get_connection():
    """Create and return a database connection"""
    try:
        connection = pymysql.connect(host=os.getenv('db_host'), user=os.getenv('db_user'),
            password=os.getenv('db_password'), database=os.getenv('db'), cursorclass=pymysql.cursors.DictCursor)
        return connection
    except pymysql.Error as e:
        print(f"Error connecting to the database: {e}")
        return None


def insert_sale(type, detail):
    """Insert a sale record with UTC timestamp"""
    conn = get_connection()
    if not conn:
        return False

    try:
        with conn.cursor() as cursor:
            sql = "INSERT INTO sales (type, detail, timestamp) VALUES (%s, %s, %s)"
            utc_now = get_utc_timestamp()
            cursor.execute(sql, (type, detail, utc_now))
            conn.commit()
            print(f"Sale record inserted successfully!")
            return True
    except pymysql.Error as e:
        print(f"Error inserting sale: {e}")
        return False
    finally:
        conn.close()


@app.get("/")
def home():
    return {'success': True, 'message': 'this is home page'}


def identify_order_type(text):
    text = text.lower()
    sell = ['wts', 'want to sell', 'wt sell', 'w.t.s']
    buy = ['wtb', 'want to buy', 'wt buy', 'w.t.b', 'need']

    if any(keyword in text for keyword in sell):
        return "sell"
    elif any(keyword in text for keyword in buy):
        return "buy"
    else:
        return "unknown"


@app.post("/webhook")
def webhook():
    try:
        req = request.json
        message_type = req['type']

        if message_type != 'message':
            return {'success': True, 'message': 'received'}

        group_name = req['conversation_name']

        text = req['message'].get("text")
        conversation = req['conversation']


        if text:  # Check if text is not None
            type = identify_order_type(text)
            order_detail = text

            unknown_text = "Please resend the order details with the transaction type e.g(w.t.b)"
            if type == "unknown" and text != unknown_text:
                sendmessage(req, unknown_text)
                return {'success': False}

            # Insert into database
            if insert_sale(type, order_detail):
                print(f"Stored order - Type: {type}, Detail: {order_detail}")
            else:
                print("Failed to store order in database")

        return {'success': True, 'message': 'received and stored'}

    except Exception as e:
        print("Something went wrong ", e)
        return {'success': False, 'message': f'Error: {str(e)}'}


# Database initialization function
conn = get_connection()

def init_database():
    if conn:
        try:
            with conn.cursor() as cursor:
                # Create sales table if it doesn't exist
                create_table_sql = """
                CREATE TABLE IF NOT EXISTS sales (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    type VARCHAR(50) NOT NULL,
                    detail VARCHAR(255) NOT NULL,
                    timestamp DATETIME,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
                cursor.execute(create_table_sql)
                conn.commit()
                print("Database initialized successfully!")
        except pymysql.Error as e:
            print(f"Error initializing database: {e}")
        finally:
            conn.close()




def log_all_sales():
    if conn:
        try:
            with conn.cursor() as cursor:
                # SQL statement to retrieve all records from the sales table
                select_sql = "SELECT * FROM sales"
                cursor.execute(select_sql)

                # Fetch all records
                sales_records = cursor.fetchall()

                # Log each sale
                for record in sales_records:
                    print(
                        f"ID: {record[0]}, Type: {record[1]}, Detail: {record[2]}, Timestamp: {record[3]}, Created At: {record[4]}")

        except pymysql.Error as e:
            print(f"Error fetching sales data: {e}")




if __name__ == '__main__':
    # Initialize database before starting the Flask app
    init_database()
    updatewebhook()
    # Example usage
    app.run()
