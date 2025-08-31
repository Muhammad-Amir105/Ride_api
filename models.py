from sqlalchemy import Column, Integer, String, Enum, Float,UniqueConstraint
from sqlalchemy.orm import declarative_base
import enum

Base = declarative_base()


class RideStatus(str, enum.Enum):
    pending = "pending"
    accepted = "accepted"
    completed = "completed"
    cancelled = "cancelled"


class Ride(Base):
    __tablename__ = "rides"

    id = Column(Integer, primary_key=True, index=True)
    rider_name = Column(String, nullable=False)
    driver_id = Column(Integer, nullable=True)
    pickup_location = Column(String, nullable=False)
    dropoff_location = Column(String, nullable=False)
    price = Column(Float, nullable=True)
    status = Column(Enum(RideStatus, name="ride_status"), default=RideStatus.pending)


class UserRole(str, enum.Enum):
    rider = "rider"
    driver = "driver"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password = Column(String, nullable=False)  # hashed password
    role = Column(Enum(UserRole), nullable=False)

__table_args__ = (UniqueConstraint("username", "email", name="uq_user_username_email"),)