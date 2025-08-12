# File: db/mysql_connector.py
import os
import mysql.connector
from dotenv import load_dotenv

load_dotenv()

def get_mysql_connection():
    try:
        connection = mysql.connector.connect(
            host=os.getenv("DB_HOST"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            database=os.getenv("DB_NAME")
        )
        return connection
    except mysql.connector.Error as err:
        print(f"[DB ERROR] Could not connect to MySQL: {err}")
        return None
