
import os
import time
from pymongo import MongoClient, ASCENDING
from pymongo.errors import DuplicateKeyError
from pymongo.errors import OperationFailure
from dotenv import load_dotenv
load_dotenv()

# MongoDB connection details
def connect_to_mongo():
    mongo_url = os.getenv("mongo_url")
    database_name = os.getenv("MONGODBNAME")
    return MongoClient(mongo_url)[database_name]['frate_users']

def insert_new_key(key,secret,ts):
    key_collection = connect_to_mongo()
    existing_record = key_collection.find_one({'key': key})
    if existing_record:
        print(f"key {key} already exists. Aborting insertion.")
        return
    
    # spot records
    sk_dict = {
        'key': key,
        'secret':secret,
        'createAt':ts,
    }

    # Insert the user into the MongoDB collection
    key_collection.insert_one(sk_dict)
    print(f"apikey {key} inserted successfully.")
