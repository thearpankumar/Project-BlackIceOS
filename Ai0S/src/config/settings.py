"""
Configuration settings for the Agentic AI OS Control System.
Loads configuration from environment variables and provides typed settings.
"""

import os
from pathlib import Path
from typing import List, Optional, Dict, Any
from pydantic import BaseSettings, Field
from dotenv import load_dotenv


# Load environment variables
load_dotenv()


class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    # =============================================================================
    # AI Models Configuration
    # =============================================================================
    GROQ_API_KEY: str = Field(..., description="Groq API key for intelligence and planning")
    GEMINI_API_KEY: str = Field(..., description="Google Gemini API key for voice transcription")
    
    # Model Selection
    GROQ_MODEL: str = Field(default="llama-3.3-70b-versatile", description="Groq model to use")
    GEMINI_MODEL: str = Field(default="gemini-2.0-flash-exp", description="Gemini model for voice")
    
    # Model Parameters
    AI_TEMPERATURE: float = Field(default=0.1, description="AI model temperature")
    AI_MAX_TOKENS: int = Field(default=4096, description="Maximum tokens per response")
    AI_TIMEOUT: int = Field(default=30, description="AI request timeout in seconds")
    
    # =============================================================================
    # System Configuration
    # =============================================================================
    MAX_PARALLEL_STEPS: int = Field(default=3, description="Maximum parallel execution steps")
    SCREENSHOT_QUALITY: float = Field(default=0.8, description="Screenshot compression quality")
    EXECUTION_TIMEOUT: int = Field(default=30, description="Step execution timeout")
    ENABLE_VOICE: bool = Field(default=True, description="Enable voice input")
    ENABLE_LEARNING: bool = Field(default=True, description="Enable learning from execution")
    
    # =============================================================================
    # Desktop Application Configuration
    # =============================================================================
    # UI Settings
    UI_THEME: str = Field(default="dark", description="Application theme")
    WINDOW_WIDTH: int = Field(default=1400, description="Default window width")
    WINDOW_HEIGHT: int = Field(default=900, description="Default window height")
    SHOW_ADVANCED_LOGS: bool = Field(default=False, description="Show detailed logs in UI")
    ENABLE_NOTIFICATIONS: bool = Field(default=True, description="Enable system notifications")
    FRAMERATE_TARGET: int = Field(default=60, description="Target UI framerate")
    
    # Voice Configuration
    AUDIO_SAMPLE_RATE: int = Field(default=16000, description="Audio sample rate for voice")
    AUDIO_VAD_AGGRESSIVENESS: int = Field(default=3, description="Voice activity detection level")
    AUDIO_SILENCE_DURATION: float = Field(default=3.0, description="Silence duration to stop recording")
    AUDIO_FRAME_DURATION: int = Field(default=30, description="Audio frame duration in ms")
    VOICE_DETECTION_TIMEOUT: int = Field(default=30, description="Voice detection timeout")
    WAKE_WORD_SENSITIVITY: float = Field(default=0.7, description="Wake word detection sensitivity")
    
    # =============================================================================
    # Security & Safety Configuration
    # =============================================================================
    REQUIRE_CONFIRMATION: bool = Field(default=False, description="Require user confirmation for actions")
    MAX_RETRIES: int = Field(default=3, description="Maximum retry attempts")
    
    # Sensitive Operations (comma-separated)
    SENSITIVE_OPERATIONS: str = Field(
        default="delete,uninstall,system_settings,format,shutdown,reboot",
        description="Operations requiring confirmation"
    )
    
    # Blocked Command Patterns
    BLOCKED_PATTERNS: str = Field(
        default="rm -rf,sudo shutdown,mkfs.,dd if=,format ,delete *,chmod 777,passwd",
        description="Dangerous command patterns to block"
    )
    
    # Critical Processes
    CRITICAL_PROCESSES: str = Field(
        default="zoom,teams,skype,discord,obs-studio,firefox,chrome",
        description="Processes that should not be interrupted"
    )
    
    # Permission System
    PERMISSION_VALIDATION_ENABLED: bool = Field(default=True, description="Enable permission validation")
    ACTION_RATE_LIMIT_PER_MINUTE: int = Field(default=100, description="Actions per minute limit")
    ACTION_RATE_LIMIT_PER_SECOND: int = Field(default=10, description="Actions per second limit")
    
    # =============================================================================
    # Platform & Display Configuration
    # =============================================================================
    USER_DISPLAY: str = Field(default=":0", description="User display identifier")
    AI_DISPLAY: str = Field(default=":1", description="AI display identifier")
    SCREEN_RESOLUTION: str = Field(default="1920x1080", description="Screen resolution")
    COLOR_DEPTH: int = Field(default=24, description="Color depth")
    
    # Performance Optimization
    VM_SCREENSHOT_QUALITY: int = Field(default=75, description="VM screenshot quality")
    VM_ANIMATION_DELAY: float = Field(default=0.2, description="Animation delay in VM")
    VM_MAX_CONCURRENT_ACTIONS: int = Field(default=2, description="Max concurrent actions in VM")
    VM_TEMPLATE_CONFIDENCE: float = Field(default=0.75, description="Template matching confidence")
    
    # =============================================================================
    # Paths Configuration
    # =============================================================================
    # Base directory for application data
    BASE_DIR: Path = Field(default=Path.cwd(), description="Base application directory")
    
    # Data directories
    TEMPLATE_BASE_DIR: str = Field(default="templates", description="Template images directory")
    SCREENSHOT_DIR: str = Field(default="screenshots", description="Screenshots directory")
    LOGS_DIR: str = Field(default="logs", description="Logs directory")
    DATA_DIR: str = Field(default="data", description="Application data directory")
    CONFIG_DIR: str = Field(default="config", description="Configuration directory")
    
    # Temporary files
    TEMP_DIR: str = Field(default="/tmp/ai-os-control", description="Temporary files directory")
    
    # Memory persistence
    ENABLE_MEMORY_PERSISTENCE: bool = Field(default=False, description="Enable memory persistence")
    MEMORY_DB_PATH: str = Field(default="data/memory.db", description="Memory database path")
    
    # =============================================================================
    # Communication & IPC Configuration
    # =============================================================================
    # Backend API
    API_HOST: str = Field(default="127.0.0.1", description="API server host")
    API_PORT: int = Field(default=8000, description="API server port")
    API_WORKERS: int = Field(default=1, description="API worker processes")
    
    # WebSocket Communication
    WS_HOST: str = Field(default="127.0.0.1", description="WebSocket host")
    WS_PORT: int = Field(default=8001, description="WebSocket port")
    WS_RECONNECT_ATTEMPTS: int = Field(default=5, description="WebSocket reconnection attempts")
    
    # MCP Server
    MCP_HOST: str = Field(default="127.0.0.1", description="MCP server host")
    MCP_PORT: int = Field(default=9000, description="MCP server port")
    
    # =============================================================================
    # Logging Configuration
    # =============================================================================
    LOG_LEVEL: str = Field(default="INFO", description="Logging level")
    LOG_FILE_PATH: str = Field(default="logs/ai-os-control.log", description="Log file path")
    DEBUG_MODE: bool = Field(default=False, description="Enable debug mode")
    VERBOSE_AUTOMATION: bool = Field(default=False, description="Verbose automation logging")
    
    # Log rotation
    LOG_MAX_SIZE: str = Field(default="10MB", description="Maximum log file size")
    LOG_BACKUP_COUNT: int = Field(default=5, description="Number of backup log files")
    
    # =============================================================================
    # Development & Testing Configuration
    # =============================================================================
    TEST_MODE: bool = Field(default=False, description="Enable test mode")
    MOCK_AUTH_ENABLED: bool = Field(default=False, description="Mock authentication")
    DEV_DISABLE_SAFETY_CHECKS: bool = Field(default=False, description="Disable safety checks for dev")
    PROFILE_PERFORMANCE: bool = Field(default=False, description="Enable performance profiling")
    
    # =============================================================================
    # Advanced Features Configuration
    # =============================================================================
    # Learning System
    ENABLE_WORKFLOW_LEARNING: bool = Field(default=True, description="Enable workflow learning")
    MAX_STORED_WORKFLOWS: int = Field(default=100, description="Maximum stored workflows")
    
    # Context Management
    CONTEXT_WINDOW_SIZE: int = Field(default=10, description="Context window for decision making")
    ENABLE_CONTEXT_PERSISTENCE: bool = Field(default=True, description="Persist context between sessions")
    
    # Performance Monitoring
    ENABLE_METRICS: bool = Field(default=True, description="Enable performance metrics")
    METRICS_RETENTION_DAYS: int = Field(default=30, description="Metrics retention period")
    
    class Config:
        """Pydantic configuration."""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
        validate_assignment = True
    
    def get_sensitive_operations_list(self) -> List[str]:
        """Get list of sensitive operations."""
        return [op.strip() for op in self.SENSITIVE_OPERATIONS.split(",")]
    
    def get_blocked_patterns_list(self) -> List[str]:
        """Get list of blocked command patterns."""
        return [pattern.strip() for pattern in self.BLOCKED_PATTERNS.split(",")]
    
    def get_critical_processes_list(self) -> List[str]:
        """Get list of critical processes."""
        return [process.strip() for process in self.CRITICAL_PROCESSES.split(",")]
    
    def get_data_paths(self) -> Dict[str, Path]:
        """Get all configured data paths."""
        base = Path(self.BASE_DIR)
        return {
            "base": base,
            "templates": base / self.TEMPLATE_BASE_DIR,
            "screenshots": base / self.SCREENSHOT_DIR,
            "logs": base / self.LOGS_DIR,
            "data": base / self.DATA_DIR,
            "config": base / self.CONFIG_DIR,
            "temp": Path(self.TEMP_DIR),
            "memory_db": base / self.MEMORY_DB_PATH if self.ENABLE_MEMORY_PERSISTENCE else None
        }
    
    def ensure_directories(self) -> None:
        """Ensure all required directories exist."""
        paths = self.get_data_paths()
        for name, path in paths.items():
            if path and name != "memory_db":  # Skip database file path
                path.mkdir(parents=True, exist_ok=True)
    
    def get_ui_config(self) -> Dict[str, Any]:
        """Get UI-specific configuration."""
        return {
            "theme": self.UI_THEME,
            "window_size": (self.WINDOW_WIDTH, self.WINDOW_HEIGHT),
            "framerate": self.FRAMERATE_TARGET,
            "show_advanced_logs": self.SHOW_ADVANCED_LOGS,
            "enable_notifications": self.ENABLE_NOTIFICATIONS,
            "voice_enabled": self.ENABLE_VOICE
        }
    
    def get_ai_config(self) -> Dict[str, Any]:
        """Get AI models configuration."""
        return {
            "groq_api_key": self.GROQ_API_KEY,
            "gemini_api_key": self.GEMINI_API_KEY,
            "groq_model": self.GROQ_MODEL,
            "gemini_model": self.GEMINI_MODEL,
            "temperature": self.AI_TEMPERATURE,
            "max_tokens": self.AI_MAX_TOKENS,
            "timeout": self.AI_TIMEOUT
        }
    
    def get_security_config(self) -> Dict[str, Any]:
        """Get security configuration."""
        return {
            "require_confirmation": self.REQUIRE_CONFIRMATION,
            "sensitive_operations": self.get_sensitive_operations_list(),
            "blocked_patterns": self.get_blocked_patterns_list(),
            "critical_processes": self.get_critical_processes_list(),
            "permission_validation": self.PERMISSION_VALIDATION_ENABLED,
            "rate_limits": {
                "per_minute": self.ACTION_RATE_LIMIT_PER_MINUTE,
                "per_second": self.ACTION_RATE_LIMIT_PER_SECOND
            }
        }


