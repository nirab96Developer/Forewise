# app/routers/websocket.py
"""WebSocket endpoints for real-time notifications."""
import json
import logging
from typing import Dict, List
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException, status
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.models.user import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ws", tags=["WebSocket"])

# Active connections storage
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[int, WebSocket] = {}
        self.user_connections: Dict[int, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, user_id: int):
        await websocket.accept()
        self.active_connections[id(websocket)] = websocket
        if user_id not in self.user_connections:
            self.user_connections[user_id] = []
        self.user_connections[user_id].append(websocket)
        logger.info(f"User {user_id} connected to WebSocket")

    def disconnect(self, websocket: WebSocket, user_id: int):
        if id(websocket) in self.active_connections:
            del self.active_connections[id(websocket)]
        if user_id in self.user_connections:
            if websocket in self.user_connections[user_id]:
                self.user_connections[user_id].remove(websocket)
            if not self.user_connections[user_id]:
                del self.user_connections[user_id]
        logger.info(f"User {user_id} disconnected from WebSocket")

    async def send_personal_message(self, message: str, websocket: WebSocket):
        try:
            await websocket.send_text(message)
        except Exception as e:
            logger.error(f"Error sending message: {e}")

    async def send_to_user(self, user_id: int, message: dict):
        if user_id in self.user_connections:
            message_str = json.dumps(message, ensure_ascii=False)
            for websocket in self.user_connections[user_id]:
                try:
                    await websocket.send_text(message_str)
                except Exception as e:
                    logger.error(f"Error sending to user {user_id}: {e}")

    async def broadcast(self, message: dict):
        message_str = json.dumps(message, ensure_ascii=False)
        for websocket in self.active_connections.values():
            try:
                await websocket.send_text(message_str)
            except Exception as e:
                logger.error(f"Error broadcasting message: {e}")

manager = ConnectionManager()

async def authenticate_websocket(websocket: WebSocket, token: str = None) -> User:
    """Authenticate WebSocket connection using Bearer token."""
    if not token:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Missing authentication token")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing authentication token")
    
    try:
        # Remove 'Bearer ' prefix if present
        if token.startswith('Bearer '):
            token = token[7:]
        
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        user_id: int = int(payload.get("sub"))
        
        if user_id is None:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Invalid token")
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
            
    except (JWTError, ValueError) as e:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Invalid token")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    
    # Get user from database
    db = next(get_db())
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user or not user.is_active:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="User not found or inactive")
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or inactive")
        return user
    finally:
        db.close()

@router.websocket("/notifications")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time notifications."""
    try:
        # Get token from query parameters or headers
        token = websocket.query_params.get("token")
        if not token:
            # Try to get from headers
            headers = dict(websocket.headers)
            auth_header = headers.get("authorization") or headers.get("Authorization")
            if auth_header and auth_header.startswith("Bearer "):
                token = auth_header[7:]
        
        # Authenticate user
        user = await authenticate_websocket(websocket, token)
        
        # Connect user
        await manager.connect(websocket, user.id)
        
        # Send welcome message
        await manager.send_personal_message(
            json.dumps({
                "type": "system:ping",
                "message": "Connected successfully",
                "user_id": user.id,
                "timestamp": str(datetime.now())
            }, ensure_ascii=False),
            websocket
        )
        
        # Keep connection alive and handle messages
        while True:
            try:
                data = await websocket.receive_text()
                message = json.loads(data)
                
                # Handle different message types
                if message.get("type") == "ping":
                    await manager.send_personal_message(
                        json.dumps({
                            "type": "pong",
                            "timestamp": str(datetime.now())
                        }, ensure_ascii=False),
                        websocket
                    )
                elif message.get("type") == "subscribe":
                    # Handle subscription to specific channels
                    channel = message.get("channel")
                    if channel:
                        await manager.send_personal_message(
                            json.dumps({
                                "type": "subscribed",
                                "channel": channel,
                                "timestamp": str(datetime.now())
                            }, ensure_ascii=False),
                            websocket
                        )
                        
            except WebSocketDisconnect:
                manager.disconnect(websocket, user.id)
                break
            except json.JSONDecodeError:
                await manager.send_personal_message(
                    json.dumps({
                        "type": "error",
                        "message": "Invalid JSON format"
                    }, ensure_ascii=False),
                    websocket
                )
            except Exception as e:
                logger.error(f"WebSocket error: {e}")
                await manager.send_personal_message(
                    json.dumps({
                        "type": "error",
                        "message": "Internal server error"
                    }, ensure_ascii=False),
                    websocket
                )
                
    except HTTPException:
        # Already handled in authenticate_websocket
        pass
    except Exception as e:
        logger.error(f"WebSocket connection error: {e}")
        try:
            await websocket.close(code=status.WS_1011_INTERNAL_ERROR, reason="Internal server error")
        except:
            pass

# Helper functions for sending notifications
async def send_notification_to_user(user_id: int, notification: dict):
    """Send notification to specific user."""
    await manager.send_to_user(user_id, {
        "type": "notification",
        "data": notification,
        "timestamp": str(datetime.now())
    })

async def broadcast_notification(notification: dict):
    """Broadcast notification to all connected users."""
    await manager.broadcast({
        "type": "notification",
        "data": notification,
        "timestamp": str(datetime.now())
    })

# Import datetime for timestamps
from datetime import datetime
