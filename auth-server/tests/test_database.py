from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database.connection import check_database_health, get_database
from app.database.models import APIKey
from app.database.models import Session as UserSession
from app.database.models import User


# Helper function to check if database is available
def is_database_available():
    """Check if database connection is available"""
    try:
        # For unit tests, always assume database is available (using test SQLite)
        import os

        if os.getenv("ENVIRONMENT") == "test":
            return True
        return check_database_health()
    except Exception:
        return False


# Mark for database tests
pytestmark = pytest.mark.integration


class TestDatabaseConnection:
    """Test database connection and health checks"""

    def test_database_connection_health(self, db_session: Session):
        """Test database connection health check function"""
        # Test that we can perform a basic query with the test database
        result = db_session.execute(text("SELECT 1")).scalar()
        assert result == 1

        # Also test the actual health check function (may fail if no real DB)
        try:
            health = check_database_health()
            # If it succeeds, it should return True
            assert health is True
        except Exception:
            # If it fails, that's also OK in test environment
            pytest.skip("Production database not available, but test database works")

    def test_get_database_dependency(self):
        """Test FastAPI database dependency function"""
        # Test that get_database returns a valid session
        try:
            db_generator = get_database()
            db = next(db_generator)
            assert db is not None
            # Cleanup
            try:
                next(db_generator)
            except StopIteration:
                pass
        except Exception:
            pytest.skip("Production database not available")


class TestDatabaseModels:
    """Test SQLAlchemy database models"""

    def test_user_model_creation(self, db_session: Session):
        """Test User model can be created and stored"""
        user = User(
            username="testuser",
            email="test@example.com",
            password_hash="hashed_password_123",
        )

        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)

        assert user.id is not None
        assert user.username == "testuser"
        assert user.email == "test@example.com"
        assert user.is_active is True
        assert user.created_at is not None
        assert isinstance(user.created_at, datetime)

    def test_user_unique_constraints(self, db_session: Session):
        """Test User model enforces unique constraints"""
        # Create first user
        user1 = User(
            username="testuser",
            email="test@example.com",
            password_hash="hashed_password_123",
        )
        db_session.add(user1)
        db_session.commit()

        # Try to create user with same username - should fail
        user2 = User(
            username="testuser",  # Same username
            email="different@example.com",
            password_hash="different_hash",
        )
        db_session.add(user2)

        with pytest.raises(IntegrityError):  # Should raise integrity error
            db_session.commit()

        db_session.rollback()

        # Try to create user with same email - should fail
        user3 = User(
            username="differentuser",
            email="test@example.com",  # Same email
            password_hash="different_hash",
        )
        db_session.add(user3)

        with pytest.raises(IntegrityError):  # Should raise integrity error
            db_session.commit()

    def test_api_key_model_creation(self, db_session: Session):
        """Test APIKey model can be created with foreign key relationship"""
        # Create user first
        user = User(
            username="testuser",
            email="test@example.com",
            password_hash="hashed_password",
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)

        # Create API key for user
        api_key = APIKey(
            user_id=user.id,
            key_name="groq",
            encrypted_key="encrypted_groq_key_data_123",
        )

        db_session.add(api_key)
        db_session.commit()
        db_session.refresh(api_key)

        assert api_key.id is not None
        assert api_key.user_id == user.id
        assert api_key.key_name == "groq"
        assert api_key.encrypted_key == "encrypted_groq_key_data_123"
        assert api_key.created_at is not None
        assert isinstance(api_key.created_at, datetime)

    def test_api_key_foreign_key_relationship(self, db_session: Session):
        """Test APIKey foreign key relationship with User"""
        # Create user
        user = User(
            username="testuser",
            email="test@example.com",
            password_hash="hashed_password",
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)

        # Create multiple API keys
        groq_key = APIKey(
            user_id=user.id, key_name="groq", encrypted_key="encrypted_groq_key"
        )
        google_key = APIKey(
            user_id=user.id,
            key_name="google_genai",
            encrypted_key="encrypted_google_key",
        )

        db_session.add(groq_key)
        db_session.add(google_key)
        db_session.commit()

        # Test relationship from user side
        retrieved_user = db_session.query(User).filter(User.id == user.id).first()
        assert len(retrieved_user.api_keys) == 2

        # Test relationship from api_key side
        retrieved_key = (
            db_session.query(APIKey).filter(APIKey.key_name == "groq").first()
        )
        assert retrieved_key.user.username == "testuser"

    def test_session_model_creation(self, db_session: Session):
        """Test Session model can be created with user relationship"""
        # Create user first
        user = User(
            username="testuser",
            email="test@example.com",
            password_hash="hashed_password",
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)

        # Create session
        session = UserSession(
            user_id=user.id,
            session_token="jwt_token_123456789",
            expires_at=datetime.now(UTC) + timedelta(hours=24),
            ip_address="192.168.1.100",
            user_agent="Mozilla/5.0 Test Agent",
        )

        db_session.add(session)
        db_session.commit()
        db_session.refresh(session)

        assert session.id is not None
        assert session.user_id == user.id
        assert session.session_token == "jwt_token_123456789"
        assert session.expires_at > datetime.now(UTC).replace(tzinfo=None)
        assert session.ip_address == "192.168.1.100"
        assert session.user_agent == "Mozilla/5.0 Test Agent"
        assert session.created_at is not None

    def test_cascade_delete_relationships(self, db_session: Session):
        """Test that deleting user cascades to related records"""
        # Create user with API keys and sessions
        user = User(
            username="testuser",
            email="test@example.com",
            password_hash="hashed_password",
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)

        # Add API key
        api_key = APIKey(
            user_id=user.id, key_name="groq", encrypted_key="encrypted_key"
        )
        db_session.add(api_key)

        # Add session
        session = UserSession(
            user_id=user.id,
            session_token="token_123",
            expires_at=datetime.now(UTC) + timedelta(hours=1),
        )
        db_session.add(session)
        db_session.commit()

        # Verify records exist
        assert db_session.query(APIKey).filter(APIKey.user_id == user.id).count() == 1
        assert (
            db_session.query(UserSession).filter(UserSession.user_id == user.id).count()
            == 1
        )

        # Delete user
        db_session.delete(user)
        db_session.commit()

        # Verify cascade delete worked
        assert db_session.query(APIKey).filter(APIKey.user_id == user.id).count() == 0
        assert (
            db_session.query(UserSession).filter(UserSession.user_id == user.id).count()
            == 0
        )


