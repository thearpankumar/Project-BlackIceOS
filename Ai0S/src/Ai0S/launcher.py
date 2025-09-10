"""
Simplified Application Launcher - Direct Desktop App Launch
Since we removed IPC and integrated all components directly into the desktop app,
this launcher now simply starts the desktop application.
"""

import logging
import sys

from .desktop_app.main_window import SimpleAIDesktopApp
from .config.settings import get_settings

logger = logging.getLogger(__name__)


def main():
    """Main entry point for the simplified application."""
    
    try:
        # Setup basic logging
        settings = get_settings()
        log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
        
        # Ensure log directory exists
        log_path = settings.get_data_paths()["logs"] / "ai0s.log"
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(sys.stdout),
                logging.FileHandler(str(log_path))
            ]
        )
        
        logger.info("Starting AI0S - Simplified Agentic OS Control")
        
        # Start the desktop application directly
        # All AI components (models, orchestrator, tools) are integrated directly
        app = SimpleAIDesktopApp()
        app.mainloop()
        
        logger.info("AI0S application closed")
        return 0
        
    except KeyboardInterrupt:
        logger.info("Application interrupted by user")
        return 0
    except Exception as e:
        import traceback
        logger.error(f"Application failed to start: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return 1


if __name__ == "__main__":
    sys.exit(main())