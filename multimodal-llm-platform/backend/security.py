#!/usr/bin/env python3
"""
Security hardening module for Autopicker Platform
Implements authentication, rate limiting, input validation, and security headers
"""

import hashlib
import hmac
import time
import secrets
import os
from datetime import datetime, timedelta
from typing import Dict, Optional, List, Tuple
import jwt
import bcrypt
from fastapi import HTTPException, Request, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi.responses import JSONResponse
import redis
import asyncio
import logging

logger = logging.getLogger(__name__)

# Security configuration
SECRET_KEY = os.getenv("SECRET_KEY", secrets.token_urlsafe(32))
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
RATE_LIMIT_REQUESTS = 100  # requests per minute
RATE_LIMIT_WINDOW = 60  # seconds
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
ALLOWED_FILE_TYPES = {
    'application/pdf', 'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'application/vnd.ms-excel', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    'text/plain', 'text/csv', 'application/json',
    'image/jpeg', 'image/png', 'image/gif', 'image/webp',
    'audio/mpeg', 'audio/wav', 'audio/mp4', 'audio/ogg'
}

# Initialize security components
security = HTTPBearer(auto_error=False)


class SecurityManager:
    """Central security management class"""
    
    def __init__(self):
        self.redis_client = None
        self.failed_attempts = {}  # Fallback for rate limiting
        self.api_keys = set()  # In production, load from secure storage
        self.setup_redis()
    
    def setup_redis(self):
        """Setup Redis connection for rate limiting"""
        try:
            self.redis_client = redis.Redis(
                host='localhost', 
                port=6379, 
                db=1, 
                decode_responses=True,
                socket_connect_timeout=5
            )
            self.redis_client.ping()
            logger.info("Redis connected for security features")
        except Exception as e:
            logger.warning(f"Redis not available, using in-memory rate limiting: {e}")
            self.redis_client = None
    
    def generate_api_key(self) -> str:
        """Generate a secure API key"""
        api_key = f"ap_{secrets.token_urlsafe(32)}"
        self.api_keys.add(api_key)
        return api_key
    
    def validate_api_key(self, api_key: str) -> bool:
        """Validate API key"""
        return api_key in self.api_keys
    
    def hash_password(self, password: str) -> str:
        """Hash password with bcrypt"""
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
    
    def verify_password(self, password: str, hashed: str) -> bool:
        """Verify password against hash"""
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
    
    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """Create JWT access token"""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
    
    def verify_token(self, token: str) -> Optional[dict]:
        """Verify JWT token"""
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            return payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token expired",
                headers={"WWW-Authenticate": "Bearer"},
            )
        except jwt.JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
                headers={"WWW-Authenticate": "Bearer"},
            )
    
    def check_rate_limit(self, client_ip: str, endpoint: str) -> bool:
        """Check if client has exceeded rate limit"""
        key = f"rate_limit:{client_ip}:{endpoint}"
        current_time = int(time.time())
        
        if self.redis_client:
            try:
                # Redis-based rate limiting
                pipe = self.redis_client.pipeline()
                pipe.incr(key)
                pipe.expire(key, RATE_LIMIT_WINDOW)
                results = pipe.execute()
                
                request_count = results[0]
                return request_count <= RATE_LIMIT_REQUESTS
                
            except Exception as e:
                logger.error(f"Redis rate limiting error: {e}")
                # Fall back to in-memory
        
        # In-memory rate limiting fallback
        if key not in self.failed_attempts:
            self.failed_attempts[key] = []
        
        # Clean old entries
        self.failed_attempts[key] = [
            timestamp for timestamp in self.failed_attempts[key]
            if current_time - timestamp < RATE_LIMIT_WINDOW
        ]
        
        # Check rate limit
        if len(self.failed_attempts[key]) >= RATE_LIMIT_REQUESTS:
            return False
        
        # Add current request
        self.failed_attempts[key].append(current_time)
        return True
    
    def validate_file_upload(self, filename: str, content_type: str, file_size: int) -> Tuple[bool, str]:
        """Validate uploaded file for security"""
        # Check file size
        if file_size > MAX_FILE_SIZE:
            return False, f"File size {file_size} exceeds maximum allowed size {MAX_FILE_SIZE}"
        
        # Check content type
        if content_type not in ALLOWED_FILE_TYPES:
            return False, f"File type {content_type} not allowed"
        
        # Check filename for path traversal
        if '..' in filename or '/' in filename or '\\' in filename:
            return False, "Invalid filename - path traversal detected"
        
        # Check for suspicious extensions
        suspicious_extensions = {'.exe', '.bat', '.cmd', '.com', '.scr', '.pif', '.js', '.vbs', '.jar'}
        filename_lower = filename.lower()
        for ext in suspicious_extensions:
            if filename_lower.endswith(ext):
                return False, f"Suspicious file extension: {ext}"
        
        return True, "File validation passed"
    
    def sanitize_input(self, text: str, max_length: int = 10000) -> str:
        """Sanitize user input"""
        if not text:
            return ""
        
        # Truncate if too long
        if len(text) > max_length:
            text = text[:max_length]
        
        # Remove or escape potentially dangerous characters
        # Basic HTML/script tag detection
        dangerous_patterns = ['<script', '</script>', '<iframe', '</iframe>', 'javascript:', 'data:text/html']
        text_lower = text.lower()
        
        for pattern in dangerous_patterns:
            if pattern in text_lower:
                logger.warning(f"Potentially dangerous content detected: {pattern}")
                text = text.replace(pattern, f"[FILTERED:{pattern.upper()}]")
        
        return text.strip()


