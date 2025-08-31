# auth.py
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from database import get_db
from models import User
import schemas
from fastapi.security import APIKeyHeader

#from utils import hash_password, verify_password

SECRET_KEY = "supersecretkey"  # ⚠️ env variable me store karna best practice hai
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")
api_key_scheme = APIKeyHeader(name="Authorization")


def hash_password(password: str):
     return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str):
     return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def create_refresh_token(data: dict, expires_delta: timedelta | None = None):
    expire = datetime.utcnow() + (expires_delta or timedelta(days=7))  # 7 din valid
    to_encode = data.copy()
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


async def get_current_user(token: str = Depends(api_key_scheme), db: AsyncSession = Depends(get_db)):
    if not token.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid token")
    token_value = token[7:]  # Remove 'Bearer ' prefix
    try:
        payload = jwt.decode(token_value, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Could not validate credentials")
    except JWTError:
        raise HTTPException(status_code=401, detail="Could not validate credentials")
    
    result = await db.execute(select(User).where(User.username == username))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    return user


async def get_current_user_from_token(token: str, db: AsyncSession = None) -> User:
    """
    Decode JWT token and return the User object from DB.

    Parameters:
        token (str): JWT token
        db (AsyncSession, optional): Database session. If not provided, a new session is created.

    Returns:
        User: Current logged-in user object.

    Raises:
        HTTPException: If token is invalid or user not found.
    """
    if not db:
        # Create temporary session if none provided
        from database import async_session
        async with async_session() as db:
            return await _get_user(token, db)
    else:
        return await _get_user(token, db)


async def _get_user(token: str, db: AsyncSession) -> User:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    
    result = await db.execute(select(User).where(User.username == username))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user