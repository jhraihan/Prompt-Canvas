import time

from rest_framework.throttling import ScopedRateThrottle

SCOPE = "generation"


def _throttle_for(request):
    throttle = ScopedRateThrottle()
    throttle.scope = SCOPE
    throttle.rate = throttle.get_rate()
    if throttle.rate is None:
        return None, None
    throttle.num_requests, throttle.duration = throttle.parse_rate(throttle.rate)

    class _View:
        throttle_scope = SCOPE

    return throttle, throttle.get_cache_key(request, _View())


def generation_quota(request):
    throttle, key = _throttle_for(request)
    if throttle is None or key is None:
        return None

    now = time.time()
    history = throttle.cache.get(key, [])
    window_start = now - throttle.duration
    active = [stamp for stamp in history if stamp > window_start]

    used = len(active)
    remaining = max(0, throttle.num_requests - used)
    resets_in = int(active[-1] + throttle.duration - now) if active else 0

    return {
        "limit": throttle.num_requests,
        "used": used,
        "remaining": remaining,
        "window_seconds": int(throttle.duration),
        "resets_in_seconds": max(0, resets_in),
    }
