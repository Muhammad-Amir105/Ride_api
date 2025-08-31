# utils.py
import asyncio

async def notify_rider(rider_id: int, ride_id: int):
    await asyncio.sleep(1)  # simulate delay
    print(f"📢 Rider {rider_id} notified about Ride {ride_id}")
