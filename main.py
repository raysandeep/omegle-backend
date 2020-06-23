from fastapi import FastAPI, WebSocket, Request, Depends,Response, HTTPException, status
from fastapi.responses import HTMLResponse,JSONResponse
from mongodb import get_mongo_connection,get_nosql_db,close_mongo_connection,AsyncIOMotorClient
import import_env_file
import logging
from os import getenv
from pydantic import BaseModel
from controller import(
    create_user,
    authenticate_user,
    create_access_token,
    get_current_active_user
)
from models import(
    UserInDB,
    User
)
app = FastAPI()
from pymongo.errors import (
    DuplicateKeyError,
    CollectionInvalid
    )
from datetime import datetime, timedelta
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm




html = """
<!DOCTYPE html>
<html>
    <head>
        <title>Chat</title>
    </head>
    <body>
        <h1>WebSocket Chat</h1>
        <form action="" onsubmit="sendMessage(event)">
            <input type="text" id="messageText" autocomplete="off"/>
            <button>Send</button>
        </form>
        <ul id='messages'>
        </ul>
        <script>
            var ws = new WebSocket("ws://localhost:8000/ws");
            ws.onmessage = function(event) {
                var messages = document.getElementById('messages')
                var message = document.createElement('li')
                var content = document.createTextNode(event.data)
                message.appendChild(content)
                messages.appendChild(message)
            };
            function sendMessage(event) {
                var input = document.getElementById("messageText")
                ws.send(input.value)
                input.value = ''
                event.preventDefault()
            }
        </script>
    </body>
</html>
"""

@app.on_event("startup")
async def startup_event():
    await get_mongo_connection()
    try:
        client = await get_nosql_db()
        db = client[getenv("MONGODB_NAME")]
        collection = db["user"]
        await collection.create_index("username",name="username",unique=True)
        await db.create_collection("rooms")
        await db["rooms"].create_index("room_name",name="room_name",unique=True)
    except CollectionInvalid as e:
        logging.info(e)
        pass



@app.on_event("shutdown")
async def startup_event():
    await close_mongo_connection()


@app.get("/")
async def get():
    return HTMLResponse(html)


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    while True:
        data = await websocket.receive_text()
        await websocket.send_text(f"Message text was: {data}")




class RegisterRequest(BaseModel):
    username : str
    password : str

class LoginRequest(BaseModel):
    username : str
    password : str


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: str = None

@app.post('/register')
async def register_user(request:RegisterRequest,client:AsyncIOMotorClient=Depends(get_nosql_db)):
    try:
        collection = client[getenv("MONGODB_NAME")]["user"]
        user = create_user(request)
        dbuser = UserInDB(**user.dict())
        response  = await collection.insert_one(dbuser.dict())
        return {
            "user_id":str(response.inserted_id)
        }
    except DuplicateKeyError as e:
        print(e)
        return JSONResponse(status_code=400,content={
            "user_id":"user_alreay exists"
        })


@app.post("/token", response_model=Token)
async def login_for_access_token(request:LoginRequest):
    print("Reached Here")
    user = await authenticate_user(request.username, request.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=int(getenv("ACCESS_TOKEN_EXPIRY")))
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/users/me/", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    return current_user


@app.get("/users/me/items/")
async def read_own_items(current_user: User = Depends(get_current_active_user)):
    return [{"item_id": "Foo", "owner": current_user.username}]