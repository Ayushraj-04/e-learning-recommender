import time
from collections import defaultdict, deque
from threading import Lock


class TTLCache:
    """Small in-process cache suitable for reducing repeated API calls per instance."""

    def __init__(self, max_size=128):
        self.max_size = max_size
        self._items = {}
        self._lock = Lock()

    def get(self, key):
        with self._lock:
            item = self._items.get(key)
            if not item:
                return None
            expires_at, value = item
            if expires_at <= time.time():
                self._items.pop(key, None)
                return None
            return value

    def set(self, key, value, ttl_seconds):
        with self._lock:
            if len(self._items) >= self.max_size:
                oldest_key = next(iter(self._items), None)
                if oldest_key:
                    self._items.pop(oldest_key, None)
            self._items[key] = (time.time() + ttl_seconds, value)


class RateLimiter:
    """Per-process sliding-window limiter. In serverless deployments it is per instance."""

    def __init__(self, max_requests, window_seconds):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._events = defaultdict(deque)
        self._lock = Lock()

    def allow(self, key):
        now = time.time()
        with self._lock:
            events = self._events[key]
            while events and events[0] <= now - self.window_seconds:
                events.popleft()

            if len(events) >= self.max_requests:
                return False

            events.append(now)
            return True
