from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException
from models import Ride, RideStatus, User
from auth import hash_password, verify_password, create_access_token, create_refresh_token
import schemas


# ✅ Create a new ride
async def create_ride(db: AsyncSession, ride_data: schemas.RideCreate, rider: User):
    """
    Creates a new ride in the database.
    
    Parameters:
        db (AsyncSession): The database session.
        ride_data (RideCreate): The ride details (pickup, dropoff, price).
        rider (User): The currently logged-in user creating the ride.
    
    Returns:
        Ride: The newly created ride object.
    """
    new_ride = Ride(
        rider_name=rider.username,  # Automatically assign the rider's username
        driver_id=None,             # No driver assigned initially
        pickup_location=ride_data.pickup_location,
        dropoff_location=ride_data.dropoff_location,
        price=ride_data.price,
        status=RideStatus.pending,  # New rides start as pending
    )
    db.add(new_ride)
    await db.commit()       # Save to DB
    await db.refresh(new_ride)  # Refresh object with DB-generated fields (like ID)
    return new_ride


# ✅ Register a new user
async def create_user(db: AsyncSession, user_data: schemas.UserCreate):
    """
    Creates a new user in the database with hashed password.
    
    Parameters:
        db (AsyncSession): The database session.
        user_data (UserCreate): User registration info.
    
    Returns:
        User: The newly created user object.
    """
    hashed_pw = hash_password(user_data.password)  # Securely hash password
    user = User(
        username=user_data.username,
        email=user_data.email,
        password=hashed_pw,
        role=user_data.role  # 'rider' or 'driver'
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


# ✅ Login user and return JWT tokens
async def login_user(db: AsyncSession, user_data: schemas.UserLogin):
    """
    Authenticates a user and returns access and refresh tokens.
    
    Parameters:
        db (AsyncSession): The database session.
        user_data (UserLogin): Username and password for login.
    
    Returns:
        dict: Dictionary containing access_token, refresh_token, and token_type.
    """
    result = await db.execute(select(User).where(User.username == user_data.username))
    print('username',User.username)
    print(user_data.username)
    db_user = result.scalar_one_or_none()

    # Validate password
    if not db_user or not verify_password(user_data.password, db_user.password):
        print(User.password)
        print(user_data.password)
        print(db_user.password)
        raise HTTPException(status_code=401, detail="Invalid credentials")

    access_token = create_access_token(data={"sub": db_user.username})
    refresh_token = create_refresh_token(data={"sub": db_user.username})

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }


# ✅ Get all pending rides
async def get_available_rides(db: AsyncSession):
    """
    Returns all rides with status 'pending' (available for drivers to accept).
    
    Parameters:
        db (AsyncSession): The database session.
    
    Returns:
        list[Ride]: List of pending ride objects.
    """
    result = await db.execute(select(Ride).where(Ride.status == RideStatus.pending))
    return result.scalars().all()


# ✅ Get a user by username
async def get_user_by_username(db: AsyncSession, username: str):
    """
    Fetch a user by username.
    
    Parameters:
        db (AsyncSession): The database session.
        username (str): Username to search for.
    
    Returns:
        User | None: User object if found, else None.
    """
    result = await db.execute(select(User).where(User.username == username))
    return result.scalar_one_or_none()


# ✅ Update ride status (accept, complete, cancel)
async def update_ride_status(db: AsyncSession, ride_id: int, status: str, current_user: User):
    """
    Update the status of a ride based on the action and user role.
    
    Parameters:
        db (AsyncSession): The database session.
        ride_id (int): ID of the ride to update.
        status (str): New status: 'accepted', 'complete', or 'cancelled'.
        current_user (User): The currently logged-in user performing the action.
    
    Returns:
        Ride | dict: Updated ride object, or a confirmation dict if cancelled.
    
    Raises:
        HTTPException: If the ride does not exist, or user is unauthorized, or invalid action.
    """
    result = await db.execute(select(Ride).where(Ride.id == ride_id))
    ride = result.scalar_one_or_none()
    if not ride:
        raise HTTPException(status_code=404, detail="Ride not found")

    # DRIVER ACCEPT RIDE
    if status == "accepted":
        if current_user.role != "driver":
            raise HTTPException(status_code=403, detail="Only drivers can accept rides")
        if ride.status in [RideStatus.cancelled, RideStatus.completed]:
            raise HTTPException(status_code=400, detail=f"Cannot accept a ride that is {ride.status}")
        if ride.status != RideStatus.pending:
            raise HTTPException(status_code=400, detail="Ride already accepted")
        ride.driver_id = current_user.id
        ride.status = RideStatus.accepted

    # DRIVER COMPLETE RIDE
    elif status == "complete":
        if current_user.role != "driver":
            raise HTTPException(status_code=403, detail="Only drivers can complete rides")
        if ride.driver_id != current_user.id:
            raise HTTPException(status_code=403, detail="Only the assigned driver can complete this ride")
        if ride.status == RideStatus.cancelled:
            raise HTTPException(status_code=400, detail="Ride has been cancelled")
        if ride.status == RideStatus.completed:
            raise HTTPException(status_code=400, detail="Ride is already completed")
        if ride.status != RideStatus.accepted:
            raise HTTPException(status_code=400, detail="Ride must be accepted before completing")
        ride.status = RideStatus.completed

    # CANCEL RIDE (driver or rider)
    elif status == "cancelled":
        if ride.status == RideStatus.completed:
            raise HTTPException(status_code=400, detail="Ride is already completed, cannot cancel")
        if current_user.id != ride.driver_id and current_user.username != ride.rider_name:
            raise HTTPException(status_code=403, detail="You are not authorized to cancel this ride")
        ride.status = RideStatus.cancelled

    # INVALID STATUS
    else:
        raise HTTPException(status_code=400, detail="Invalid action")

    # Save changes
    db.add(ride)
    await db.commit()
    await db.refresh(ride)

    # If cancelled, return a simple confirmation message
    return {"detail": f"Ride with ID {ride_id} updated to {ride.status}"} if status == "cancelled" else ride
