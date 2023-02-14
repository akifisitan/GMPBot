import os
from dotenv import load_dotenv
from pymongo import MongoClient

# Load environment variables
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
DATABASE_URI = os.getenv("MONGODB_URI")
CLIENT = MongoClient(DATABASE_URI)

# Test if the connection to the database was successful, exit the script if not
try:
    CLIENT.server_info()
    print("Connected to MongoDB")
    # Get the database
    DATABASE = CLIENT["development"]
    print(f"Collection names are: {DATABASE.list_collection_names()}")
    CHECK = True
except Exception as e:
    print(f"Error connecting to MongoDB: {e}")
    CHECK = False
