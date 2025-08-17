"""Unit tests for rate limiting middleware."""

import asyncio
import time
from unittest.mock import AsyncMock, Mock

import pytest
from fastapi import HTTPException, Request, status

from myunla.middleware.rate_limit import (
    AbuseDetector,
    RateLimiter,
    RateLimitMiddleware,
)
from myunla.models.config import RateLimitConfig


class TestRateLimiter:
    """Test rate limiter functionality."""

    def test_init(self):
        """Test rate limiter initialization."""
        config = RateLimitConfig(requests_per_minute=10)
        limiter = RateLimiter(config)
        assert limiter.config == config
        assert limiter._requests == {}
        assert limiter._counters == {}

    @pytest.mark.asyncio
    async def test_check_rate_limit_within_limit(self):
        """Test rate limiting within limits."""
        config = RateLimitConfig(requests_per_minute=5)
        limiter = RateLimiter(config)
        # Should allow requests within limit
        for i in range(5):
            allowed = await limiter.check_rate_limit("test_key", 60, 5)
            assert allowed is True

    @pytest.mark.asyncio
    async def test_check_rate_limit_exceeded(self):
        """Test rate limiting when limit exceeded."""
        config = RateLimitConfig(requests_per_minute=5)
        limiter = RateLimiter(config)
        # Fill up the limit
        for i in range(5):
            await limiter.check_rate_limit("test_key", 60, 5)
        # Should block request exceeding limit
        allowed = await limiter.check_rate_limit("test_key", 60, 5)
        assert allowed is False

    @pytest.mark.asyncio
    async def test_check_rate_limit_disabled(self):
        """Test rate limiting when disabled."""
        config = RateLimitConfig(enabled=False)
        limiter = RateLimiter(config)
        # Should allow all requests when disabled
        for i in range(10):
            allowed = await limiter.check_rate_limit("test_key", 60, 5)
            assert allowed is True

    @pytest.mark.asyncio
    async def test_get_remaining_requests(self):
        """Test getting remaining requests."""
        config = RateLimitConfig(requests_per_minute=5)
        limiter = RateLimiter(config)
        # Initially should have full allowance
        remaining, retry_after = await limiter.get_remaining_requests(
            "test_key", 60, 5
        )
        assert remaining == 5
        assert retry_after is None
        # Add some requests
        for i in range(3):
            await limiter.check_rate_limit("test_key", 60, 5)
        # Should have reduced remaining
        remaining, retry_after = await limiter.get_remaining_requests(
            "test_key", 60, 5
        )
        assert remaining == 2
        assert retry_after is None
        # Fill up the limit
        for i in range(2):
            await limiter.check_rate_limit("test_key", 60, 5)
        # Should have no remaining and retry_after set
        remaining, retry_after = await limiter.get_remaining_requests(
            "test_key", 60, 5
        )
        assert remaining == 0
        assert retry_after is not None
        assert retry_after > 0

    @pytest.mark.asyncio
    async def test_sliding_window(self):
        """Test sliding window behavior."""
        config = RateLimitConfig(requests_per_minute=2)
        limiter = RateLimiter(config)
        # Fill up the limit
        await limiter.check_rate_limit("test_key", 1, 2)  # 1 second window
        await limiter.check_rate_limit("test_key", 1, 2)
        # Should be blocked
        allowed = await limiter.check_rate_limit("test_key", 1, 2)
        assert allowed is False
        # Wait for window to slide
        await asyncio.sleep(1.1)
        # Should be allowed again
        allowed = await limiter.check_rate_limit("test_key", 1, 2)
        assert allowed is True

    def test_cleanup(self):
        """Test cleanup of old records."""
        config = RateLimitConfig()
        limiter = RateLimiter(config)
        # Add some requests
        limiter._requests["test_key"] = asyncio.run(
            limiter.check_rate_limit("test_key", 60, 5)
        )
        # Manually set old timestamp
        old_time = time.time() - 3700  # More than 1 hour ago
        limiter._requests["test_key"] = [old_time]
        # Cleanup should remove old records
        limiter.cleanup()
        assert "test_key" not in limiter._requests


