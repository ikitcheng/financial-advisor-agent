import os
import time
from typing import Dict, Any, List
from pymongo import MongoClient
from dotenv import load_dotenv
dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(dotenv_path)
# We import MongoClient from pymongo, which is the standard Python MongoDB driver.
# NOTE: This requires 'pymongo' to be installed in the environment (e.g., pip install pymongo).

class MongoDBClient:
    """
    Client to interact with MongoDB for chat and data storage.
    Configuration details (URL, DB, Collections) are expected to be set 
    as environment variables (simulating reading from a .env file).
    
    If MongoDB connection fails, it automatically falls back to in-memory mock storage.
    """
    def __init__(self):
        # 1. Fetch config from environment (simulating .env file loading)
        MONGO_URL = os.environ.get("MONGO_URL", "mongodb://localhost:27017/")
        MONGO_DB_NAME = os.environ.get("MONGO_DB_NAME", "credit_card_analysis_db")
        self.CHAT_COLLECTION = os.environ.get("CHAT_COLLECTION", "chat_history")
        self.EXTRACTION_COLLECTION = os.environ.get("EXTRACTION_COLLECTION", "extraction_results")
        
        self.client = None
        self.db = None
        
        # 2. Attempt to establish connection
        try:
            self.client = MongoClient(MONGO_URL, serverSelectionTimeoutMS=3000) # Short timeout for startup check
            self.client.admin.command('ping') # Check connection immediately
            self.db = self.client[MONGO_DB_NAME]
            print(f"MongoDB Client connected successfully to DB: {MONGO_DB_NAME}")
            
            # Reset mock storage if connection is successful (no fallback needed)
            self.chats = None 
            self.extraction_results = None
            
        except Exception as e:
            # Fallback to in-memory dictionaries if connection fails or pymongo is missing
            print(f"ERROR: Could not connect to MongoDB at {MONGO_URL}. Using in-memory mock storage. Error: {type(e).__name__}: {e}")
            
            # Initialize in-memory mock storage
            self.chats = {} 
            self.extraction_results = {} 

    def save_chat_history(self, session_id: str, message: Dict[str, str]) -> bool:
        """Saves a new message (user or assistant) to the chat history collection."""
        
        # Add session and timestamp before saving
        message['session_id'] = session_id
        message['timestamp'] = time.time()
        
        if self.db is not None: # Real MongoDB connection is active
            try:
                collection = self.db[self.CHAT_COLLECTION]
                result = collection.insert_one(message)
                print(f"DB Log: [{session_id}] Chat message saved to MongoDB. ID: {result.inserted_id}")
                return True
            except Exception as e:
                print(f"DB Error: Failed to save chat to MongoDB. {e}")
                return False
        else: # Fallback to in-memory mock storage
            if session_id not in self.chats:
                self.chats[session_id] = []
            self.chats[session_id].append(message)
            print(f"DB Log: [{session_id}] Chat message saved to MOCK storage. Role: {message['role']}")
            return True

    def save_document_extraction(self, session_id: str, file_name: str, extraction_data: Dict[str, Any]) -> bool:
        """Saves the document extraction results to the extraction collection."""
        
        document = {
            'session_id': session_id,
            'file_name': file_name,
            'timestamp': time.time(),
            **extraction_data
        }
        
        if self.db is not None: # Real MongoDB connection is active
            try:
                collection = self.db[self.EXTRACTION_COLLECTION]
                result = collection.insert_one(document)
                print(f"DB Log: [{session_id}] Extraction data saved to MongoDB. ID: {result.inserted_id}")
                return True
            except Exception as e:
                print(f"DB Error: Failed to save extraction data to MongoDB. {e}")
                return False
        else: # Fallback to in-memory mock storage
            if session_id not in self.extraction_results:
                self.extraction_results[session_id] = []
            self.extraction_results[session_id].append(document)
            print(f"DB Log: [{session_id}] Extraction data saved to MOCK storage for {file_name}.")
            return True

# Export a singleton instance to be used by the API layer
db_client = MongoDBClient()