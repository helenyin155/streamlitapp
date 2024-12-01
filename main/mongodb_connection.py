import os
from dotenv import load_dotenv
from pymongo import MongoClient
import streamlit as st

# Load environment variables
load_dotenv()

def get_database_connection():
    """Establish connection to MongoDB with secure credentials."""
    try:
        username = os.getenv('MONGO_USERNAME')
        password = os.getenv('MONGO_PASSWORD')
        cluster = os.getenv('MONGO_CLUSTER')
        
        if not all([username, password, cluster]):
            raise ValueError("Missing required MongoDB credentials")
            
        uri = f"mongodb+srv://{username}:{password}@{cluster}/?retryWrites=true&w=majority&appName=Cluster0"
        
        client = MongoClient(
            uri,
            serverSelectionTimeoutMS=5000,
            connectTimeoutMS=10000,
            socketTimeoutMS=10000
        )
        
        # Test the connection
        client.server_info()
        return client
    except Exception as e:
        st.error(f"Database connection error: {str(e)}")
        return None