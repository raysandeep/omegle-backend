from motor.motor_asyncio import AsyncIOMotorClient
import logging
# import import_env_file
import os
from pymongo.errors import AutoReconnect
from config_params import( 
    MONGODB_URL,
    MIN_POOL_SIZE,
    MAX_POOL_SIZE
    )

class MonogDB:
    client: AsyncIOMotorClient = True


db = MonogDB()

async def get_nosql_db() -> AsyncIOMotorClient:
    print("3")
    return db.client


async def get_mongo_connection():
    db.client = AsyncIOMotorClient(
        str(MONGODB_URL), 
        maxPoolSize=int(MAX_POOL_SIZE),
        minPoolSize=int(MIN_POOL_SIZE),
    )
    logging.info("Connected to Mongo Client")


async def close_mongo_connection():
    db.client.close()
    logging.info("Closed Mongo Client")
