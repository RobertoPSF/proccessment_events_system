import time


class RateLimiter:
    def __init__(self, rate_per_minute):
        self.rate_per_second = rate_per_minute / 60
        self.tokens = self.rate_per_second
        self.last_check = time.time()

    def allow(self):
        now = time.time()
        elapsed = now - self.last_check

        self.tokens += elapsed * self.rate_per_second
        self.tokens = min(self.tokens, self.rate_per_second)

        self.last_check = now

        if self.tokens >= 1:
            self.tokens -= 1
            return True

        return False