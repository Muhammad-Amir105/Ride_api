from pydantic import BaseModel,EmailStr,StringConstraints, validator
import re
from typing import Optional,Annotated
from enum import Enum


class RideStatus(str, Enum):
    pending = "pending"
    accepted = "accepted"
    completed = "completed"


class UserRole(str, Enum):
    rider = "rider"
    driver = "driver"


class RideCreate(BaseModel):
    pickup_location: str
    dropoff_location: str
    price: Optional[float] = None



class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: Annotated[str, StringConstraints(min_length=8)]
    role: UserRole

    @validator("password")
    def validate_password(cls, v):
        if not re.search(r"[A-Za-z]", v):
            raise ValueError("Password must contain at least one letter")
        if not re.search(r"\d", v):
            raise ValueError("Password must contain at least one number")
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", v):
            raise ValueError("Password must contain at least one special character")
        return v
    

class UserLogin(BaseModel):
    username: str
    password: str  # No validator needed
    


class UserOut(BaseModel):
    id: int
    username: str
    email: EmailStr
    role: UserRole

    class Config:
        orm_mode = True


class RideResponse(RideCreate):
    id: int
    rider_name: str
    driver_id: Optional[int] = None
    status: RideStatus

    class Config:
        from_attributes = True


class UserResponse(BaseModel):
    id: int
    username: str
    role: UserRole
    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str