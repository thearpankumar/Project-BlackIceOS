"""
Application Launcher - Start both backend and desktop app
Coordinates startup of backend service and desktop application.
"""

import asyncio
import logging
import subprocess
import sys
import time
from pathlib import Path
from typing import Optional
import threading

from .backend.main import BackendService
from .desktop_app.main_window import ProfessionalAIDesktopApp
from .config.settings import get_settings

logger = logging.getLogger(__name__)


class ApplicationLauncher:
    """Coordinates startup of backend and desktop components."""
    
    def __init__(self):
        self.settings = get_settings()
        self.backend_service = None
        self.desktop_app = None
        self.backend_task = None
        
        # Setup logging
        self._setup_logging()
    
    def _setup_logging(self) -> None:
        """Setup logging configuration."""
        
        log_level = getattr(logging, self.settings.LOG_LEVEL.upper(), logging.INFO)
        
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(sys.stdout),
                logging.FileHandler(
                    self.settings.get_data_paths()["logs"] / "launcher.log"
                )
            ]
        )
    
    async def start_backend_service(self) -> bool:
        """Start the backend service."""
        
        try:
            logger.info("Starting backend service...")
            
            self.backend_service = BackendService()
            
            # Start backend in background task
            self.backend_task = asyncio.create_task(self.backend_service.start())
            
            # Give backend time to initialize
            await asyncio.sleep(2)
            
            # Check if backend started successfully
            if self.backend_service.running:
                logger.info("Backend service started successfully")
                return True
            else:
                logger.error("Backend service failed to start")
                return False
                
        except Exception as e:
            logger.error(f"Failed to start backend service: {e}")
            return False
    
    def start_desktop_app(self) -> None:
        """Start the desktop application."""
        
        try:
            logger.info("Starting desktop application...")
            
            # Create and run desktop app
            self.desktop_app = ProfessionalAIDesktopApp()
            self.desktop_app.mainloop()
            
        except Exception as e:
            logger.error(f"Desktop application error: {e}")
    
    async def shutdown(self) -> None:
        """Shutdown all services."""
        
        try:
            logger.info("Shutting down services...")
            
            # Shutdown backend service
            if self.backend_service:
                await self.backend_service.shutdown()
            
            # Cancel backend task
            if self.backend_task:
                self.backend_task.cancel()
                try:
                    await self.backend_task
                except asyncio.CancelledError:
                    pass
            
            logger.info("Shutdown complete")
            
        except Exception as e:
            logger.error(f"Shutdown error: {e}")
    
    def run(self) -> None:
        """Run the complete application."""
        
        async def run_with_backend():
            try:
                # Start backend service
                backend_started = await self.start_backend_service()
                
                if not backend_started:
                    logger.error("Cannot start desktop app without backend")
                    return
                
                # Start desktop app in a separate thread
                desktop_thread = threading.Thread(
                    target=self.start_desktop_app,
                    daemon=True
                )
                desktop_thread.start()
                
                # Keep backend running until desktop app closes
                desktop_thread.join()
                
                # Cleanup
                await self.shutdown()
                
            except KeyboardInterrupt:
                logger.info("Application interrupted by user")
                await self.shutdown()
            except Exception as e:
                logger.error(f"Application error: {e}")
                await self.shutdown()
        
        # Run the application
        try:
            asyncio.run(run_with_backend())
        except Exception as e:
            logger.error(f"Failed to run application: {e}")


def main():
    """Main entry point for the application."""
    
    try:
        launcher = ApplicationLauncher()
        launcher.run()
        
    except KeyboardInterrupt:
        logger.info("Application interrupted")
    except Exception as e:
        logger.error(f"Application failed: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())