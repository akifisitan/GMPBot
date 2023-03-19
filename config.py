import os
from dotenv import load_dotenv
from pymongo import MongoClient

# Load environment variables
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
SERVER_IDS = [int(server_id) for server_id in os.getenv("SERVER_IDS").split(",")]
DATABASE_URI = os.getenv("MONGODB_URI")
CLIENT = MongoClient(DATABASE_URI)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Test if the connection to the database was successful, exit the script if not
try:
    CLIENT.server_info()
    print("Connected to MongoDB")
    # Get the database
    DATABASE = CLIENT["development"]
    participants = DATABASE["participants"]
    CHECK = True
except Exception as e:
    print(f"Error connecting to MongoDB: {e}")
    CHECK = False
