from pydantic import BaseModel, Field, validator
from datetime import datetime
from uuid import UUID,uuid4
from typing import List,Optional
from mongodb import get_nosql_db
import import_env_file
from os import getenv


class User(BaseModel):
    username : str
    password : str
    salt : str


class UserInDB(User):
    _id : UUID = Field(default_factory=uuid4)
    date_created : datetime= Field(default_factory=datetime.utcnow)


def get_user(username):
    client = get_nosql_db()
    db = client[getenv("MONGODB_NAME")]
    collection = db["user"]
    row = collection.find_one({'username':username})
    if row is not None:
        return row
    else:
        return False