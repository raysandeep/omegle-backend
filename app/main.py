from fastapi import FastAPI, Request, Depends,Response, HTTPException, status
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
    get_current_active_user,
    insert_room
)
from models import(
    UserInDB,
    User
)

from pymongo.errors import (
    DuplicateKeyError,
    CollectionInvalid,
    AutoReconnect
    )
from datetime import datetime, timedelta
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from notifier import Notifier
from starlette.websockets import WebSocketDisconnect,WebSocket
app = FastAPI(debug=True)

notifier = Notifier()


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
    print("1")
    await notifier.generator.asend(None)
    print("2")

    try:
        client = await get_nosql_db()
        print("4")
        db = client[getenv("MONGODB_NAME")]
        print("5")
        collection = db["user"]
        # print(collection)
        await collection.create_index("username",name="username",unique=True)
        print("7")
        await db.create_collection("room")
        
    except AutoReconnect as e:
        logging.error(e)
        pass

    except CollectionInvalid as e:
        logging.error(e)
        pass
    



@app.on_event("shutdown")
async def startup_event():
    await close_mongo_connection()


@app.get("/")
async def get():
    return HTMLResponse(html)


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await notifier.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            await notifier.push(f"Message text was: {data}")
    except WebSocketDisconnect:
        notifier.remove(websocket)


@app.get("/push/{message}")
async def push_to_connected_websockets(message: str):
    await notifier.push(f"! Push notification: {message} !")




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



@app.post("/room/create")
async def read_users_me(current_user:User=Depends(get_current_active_user),client:AsyncIOMotorClient=Depends(get_nosql_db)):
    return await insert_room(current_user,client)




