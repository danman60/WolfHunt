"""Tests for authentication API endpoints."""

import pytest
from fastapi.testclient import TestClient


class TestAuthEndpoints:
    """Test authentication endpoints."""
    
    def test_health_check(self, test_client: TestClient):
        """Test health check endpoint."""
        response = test_client.get("/health")
        assert response.status_code == 200
        
        data = response.json()
        assert "status" in data
        assert "timestamp" in data
        assert "uptime_seconds" in data
    
    def test_register_user(self, test_client: TestClient):
        """Test user registration."""
        user_data = {
            "email": "newuser@test.com",
            "username": "newuser",
            "password": "testpassword123",
            "confirm_password": "testpassword123"
        }
        
        response = test_client.post("/api/auth/register", json=user_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["email"] == user_data["email"]
        assert data["username"] == user_data["username"]
        assert data["is_active"] is True
        assert data["paper_trading_mode"] is True
    
    def test_register_user_password_mismatch(self, test_client: TestClient):
        """Test user registration with password mismatch."""
        user_data = {
            "email": "newuser@test.com",
            "username": "newuser", 
            "password": "testpassword123",
            "confirm_password": "differentpassword"
        }
        
        response = test_client.post("/api/auth/register", json=user_data)
        assert response.status_code == 400
    
    def test_register_duplicate_user(self, test_client: TestClient, test_user):
        """Test registering duplicate user."""
        user_data = {
            "email": test_user.email,
            "username": "differentusername",
            "password": "testpassword123",
            "confirm_password": "testpassword123"
        }
        
        response = test_client.post("/api/auth/register", json=user_data)
        assert response.status_code == 400
    
    def test_login_success(self, test_client: TestClient, test_user):
        """Test successful user login."""
        login_data = {
            "email": test_user.email,
            "password": "testpassword123"
        }
        
        response = test_client.post("/api/auth/login", json=login_data)
        assert response.status_code == 200
        
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["requires_2fa"] is False
    
    def test_login_invalid_credentials(self, test_client: TestClient, test_user):
        """Test login with invalid credentials."""
        login_data = {
            "email": test_user.email,
            "password": "wrongpassword"
        }
        
        response = test_client.post("/api/auth/login", json=login_data)
        assert response.status_code == 401
    
    def test_login_nonexistent_user(self, test_client: TestClient):
        """Test login with nonexistent user."""
        login_data = {
            "email": "nonexistent@test.com",
            "password": "testpassword123"
        }
        
        response = test_client.post("/api/auth/login", json=login_data)
        assert response.status_code == 401
    
    def test_get_current_user(self, authenticated_client: TestClient, test_user):
        """Test getting current user information."""
        response = authenticated_client.get("/api/auth/me")
        assert response.status_code == 200
        
        data = response.json()
        assert data["email"] == test_user.email
        assert data["username"] == test_user.username
        assert data["is_active"] == test_user.is_active
    
    def test_get_current_user_unauthorized(self, test_client: TestClient):
        """Test getting current user without authentication."""
        response = test_client.get("/api/auth/me")
        assert response.status_code == 401
    
    def test_change_password(self, authenticated_client: TestClient):
        """Test password change."""
        password_data = {
            "current_password": "testpassword123",
            "new_password": "newtestpassword123"
        }
        
        response = authenticated_client.post("/api/auth/change-password", json=password_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
    
    def test_change_password_invalid_current(self, authenticated_client: TestClient):
        """Test password change with invalid current password."""
        password_data = {
            "current_password": "wrongpassword",
            "new_password": "newtestpassword123"
        }
        
        response = authenticated_client.post("/api/auth/change-password", json=password_data)
        assert response.status_code == 400
    
    def test_api_keys_status(self, authenticated_client: TestClient):
        """Test API keys status endpoint."""
        response = authenticated_client.get("/api/auth/api-keys/status")
        assert response.status_code == 200
        
        data = response.json()
        assert "success" in data
        assert "data" in data
        assert "has_keys" in data["data"]
    
    def test_logout(self, authenticated_client: TestClient):
        """Test user logout."""
        response = authenticated_client.post("/api/auth/logout")
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True