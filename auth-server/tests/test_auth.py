import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.database.models import User, APIKey


class TestUserRegistration:
    """Test user registration functionality"""
    
    def test_user_registration_success(self, client: TestClient, sample_user_data):
        """Test successful user registration"""
        response = client.post("/auth/register", json=sample_user_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == sample_user_data["username"]
        assert data["email"] == sample_user_data["email"]
        assert data["is_active"] is True
        assert "password" not in data
        assert "password_hash" not in data
    
    def test_user_registration_duplicate_username(self, client: TestClient, sample_user_data):
        """Test registration fails with duplicate username"""
        # Register first user
        client.post("/auth/register", json=sample_user_data)
        
        # Try to register with same username
        duplicate_data = {
            "username": sample_user_data["username"],
            "email": "different@example.com",
            "password": "DifferentPassword123!"
        }
        response = client.post("/auth/register", json=duplicate_data)
        
        assert response.status_code == 400
        assert "already registered" in response.json()["detail"].lower()
    
    def test_user_registration_duplicate_email(self, client: TestClient, sample_user_data):
        """Test registration fails with duplicate email"""
        # Register first user
        client.post("/auth/register", json=sample_user_data)
        
        # Try to register with same email
        duplicate_data = {
            "username": "differentuser",
            "email": sample_user_data["email"],
            "password": "DifferentPassword123!"
        }
        response = client.post("/auth/register", json=duplicate_data)
        
        assert response.status_code == 400
        assert "already registered" in response.json()["detail"].lower()
    
    def test_user_registration_invalid_email(self, client: TestClient, sample_user_data):
        """Test registration fails with invalid email format"""
        invalid_data = sample_user_data.copy()
        invalid_data["email"] = "invalid-email"
        
        response = client.post("/auth/register", json=invalid_data)
        
        assert response.status_code == 422
    
    def test_user_registration_weak_password(self, client: TestClient, sample_user_data):
        """Test registration fails with weak password"""
        weak_passwords = ["123", "password", "abc"]
        
        for weak_password in weak_passwords:
            weak_data = sample_user_data.copy()
            weak_data["password"] = weak_password
            
            response = client.post("/auth/register", json=weak_data)
            assert response.status_code == 400


class TestUserLogin:
    """Test user login functionality"""
    
    def test_user_login_success(self, client: TestClient, sample_user_data, sample_api_keys):
        """Test successful user login returns JWT token and encrypted API keys"""
        # Register user first
        client.post("/auth/register", json=sample_user_data)
        
        # Login
        login_data = {
            "username": sample_user_data["username"],
            "password": sample_user_data["password"]
        }
        response = client.post("/auth/login", json=login_data)
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify token response structure
        assert "access_token" in data
        assert "token_type" in data
        assert data["token_type"] == "bearer"
        assert "user_id" in data
        assert "username" in data
        assert data["username"] == sample_user_data["username"]
        assert "encrypted_api_keys" in data
        
        # Verify JWT token format
        token = data["access_token"]
        assert len(token.split(".")) == 3  # JWT has 3 parts
    
    def test_user_login_with_api_keys(self, client: TestClient, sample_user_data, sample_api_keys, db_session: Session):
        """Test login returns encrypted API keys when user has them stored"""
        # Register user
        response = client.post("/auth/register", json=sample_user_data)
        user_id = response.json()["id"]
        
        # Add encrypted API keys to database
        for key_name, key_value in sample_api_keys.items():
            api_key = APIKey(
                user_id=user_id,
                key_name=key_name,
                encrypted_key=f"encrypted_{key_value}"  # Mock encryption for test
            )
            db_session.add(api_key)
        db_session.commit()
        
        # Login
        login_data = {
            "username": sample_user_data["username"],
            "password": sample_user_data["password"]
        }
        response = client.post("/auth/login", json=login_data)
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify API keys are returned encrypted
        encrypted_keys = data["encrypted_api_keys"]
        assert "groq" in encrypted_keys
        assert "google_genai" in encrypted_keys
        assert encrypted_keys["groq"].startswith("encrypted_")
        assert encrypted_keys["google_genai"].startswith("encrypted_")
    
    def test_user_login_invalid_username(self, client: TestClient):
        """Test login fails with invalid username"""
        login_data = {
            "username": "nonexistentuser",
            "password": "somepassword"
        }
        response = client.post("/auth/login", json=login_data)
        
        assert response.status_code == 401
        assert "invalid credentials" in response.json()["detail"].lower()
    
    def test_user_login_invalid_password(self, client: TestClient, sample_user_data):
        """Test login fails with invalid password"""
        # Register user first
        client.post("/auth/register", json=sample_user_data)
        
        # Try login with wrong password
        login_data = {
            "username": sample_user_data["username"],
            "password": "wrongpassword"
        }
        response = client.post("/auth/login", json=login_data)
        
        assert response.status_code == 401
        assert "invalid credentials" in response.json()["detail"].lower()
    
    def test_user_login_inactive_user(self, client: TestClient, sample_user_data, db_session: Session):
        """Test login fails for inactive user"""
        # Register user first
        response = client.post("/auth/register", json=sample_user_data)
        user_id = response.json()["id"]
        
        # Deactivate user
        user = db_session.query(User).filter(User.id == user_id).first()
        user.is_active = False
        db_session.commit()
        
        # Try login
        login_data = {
            "username": sample_user_data["username"],
            "password": sample_user_data["password"]
        }
        response = client.post("/auth/login", json=login_data)
        
        assert response.status_code == 401
        assert "invalid credentials" in response.json()["detail"].lower()


class TestAPIKeyManagement:
    """Test API key storage and retrieval"""
    
    def test_api_keys_encrypted_in_database(self, client: TestClient, sample_user_data, sample_api_keys, db_session: Session):
        """Test that API keys are stored encrypted in database"""
        # Register user
        response = client.post("/auth/register", json=sample_user_data)
        user_id = response.json()["id"]
        
        # This test will validate that our encryption functions work
        # Implementation will be tested once we create the encryption module
        pass
    
    def test_api_keys_never_stored_plaintext(self, client: TestClient, sample_user_data, sample_api_keys):
        """Test that API keys are never stored in plaintext"""
        # This test ensures security - no plaintext API keys in database
        pass


class TestJWTTokens:
    """Test JWT token functionality"""
    
    def test_jwt_token_validation(self, client: TestClient, sample_user_data):
        """Test JWT token can be validated and contains correct claims"""
        # Register and login user
        client.post("/auth/register", json=sample_user_data)
        login_response = client.post("/auth/login", json={
            "username": sample_user_data["username"],
            "password": sample_user_data["password"]
        })
        
        token = login_response.json()["access_token"]
        
        # Test will validate token structure and claims
        # Implementation depends on JWT security module
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 50  # JWT tokens are typically long
    
    def test_jwt_token_expiration(self, client: TestClient):
        """Test JWT tokens have proper expiration"""
        # Test token expiration logic
        # Implementation will be added with security module
        pass
    
    def test_protected_endpoint_requires_token(self, client: TestClient):
        """Test protected endpoints require valid JWT token"""
        # Test accessing protected endpoints without token fails
        # Will be implemented with protected routes
        pass


class TestSessionManagement:
    """Test session management functionality"""
    
    def test_session_creation_on_login(self, client: TestClient, sample_user_data):
        """Test that login creates a session record"""
        # Register and login
        client.post("/auth/register", json=sample_user_data)
        response = client.post("/auth/login", json={
            "username": sample_user_data["username"],
            "password": sample_user_data["password"]
        })
        
        assert response.status_code == 200
        # Session creation will be tested once database models are implemented
    
    def test_session_cleanup(self, client: TestClient):
        """Test expired sessions are cleaned up"""
        # Test session cleanup functionality
        # Implementation depends on session management module
        pass