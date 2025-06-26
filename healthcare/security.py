"""
Security utilities for XSS and SQL injection protection.
"""

import re
import html
import unicodedata
from typing import Optional
from django.core.exceptions import ValidationError


class SecurityUtils:
    """Utility class for XSS and SQL injection protection."""
    
    # Dangerous HTML tags that should be removed
    DANGEROUS_TAGS = [
        'script', 'iframe', 'object', 'embed', 'form', 'input', 'textarea',
        'select', 'button', 'link', 'meta', 'style', 'base', 'bgsound',
        'title', 'xmp', 'plaintext', 'listing', 'marquee', 'applet'
    ]
    
    # Dangerous attributes that should be removed
    DANGEROUS_ATTRIBUTES = [
        'onload', 'onerror', 'onclick', 'onmouseover', 'onmouseout',
        'onfocus', 'onblur', 'onchange', 'onsubmit', 'onreset',
        'onkeydown', 'onkeyup', 'onkeypress', 'onabort', 'onbeforeunload'
    ]
    
    @staticmethod
    def sanitize_input(value: str, max_length: Optional[int] = None) -> str:
        """Sanitize user input to prevent XSS attacks."""
        if not value:
            return ''
        
        # Convert to string and normalize unicode
        value = str(value)
        value = unicodedata.normalize('NFKC', value)
        
        # Remove HTML tags
        value = SecurityUtils._remove_html_tags(value)
        
        # Remove dangerous attributes
        value = SecurityUtils._remove_dangerous_attributes(value)
        
        # Remove dangerous protocols
        value = SecurityUtils._remove_dangerous_protocols(value)
        
        # Remove null bytes and control characters
        value = SecurityUtils._remove_control_characters(value)
        
        # Truncate if needed
        if max_length and len(value) > max_length:
            value = value[:max_length]
        
        return value.strip()
    
    @staticmethod
    def _remove_html_tags(value: str) -> str:
        """Remove all HTML tags from the input."""
        # Remove dangerous tags completely
        for tag in SecurityUtils.DANGEROUS_TAGS:
            value = re.sub(f'<{tag}[^>]*>', '', value, flags=re.IGNORECASE)
            value = re.sub(f'</{tag}>', '', value, flags=re.IGNORECASE)
        
        # Remove any remaining HTML tags
        value = re.sub(r'<[^>]*>', '', value)
        
        return value
    
    @staticmethod
    def _remove_dangerous_attributes(value: str) -> str:
        """Remove dangerous HTML attributes from the input."""
        for attr in SecurityUtils.DANGEROUS_ATTRIBUTES:
            value = re.sub(f'{attr}\\s*=\\s*["\'][^"\']*["\']', '', value, flags=re.IGNORECASE)
            value = re.sub(f'{attr}\\s*=\\s*[^\\s>]+', '', value, flags=re.IGNORECASE)
        
        return value
    
    @staticmethod
    def _remove_dangerous_protocols(value: str) -> str:
        """Remove dangerous protocols from URLs."""
        dangerous_protocols = ['javascript:', 'vbscript:', 'data:', 'mocha:', 'livescript:']
        for protocol in dangerous_protocols:
            value = re.sub(protocol, '', value, flags=re.IGNORECASE)
        
        return value
    
    @staticmethod
    def _remove_control_characters(value: str) -> str:
        """Remove null bytes and control characters."""
        value = value.replace('\x00', '')
        value = ''.join(char for char in value if ord(char) >= 32 or char in '\n\t\r')
        return value
    
    @staticmethod
    def is_suspicious_input(value: str) -> bool:
        """Check if input contains XSS or SQL injection patterns."""
        if not value:
            return False
        
        value_lower = value.lower()
        
        # XSS patterns
        xss_patterns = [
            '<script', '</script>', 'javascript:', 'vbscript:', 'data:',
            'onload=', 'onclick=', 'onerror=', '<iframe', '<object',
            'document.cookie', 'window.location', 'eval(', 'alert('
        ]
        
        # SQL injection patterns
        sql_patterns = [
            'union select', 'drop table', 'insert into', 'delete from',
            'update set', 'alter table', 'create table', 'exec(',
            'execute(', 'union all', 'or 1=1', 'or 1=1--', 'admin\'--',
            'select *', 'select count', 'select user', 'select database'
        ]
        
        # Check for XSS patterns
        for pattern in xss_patterns:
            if pattern in value_lower:
                return True
        
        # Check for SQL injection patterns
        for pattern in sql_patterns:
            if pattern in value_lower:
                return True
        
        return False


class SecurityValidator:
    """Validator class for XSS and SQL injection protection."""
    
    @staticmethod
    def validate_and_sanitize_text(value: str, field_name: str, max_length: Optional[int] = None) -> str:
        """Validate and sanitize text input."""
        if not value:
            raise ValidationError(f"{field_name} cannot be empty.")
        
        if SecurityUtils.is_suspicious_input(value):
            raise ValidationError(f"{field_name} contains invalid characters.")
        
        sanitized = SecurityUtils.sanitize_input(value, max_length)
        
        if not sanitized:
            raise ValidationError(f"{field_name} cannot be empty after sanitization.")
        
        return sanitized 