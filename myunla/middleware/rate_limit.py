"""Rate limiting middleware for MCP Gateway."""

import asyncio
import time
from collections import defaultdict, deque
from collections.abc import Awaitable, Callable

from fastapi import HTTPException, Request, Response, status
from starlette.middleware.base import BaseHTTPMiddleware

from myunla.models.config import RateLimitConfig
from myunla.utils.logger import get_logger

logger = get_logger(__name__)


class RateLimitError(Exception):
    """Rate limit exceeded error."""

    def __init__(self, message: str, retry_after: int | None = None):
        self.message = message
        self.retry_after = retry_after
        super().__init__(message)


class RateLimiter:
    """Rate limiting implementation using sliding window algorithm."""

    def __init__(self, config: RateLimitConfig):
        self.config = config
        self._requests: dict[str, deque[float]] = defaultdict(deque)
        self._counters: dict[str, int] = defaultdict(int)
        self._lock = asyncio.Lock()

    async def check_rate_limit(
        self, key: str, window: int, max_requests: int
    ) -> bool:
        """Check if the key is within rate limits."""
        if not self.config.enabled:
            return True

        async with self._lock:
            now = time.time()
            cutoff = now - window

            # Remove expired requests
            while self._requests[key] and self._requests[key][0] < cutoff:
                self._requests[key].popleft()

            # Check if limit exceeded
            if len(self._requests[key]) >= max_requests:
                return False

            # Add current request
            self._requests[key].append(now)
            return True

    async def get_remaining_requests(
        self, key: str, window: int, max_requests: int
    ) -> tuple[int, int | None]:
        """Get remaining requests and retry_after time."""
        if not self.config.enabled:
            return max_requests, None

        async with self._lock:
            now = time.time()
            cutoff = now - window

            # Remove expired requests
            while self._requests[key] and self._requests[key][0] < cutoff:
                self._requests[key].popleft()

            current_count = len(self._requests[key])
            remaining = max(0, max_requests - current_count)

            # Calculate retry_after if limit exceeded
            retry_after = None
            if current_count >= max_requests and self._requests[key]:
                retry_after = int(self._requests[key][0] + window - now)

            return remaining, retry_after

    def cleanup(self) -> None:
        """Clean up old request records."""
        now = time.time()
        keys_to_remove = []

        for key, requests in self._requests.items():
            # Remove keys with no recent requests (older than 1 hour)
            if requests and requests[-1] < now - 3600:
                keys_to_remove.append(key)

        for key in keys_to_remove:
            del self._requests[key]


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware for FastAPI."""

    def __init__(self, app, config: RateLimitConfig):
        super().__init__(app)
        self.config = config
        self.limiter = RateLimiter(config)
        self._ip_whitelist: set[str] = set()
        self._api_key_limits: dict[str, dict[str, tuple[int, int]]] = {}

        # Start cleanup task
        asyncio.create_task(self._cleanup_task())

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        """Process request through rate limiting."""

        # Skip rate limiting for health check and public endpoints
        if self._is_public_endpoint(request):
            return await call_next(request)

        # Get client identifier
        client_key = await self._get_client_key(request)

        # Check if IP is whitelisted
        client_ip = self._get_client_ip(request)
        if client_ip in self._ip_whitelist:
            return await call_next(request)

        # Get rate limits for this client
        limits = await self._get_rate_limits(client_key, request)

        # Check rate limits
        for window_name, (window_seconds, max_requests) in limits.items():
            if not await self.limiter.check_rate_limit(
                client_key, window_seconds, max_requests
            ):
                (
                    remaining,
                    retry_after,
                ) = await self.limiter.get_remaining_requests(
                    client_key, window_seconds, max_requests
                )

                logger.warning(
                    f"Rate limit exceeded for {client_key}: {window_name} limit"
                )

                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail={
                        "error": "Rate limit exceeded",
                        "limit_type": window_name,
                        "remaining": remaining,
                        "retry_after": retry_after,
                    },
                    headers={
                        "X-RateLimit-Limit": str(max_requests),
                        "X-RateLimit-Remaining": str(remaining),
                        "X-RateLimit-Reset": (
                            str(retry_after) if retry_after else ""
                        ),
                        "Retry-After": str(retry_after) if retry_after else "",
                    },
                )

        # Add rate limit headers to response
        response = await call_next(request)

        # Add current rate limit info
        for window_name, (window_seconds, max_requests) in limits.items():
            remaining, _ = await self.limiter.get_remaining_requests(
                client_key, window_seconds, max_requests
            )
            response.headers[f"X-RateLimit-{window_name.title()}-Limit"] = str(
                max_requests
            )
            response.headers[f"X-RateLimit-{window_name.title()}-Remaining"] = (
                str(remaining)
            )

        return response

    def _is_public_endpoint(self, request: Request) -> bool:
        """Check if endpoint is public."""
        public_paths = ["/health", "/docs", "/openapi.json", "/redoc"]
        return any(request.url.path.startswith(path) for path in public_paths)

    async def _get_client_key(self, request: Request) -> str:
        """Get unique client identifier for rate limiting."""
        # Try to get API key first
        api_key = request.headers.get("X-API-Key") or request.headers.get(
            "Authorization"
        )
        if api_key:
            return f"api_key:{api_key}"

        # Fall back to IP address
        ip = self._get_client_ip(request)
        return f"ip:{ip}"

    def _get_client_ip(self, request: Request) -> str:
        """Get client IP address."""
        # Check for forwarded IP
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()

        # Check for real IP
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip

        # Use client host
        return request.client.host if request.client else "unknown"

    async def _get_rate_limits(
        self, client_key: str, request: Request
    ) -> dict[str, tuple[int, int]]:
        """Get rate limits for the client."""
        limits = {}

        # Default limits
        limits["minute"] = (60, self.config.requests_per_minute)
        limits["hour"] = (3600, self.config.requests_per_hour)

        # Check for API key specific limits
        if client_key.startswith("api_key:"):
            api_key = client_key[8:]  # Remove "api_key:" prefix
            if api_key in self._api_key_limits:
                custom_limits = self._api_key_limits[api_key]
                for name, (window, max_req) in custom_limits.items():
                    limits[name] = (window, max_req)

        # Burst limit for short bursts
        limits["burst"] = (10, self.config.burst_size)

        return limits

    def add_ip_whitelist(self, ip: str) -> None:
        """Add IP to whitelist."""
        self._ip_whitelist.add(ip)

    def remove_ip_whitelist(self, ip: str) -> None:
        """Remove IP from whitelist."""
        self._ip_whitelist.discard(ip)

    def set_api_key_limit(
        self, api_key: str, limits: dict[str, tuple[int, int]]
    ) -> None:
        """Set custom rate limits for an API key."""
        self._api_key_limits[api_key] = limits

    async def _cleanup_task(self) -> None:
        """Background task to clean up old rate limit records."""
        while True:
            try:
                await asyncio.sleep(3600)  # Run every hour
                self.limiter.cleanup()
                logger.info("Rate limit cleanup completed")
            except Exception as e:
                logger.error(f"Rate limit cleanup error: {e}")


class AbuseDetector:
    """Detects and prevents abuse patterns."""

    def __init__(self) -> None:
        self._suspicious_patterns: dict[str, int] = defaultdict(int)
        self._blocked_ips: set[str] = set()
        self._suspicious_threshold = 10

    def check_request(self, request: Request) -> bool:
        """Check if request appears suspicious."""
        ip = self._get_client_ip(request)

        # Check if IP is blocked
        if ip in self._blocked_ips:
            return False

        # Check for suspicious patterns
        suspicious_score = self._calculate_suspicion_score(request)

        if suspicious_score > 0:
            self._suspicious_patterns[ip] += suspicious_score

            # Block if threshold exceeded
            if self._suspicious_patterns[ip] > self._suspicious_threshold:
                self._blocked_ips.add(ip)
                logger.warning(f"IP blocked for suspicious activity: {ip}")
                return False

        return True

    def _get_client_ip(self, request: Request) -> str:
        """Get client IP address."""
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()

        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip

        return request.client.host if request.client else "unknown"

    def _calculate_suspicion_score(self, request: Request) -> int:
        """Calculate suspicion score for request."""
        score = 0

        # Check for suspicious user agents
        user_agent = request.headers.get("User-Agent", "")
        if not user_agent or len(user_agent) < 10:
            score += 2

        # Check for suspicious headers
        suspicious_headers = ["X-Forwarded-For", "X-Real-IP", "Via"]
        header_count = sum(
            1 for header in suspicious_headers if header in request.headers
        )
        if header_count > 2:
            score += 1

        # Check for rapid endpoint access
        # This would need to be implemented with a more sophisticated tracking system
        # For now, return 0
        return score

    def unblock_ip(self, ip: str) -> None:
        """Unblock an IP address."""
        self._blocked_ips.discard(ip)
        self._suspicious_patterns[ip] = 0
        logger.info(f"IP unblocked: {ip}")

    def get_blocked_ips(self) -> set[str]:
        """Get set of blocked IPs."""
        return self._blocked_ips.copy()