class TestRateLimitMiddleware:
    """Test rate limiting middleware."""

    @pytest.mark.asyncio
    async def test_public_endpoint(self):
        """Test that public endpoints bypass rate limiting."""
        config = RateLimitConfig(enabled=True)
        middleware = RateLimitMiddleware(None, config)
        request = Mock(spec=Request)
        request.url.path = "/health"
        call_next = AsyncMock()
        call_next.return_value = Mock()
        await middleware.dispatch(request, call_next)
        # Should not call rate limiting for public endpoints
        call_next.assert_called_once_with(request)

    @pytest.mark.asyncio
    async def test_rate_limit_exceeded(self):
        """Test rate limit exceeded response."""
        config = RateLimitConfig(requests_per_minute=1)
        middleware = RateLimitMiddleware(None, config)
        request = Mock(spec=Request)
        request.url.path = "/mcp"
        request.headers = {}
        request.client = Mock()
        request.client.host = "127.0.0.1"
        # First request should pass
        call_next = AsyncMock()
        call_next.return_value = Mock(headers={})
        response = await middleware.dispatch(request, call_next)
        assert response is not None
        # Second request should be rate limited
        with pytest.raises(HTTPException) as exc_info:
            await middleware.dispatch(request, call_next)
        assert exc_info.value.status_code == status.HTTP_429_TOO_MANY_REQUESTS
        assert "Rate limit exceeded" in exc_info.value.detail["error"]
        # Check rate limit headers
        headers = exc_info.value.headers
        assert "X-RateLimit-Limit" in headers
        assert "X-RateLimit-Remaining" in headers
        assert "Retry-After" in headers

    @pytest.mark.asyncio
    async def test_ip_whitelist(self):
        """Test IP whitelist functionality."""
        config = RateLimitConfig(requests_per_minute=1)
        middleware = RateLimitMiddleware(None, config)
        # Add IP to whitelist
        middleware.add_ip_whitelist("127.0.0.1")
        request = Mock(spec=Request)
        request.url.path = "/mcp"
        request.headers = {}
        request.client = Mock()
        request.client.host = "127.0.0.1"
        call_next = AsyncMock()
        call_next.return_value = Mock(headers={})
        # Should allow multiple requests for whitelisted IP
        for i in range(3):
            response = await middleware.dispatch(request, call_next)
            assert response is not None

    @pytest.mark.asyncio
    async def test_api_key_rate_limits(self):
        """Test API key specific rate limits."""
        config = RateLimitConfig(requests_per_minute=1)
        middleware = RateLimitMiddleware(None, config)
        # Set custom limits for API key
        middleware.set_api_key_limit("test_key", {"minute": (60, 5)})
        request = Mock(spec=Request)
        request.url.path = "/mcp"
        request.headers = {"X-API-Key": "test_key"}
        request.client = Mock()
        request.client.host = "127.0.0.1"
        call_next = AsyncMock()
        call_next.return_value = Mock(headers={})
        # Should allow 5 requests with custom limit
        for i in range(5):
            response = await middleware.dispatch(request, call_next)
            assert response is not None
        # 6th request should be blocked
        with pytest.raises(HTTPException) as exc_info:
            await middleware.dispatch(request, call_next)
        assert exc_info.value.status_code == status.HTTP_429_TOO_MANY_REQUESTS

    @pytest.mark.asyncio
    async def test_rate_limit_headers(self):
        """Test rate limit headers in response."""
        config = RateLimitConfig(requests_per_minute=5)
        middleware = RateLimitMiddleware(None, config)
        request = Mock(spec=Request)
        request.url.path = "/mcp"
        request.headers = {}
        request.client = Mock()
        request.client.host = "127.0.0.1"
        call_next = AsyncMock()
        call_next.return_value = Mock(headers={})
        response = await middleware.dispatch(request, call_next)
        # Should have rate limit headers
        assert "X-RateLimit-Minute-Limit" in response.headers
        assert "X-RateLimit-Minute-Remaining" in response.headers
        assert "X-RateLimit-Burst-Limit" in response.headers
        assert "X-RateLimit-Burst-Remaining" in response.headers

    def test_get_client_key(self):
        """Test client key generation."""
        config = RateLimitConfig()
        middleware = RateLimitMiddleware(None, config)
        # Test API key client key
        request = Mock(spec=Request)
        request.headers = {"X-API-Key": "test_key"}
        request.client = Mock()
        request.client.host = "127.0.0.1"
        client_key = asyncio.run(middleware._get_client_key(request))
        assert client_key == "api_key:test_key"
        # Test IP-based client key
        request.headers = {}
        client_key = asyncio.run(middleware._get_client_key(request))
        assert client_key == "ip:127.0.0.1"

    def test_get_client_ip(self):
        """Test client IP extraction."""
        config = RateLimitConfig()
        middleware = RateLimitMiddleware(None, config)
        # Test X-Forwarded-For header
        request = Mock(spec=Request)
        request.headers = {"X-Forwarded-For": "192.168.1.1, 10.0.0.1"}
        request.client = Mock()
        request.client.host = "127.0.0.1"
        ip = middleware._get_client_ip(request)
        assert ip == "192.168.1.1"
        # Test X-Real-IP header
        request.headers = {"X-Real-IP": "192.168.1.1"}
        ip = middleware._get_client_ip(request)
        assert ip == "192.168.1.1"
        # Test fallback to client host
        request.headers = {}
        ip = middleware._get_client_ip(request)
        assert ip == "127.0.0.1"


