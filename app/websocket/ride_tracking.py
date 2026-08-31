import socketio
import redis
import json
from typing import Dict

from app.core.config import settings

sio = socketio.AsyncServer(async_mode='asgi', cors_allowed_origins='*')
redis_client = redis.from_url(settings.REDIS_URL)

active_connections: Dict[str, str] = {}


@sio.event
async def connect(sid, environ):
    """Handle client connection"""
    print(f"Client connected: {sid}")
    await sio.emit('connection_established', {'sid': sid}, room=sid)


@sio.event
async def disconnect(sid):
    """Handle client disconnection"""
    print(f"Client disconnected: {sid}")
    if sid in active_connections:
        ride_id = active_connections[sid]
        del active_connections[sid]


@sio.event
async def join_ride(sid, data):
    """Join a ride room for real-time updates"""
    ride_id = data.get('ride_id')
    user_type = data.get('user_type')
    
    if not ride_id:
        await sio.emit('error', {'message': 'ride_id is required'}, room=sid)
        return
    
    await sio.enter_room(sid, ride_id)
    active_connections[sid] = ride_id
    
    print(f"{user_type} {sid} joined ride {ride_id}")
    await sio.emit('joined_ride', {
        'ride_id': ride_id,
        'user_type': user_type
    }, room=sid)


@sio.event
async def leave_ride(sid, data):
    """Leave a ride room"""
    ride_id = data.get('ride_id')
    
    if ride_id:
        await sio.leave_room(sid, ride_id)
        if sid in active_connections:
            del active_connections[sid]
        
        await sio.emit('left_ride', {'ride_id': ride_id}, room=sid)


@sio.event
async def driver_location_update(sid, data):
    """Driver sends location update"""
    ride_id = data.get('ride_id')
    latitude = data.get('latitude')
    longitude = data.get('longitude')
    
    if not all([ride_id, latitude, longitude]):
        await sio.emit('error', {'message': 'Invalid location data'}, room=sid)
        return
    
    location_data = {
        'ride_id': ride_id,
        'latitude': latitude,
        'longitude': longitude,
        'timestamp': data.get('timestamp')
    }
    
    redis_key = f"ride_location:{ride_id}"
    redis_client.setex(redis_key, 300, json.dumps(location_data))
    
    await sio.emit('customer_location_receive', location_data, room=ride_id, skip_sid=sid)


@sio.event
async def ride_status_change(sid, data):
    """Broadcast ride status change"""
    ride_id = data.get('ride_id')
    status = data.get('status')
    message = data.get('message', '')
    
    if not all([ride_id, status]):
        await sio.emit('error', {'message': 'Invalid status data'}, room=sid)
        return
    
    await sio.emit('ride_status_update', {
        'ride_id': ride_id,
        'status': status,
        'message': message
    }, room=ride_id)


def get_socket_app():
    """Get the Socket.IO ASGI app"""
    return socketio.ASGIApp(sio)
