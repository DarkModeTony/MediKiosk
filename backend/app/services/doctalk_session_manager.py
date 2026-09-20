import asyncio
import json
import logging
import uuid
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, Optional, Set
from fastapi import WebSocket, WebSocketDisconnect

logger = logging.getLogger("doctalk.session_manager")


class ActivePeer:
    def __init__(self, websocket: WebSocket, user_id: str, role: str, user_name: Optional[str] = None):
        self.websocket = websocket
        self.user_id = str(user_id)
        self.role = role  # "REQUESTING_DOCTOR" or "SPECIALIST"
        self.user_name = user_name or ("Requesting Doctor" if role == "REQUESTING_DOCTOR" else "Specialist")
        self.audio_enabled = True
        self.video_enabled = True
        self.connected_at = datetime.now(timezone.utc)


class ConsultationRoom:
    def __init__(self, consultation_id: str, duration_minutes: int, started_at: Optional[datetime] = None):
        self.consultation_id = str(consultation_id)
        self.duration_minutes = duration_minutes
        self.started_at = started_at
        self.peers: Dict[str, ActivePeer] = {}  # user_id -> ActivePeer
        self.is_ended = False

    def get_remaining_seconds(self) -> int:
        if not self.started_at:
            return self.duration_minutes * 60
        now = datetime.now(timezone.utc)
        # Ensure started_at is aware
        started = self.started_at
        if started.tzinfo is None:
            started = started.replace(tzinfo=timezone.utc)
        elapsed = (now - started).total_seconds()
        total = self.duration_minutes * 60
        remaining = int(total - elapsed)
        return max(0, remaining)


class DocTalkConnectionManager:
    """
    Manages active doctor-to-doctor consultation rooms and WebRTC signaling.
    Strictly isolated: only the two authorized doctors can communicate in a room.
    Zero media storage: audio/video is peer-to-peer WebRTC and never recorded on the server.
    """

    def __init__(self):
        # consultation_id -> ConsultationRoom
        self.rooms: Dict[str, ConsultationRoom] = {}
        self._lock = asyncio.Lock()

    async def get_or_create_room(
        self, consultation_id: str, duration_minutes: int, started_at: Optional[datetime] = None
    ) -> ConsultationRoom:
        async with self._lock:
            if consultation_id not in self.rooms:
                self.rooms[consultation_id] = ConsultationRoom(
                    consultation_id=consultation_id,
                    duration_minutes=duration_minutes,
                    started_at=started_at,
                )
            room = self.rooms[consultation_id]
            if started_at and not room.started_at:
                room.started_at = started_at
            return room

    async def connect(
        self,
        websocket: WebSocket,
        consultation_id: str,
        user_id: str,
        role: str,
        user_name: Optional[str] = None,
        duration_minutes: int = 5,
        started_at: Optional[datetime] = None,
    ) -> ConsultationRoom:
        """Register a peer in the consultation room. Replaces existing connection if user reconnects."""
        await websocket.accept()
        room = await self.get_or_create_room(consultation_id, duration_minutes, started_at)

        async with self._lock:
            # If this user already has an active websocket (e.g. refreshed tab), close old one
            if user_id in room.peers:
                old_peer = room.peers[user_id]
                try:
                    await old_peer.websocket.close(code=1000, reason="Reconnected from another tab/session")
                except Exception:
                    pass

            peer = ActivePeer(websocket, user_id, role, user_name)
            room.peers[user_id] = peer

        logger.info(
            f"DocTalk room {consultation_id}: user {user_id} ({role}) connected. Total peers: {len(room.peers)}"
        )

        # Notify other peer that this peer joined
        await self.broadcast_to_others(
            consultation_id=consultation_id,
            sender_id=user_id,
            message={
                "type": "peer_joined",
                "peer_id": user_id,
                "role": role,
                "peer_name": peer.user_name,
                "remaining_seconds": room.get_remaining_seconds(),
            },
        )

        # Send welcome message to the connecting peer with room state and peer list
        other_peer = next((p for uid, p in room.peers.items() if uid != user_id), None)
        welcome_payload = {
            "type": "room_state",
            "consultation_id": consultation_id,
            "role": role,
            "remaining_seconds": room.get_remaining_seconds(),
            "duration_minutes": room.duration_minutes,
            "has_peer": other_peer is not None,
            "peer_info": {
                "peer_id": other_peer.user_id,
                "role": other_peer.role,
                "peer_name": other_peer.user_name,
                "audio_enabled": other_peer.audio_enabled,
                "video_enabled": other_peer.video_enabled,
            }
            if other_peer
            else None,
        }
        await websocket.send_text(json.dumps(welcome_payload))

        return room

    async def disconnect(self, consultation_id: str, user_id: str):
        """Remove a peer from the room and notify the remaining peer."""
        async with self._lock:
            room = self.rooms.get(consultation_id)
            if not room:
                return

            if user_id in room.peers:
                del room.peers[user_id]
                logger.info(f"DocTalk room {consultation_id}: user {user_id} disconnected. Remaining peers: {len(room.peers)}")

            # If room is completely empty, prune it after some time or immediately
            if len(room.peers) == 0:
                # remove room
                del self.rooms[consultation_id]
                return

        # Notify the remaining peer
        await self.broadcast_to_room(
            consultation_id=consultation_id,
            message={
                "type": "peer_left",
                "peer_id": user_id,
            },
        )

    async def relay_signal(self, consultation_id: str, sender_id: str, message: Dict[str, Any]):
        """Relay WebRTC signaling messages (offer, answer, candidate, media_state, chat) to the other peer."""
        room = self.rooms.get(consultation_id)
        if not room:
            return

        # Update media state if message is media_state
        if message.get("type") == "media_state":
            sender_peer = room.peers.get(sender_id)
            if sender_peer:
                sender_peer.audio_enabled = bool(message.get("audio", True))
                sender_peer.video_enabled = bool(message.get("video", True))

        # Relay to the other peer
        await self.broadcast_to_others(consultation_id, sender_id, message)

    async def broadcast_to_others(self, consultation_id: str, sender_id: str, message: Dict[str, Any]):
        room = self.rooms.get(consultation_id)
        if not room:
            return

        text = json.dumps(message)
        for uid, peer in list(room.peers.items()):
            if uid != sender_id:
                try:
                    await peer.websocket.send_text(text)
                except Exception as e:
                    logger.warning(f"Failed to send to peer {uid} in room {consultation_id}: {e}")

    async def broadcast_to_room(self, consultation_id: str, message: Dict[str, Any]):
        room = self.rooms.get(consultation_id)
        if not room:
            return

        text = json.dumps(message)
        for uid, peer in list(room.peers.items()):
            try:
                await peer.websocket.send_text(text)
            except Exception as e:
                logger.warning(f"Failed to send to peer {uid} in room {consultation_id}: {e}")

    async def end_consultation(self, consultation_id: str, ended_by_user_id: Optional[str] = None, reason: str = "COMPLETED"):
        """Broadcast consultation_ended event to all peers in the room and mark room ended."""
        async with self._lock:
            room = self.rooms.get(consultation_id)
            if not room:
                return
            room.is_ended = True

        logger.info(f"DocTalk room {consultation_id} ended. Reason: {reason}")
        await self.broadcast_to_room(
            consultation_id=consultation_id,
            message={
                "type": "consultation_ended",
                "consultation_id": consultation_id,
                "ended_by": ended_by_user_id,
                "reason": reason,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        )


# Global singleton instance
session_manager = DocTalkConnectionManager()
