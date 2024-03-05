from typing import Optional
from datetime import timedelta, datetime

import jwt
from jwt import PyJWTError
from jwt.types import JWKDict

from app.config import Config
from app.utils.models import Token


def create_access_token(data: dict, expire_delta: Optional[timedelta] = None) -> JWKDict:
    to_encode = data.copy()

    if expire_delta:
        expire = datetime.utcnow() + expire_delta
    else:
        expire = datetime.utcnow() + timedelta(days=Config.ACCESS_TOKEN_EXPIRES_DAYS,
                                               hours=Config.ACCESS_TOKEN_EXPIRES_HOURS,
                                               minutes=Config.ACCESS_TOKEN_EXPIRES_MINUTES)

    to_encode.update({"exp": expire})
    encode_jwt = jwt.encode(payload=to_encode, key=Config.RANDOM_SECRET, algorithm=Config.ALGORITHM)

    return encode_jwt


def decode_access_token(token: Token) -> dict:
    try:
        payload = jwt.decode(jwt=token, key=Config.RANDOM_SECRET, algorithms=[Config.ALGORITHM])

        return payload
    except PyJWTError:
        return None
