#!/usr/bin/env python3
"""
Data Archival Script
Automated data archival and cleanup for the ZaloPay Merchant Phishing Platform
"""

import os
import sys
import asyncio
import argparse
import logging
from datetime import datetime, timezone
from pathlib import Path

# Add the backend directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from database.retention_manager import get_data_retention_manager
from database.mongodb.schema_manager import get_mongodb_manager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def run_archival_process():
    """Run the complete archival process"""
    try:
        logger.info("Starting data archival process")
        
        # Initialize managers
        mongodb_manager = get_mongodb_manager()
        retention_manager = get_data_retention_manager(mongodb_manager.db)
        
        # Process retention policies
        await retention_manager.process_retention_policies()
        
        # Clean up old archives
        deleted_archives = await retention_manager.cleanup_old_archives()
        
        # Get statistics
        stats = retention_manager.get_retention_stats()
        
        logger.info("Data archival process completed successfully")
        logger.info(f"Statistics: {stats}")
        logger.info(f"Deleted {deleted_archives} old archives")
        
        return True
        
    except Exception as e:
        logger.error(f"Error in archival process: {e}")
        return False

async def restore_archive(archive_id: str, target_collection: str = None):
    """Restore documents from archive"""
    try:
        logger.info(f"Restoring archive: {archive_id}")
        
        # Initialize managers
        mongodb_manager = get_mongodb_manager()
        retention_manager = get_data_retention_manager(mongodb_manager.db)
        
        # Restore archive
        documents = await retention_manager.restore_archive(archive_id, target_collection)
        
        logger.info(f"Restored {len(documents)} documents from archive {archive_id}")
        return True
        
    except Exception as e:
        logger.error(f"Error restoring archive {archive_id}: {e}")
        return False

async def list_archives():
    """List all available archives"""
    try:
        logger.info("Listing all archives")
        
        # Initialize managers
        mongodb_manager = get_mongodb_manager()
        retention_manager = get_data_retention_manager(mongodb_manager.db)
        
        # Get archive list
        archives = retention_manager.get_archive_list()
        
        if not archives:
            logger.info("No archives found")
            return
        
        logger.info(f"Found {len(archives)} archives:")
        for archive in archives:
            logger.info(f"  {archive['archive_id']} - {archive['collection_name']} - {archive['document_count']} docs - {archive['archive_size']} bytes")
        
        return archives
        
    except Exception as e:
        logger.error(f"Error listing archives: {e}")
        return []

async def get_archive_info(archive_id: str):
    """Get detailed information about an archive"""
    try:
        logger.info(f"Getting info for archive: {archive_id}")
        
        # Initialize managers
        mongodb_manager = get_mongodb_manager()
        retention_manager = get_data_retention_manager(mongodb_manager.db)
        
        # Get archive metadata
        metadata = retention_manager.get_archive_metadata(archive_id)
        
        if not metadata:
            logger.error(f"Archive {archive_id} not found")
            return None
        
        logger.info(f"Archive Info:")
        logger.info(f"  ID: {metadata.archive_id}")
        logger.info(f"  Collection: {metadata.collection_name}")
        logger.info(f"  Document Count: {metadata.document_count}")
        logger.info(f"  Archive Size: {metadata.archive_size} bytes")
        logger.info(f"  Compression Ratio: {metadata.compression_ratio:.2f}")
        logger.info(f"  Created At: {metadata.created_at}")
        logger.info(f"  Checksum: {metadata.checksum}")
        
        return metadata
        
    except Exception as e:
        logger.error(f"Error getting archive info: {e}")
        return None

async def delete_archive(archive_id: str):
    """Delete an archive"""
    try:
        logger.info(f"Deleting archive: {archive_id}")
        
        # Initialize managers
        mongodb_manager = get_mongodb_manager()
        retention_manager = get_data_retention_manager(mongodb_manager.db)
        
        # Delete archive
        success = retention_manager.delete_archive(archive_id)
        
        if success:
            logger.info(f"Successfully deleted archive {archive_id}")
        else:
            logger.error(f"Failed to delete archive {archive_id}")
        
        return success
        
    except Exception as e:
        logger.error(f"Error deleting archive {archive_id}: {e}")
        return False

async def get_retention_stats():
    """Get retention statistics"""
    try:
        logger.info("Getting retention statistics")
        
        # Initialize managers
        mongodb_manager = get_mongodb_manager()
        retention_manager = get_data_retention_manager(mongodb_manager.db)
        
        # Get statistics
        stats = retention_manager.get_retention_stats()
        
        logger.info("Retention Statistics:")
        logger.info(f"  Total Policies: {stats['total_policies']}")
        logger.info(f"  Total Archives: {stats['total_archives']}")
        logger.info(f"  Total Archive Size: {stats['total_archive_size']} bytes")
        
        logger.info("Policies:")
        for collection, policy_stats in stats['policies'].items():
            logger.info(f"  {collection}: {policy_stats['retention_days']} days retention, {policy_stats['archive_days']} days archive")
        
        logger.info("Archives by Collection:")
        for collection, archive_stats in stats['archives_by_collection'].items():
            logger.info(f"  {collection}: {archive_stats['count']} archives, {archive_stats['total_documents']} documents, {archive_stats['total_size']} bytes")
        
        return stats
        
    except Exception as e:
        logger.error(f"Error getting retention stats: {e}")
        return {}

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Data Archival Script for ZaloPay Phishing Platform")
    parser.add_argument("--action", choices=["archive", "restore", "list", "info", "delete", "stats"], 
                       default="archive", help="Action to perform")
    parser.add_argument("--archive-id", help="Archive ID for restore/info/delete operations")
    parser.add_argument("--target-collection", help="Target collection for restore operation")
    parser.add_argument("--config", help="Configuration file path")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose logging")
    
    args = parser.parse_args()
    
    # Set logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Load configuration if provided
    if args.config:
        # TODO: Load configuration from file
        pass
    
    # Run the appropriate action
    try:
        if args.action == "archive":
            success = asyncio.run(run_archival_process())
            sys.exit(0 if success else 1)
        
        elif args.action == "restore":
            if not args.archive_id:
                logger.error("Archive ID is required for restore operation")
                sys.exit(1)
            success = asyncio.run(restore_archive(args.archive_id, args.target_collection))
            sys.exit(0 if success else 1)
        
        elif args.action == "list":
            archives = asyncio.run(list_archives())
            sys.exit(0)
        
        elif args.action == "info":
            if not args.archive_id:
                logger.error("Archive ID is required for info operation")
                sys.exit(1)
            metadata = asyncio.run(get_archive_info(args.archive_id))
            sys.exit(0 if metadata else 1)
        
        elif args.action == "delete":
            if not args.archive_id:
                logger.error("Archive ID is required for delete operation")
                sys.exit(1)
            success = asyncio.run(delete_archive(args.archive_id))
            sys.exit(0 if success else 1)
        
        elif args.action == "stats":
            stats = asyncio.run(get_retention_stats())
            sys.exit(0)
        
    except KeyboardInterrupt:
        logger.info("Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
