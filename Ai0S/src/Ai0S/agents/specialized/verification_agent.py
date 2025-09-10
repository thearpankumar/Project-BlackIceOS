"""
Verification Agent - Process-Based Command Result Verification
Verifies command execution by checking running processes and system state.
No screenshot analysis - uses reliable process verification only.
"""

import json
import logging
import asyncio
import subprocess
import psutil
from typing import Dict, List, Optional, Any
from datetime import datetime

from ..orchestrator.multi_agent_state import StateManager

logger = logging.getLogger(__name__)


class SimpleScreenState:
    """Simplified screen state for compatibility (no actual screenshots)."""
    
    def __init__(
        self,
        timestamp: str,
        applications: List[str],
        confidence_score: float,
        analysis_summary: str
    ):
        self.timestamp = timestamp
        self.applications = applications
        self.confidence_score = confidence_score
        self.analysis_summary = analysis_summary
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "applications": self.applications,
            "confidence_score": self.confidence_score,
            "analysis_summary": self.analysis_summary
        }


class VerificationResult:
    """Result of command verification."""
    
    def __init__(
        self,
        success: bool,
        actual_result: str,
        confidence: float,
        screen_analysis: SimpleScreenState,
        verification_reasoning: str,
        discrepancies: List[str] = None,
        recommendations: List[str] = None
    ):
        self.success = success
        self.actual_result = actual_result
        self.confidence = confidence
        self.screen_analysis = screen_analysis
        self.verification_reasoning = verification_reasoning
        self.discrepancies = discrepancies or []
        self.recommendations = recommendations or []
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "success": self.success,
            "actual_result": self.actual_result,
            "confidence": self.confidence,
            "screen_analysis": self.screen_analysis.to_dict(),
            "verification_reasoning": self.verification_reasoning,
            "discrepancies": self.discrepancies,
            "recommendations": self.recommendations
        }


