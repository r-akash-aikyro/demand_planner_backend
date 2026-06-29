def test_app_imports_and_routes():
    from app.main import app
    paths = set(app.openapi()["paths"].keys())
    assert "/health" in paths
    for frag in ["/api/v1/auth/login", "/api/v1/users", "/api/v1/import/sources",
                 "/api/v1/kpis", "/api/v1/forecasts/generate", "/api/v1/overrides",
                 "/api/v1/traces", "/api/v1/metrics"]:
        assert frag in paths, frag