# Global settings instance
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Get global settings instance."""
    global _settings
    if _settings is None:
        _settings = Settings()
        _settings.ensure_directories()
    return _settings


def reload_settings() -> Settings:
    """Reload settings from environment."""
    global _settings
    _settings = Settings()
    _settings.ensure_directories()
    return _settings


# Convenience functions for common configurations
def get_ai_config() -> Dict[str, Any]:
    """Get AI models configuration."""
    return get_settings().get_ai_config()


def get_ui_config() -> Dict[str, Any]:
    """Get UI configuration."""
    return get_settings().get_ui_config()


def get_security_config() -> Dict[str, Any]:
    """Get security configuration."""
    return get_settings().get_security_config()


def get_data_paths() -> Dict[str, Path]:
    """Get all data paths."""
    return get_settings().get_data_paths()


if __name__ == "__main__":
    # Test configuration loading
    settings = get_settings()
    print("=== Configuration Loaded ===")
    print(f"AI Models: Groq={settings.GROQ_MODEL}, Gemini={settings.GEMINI_MODEL}")
    print(f"UI Theme: {settings.UI_THEME}")
    print(f"Voice Enabled: {settings.ENABLE_VOICE}")
    print(f"Security: Confirmation={settings.REQUIRE_CONFIRMATION}")
    print(f"Data Paths: {list(settings.get_data_paths().keys())}")
    
    print("\n=== AI Configuration ===")
    ai_config = get_ai_config()
    for key, value in ai_config.items():
        if "api_key" in key:
            print(f"{key}: {'*' * len(str(value)) if value else 'Not set'}")
        else:
            print(f"{key}: {value}")