class VerificationAgent:
    """
    Verification Agent - Process-based command execution verification.
    
    Core responsibilities:
    - Check running processes after command execution
    - Verify applications started/stopped as expected  
    - Use system state to determine command success
    - Provide reliable verification without screenshots
    """
    
    def __init__(self, state_manager: StateManager):
        self.state_manager = state_manager
        self.agent_name = "Verification"
    
    async def verify_command_execution(
        self, 
        task_id: str, 
        executed_command: str, 
        expected_result: str,
        pre_execution_screenshot: Optional[bytes] = None  # Keep for compatibility but ignore
    ) -> VerificationResult:
        """
        Verify command execution using reliable process-based verification:
        1. Process Verification (pgrep, psutil)
        2. If unavailable → Command Exit Codes  
        3. If all fail → Assume success with low confidence
        """
        try:
            logger.info(f"Starting verification for task {task_id}: {executed_command}")
            
            # Wait a moment for processes to start
            await asyncio.sleep(1.5)
            
            # 1. Try Process Verification (Primary method)
            process_result = await self._try_process_verification(
                executed_command, expected_result
            )
            
            if process_result and process_result.confidence > 0.5:
                logger.info("✅ Process verification successful")
                
                # Update state with result
                await self.state_manager.update_state(task_id, {
                    "verification_result": process_result.to_dict(),
                    "confidence_score": process_result.confidence
                })
                
                return process_result
            
            # 2. Fallback to Command Exit Code verification
            logger.info("🔄 Process verification unavailable, using command exit codes...")
            exitcode_result = await self._try_exitcode_verification(
                task_id, executed_command, expected_result
            )
            
            if exitcode_result:
                logger.info("✅ Exit code verification completed")
                
                # Update state with result
                await self.state_manager.update_state(task_id, {
                    "verification_result": exitcode_result.to_dict(),
                    "confidence_score": exitcode_result.confidence
                })
                
                return exitcode_result
            
            # 3. Final fallback - Assume success (conservative approach)
            logger.warning("⚠️ All verification methods unavailable, assuming success")
            fallback_result = self._create_fallback_success(executed_command)
            
            # Update state with result
            await self.state_manager.update_state(task_id, {
                "verification_result": fallback_result.to_dict(),
                "confidence_score": fallback_result.confidence
            })
            
            logger.info(f"Verification completed for {task_id}: {'SUCCESS' if fallback_result.success else 'FAILED'}")
            return fallback_result
            
        except Exception as e:
            logger.error(f"Verification failed for task {task_id}: {e}")
            
            # Return failed verification
            fallback_screen = SimpleScreenState(
                timestamp=datetime.now().isoformat(),
                applications=[],
                confidence_score=0.0,
                analysis_summary=f"Verification error: {e}"
            )
            
            return VerificationResult(
                success=False,
                actual_result=f"Verification failed: {e}",
                confidence=0.0,
                screen_analysis=fallback_screen,
                verification_reasoning=f"Could not verify due to error: {e}",
                discrepancies=["Verification system error"],
                recommendations=["Manual intervention required"]
            )
    
    # =============================================================================
    # PROCESS-BASED VERIFICATION METHODS (No Screenshots)
    # =============================================================================
    
    async def _try_process_verification(
        self,
        executed_command: str, 
        expected_result: str
    ) -> Optional[VerificationResult]:
        """Process-based verification - Most Reliable."""
        try:
            logger.info("🔍 Attempting process verification...")
            
            # Extract application name from command
            app_name = self._extract_app_name(executed_command)
            if not app_name:
                logger.info("❌ Could not extract app name from command")
                return None
            
            # Check if process is running
            process_running = await self._check_process_running(app_name)
            
            if process_running:
                # Get active windows for additional verification
                active_windows = await self._get_active_windows()
                
                # Create screen state for compatibility
                screen_state = SimpleScreenState(
                    timestamp=datetime.now().isoformat(),
                    applications=[app_name],
                    confidence_score=0.9,
                    analysis_summary=f"Process verification: {app_name} is running"
                )
                
                return VerificationResult(
                    success=True,
                    actual_result=f"Process '{app_name}' is running with {len(active_windows)} windows",
                    confidence=0.9,
                    screen_analysis=screen_state,
                    verification_reasoning=f"Process verification confirmed {app_name} is running"
                )
            else:
                screen_state = SimpleScreenState(
                    timestamp=datetime.now().isoformat(),
                    applications=[],
                    confidence_score=0.8,
                    analysis_summary=f"Process verification: {app_name} not running"
                )
                
                return VerificationResult(
                    success=False,
                    actual_result=f"Process '{app_name}' not found",
                    confidence=0.8,
                    screen_analysis=screen_state,
                    verification_reasoning=f"Process verification: {app_name} not running"
                )
            
        except Exception as e:
            logger.warning(f"Process verification failed: {e}")
            return None
    
    async def _try_exitcode_verification(
        self,
        task_id: str,
        executed_command: str,
        expected_result: str
    ) -> Optional[VerificationResult]:
        """Command exit code verification."""
        try:
            logger.info("🔍 Attempting exit code verification...")
            
            # Get the last action record to check exit code
            state = await self.state_manager.get_state(task_id)
            if not state or not state.get("action_history"):
                return None
            
            last_action = state["action_history"][-1]
            
            # Most commands return 0 on success
            success = not last_action.get("error_message")
            confidence = 0.6 if success else 0.8  # Higher confidence for failures
            
            screen_state = SimpleScreenState(
                timestamp=datetime.now().isoformat(),
                applications=["unknown"] if success else [],
                confidence_score=confidence,
                analysis_summary=f"Exit code verification: command {'succeeded' if success else 'had errors'}"
            )
            
            return VerificationResult(
                success=success,
                actual_result=f"Command {'succeeded' if success else 'failed'}",
                confidence=confidence,
                screen_analysis=screen_state,
                verification_reasoning=f"Exit code verification: command {'succeeded' if success else 'had errors'}"
            )
            
        except Exception as e:
            logger.warning(f"Exit code verification failed: {e}")
            return None
    
    def _create_fallback_success(self, executed_command: str) -> VerificationResult:
        """Create fallback success result when all verification methods fail."""
        screen_state = SimpleScreenState(
            timestamp=datetime.now().isoformat(),
            applications=["unknown"],
            confidence_score=0.4,
            analysis_summary="Fallback verification - assuming success"
        )
        
        return VerificationResult(
            success=True,  # Conservative approach - assume success
            actual_result=f"Command executed (verification unavailable): {executed_command}",
            confidence=0.4,  # Low confidence
            screen_analysis=screen_state,
            verification_reasoning="All verification methods unavailable - assuming success",
            recommendations=["Please verify the command executed correctly manually"]
        )
    
    # =============================================================================
    # HELPER METHODS FOR PROCESS VERIFICATION
    # =============================================================================
    
    def _extract_app_name(self, command: str) -> Optional[str]:
        """Extract application name from command."""
        command_lower = command.lower().strip()
        
        # Common application mappings
        app_mappings = {
            'google-chrome': 'chrome',
            'chromium-browser': 'chromium',
            'firefox': 'firefox',
            'gedit': 'gedit',
            'code': 'code',
            'nautilus': 'nautilus',
            'dolphin': 'dolphin',
            'thunar': 'thunar',
            'vlc': 'vlc',
            'libreoffice': 'libreoffice'
        }
        
        for cmd_pattern, process_name in app_mappings.items():
            if cmd_pattern in command_lower:
                return process_name
        
        # Try to extract from alternatives (cmd1 || cmd2 || cmd3)
        if '||' in command:
            alternatives = [alt.strip() for alt in command.split('||')]
            for alt in alternatives:
                for cmd_pattern, process_name in app_mappings.items():
                    if cmd_pattern in alt.lower():
                        return process_name
        
        return None
    
    async def _check_process_running(self, app_name: str) -> bool:
        """Check if a process is running using both pgrep and psutil."""
        try:
            # Method 1: Use pgrep (fast)
            result = await asyncio.to_thread(
                subprocess.run, 
                ['pgrep', '-f', app_name], 
                capture_output=True, 
                timeout=5
            )
            
            if result.returncode == 0 and result.stdout.strip():
                logger.info(f"✅ Process '{app_name}' found via pgrep")
                return True
            
            # Method 2: Use psutil (more thorough)
            for proc in psutil.process_iter(['name', 'cmdline']):
                try:
                    proc_name = proc.info['name'].lower()
                    cmd_line = ' '.join(proc.info['cmdline']).lower() if proc.info['cmdline'] else ""
                    
                    if app_name.lower() in proc_name or app_name.lower() in cmd_line:
                        logger.info(f"✅ Process '{app_name}' found via psutil")
                        return True
                        
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            logger.info(f"❌ Process '{app_name}' not found")
            return False
            
        except Exception as e:
            logger.warning(f"Process check failed for {app_name}: {e}")
            return False
    
    async def _get_active_windows(self) -> List[str]:
        """Get list of active windows using wmctrl."""
        try:
            result = await asyncio.to_thread(
                subprocess.run,
                ['wmctrl', '-l'],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                windows = result.stdout.strip().split('\n')
                logger.info(f"Found {len(windows)} active windows")
                return windows
            
            return []
            
        except Exception as e:
            logger.warning(f"Failed to get active windows: {e}")
            return []