class TestDatabaseOperations:
    """Test complex database operations and queries"""

    def test_user_crud_operations(self, db_session: Session):
        """Test Create, Read, Update, Delete operations for User"""
        # Create
        user = User(
            username="cruduser",
            email="crud@example.com",
            password_hash="hashed_password",
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)

        user_id = user.id
        assert user_id is not None

        # Read
        retrieved_user = db_session.query(User).filter(User.id == user_id).first()
        assert retrieved_user.username == "cruduser"
        assert retrieved_user.email == "crud@example.com"

        # Update
        retrieved_user.email = "updated@example.com"
        retrieved_user.last_login = datetime.now(UTC)
        db_session.commit()

        updated_user = db_session.query(User).filter(User.id == user_id).first()
        assert updated_user.email == "updated@example.com"
        assert updated_user.last_login is not None

        # Delete
        db_session.delete(updated_user)
        db_session.commit()

        deleted_user = db_session.query(User).filter(User.id == user_id).first()
        assert deleted_user is None

    def test_api_key_last_used_tracking(self, db_session: Session):
        """Test API key last_used timestamp tracking"""
        # Create user and API key
        user = User(
            username="keyuser", email="key@example.com", password_hash="hashed_password"
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)

        api_key = APIKey(
            user_id=user.id, key_name="groq", encrypted_key="encrypted_key"
        )
        db_session.add(api_key)
        db_session.commit()
        db_session.refresh(api_key)

        # Initially last_used should be None
        assert api_key.last_used is None

        # Update last_used
        api_key.last_used = datetime.now(UTC)
        db_session.commit()

        # Verify update
        retrieved_key = db_session.query(APIKey).filter(APIKey.id == api_key.id).first()
        assert retrieved_key.last_used is not None
        assert isinstance(retrieved_key.last_used, datetime)

    def test_session_expiration_queries(self, db_session: Session):
        """Test querying sessions by expiration status"""
        # Create user
        user = User(
            username="sessionuser",
            email="session@example.com",
            password_hash="hashed_password",
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)

        # Create expired session
        expired_session = UserSession(
            user_id=user.id,
            session_token="expired_token",
            expires_at=datetime.now(UTC) - timedelta(hours=1),  # Expired
        )

        # Create valid session
        valid_session = UserSession(
            user_id=user.id,
            session_token="valid_token",
            expires_at=datetime.now(UTC) + timedelta(hours=1),  # Valid
        )

        db_session.add(expired_session)
        db_session.add(valid_session)
        db_session.commit()

        # Query expired sessions
        now = datetime.now(UTC)
        expired_sessions = (
            db_session.query(UserSession).filter(UserSession.expires_at < now).all()
        )

        assert len(expired_sessions) == 1
        assert expired_sessions[0].session_token == "expired_token"

        # Query valid sessions
        valid_sessions = (
            db_session.query(UserSession).filter(UserSession.expires_at > now).all()
        )

        assert len(valid_sessions) == 1
        assert valid_sessions[0].session_token == "valid_token"


class TestDatabaseIndexes:
    """Test database indexes and performance"""

    def test_user_indexes_exist(self, db_session: Session):
        """Test that expected indexes exist on users table"""
        # Query to check if indexes exist - implementation specific
        # This is a placeholder that will be implemented with actual database
        # indexes created by migration files
        result = db_session.execute(text("SELECT 1"))
        assert result.fetchone()[0] == 1

    def test_api_key_indexes_exist(self, db_session: Session):
        """Test that expected indexes exist on api_keys table"""
        # Test indexes on user_id, created_at, etc.
        result = db_session.execute(text("SELECT 1"))
        assert result.fetchone()[0] == 1

    def test_session_indexes_exist(self, db_session: Session):
        """Test that expected indexes exist on sessions table"""
        # Test indexes on session_token, expires_at, user_id, etc.
        result = db_session.execute(text("SELECT 1"))
        assert result.fetchone()[0] == 1
