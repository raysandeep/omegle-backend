FROM tiangolo/uvicorn-gunicorn-fastapi:python3.7

COPY requirements.txt /tmp/

RUN pip install --requirement /tmp/requirements.txt

COPY . /tmp/

# ENV MONGODB_NAME = omegle
# ENV MONGODB_URL=mongodb://localhost:27017/
# ENV MAX_POOL_SIZE=10
# ENV MIN_POOL_SIZE=1
# ENV JWT_TOKEN_PREFIX = TOKEN
# ENV SECRET_KEY = ZHBCJHCJEDSJNKFDJDNKDJNKLD
# ENV ACCESS_TOKEN_EXPIRY = 60
# ENV ALGORITHM = HS512

COPY ./app /app