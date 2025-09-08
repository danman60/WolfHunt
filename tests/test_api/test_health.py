"""Tests for health check API endpoints."""

import pytest
from fastapi.testclient import TestClient


class TestHealthEndpoints:
    """Test health check endpoints."""
    
    def test_basic_health_check(self, test_client: TestClient):
        """Test basic health check endpoint."""
        response = test_client.get("/health")
        assert response.status_code == 200
        
        data = response.json()
        assert "status" in data
        assert "timestamp" in data
        assert "uptime_seconds" in data
    
    def test_health_status_public(self, test_client: TestClient):
        """Test public health status endpoint."""
        response = test_client.get("/api/health/")
        assert response.status_code == 200
        
        data = response.json()
        assert "status" in data
        assert "timestamp" in data
        assert "uptime_seconds" in data
        assert "version" in data
        assert "checks" in data
    
    def test_detailed_health_requires_auth(self, test_client: TestClient):
        """Test that detailed health requires authentication."""
        response = test_client.get("/api/health/detailed")
        assert response.status_code == 401
    
    def test_detailed_health_authenticated(self, authenticated_client: TestClient):
        """Test detailed health check with authentication."""
        response = authenticated_client.get("/api/health/detailed")
        assert response.status_code == 200
        
        data = response.json()
        assert "status" in data
        assert "checks" in data
        assert isinstance(data["checks"], list)
        
        # Check that individual health checks have required fields
        for check in data["checks"]:
            assert "name" in check
            assert "status" in check
            assert "message" in check
            assert "response_time" in check
            assert "timestamp" in check
    
    def test_health_history_requires_auth(self, test_client: TestClient):
        """Test that health history requires authentication."""
        response = test_client.get("/api/health/history")
        assert response.status_code == 401
    
    def test_health_history_authenticated(self, authenticated_client: TestClient):
        """Test health history with authentication."""
        response = authenticated_client.get("/api/health/history?limit=10")
        assert response.status_code == 200
        
        data = response.json()
        assert "history" in data
        assert "total_entries" in data
        assert isinstance(data["history"], list)
    
    def test_system_metrics_requires_auth(self, test_client: TestClient):
        """Test that system metrics require authentication."""
        response = test_client.get("/api/health/metrics")
        assert response.status_code == 401
    
    def test_system_metrics_authenticated(self, authenticated_client: TestClient):
        """Test system metrics with authentication."""
        response = authenticated_client.get("/api/health/metrics?hours=24")
        assert response.status_code == 200
        
        data = response.json()
        assert "trading_summary" in data
        assert "performance_metrics" in data
        assert "current_gauges" in data
        assert "counters" in data
    
    def test_active_alerts_requires_auth(self, test_client: TestClient):
        """Test that active alerts require authentication."""
        response = test_client.get("/api/health/alerts")
        assert response.status_code == 401
    
    def test_active_alerts_authenticated(self, authenticated_client: TestClient):
        """Test active alerts with authentication."""
        response = authenticated_client.get("/api/health/alerts")
        assert response.status_code == 200
        
        data = response.json()
        assert "active_alerts" in data
        assert "count" in data
        assert isinstance(data["active_alerts"], list)
    
    def test_alert_history_authenticated(self, authenticated_client: TestClient):
        """Test alert history with authentication."""
        response = authenticated_client.get("/api/health/alerts/history?hours=24")
        assert response.status_code == 200
        
        data = response.json()
        assert "alert_history" in data
        assert "period_hours" in data
        assert "count" in data
        assert isinstance(data["alert_history"], list)
    
    def test_alert_stats_authenticated(self, authenticated_client: TestClient):
        """Test alert statistics with authentication."""
        response = authenticated_client.get("/api/health/alerts/stats?hours=24")
        assert response.status_code == 200
        
        data = response.json()
        assert "period_hours" in data
        assert "total_alerts" in data
        assert "active_alerts" in data
        assert "severity_breakdown" in data
        assert "component_breakdown" in data
    
    def test_trigger_health_check_requires_auth(self, test_client: TestClient):
        """Test that manual health check trigger requires authentication."""
        response = test_client.post("/api/health/check")
        assert response.status_code == 401
    
    def test_trigger_health_check_authenticated(self, authenticated_client: TestClient):
        """Test manual health check trigger with authentication."""
        response = authenticated_client.post("/api/health/check")
        assert response.status_code == 200
        
        data = response.json()
        assert "success" in data
        assert "message" in data
        assert "status" in data
        assert "checks_performed" in data
    
    def test_readiness_check_public(self, test_client: TestClient):
        """Test Kubernetes-style readiness check."""
        response = test_client.get("/api/health/readiness")
        assert response.status_code == 200
        
        data = response.json()
        assert "status" in data
        assert "ready" in data
        assert isinstance(data["ready"], bool)
    
    def test_liveness_check_public(self, test_client: TestClient):
        """Test Kubernetes-style liveness check."""
        response = test_client.get("/api/health/liveness")
        assert response.status_code == 200
        
        data = response.json()
        assert "status" in data
        assert "live" in data
        assert "uptime_seconds" in data
        assert isinstance(data["live"], bool)
    
    def test_prometheus_metrics_endpoint(self, test_client: TestClient):
        """Test Prometheus metrics endpoint."""
        response = test_client.get("/metrics")
        assert response.status_code == 200
        assert "text/plain" in response.headers["content-type"]