class TestAbuseDetector:
    """Test abuse detection functionality."""

    def test_init(self):
        """Test abuse detector initialization."""
        detector = AbuseDetector()
        assert detector._suspicious_patterns == {}
        assert detector._blocked_ips == set()
        assert detector._suspicious_threshold == 10

    def test_check_request_normal(self):
        """Test checking normal request."""
        detector = AbuseDetector()
        request = Mock(spec=Request)
        request.headers = {"User-Agent": "Mozilla/5.0 (Test Browser)"}
        request.client = Mock()
        request.client.host = "127.0.0.1"
        result = detector.check_request(request)
        assert result is True

    def test_check_request_blocked_ip(self):
        """Test checking request from blocked IP."""
        detector = AbuseDetector()
        detector._blocked_ips.add("127.0.0.1")
        request = Mock(spec=Request)
        request.headers = {"User-Agent": "Mozilla/5.0 (Test Browser)"}
        request.client = Mock()
        request.client.host = "127.0.0.1"
        result = detector.check_request(request)
        assert result is False

    def test_check_request_suspicious_user_agent(self):
        """Test checking request with suspicious user agent."""
        detector = AbuseDetector()
        request = Mock(spec=Request)
        request.headers = {"User-Agent": ""}
        request.client = Mock()
        request.client.host = "127.0.0.1"
        result = detector.check_request(request)
        assert result is True  # Should still pass, just score increased
        # Check that suspicious score was recorded
        assert "127.0.0.1" in detector._suspicious_patterns
        assert detector._suspicious_patterns["127.0.0.1"] > 0

    def test_check_request_suspicious_headers(self):
        """Test checking request with suspicious headers."""
        detector = AbuseDetector()
        request = Mock(spec=Request)
        request.headers = {
            "User-Agent": "Mozilla/5.0 (Test Browser)",
            "X-Forwarded-For": "192.168.1.1",
            "X-Real-IP": "192.168.1.1",
            "Via": "1.1 proxy",
        }
        request.client = Mock()
        request.client.host = "127.0.0.1"
        result = detector.check_request(request)
        assert result is True
        # Check that suspicious score was recorded
        assert "127.0.0.1" in detector._suspicious_patterns
        assert detector._suspicious_patterns["127.0.0.1"] > 0

    def test_block_ip_threshold(self):
        """Test IP blocking when threshold exceeded."""
        detector = AbuseDetector()
        detector._suspicious_threshold = 5
        # Add suspicious activity below threshold
        detector._suspicious_patterns["127.0.0.1"] = 4
        request = Mock(spec=Request)
        request.headers = {"User-Agent": ""}
        request.client = Mock()
        request.client.host = "127.0.0.1"
        result = detector.check_request(request)
        assert result is True  # Should not be blocked yet
        assert "127.0.0.1" not in detector._blocked_ips
        # Add more suspicious activity to exceed threshold
        detector._suspicious_patterns["127.0.0.1"] = 10
        result = detector.check_request(request)
        assert result is False  # Should be blocked
        assert "127.0.0.1" in detector._blocked_ips

    def test_unblock_ip(self):
        """Test unblocking IP address."""
        detector = AbuseDetector()
        detector._blocked_ips.add("127.0.0.1")
        detector._suspicious_patterns["127.0.0.1"] = 10
        detector.unblock_ip("127.0.0.1")
        assert "127.0.0.1" not in detector._blocked_ips
        assert detector._suspicious_patterns["127.0.0.1"] == 0

    def test_get_blocked_ips(self):
        """Test getting blocked IPs."""
        detector = AbuseDetector()
        detector._blocked_ips.add("127.0.0.1")
        detector._blocked_ips.add("192.168.1.1")
        blocked_ips = detector.get_blocked_ips()
        assert "127.0.0.1" in blocked_ips
        assert "192.168.1.1" in blocked_ips
        assert len(blocked_ips) == 2
