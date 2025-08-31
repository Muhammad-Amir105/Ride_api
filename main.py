from fastapi import FastAPI, Depends, Query, Request,HTTPException, WebSocketDisconnect, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from database import engine, Base, get_db, get_db_session
import schemas, crud, models
from auth import get_current_user, get_current_user_from_token
from models import User
import traceback
from fastapi import WebSocket
from websocket_manager import manager



app = FastAPI(title="Ride Matching API")


# ✅ Global Exception Handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"detail": str(exc), "trace": traceback.format_exc()},
    )


# ✅ Create tables on startup
@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


# ✅ Register
@app.post("/auth/register", response_model=schemas.UserOut)
async def register(user: schemas.UserCreate, db: AsyncSession = Depends(get_db)):
    existing = await db.execute(
        models.User.__table__.select().where(
            (models.User.username == user.username) | (models.User.email == user.email)
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Username or Email already registered")
    return await crud.create_user(db, user)


# ✅ Login
@app.post("/auth/login", response_model=schemas.Token)
async def login(user: schemas.UserLogin, db: AsyncSession = Depends(get_db)):
    return await crud.login_user(db, user)


# ✅ Create Ride (riders only)
@app.post("/rides/", response_model=schemas.RideResponse)
async def create_ride(
    ride: schemas.RideCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role != "rider":
        raise HTTPException(status_code=403, detail="Only riders can create rides")
    
    # 1️⃣ Create ride in DB
    new_ride = await crud.create_ride(db, ride, current_user)
    
    # 2️⃣ Broadcast notification to all connected clients
    await manager.broadcast({
        "event": "new_ride",
        "ride_id": new_ride.id,
        "pickup": new_ride.pickup_location,
        "dropoff": new_ride.dropoff_location,
        "price": new_ride.price,
        "rider": new_ride.rider_name
    }, role='driver')
    
    return new_ride
    # return await crud.create_ride(db, ride, current_user)


# ✅ Get all available rides
@app.get("/rides/available/", response_model=list[schemas.RideResponse])
async def get_available_rides(db: AsyncSession = Depends(get_db)):
    return await crud.get_available_rides(db)


# ✅ Update ride status (accept, complete, cancel)
@app.post("/rides/{ride_id}/status/", response_model=schemas.RideResponse | dict)
async def ride_status(
    ride_id: int,
    status: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return await crud.update_ride_status(db, ride_id, status, current_user)


@app.websocket("/ws/notifications")
async def websocket_endpoint(websocket: WebSocket, token: str):
    async with get_db_session() as db:
        current_user = await get_current_user_from_token(token, db)

    print(f"{current_user.username} connected with role {current_user.role}")

    await manager.connect(websocket, role=current_user.role)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)


