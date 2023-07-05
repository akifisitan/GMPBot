import os
from dotenv import load_dotenv
from psycopg2 import connect as postgres_connect

# Load environment variables
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
db_connection = postgres_connect(os.getenv("POSTGRES_URI"))
db_connection.autocommit = True
database_cursor = db_connection.cursor()
