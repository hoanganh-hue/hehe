"""
Credential Validation Pipeline
Advanced credential validation and analysis service
"""

import logging
import asyncio
import re
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Tuple
from email_validator import validate_email, EmailNotValidError
import phonenumbers
from phonenumbers import NumberParseException
import hashlib
import bcrypt

logger = logging.getLogger(__name__)

class CredentialValidationPipeline:
    """Advanced credential validation and analysis pipeline"""

    def __init__(self):
        self.validation_rules = {
            'email': self._validate_email_format,
            'password': self._validate_password_strength,
            'phone': self._validate_phone_format,
            'name': self._validate_name_format,
            'credentials': self._validate_credential_pair
        }

        self.strength_thresholds = {
            'weak': 0.3,
            'medium': 0.6,
            'strong': 0.8
        }

    async def validate_credentials(self, credentials: Dict[str, Any]) -> Dict[str, Any]:
        """
        Comprehensive credential validation

        Args:
            credentials: Dictionary containing credential data

        Returns:
            Validation results with scores and recommendations
        """
        try:
            validation_results = {
                'overall_score': 0.0,
                'is_valid': False,
                'field_validations': {},
                'recommendations': [],
                'risk_assessment': {},
                'validation_timestamp': datetime.now(timezone.utc).isoformat()
            }

            # Validate individual fields
            field_scores = []
            for field_name, validator in self.validation_rules.items():
                if field_name in credentials:
                    field_result = await validator(credentials[field_name], credentials)
                    validation_results['field_validations'][field_name] = field_result
                    field_scores.append(field_result.get('score', 0.0))

            # Calculate overall score
            if field_scores:
                validation_results['overall_score'] = sum(field_scores) / len(field_scores)

            # Determine validity
            validation_results['is_valid'] = validation_results['overall_score'] >= 0.5

            # Generate recommendations
            validation_results['recommendations'] = self._generate_recommendations(validation_results)

            # Risk assessment
            validation_results['risk_assessment'] = self._assess_credential_risk(credentials, validation_results)

            return validation_results

        except Exception as e:
            logger.error(f"Credential validation error: {e}")
            return {
                'overall_score': 0.0,
                'is_valid': False,
                'error': str(e),
                'validation_timestamp': datetime.now(timezone.utc).isoformat()
            }

    async def _validate_email_format(self, email: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Validate email format and characteristics"""
        try:
            result = {
                'is_valid': False,
                'score': 0.0,
                'issues': [],
                'strength': 'weak',
                'details': {}
            }

            # Basic format validation
            try:
                valid = validate_email(email, check_deliverability=False)
                email = valid.email
                result['is_valid'] = True
                result['score'] = 0.6
            except EmailNotValidError as e:
                result['issues'].append(f"Invalid email format: {str(e)}")
                return result

            # Domain analysis
            domain = email.split('@')[1].lower()
            result['details']['domain'] = domain

            # Check for suspicious patterns
            suspicious_patterns = [
                r'\d{8,}',  # Too many consecutive numbers
                r'[a-zA-Z0-9]{30,}',  # Too long
                r'^.{1,2}@',  # Very short local part
                r'@.*\..*\.',  # Multiple dots in domain
            ]

            for pattern in suspicious_patterns:
                if re.search(pattern, email):
                    result['issues'].append("Suspicious email pattern detected")
                    result['score'] -= 0.2

            # Check for common disposable email domains
            disposable_domains = [
                '10minutemail.com', 'guerrillamail.com', 'mailinator.com',
                'temp-mail.org', 'throwaway.email', 'yopmail.com'
            ]

            if domain in disposable_domains:
                result['issues'].append("Disposable email domain detected")
                result['score'] -= 0.3

            # Length analysis
            if len(email) > 50:
                result['issues'].append("Email address too long")
                result['score'] -= 0.1

            # Determine strength
            if result['score'] >= 0.8:
                result['strength'] = 'strong'
            elif result['score'] >= 0.5:
                result['strength'] = 'medium'

            result['score'] = max(0.0, min(1.0, result['score']))
            return result

        except Exception as e:
            logger.error(f"Email validation error: {e}")
            return {
                'is_valid': False,
                'score': 0.0,
                'issues': [f"Validation error: {str(e)}"],
                'strength': 'weak'
            }

    async def _validate_password_strength(self, password: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Validate password strength and characteristics"""
        try:
            result = {
                'is_valid': False,
                'score': 0.0,
                'issues': [],
                'strength': 'weak',
                'details': {}
            }

            if not password:
                result['issues'].append("Password is empty")
                return result

            # Length check
            length = len(password)
            result['details']['length'] = length

            if length < 6:
                result['issues'].append("Password too short (minimum 6 characters)")
                result['score'] = 0.1
            elif length < 8:
                result['score'] = 0.3
            elif length < 12:
                result['score'] = 0.6
            else:
                result['score'] = 0.8

            # Character variety checks
            has_lower = bool(re.search(r'[a-z]', password))
            has_upper = bool(re.search(r'[A-Z]', password))
            has_digit = bool(re.search(r'\d', password))
            has_special = bool(re.search(r'[^a-zA-Z0-9]', password))

            result['details']['has_lower'] = has_lower
            result['details']['has_upper'] = has_upper
            result['details']['has_digit'] = has_digit
            result['details']['has_special'] = has_special

            # Bonus for character variety
            variety_score = sum([has_lower, has_upper, has_digit, has_special]) * 0.1
            result['score'] += variety_score

            # Check for common weak patterns
            weak_patterns = [
                r'^password', r'123456', r'qwerty', r'admin', r'user',
                r'letmein', r'welcome', r'monkey', r'dragon', r'passw0rd'
            ]

            for pattern in weak_patterns:
                if re.search(pattern, password, re.IGNORECASE):
                    result['issues'].append("Contains common weak password pattern")
                    result['score'] -= 0.3
                    break

            # Check for sequential characters
            if re.search(r'(?:012|123|234|345|456|567|678|789|890|abc|bcd|cde|def)', password, re.IGNORECASE):
                result['issues'].append("Contains sequential characters")
                result['score'] -= 0.2

            # Check for repeated characters
            if re.search(r'(.)\1{2,}', password):
                result['issues'].append("Contains repeated characters")
                result['score'] -= 0.1

            # Determine strength category
            if result['score'] >= 0.8:
                result['strength'] = 'strong'
                result['is_valid'] = True
            elif result['score'] >= 0.5:
                result['strength'] = 'medium'
                result['is_valid'] = True
            else:
                result['strength'] = 'weak'

            result['score'] = max(0.0, min(1.0, result['score']))
            return result

        except Exception as e:
            logger.error(f"Password validation error: {e}")
            return {
                'is_valid': False,
                'score': 0.0,
                'issues': [f"Validation error: {str(e)}"],
                'strength': 'weak'
            }

    async def _validate_phone_format(self, phone: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Validate phone number format"""
        try:
            result = {
                'is_valid': False,
                'score': 0.0,
                'issues': [],
                'strength': 'weak',
                'details': {}
            }

            if not phone:
                result['issues'].append("Phone number is empty")
                return result

            # Remove common separators
            clean_phone = re.sub(r'[\s\-\(\)\.\+]', '', phone)

            # Check if it's all digits (basic validation)
            if not clean_phone.isdigit():
                result['issues'].append("Phone number contains invalid characters")
                return result

            # Length check
            if len(clean_phone) < 7:
                result['issues'].append("Phone number too short")
                return result
            elif len(clean_phone) > 15:
                result['issues'].append("Phone number too long")
                return result

            # Try to parse with phonenumbers library
            try:
                parsed_number = phonenumbers.parse(phone, "VN")  # Default to Vietnam
                if phonenumbers.is_valid_number(parsed_number):
                    result['is_valid'] = True
                    result['score'] = 0.8
                    result['details']['country_code'] = parsed_number.country_code
                    result['details']['national_number'] = parsed_number.national_number
                    result['details']['formatted'] = phonenumbers.format_number(parsed_number, phonenumbers.PhoneNumberFormat.INTERNATIONAL)
                else:
                    result['issues'].append("Invalid phone number format")
                    result['score'] = 0.3
            except NumberParseException:
                # Fallback to basic validation
                result['issues'].append("Could not parse phone number")
                result['score'] = 0.4
                result['is_valid'] = len(clean_phone) >= 10

            # Determine strength
            if result['score'] >= 0.7:
                result['strength'] = 'strong'
            elif result['score'] >= 0.4:
                result['strength'] = 'medium'

            result['score'] = max(0.0, min(1.0, result['score']))
            return result

        except Exception as e:
            logger.error(f"Phone validation error: {e}")
            return {
                'is_valid': False,
                'score': 0.0,
                'issues': [f"Validation error: {str(e)}"],
                'strength': 'weak'
            }

    async def _validate_name_format(self, name: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Validate name format"""
        try:
            result = {
                'is_valid': False,
                'score': 0.0,
                'issues': [],
                'strength': 'weak',
                'details': {}
            }

            if not name:
                result['issues'].append("Name is empty")
                return result

            # Length check
            if len(name.strip()) < 2:
                result['issues'].append("Name too short")
                return result
            elif len(name) > 100:
                result['issues'].append("Name too long")
                result['score'] -= 0.1

            # Check for valid characters (letters, spaces, hyphens, apostrophes)
            if not re.match(r"^[a-zA-Z\s\-']+$", name):
                result['issues'].append("Name contains invalid characters")
                return result

            # Check for too many consecutive spaces or special chars
            if re.search(r'\s{2,}', name):
                result['issues'].append("Too many consecutive spaces")
                result['score'] -= 0.1

            # Basic validation passed
            result['is_valid'] = True
            result['score'] = 0.7

            # Split into parts for analysis
            name_parts = name.strip().split()
            result['details']['parts_count'] = len(name_parts)

            if len(name_parts) < 2:
                result['issues'].append("Name appears incomplete (only one part)")
                result['score'] -= 0.2

            # Check for common fake name patterns
            fake_patterns = [
                r'^test', r'^user\d', r'^admin', r'^guest',
                r'fake', r'temp', r'dummy', r'sample'
            ]

            for pattern in fake_patterns:
                if re.search(pattern, name, re.IGNORECASE):
                    result['issues'].append("Name appears to be a test/fake entry")
                    result['score'] -= 0.3
                    break

            # Determine strength
            if result['score'] >= 0.8:
                result['strength'] = 'strong'
            elif result['score'] >= 0.5:
                result['strength'] = 'medium'

            result['score'] = max(0.0, min(1.0, result['score']))
            return result

        except Exception as e:
            logger.error(f"Name validation error: {e}")
            return {
                'is_valid': False,
                'score': 0.0,
                'issues': [f"Validation error: {str(e)}"],
                'strength': 'weak'
            }

    async def _validate_credential_pair(self, credentials: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Validate credential pair coherence"""
        try:
            result = {
                'is_valid': False,
                'score': 0.0,
                'issues': [],
                'strength': 'weak',
                'details': {}
            }

            email = credentials.get('email', '').lower()
            password = credentials.get('password', '')

            if not email or not password:
                result['issues'].append("Missing email or password")
                return result

            # Check if password contains parts of email
            email_parts = re.split(r'[@\.]', email)
            for part in email_parts:
                if len(part) > 3 and part in password.lower():
                    result['issues'].append("Password contains email parts")
                    result['score'] -= 0.2

            # Check password length vs email length ratio
            ratio = len(password) / len(email)
            if ratio < 0.5:
                result['issues'].append("Password significantly shorter than email")
                result['score'] -= 0.1

            # Basic coherence check passed
            result['is_valid'] = True
            result['score'] = 0.6

            # Determine strength
            if result['score'] >= 0.7:
                result['strength'] = 'strong'
            elif result['score'] >= 0.4:
                result['strength'] = 'medium'

            result['score'] = max(0.0, min(1.0, result['score']))
            return result

        except Exception as e:
            logger.error(f"Credential pair validation error: {e}")
            return {
                'is_valid': False,
                'score': 0.0,
                'issues': [f"Validation error: {str(e)}"],
                'strength': 'weak'
            }

    def _generate_recommendations(self, validation_results: Dict[str, Any]) -> List[str]:
        """Generate improvement recommendations"""
        recommendations = []

        field_validations = validation_results.get('field_validations', {})

        # Email recommendations
        if 'email' in field_validations:
            email_result = field_validations['email']
            if not email_result.get('is_valid', False):
                recommendations.append("Use a valid email format")
            if email_result.get('score', 0) < 0.7:
                recommendations.append("Avoid disposable email services")

        # Password recommendations
        if 'password' in field_validations:
            password_result = field_validations['password']
            if password_result.get('strength') == 'weak':
                recommendations.extend([
                    "Use at least 8 characters",
                    "Include uppercase and lowercase letters",
                    "Include numbers and special characters",
                    "Avoid common passwords and patterns"
                ])

        # Phone recommendations
        if 'phone' in field_validations:
            phone_result = field_validations['phone']
            if not phone_result.get('is_valid', False):
                recommendations.append("Use a valid phone number format")

        # Name recommendations
        if 'name' in field_validations:
            name_result = field_validations['name']
            if not name_result.get('is_valid', False):
                recommendations.append("Provide a complete name")

        return list(set(recommendations))  # Remove duplicates

    def _assess_credential_risk(self, credentials: Dict[str, Any], validation_results: Dict[str, Any]) -> Dict[str, Any]:
        """Assess overall credential risk"""
        risk_assessment = {
            'risk_level': 'low',
            'risk_score': 0.0,
            'risk_factors': [],
            'confidence': 'medium'
        }

        overall_score = validation_results.get('overall_score', 0.0)

        # Calculate risk score (inverse of validation score)
        risk_assessment['risk_score'] = 1.0 - overall_score

        # Determine risk level
        if risk_assessment['risk_score'] >= 0.7:
            risk_assessment['risk_level'] = 'high'
        elif risk_assessment['risk_score'] >= 0.4:
            risk_assessment['risk_level'] = 'medium'
        else:
            risk_assessment['risk_level'] = 'low'

        # Identify risk factors
        field_validations = validation_results.get('field_validations', {})

        for field_name, field_result in field_validations.items():
            if field_result.get('score', 1.0) < 0.5:
                risk_assessment['risk_factors'].append(f"Low {field_name} quality")

            issues = field_result.get('issues', [])
            if issues:
                risk_assessment['risk_factors'].extend([f"{field_name}: {issue}" for issue in issues])

        # Determine confidence
        if len(field_validations) >= 3:
            risk_assessment['confidence'] = 'high'
        elif len(field_validations) >= 2:
            risk_assessment['confidence'] = 'medium'
        else:
            risk_assessment['confidence'] = 'low'

        return risk_assessment

    async def hash_password(self, password: str) -> str:
        """Hash password using bcrypt"""
        try:
            salt = bcrypt.gensalt()
            hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
            return hashed.decode('utf-8')
        except Exception as e:
            logger.error(f"Password hashing error: {e}")
            raise

    async def verify_password(self, password: str, hashed: str) -> bool:
        """Verify password against hash"""
        try:
            return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
        except Exception as e:
            logger.error(f"Password verification error: {e}")
            return False

    def generate_credential_hash(self, credentials: Dict[str, Any]) -> str:
        """Generate hash of credential combination for deduplication"""
        try:
            # Create a normalized string representation
            cred_string = ""
            for key in sorted(credentials.keys()):
                value = str(credentials[key]).lower().strip()
                cred_string += f"{key}:{value}|"

            return hashlib.sha256(cred_string.encode()).hexdigest()
        except Exception as e:
            logger.error(f"Credential hash generation error: {e}")
            return ""