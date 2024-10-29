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

base_url = "https://api.maytapi.com"

phone_id = ""


url = f"{base_url}/api/{product_id}/listPhones"

headers = {'Content-Type': 'application/json', 'x-maytapi-key': product_token}

response = requests.get(url, headers=headers).json()
print(response)