# Ride Matching API

A **FastAPI** based application for ride matching between riders and drivers, with authentication, ride creation, and real-time notifications using WebSockets.

---

## Features

- User registration and login with **JWT authentication**.
- Role-based access: **Rider** and **Driver**.
- Riders can create rides with pickup, dropoff, and price.
- Drivers can view pending rides and accept or complete them.
- Both riders and drivers can cancel rides.
- **WebSocket notifications** for real-time ride updates.
- Async database operations with **SQLAlchemy** and **PostgreSQL**.

---

## Tech Stack

- Python 3.11+
- FastAPI
- SQLAlchemy (Async)
- PostgreSQL
- Asyncpg
- Passlib (for password hashing)
- JWT Authentication
- WebSockets
- Uvicorn (ASGI server)

---

## Install requirement
- pip install -r requirements.txt