# Global security manager instance
security_manager = SecurityManager()


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware"""
    
    async def dispatch(self, request: Request, call_next):
        client_ip = self.get_client_ip(request)
        endpoint = request.url.path
        
        # Skip rate limiting for health checks
        if endpoint in ['/health', '/']:
            response = await call_next(request)
            return response
        
        # Check rate limit
        if not security_manager.check_rate_limit(client_ip, endpoint):
            logger.warning(f"Rate limit exceeded for {client_ip} on {endpoint}")
            return JSONResponse(
                status_code=429,
                content={
                    "error": "Rate limit exceeded", 
                    "message": f"Maximum {RATE_LIMIT_REQUESTS} requests per minute allowed"
                },
                headers={"Retry-After": str(RATE_LIMIT_WINDOW)}
            )
        
        response = await call_next(request)
        return response
    
    def get_client_ip(self, request: Request) -> str:
        """Get client IP address"""
        # Check for forwarded IP (behind proxy)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        # Check for real IP (behind proxy)
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        # Fall back to direct client IP
        return request.client.host if request.client else "unknown"


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Security headers middleware"""
    
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        response.headers["X-Permitted-Cross-Domain-Policies"] = "none"
        
        # Remove server information
        if "Server" in response.headers:
            del response.headers["Server"]
        
        return response


# Authentication dependencies
async def get_current_user(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)):
    """Get current authenticated user"""
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Verify token
    payload = security_manager.verify_token(credentials.credentials)
    username = payload.get("sub")
    
    if username is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return {"username": username}


async def get_optional_user(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)):
    """Get user if authenticated, otherwise None"""
    if not credentials:
        return None
    
    try:
        payload = security_manager.verify_token(credentials.credentials)
        username = payload.get("sub")
        return {"username": username} if username else None
    except HTTPException:
        return None


def validate_api_key(api_key: str) -> bool:
    """Validate API key"""
    return security_manager.validate_api_key(api_key)


def secure_filename(filename: str) -> str:
    """Generate secure filename"""
    # Remove path components
    filename = os.path.basename(filename)
    
    # Replace spaces and special characters
    secure_name = "".join(c for c in filename if c.isalnum() or c in ".-_")
    
    # Ensure it's not empty
    if not secure_name:
        secure_name = f"file_{secrets.token_hex(8)}"
    
    return secure_name


def log_security_event(event_type: str, details: dict, severity: str = "INFO"):
    """Log security events"""
    log_entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "event_type": event_type,
        "severity": severity,
        "details": details
    }
    
    if severity == "CRITICAL":
        logger.critical(f"SECURITY: {event_type} - {details}")
    elif severity == "WARNING":
        logger.warning(f"SECURITY: {event_type} - {details}")
    else:
        logger.info(f"SECURITY: {event_type} - {details}")


# Security utilities
def generate_csrf_token() -> str:
    """Generate CSRF token"""
    return secrets.token_urlsafe(32)


def verify_csrf_token(token: str, session_token: str) -> bool:
    """Verify CSRF token"""
    return hmac.compare_digest(token, session_token)


def hash_data(data: str) -> str:
    """Hash sensitive data"""
    return hashlib.sha256(data.encode()).hexdigest()


# Input validation schemas
class SecureRequest:
    """Base class for secure request validation"""
    
    @staticmethod
    def validate_text_input(text: str, max_length: int = 10000) -> str:
        """Validate and sanitize text input"""
        if not isinstance(text, str):
            raise ValueError("Input must be a string")
        
        return security_manager.sanitize_input(text, max_length)
    
    @staticmethod
    def validate_filename(filename: str) -> str:
        """Validate filename"""
        if not filename:
            raise ValueError("Filename cannot be empty")
        
        if len(filename) > 255:
            raise ValueError("Filename too long")
        
        return secure_filename(filename)


# Security monitoring
async def monitor_security_events():
    """Background task to monitor security events"""
    while True:
        try:
            # Check for suspicious activity patterns
            # This could include:
            # - Multiple failed authentication attempts
            # - Unusual file upload patterns
            # - Rate limit violations
            # - Suspicious request patterns
            
            # For now, just log that monitoring is active
            logger.debug("Security monitoring active")
            
            await asyncio.sleep(300)  # Check every 5 minutes
            
        except Exception as e:
            logger.error(f"Security monitoring error: {e}")
            await asyncio.sleep(60)  # Retry after 1 minute


if __name__ == "__main__":
    # Test security features
    print("Testing security features...")
    
    # Test password hashing
    password = "test_password"
    hashed = security_manager.hash_password(password)
    print(f"Password hashed: {security_manager.verify_password(password, hashed)}")
    
    # Test API key generation
    api_key = security_manager.generate_api_key()
    print(f"API key generated: {api_key}")
    print(f"API key valid: {security_manager.validate_api_key(api_key)}")
    
    # Test token creation
    token = security_manager.create_access_token({"sub": "testuser"})
    print(f"Token created: {token[:50]}...")
    
    # Test file validation
    valid, msg = security_manager.validate_file_upload("test.pdf", "application/pdf", 1000)
    print(f"File validation: {valid} - {msg}")
    
    print("Security features tested successfully!")