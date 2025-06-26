"""
Template filters for XSS and SQL injection protection.
"""

import re
from django import template
from django.utils.safestring import mark_safe
from django.utils.html import escape
from healthcare.security import SecurityUtils

register = template.Library()


@register.filter
def safe_output(value):
    """
    Safely output user content by escaping HTML to prevent XSS.
    Use this for any user-generated content that should be displayed as text.
    """
    if value is None:
        return ''
    
    # First sanitize the input
    sanitized = SecurityUtils.sanitize_input(str(value))
    
    # Then escape any remaining HTML
    return escape(sanitized)


@register.filter
def sanitize_html(value):
    """
    Sanitize HTML content by removing dangerous tags and attributes.
    Use this for content that should allow some HTML but be safe from XSS.
    """
    if value is None:
        return ''
    
    value_str = str(value)
    
    # Remove dangerous HTML tags
    dangerous_tags = [
        'script', 'iframe', 'object', 'embed', 'form', 'input', 'textarea',
        'select', 'button', 'link', 'meta', 'style', 'base', 'bgsound',
        'title', 'xmp', 'plaintext', 'listing', 'marquee', 'applet'
    ]
    
    for tag in dangerous_tags:
        # Remove opening and closing tags
        value_str = re.sub(f'<{tag}[^>]*>', '', value_str, flags=re.IGNORECASE)
        value_str = re.sub(f'</{tag}>', '', value_str, flags=re.IGNORECASE)
    
    # Remove dangerous attributes
    dangerous_attrs = [
        'onload', 'onerror', 'onclick', 'onmouseover', 'onmouseout',
        'onfocus', 'onblur', 'onchange', 'onsubmit', 'onreset',
        'onkeydown', 'onkeyup', 'onkeypress', 'onabort', 'onbeforeunload'
    ]
    
    for attr in dangerous_attrs:
        # Remove attributes with any value
        value_str = re.sub(f'{attr}\\s*=\\s*["\'][^"\']*["\']', '', value_str, flags=re.IGNORECASE)
        value_str = re.sub(f'{attr}\\s*=\\s*[^\\s>]+', '', value_str, flags=re.IGNORECASE)
    
    # Remove javascript: and data: URLs
    value_str = re.sub(r'javascript:', '', value_str, flags=re.IGNORECASE)
    value_str = re.sub(r'data:text/html', '', value_str, flags=re.IGNORECASE)
    value_str = re.sub(r'data:application/javascript', '', value_str, flags=re.IGNORECASE)
    
    return mark_safe(value_str)


@register.filter
def safe_url(value):
    """
    Safely output a URL, ensuring it doesn't contain dangerous protocols.
    """
    if value is None:
        return ''
    
    value_str = str(value)
    
    # Remove dangerous protocols
    dangerous_protocols = ['javascript:', 'vbscript:', 'data:', 'mocha:', 'livescript:']
    for protocol in dangerous_protocols:
        if value_str.lower().startswith(protocol):
            return ''
    
    return escape(value_str) 