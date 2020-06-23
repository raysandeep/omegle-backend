from motor.motor_asyncio import AsyncIOMotorClient
import logging
import import_env_file
import os

class MonogDB:
    client: AsyncIOMotorClient = True


db = MonogDB()

async def get_nosql_db() -> AsyncIOMotorClient:
    return db.client


async def get_mongo_connection():
    db.client = AsyncIOMotorClient(
        str(os.getenv("MONGODB_URL")), 
        maxPoolSize=int(os.getenv("MAX_POOL_SIZE")),
        minPoolSize=int(os.getenv("MIN_POOL_SIZE")),
    )
    logging.info("Connected to Mongo Client")


async def close_mongo_connection():
    db.client.close()
    logging.info("Closed Mongo Client")
