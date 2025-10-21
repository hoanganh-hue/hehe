"""
Log Rotation Management
Handles log file rotation and cleanup
"""

import os
import time
import gzip
import shutil
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import List, Dict, Any
import logging
import asyncio

from .structured_logging import get_logger

logger = get_logger(__name__)

class LogRotationManager:
    """
    Manages log file rotation and cleanup
    """
    
    def __init__(self, log_dir: str = "logs", max_file_size: int = 10 * 1024 * 1024, backup_count: int = 5):
        """
        Initialize log rotation manager
        
        Args:
            log_dir: Directory containing log files
            max_file_size: Maximum size of log file before rotation (bytes)
            backup_count: Number of backup files to keep
        """
        self.log_dir = Path(log_dir)
        self.max_file_size = max_file_size
        self.backup_count = backup_count
        self.rotation_interval = 24 * 60 * 60  # 24 hours in seconds
        self.last_rotation = {}
        self.running = False
        
        # Ensure log directory exists
        self.log_dir.mkdir(exist_ok=True)
    
    async def start(self):
        """Start log rotation service"""
        self.running = True
        logger.info("Starting log rotation service")
        
        while self.running:
            try:
                await self.check_and_rotate_logs()
                await asyncio.sleep(3600)  # Check every hour
            except Exception as e:
                logger.error(f"Error in log rotation: {e}")
                await asyncio.sleep(3600)
    
    async def stop(self):
        """Stop log rotation service"""
        self.running = False
        logger.info("Stopping log rotation service")
    
    async def check_and_rotate_logs(self):
        """Check all log files and rotate if necessary"""
        try:
            for log_file in self.log_dir.glob("*.log"):
                await self.rotate_log_file(log_file)
            
            # Clean up old compressed files
            await self.cleanup_old_logs()
            
        except Exception as e:
            logger.error(f"Error checking log files: {e}")
    
    async def rotate_log_file(self, log_file: Path):
        """
        Rotate a single log file if necessary
        
        Args:
            log_file: Path to log file
        """
        try:
            # Check if file exists and has content
            if not log_file.exists() or log_file.stat().st_size == 0:
                return
            
            # Check file size
            file_size = log_file.stat().st_size
            if file_size < self.max_file_size:
                return
            
            # Check rotation interval
            file_mtime = log_file.stat().st_mtime
            last_rotation = self.last_rotation.get(str(log_file), 0)
            if file_mtime - last_rotation < self.rotation_interval:
                return
            
            # Rotate the file
            await self.perform_rotation(log_file)
            
            # Update last rotation time
            self.last_rotation[str(log_file)] = time.time()
            
        except Exception as e:
            logger.error(f"Error rotating log file {log_file}: {e}")
    
    async def perform_rotation(self, log_file: Path):
        """
        Perform the actual log rotation
        
        Args:
            log_file: Path to log file
        """
        try:
            # Create backup filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = log_file.with_suffix(f".{timestamp}.log")
            
            # Move current log to backup
            shutil.move(str(log_file), str(backup_file))
            
            # Compress the backup file
            compressed_file = backup_file.with_suffix(".gz")
            await self.compress_file(backup_file, compressed_file)
            
            # Remove uncompressed backup
            backup_file.unlink()
            
            logger.info(f"Rotated log file: {log_file} -> {compressed_file}")
            
        except Exception as e:
            logger.error(f"Error performing rotation for {log_file}: {e}")
    
    async def compress_file(self, source_file: Path, target_file: Path):
        """
        Compress a file using gzip
        
        Args:
            source_file: Source file path
            target_file: Target compressed file path
        """
        try:
            with open(source_file, 'rb') as f_in:
                with gzip.open(target_file, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            
            logger.info(f"Compressed file: {source_file} -> {target_file}")
            
        except Exception as e:
            logger.error(f"Error compressing file {source_file}: {e}")
    
    async def cleanup_old_logs(self, retention_days: int = 30):
        """
        Clean up old log files
        
        Args:
            retention_days: Number of days to retain logs
        """
        try:
            cutoff_time = time.time() - (retention_days * 24 * 60 * 60)
            
            # Find all compressed log files
            for log_file in self.log_dir.glob("*.log.*.gz"):
                if log_file.stat().st_mtime < cutoff_time:
                    log_file.unlink()
                    logger.info(f"Deleted old log file: {log_file}")
            
            # Find all uncompressed backup files
            for log_file in self.log_dir.glob("*.log.*"):
                if not log_file.name.endswith('.gz') and log_file.stat().st_mtime < cutoff_time:
                    log_file.unlink()
                    logger.info(f"Deleted old log file: {log_file}")
            
        except Exception as e:
            logger.error(f"Error cleaning up old logs: {e}")
    
    async def get_log_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about log files
        
        Returns:
            Dictionary of log statistics
        """
        try:
            stats = {
                'total_files': 0,
                'total_size': 0,
                'compressed_files': 0,
                'compressed_size': 0,
                'uncompressed_files': 0,
                'uncompressed_size': 0,
                'oldest_file': None,
                'newest_file': None,
                'files_by_type': {}
            }
            
            oldest_time = float('inf')
            newest_time = 0
            
            for log_file in self.log_dir.glob("*.log*"):
                stats['total_files'] += 1
                file_size = log_file.stat().st_size
                stats['total_size'] += file_size
                
                file_mtime = log_file.stat().st_mtime
                if file_mtime < oldest_time:
                    oldest_time = file_mtime
                    stats['oldest_file'] = str(log_file)
                
                if file_mtime > newest_time:
                    newest_time = file_mtime
                    stats['newest_file'] = str(log_file)
                
                # Categorize by file type
                if log_file.name.endswith('.gz'):
                    stats['compressed_files'] += 1
                    stats['compressed_size'] += file_size
                    file_type = 'compressed'
                else:
                    stats['uncompressed_files'] += 1
                    stats['uncompressed_size'] += file_size
                    file_type = 'uncompressed'
                
                if file_type not in stats['files_by_type']:
                    stats['files_by_type'][file_type] = {'count': 0, 'size': 0}
                
                stats['files_by_type'][file_type]['count'] += 1
                stats['files_by_type'][file_type]['size'] += file_size
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting log statistics: {e}")
            return {}
    
    async def force_rotation(self, log_file: Path):
        """
        Force rotation of a specific log file
        
        Args:
            log_file: Path to log file
        """
        try:
            if log_file.exists():
                await self.perform_rotation(log_file)
                self.last_rotation[str(log_file)] = time.time()
                logger.info(f"Force rotated log file: {log_file}")
            else:
                logger.warning(f"Log file does not exist: {log_file}")
                
        except Exception as e:
            logger.error(f"Error force rotating log file {log_file}: {e}")
    
    async def get_log_file_info(self, log_file: Path) -> Dict[str, Any]:
        """
        Get information about a specific log file
        
        Args:
            log_file: Path to log file
            
        Returns:
            Dictionary of file information
        """
        try:
            if not log_file.exists():
                return {'exists': False}
            
            stat = log_file.stat()
            
            info = {
                'exists': True,
                'size': stat.st_size,
                'size_mb': stat.st_size / (1024 * 1024),
                'created': datetime.fromtimestamp(stat.st_ctime, tz=timezone.utc).isoformat(),
                'modified': datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat(),
                'accessed': datetime.fromtimestamp(stat.st_atime, tz=timezone.utc).isoformat(),
                'needs_rotation': stat.st_size >= self.max_file_size,
                'last_rotation': self.last_rotation.get(str(log_file), 0)
            }
            
            return info
            
        except Exception as e:
            logger.error(f"Error getting log file info for {log_file}: {e}")
            return {'error': str(e)}

class LogAnalyzer:
    """
    Analyzes log files for patterns and statistics
    """
    
    def __init__(self, log_dir: str = "logs"):
        """
        Initialize log analyzer
        
        Args:
            log_dir: Directory containing log files
        """
        self.log_dir = Path(log_dir)
    
    async def analyze_log_file(self, log_file: Path) -> Dict[str, Any]:
        """
        Analyze a single log file
        
        Args:
            log_file: Path to log file
            
        Returns:
            Dictionary of analysis results
        """
        try:
            analysis = {
                'total_lines': 0,
                'error_count': 0,
                'warning_count': 0,
                'info_count': 0,
                'debug_count': 0,
                'unique_ips': set(),
                'unique_users': set(),
                'error_types': {},
                'hourly_distribution': {},
                'top_errors': []
            }
            
            if not log_file.exists():
                return analysis
            
            # Read log file
            with open(log_file, 'r', encoding='utf-8') as f:
                for line in f:
                    analysis['total_lines'] += 1
                    
                    try:
                        # Parse JSON log entry
                        import json
                        log_entry = json.loads(line.strip())
                        
                        # Count log levels
                        level = log_entry.get('level', '').lower()
                        if level == 'error':
                            analysis['error_count'] += 1
                        elif level == 'warning':
                            analysis['warning_count'] += 1
                        elif level == 'info':
                            analysis['info_count'] += 1
                        elif level == 'debug':
                            analysis['debug_count'] += 1
                        
                        # Extract IP addresses
                        ip = log_entry.get('ip_address')
                        if ip:
                            analysis['unique_ips'].add(ip)
                        
                        # Extract user IDs
                        user_id = log_entry.get('user_id') or log_entry.get('admin_id')
                        if user_id:
                            analysis['unique_users'].add(user_id)
                        
                        # Count error types
                        if level == 'error':
                            error_type = log_entry.get('error_type', 'unknown')
                            analysis['error_types'][error_type] = analysis['error_types'].get(error_type, 0) + 1
                        
                        # Hourly distribution
                        timestamp = log_entry.get('timestamp', '')
                        if timestamp:
                            try:
                                hour = datetime.fromisoformat(timestamp.replace('Z', '+00:00')).hour
                                analysis['hourly_distribution'][hour] = analysis['hourly_distribution'].get(hour, 0) + 1
                            except:
                                pass
                        
                    except json.JSONDecodeError:
                        # Handle non-JSON log entries
                        if 'ERROR' in line.upper():
                            analysis['error_count'] += 1
                        elif 'WARNING' in line.upper():
                            analysis['warning_count'] += 1
                        elif 'INFO' in line.upper():
                            analysis['info_count'] += 1
            
            # Convert sets to lists for JSON serialization
            analysis['unique_ips'] = list(analysis['unique_ips'])
            analysis['unique_users'] = list(analysis['unique_users'])
            
            # Get top errors
            analysis['top_errors'] = sorted(
                analysis['error_types'].items(),
                key=lambda x: x[1],
                reverse=True
            )[:10]
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing log file {log_file}: {e}")
            return {'error': str(e)}
    
    async def analyze_all_logs(self) -> Dict[str, Any]:
        """
        Analyze all log files in the directory
        
        Returns:
            Dictionary of analysis results
        """
        try:
            analysis = {
                'total_files': 0,
                'total_lines': 0,
                'total_errors': 0,
                'total_warnings': 0,
                'total_info': 0,
                'total_debug': 0,
                'unique_ips': set(),
                'unique_users': set(),
                'error_types': {},
                'files': {}
            }
            
            for log_file in self.log_dir.glob("*.log"):
                if log_file.name.endswith('.gz'):
                    continue  # Skip compressed files for now
                
                analysis['total_files'] += 1
                file_analysis = await self.analyze_log_file(log_file)
                
                # Aggregate results
                analysis['total_lines'] += file_analysis.get('total_lines', 0)
                analysis['total_errors'] += file_analysis.get('error_count', 0)
                analysis['total_warnings'] += file_analysis.get('warning_count', 0)
                analysis['total_info'] += file_analysis.get('info_count', 0)
                analysis['total_debug'] += file_analysis.get('debug_count', 0)
                
                # Merge unique sets
                analysis['unique_ips'].update(file_analysis.get('unique_ips', []))
                analysis['unique_users'].update(file_analysis.get('unique_users', []))
                
                # Merge error types
                for error_type, count in file_analysis.get('error_types', {}).items():
                    analysis['error_types'][error_type] = analysis['error_types'].get(error_type, 0) + count
                
                # Store file-specific analysis
                analysis['files'][str(log_file)] = file_analysis
            
            # Convert sets to lists
            analysis['unique_ips'] = list(analysis['unique_ips'])
            analysis['unique_users'] = list(analysis['unique_users'])
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing all logs: {e}")
            return {'error': str(e)}

# Global log rotation manager instance
log_rotation_manager: LogRotationManager = None

def get_log_rotation_manager() -> LogRotationManager:
    """Get the global log rotation manager instance"""
    global log_rotation_manager
    if log_rotation_manager is None:
        log_rotation_manager = LogRotationManager()
    return log_rotation_manager

async def start_log_rotation():
    """Start log rotation service"""
    manager = get_log_rotation_manager()
    await manager.start()

async def stop_log_rotation():
    """Stop log rotation service"""
    manager = get_log_rotation_manager()
    await manager.stop()

async def force_rotate_logs():
    """Force rotation of all log files"""
    manager = get_log_rotation_manager()
    await manager.check_and_rotate_logs()

async def get_log_statistics():
    """Get log statistics"""
    manager = get_log_rotation_manager()
    return await manager.get_log_statistics()

async def analyze_logs():
    """Analyze all log files"""
    analyzer = LogAnalyzer()
    return await analyzer.analyze_all_logs()
