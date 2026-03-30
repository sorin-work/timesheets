from timesheets.ratelimit import RateLimiter


def test_limiter_allows_up_to_the_limit():
    limiter = RateLimiter(limit=2, window_seconds=60)
    assert limiter.hit("a") is None
    assert limiter.hit("a") is None
    assert limiter.hit("a") > 0
    assert limiter.hit("b") is None


def test_limiter_forgets_old_hits(monkeypatch):
    import timesheets.ratelimit as rl

    now = [1000.0]
    monkeypatch.setattr(rl.time, "monotonic", lambda: now[0])
    limiter = RateLimiter(limit=1, window_seconds=10)
    assert limiter.hit("a") is None
    assert limiter.hit("a") is not None
    now[0] += 10.5
    assert limiter.hit("a") is None


def test_login_is_rate_limited(client):
    payload = {"email": "nobody@example.com", "password": "wrong-password"}
    for _ in range(10):
        assert client.post("/api/auth/login", json=payload).status_code == 401
    r = client.post("/api/auth/login", json=payload)
    assert r.status_code == 429
    assert int(r.headers["retry-after"]) > 0
