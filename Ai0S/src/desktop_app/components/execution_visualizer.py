"""
Execution Visualizer - Real-time plan visualization and progress tracking
Professional component for displaying task execution plans with live progress updates.
"""

import time
from typing import List, Dict, Any, Optional, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import logging

import customtkinter as ctk
import tkinter as tk
from tkinter import ttk

from ..themes.professional_theme import professional_theme


logger = logging.getLogger(__name__)


class StepStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class ExecutionStep:
    """Represents a single execution step in a plan."""
    id: str
    title: str
    description: str
    status: StepStatus = StepStatus.PENDING
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    progress: float = 0.0  # 0.0 to 1.0
    substeps: List['ExecutionStep'] = None
    metadata: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None


@dataclass
class ExecutionPlan:
    """Represents a complete execution plan."""
    id: str
    title: str
    description: str
    steps: List[ExecutionStep]
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    status: StepStatus = StepStatus.PENDING


class ExecutionVisualizer(ctk.CTkFrame):
    """Professional execution plan visualizer with real-time progress tracking."""
    
    def __init__(self, parent, on_step_click: Callable[[str], None] = None):
        super().__init__(parent)
        
        self.on_step_click = on_step_click
        
        # Execution state
        self.current_plan: Optional[ExecutionPlan] = None
        self.step_widgets: Dict[str, Dict[str, Any]] = {}
        
        # Animation state
        self.animation_running = False
        self.progress_animations = {}
        
        # Setup UI
        self._setup_ui()
    
    def _setup_ui(self) -> None:
        """Setup the execution visualizer UI."""
        
        self.configure(
            corner_radius=12,
            fg_color=professional_theme.get_color("bg_secondary"),
            border_width=1,
            border_color=professional_theme.get_color("border")
        )
        
        # Main container
        self.main_container = ctk.CTkFrame(
            self,
            fg_color="transparent"
        )
        self.main_container.pack(fill="both", expand=True, padx=15, pady=15)
        
        # Header
        self.header_frame = ctk.CTkFrame(
            self.main_container,
            fg_color="transparent",
            height=60
        )
        self.header_frame.pack(fill="x", pady=(0, 15))
        self.header_frame.pack_propagate(False)
        
        # Title and plan info
        self.title_label = ctk.CTkLabel(
            self.header_frame,
            text="Execution Plan",
            font=professional_theme.get_font("heading_small"),
            text_color=professional_theme.get_color("text_primary")
        )
        self.title_label.pack(side="top", anchor="w")
        
        self.plan_info_label = ctk.CTkLabel(
            self.header_frame,
            text="No active plan",
            font=professional_theme.get_font("body_small"),
            text_color=professional_theme.get_color("text_muted")
        )
        self.plan_info_label.pack(side="top", anchor="w", pady=(5, 0))
        
        # Controls
        self.controls_frame = ctk.CTkFrame(
            self.header_frame,
            fg_color="transparent"
        )
        self.controls_frame.pack(side="right", fill="y")
        
        self.pause_button = professional_theme.create_styled_button(
            self.controls_frame,
            text="⏸️",
            style="small",
            command=self._pause_execution,
            width=35
        )
        self.pause_button.pack(side="left", padx=(0, 5))
        
        self.stop_button = professional_theme.create_styled_button(
            self.controls_frame,
            text="⏹️",
            style="small", 
            command=self._stop_execution,
            width=35
        )
        self.stop_button.pack(side="left", padx=(0, 5))
        
        self.clear_button = professional_theme.create_styled_button(
            self.controls_frame,
            text="🗑️",
            style="small",
            command=self._clear_plan,
            width=35
        )
        self.clear_button.pack(side="left")
        
        # Progress overview
        self.overview_frame = ctk.CTkFrame(
            self.main_container,
            corner_radius=8,
            fg_color=professional_theme.get_color("bg_primary"),
            border_width=1,
            border_color=professional_theme.get_color("border"),
            height=80
        )
        self.overview_frame.pack(fill="x", pady=(0, 15))
        self.overview_frame.pack_propagate(False)
        
        # Overall progress
        self.progress_container = ctk.CTkFrame(
            self.overview_frame,
            fg_color="transparent"
        )
        self.progress_container.pack(fill="both", expand=True, padx=15, pady=10)
        
        self.overall_progress_label = ctk.CTkLabel(
            self.progress_container,
            text="Overall Progress: 0%",
            font=professional_theme.get_font("body_medium"),
            text_color=professional_theme.get_color("text_primary")
        )
        self.overall_progress_label.pack(anchor="w")
        
        self.overall_progress_bar = ctk.CTkProgressBar(
            self.progress_container,
            height=20,
            corner_radius=10
        )
        self.overall_progress_bar.pack(fill="x", pady=(5, 0))
        self.overall_progress_bar.set(0)
        
        # Status info
        self.status_container = ctk.CTkFrame(
            self.progress_container,
            fg_color="transparent"
        )
        self.status_container.pack(fill="x", pady=(10, 0))
        
        self.steps_info_label = ctk.CTkLabel(
            self.status_container,
            text="Steps: 0 / 0",
            font=professional_theme.get_font("body_small"),
            text_color=professional_theme.get_color("text_muted")
        )
        self.steps_info_label.pack(side="left")
        
        self.time_info_label = ctk.CTkLabel(
            self.status_container,
            text="Elapsed: --:--",
            font=professional_theme.get_font("body_small"),
            text_color=professional_theme.get_color("text_muted")
        )
        self.time_info_label.pack(side="right")
        
        # Steps container (scrollable)
        self.steps_container = ctk.CTkScrollableFrame(
            self.main_container,
            corner_radius=8,
            fg_color=professional_theme.get_color("bg_primary"),
            border_width=1,
            border_color=professional_theme.get_color("border")
        )
        self.steps_container.pack(fill="both", expand=True)
        
        # Empty state
        self._show_empty_state()
    
    def _show_empty_state(self) -> None:
        """Show empty state when no plan is loaded."""
        
        self.empty_label = ctk.CTkLabel(
            self.steps_container,
            text="No execution plan loaded\nPlans will appear here when tasks are started",
            font=professional_theme.get_font("body_medium"),
            text_color=professional_theme.get_color("text_muted"),
            justify="center"
        )
        self.empty_label.pack(expand=True, pady=50)
    
    def _clear_empty_state(self) -> None:
        """Clear empty state display."""
        
        for widget in self.steps_container.winfo_children():
            widget.destroy()
    
    def load_plan(self, plan: ExecutionPlan) -> None:
        """Load and display an execution plan."""
        
        self.current_plan = plan
        self._clear_empty_state()
        self.step_widgets.clear()
        
        # Update header
        self.title_label.configure(text=plan.title)
        self.plan_info_label.configure(text=plan.description)
        
        # Create step widgets
        for i, step in enumerate(plan.steps):
            self._create_step_widget(step, i)
        
        # Update overall progress
        self._update_overall_progress()
        
        logger.info(f"Loaded execution plan: {plan.title}")
    
    def _create_step_widget(self, step: ExecutionStep, index: int) -> None:
        """Create a widget for displaying a step."""
        
        # Main step container
        step_frame = ctk.CTkFrame(
            self.steps_container,
            corner_radius=8,
            fg_color=professional_theme.get_color("bg_secondary"),
            border_width=1,
            border_color=self._get_step_border_color(step.status),
            height=100
        )
        step_frame.pack(fill="x", padx=10, pady=5)
        step_frame.pack_propagate(False)
        
        # Make clickable
        step_frame.bind("<Button-1>", lambda e: self._on_step_clicked(step.id))
        
        # Step header
        step_header = ctk.CTkFrame(
            step_frame,
            fg_color="transparent",
            height=30
        )
        step_header.pack(fill="x", padx=15, pady=(10, 5))
        step_header.pack_propagate(False)
        
        # Step number and status
        step_number_frame = ctk.CTkFrame(
            step_header,
            fg_color=self._get_step_status_color(step.status),
            corner_radius=15,
            width=30,
            height=30
        )
        step_number_frame.pack(side="left")
        step_number_frame.pack_propagate(False)
        
        step_number_label = ctk.CTkLabel(
            step_number_frame,
            text=str(index + 1),
            font=professional_theme.get_font("body_small"),
            text_color="white"
        )
        step_number_label.pack(expand=True)
        
        # Step title
        step_title_label = ctk.CTkLabel(
            step_header,
            text=step.title,
            font=professional_theme.get_font("body_medium"),
            text_color=professional_theme.get_color("text_primary")
        )
        step_title_label.pack(side="left", padx=(10, 0))
        
        # Status text
        status_label = ctk.CTkLabel(
            step_header,
            text=step.status.value.title(),
            font=professional_theme.get_font("body_small"),
            text_color=self._get_step_status_color(step.status)
        )
        status_label.pack(side="right")
        
        # Step description
        if step.description:
            desc_label = ctk.CTkLabel(
                step_frame,
                text=step.description,
                font=professional_theme.get_font("body_small"),
                text_color=professional_theme.get_color("text_muted"),
                wraplength=400,
                justify="left"
            )
            desc_label.pack(anchor="w", padx=60, pady=(0, 5))
        
        # Progress bar for running steps
        progress_bar = ctk.CTkProgressBar(
            step_frame,
            height=6,
            corner_radius=3
        )
        progress_bar.pack(fill="x", padx=60, pady=(0, 10))
        progress_bar.set(step.progress)
        
        if step.status != StepStatus.RUNNING:
            progress_bar.pack_forget()
        
        # Timing info
        timing_frame = ctk.CTkFrame(
            step_frame,
            fg_color="transparent"
        )
        timing_frame.pack(fill="x", padx=60, pady=(0, 10))
        
        timing_text = self._get_step_timing_text(step)
        timing_label = ctk.CTkLabel(
            timing_frame,
            text=timing_text,
            font=professional_theme.get_font("body_small"),
            text_color=professional_theme.get_color("text_muted")
        )
        timing_label.pack(side="left")
        
        # Error message for failed steps
        if step.status == StepStatus.FAILED and step.error_message:
            error_label = ctk.CTkLabel(
                step_frame,
                text=f"Error: {step.error_message}",
                font=professional_theme.get_font("body_small"),
                text_color=professional_theme.get_color("error"),
                wraplength=400,
                justify="left"
            )
            error_label.pack(anchor="w", padx=60, pady=(0, 5))
        
        # Store widget references
        self.step_widgets[step.id] = {
            "frame": step_frame,
            "status_label": status_label,
            "progress_bar": progress_bar,
            "timing_label": timing_label,
            "number_frame": step_number_frame
        }
    
    def _get_step_border_color(self, status: StepStatus) -> str:
        """Get border color for step based on status."""
        
        colors = {
            StepStatus.PENDING: professional_theme.get_color("border"),
            StepStatus.RUNNING: professional_theme.get_color("primary"),
            StepStatus.COMPLETED: professional_theme.get_color("success"),
            StepStatus.FAILED: professional_theme.get_color("error"),
            StepStatus.SKIPPED: professional_theme.get_color("text_muted")
        }
        
        return colors.get(status, professional_theme.get_color("border"))
    
    def _get_step_status_color(self, status: StepStatus) -> str:
        """Get status color for step."""
        
        colors = {
            StepStatus.PENDING: professional_theme.get_color("text_muted"),
            StepStatus.RUNNING: professional_theme.get_color("primary"),
            StepStatus.COMPLETED: professional_theme.get_color("success"),
            StepStatus.FAILED: professional_theme.get_color("error"),
            StepStatus.SKIPPED: professional_theme.get_color("warning")
        }
        
        return colors.get(status, professional_theme.get_color("text_muted"))
    
    def _get_step_timing_text(self, step: ExecutionStep) -> str:
        """Get timing text for step."""
        
        if step.status == StepStatus.PENDING:
            return "Not started"
        elif step.status == StepStatus.RUNNING:
            if step.start_time:
                elapsed = datetime.now() - step.start_time
                return f"Running for {self._format_duration(elapsed)}"
            return "Running..."
        elif step.status in [StepStatus.COMPLETED, StepStatus.FAILED]:
            if step.start_time and step.end_time:
                duration = step.end_time - step.start_time
                return f"Completed in {self._format_duration(duration)}"
            return "Completed"
        else:
            return "Skipped"
    
    def _format_duration(self, duration: timedelta) -> str:
        """Format duration for display."""
        
        total_seconds = int(duration.total_seconds())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        else:
            return f"{minutes:02d}:{seconds:02d}"
    
    def update_step_status(self, step_id: str, status: StepStatus, 
                          progress: float = 0.0, error_message: str = None) -> None:
        """Update the status of a specific step."""
        
        if not self.current_plan:
            return
        
        # Find and update step in plan
        step = None
        for s in self.current_plan.steps:
            if s.id == step_id:
                step = s
                break
        
        if not step:
            return
        
        # Update step data
        old_status = step.status
        step.status = status
        step.progress = progress
        
        if error_message:
            step.error_message = error_message
        
        # Update timing
        if status == StepStatus.RUNNING and old_status == StepStatus.PENDING:
            step.start_time = datetime.now()
        elif status in [StepStatus.COMPLETED, StepStatus.FAILED] and not step.end_time:
            step.end_time = datetime.now()
        
        # Update UI
        self._update_step_widget(step_id, step)
        self._update_overall_progress()
        
        logger.debug(f"Updated step {step_id} status: {status}")
    
    def _update_step_widget(self, step_id: str, step: ExecutionStep) -> None:
        """Update the visual representation of a step."""
        
        if step_id not in self.step_widgets:
            return
        
        widgets = self.step_widgets[step_id]
        
        # Update status label
        widgets["status_label"].configure(
            text=step.status.value.title(),
            text_color=self._get_step_status_color(step.status)
        )
        
        # Update border color
        widgets["frame"].configure(
            border_color=self._get_step_border_color(step.status)
        )
        
        # Update number frame color
        widgets["number_frame"].configure(
            fg_color=self._get_step_status_color(step.status)
        )
        
        # Update progress bar
        if step.status == StepStatus.RUNNING:
            widgets["progress_bar"].pack(fill="x", padx=60, pady=(0, 10))
            widgets["progress_bar"].set(step.progress)
            
            # Animate progress if needed
            if step_id not in self.progress_animations:
                self._animate_step_progress(step_id)
        else:
            widgets["progress_bar"].pack_forget()
            if step_id in self.progress_animations:
                del self.progress_animations[step_id]
        
        # Update timing
        timing_text = self._get_step_timing_text(step)
        widgets["timing_label"].configure(text=timing_text)
    
    def _animate_step_progress(self, step_id: str) -> None:
        """Animate step progress bar."""
        
        if step_id not in self.step_widgets:
            return
        
        if not self.current_plan:
            return
        
        # Find step
        step = None
        for s in self.current_plan.steps:
            if s.id == step_id:
                step = s
                break
        
        if not step or step.status != StepStatus.RUNNING:
            if step_id in self.progress_animations:
                del self.progress_animations[step_id]
            return
        
        # Update progress bar
        widgets = self.step_widgets[step_id]
        widgets["progress_bar"].set(step.progress)
        
        # Schedule next update
        self.progress_animations[step_id] = True
        self.after(100, lambda: self._animate_step_progress(step_id))
    
    def _update_overall_progress(self) -> None:
        """Update overall progress display."""
        
        if not self.current_plan:
            return
        
        total_steps = len(self.current_plan.steps)
        completed_steps = len([s for s in self.current_plan.steps 
                             if s.status == StepStatus.COMPLETED])
        failed_steps = len([s for s in self.current_plan.steps 
                          if s.status == StepStatus.FAILED])
        
        # Calculate overall progress
        progress = completed_steps / total_steps if total_steps > 0 else 0
        
        # Update progress bar and label
        self.overall_progress_bar.set(progress)
        self.overall_progress_label.configure(
            text=f"Overall Progress: {int(progress * 100)}%"
        )
        
        # Update steps info
        self.steps_info_label.configure(
            text=f"Steps: {completed_steps} / {total_steps} ({failed_steps} failed)"
        )
        
        # Update timing info
        if self.current_plan.started_at:
            if self.current_plan.completed_at:
                duration = self.current_plan.completed_at - self.current_plan.started_at
                timing_text = f"Completed in {self._format_duration(duration)}"
            else:
                elapsed = datetime.now() - self.current_plan.started_at
                timing_text = f"Elapsed: {self._format_duration(elapsed)}"
        else:
            timing_text = "Elapsed: --:--"
        
        self.time_info_label.configure(text=timing_text)
    
    def _on_step_clicked(self, step_id: str) -> None:
        """Handle step click event."""
        
        if self.on_step_click:
            self.on_step_click(step_id)
    
    def _pause_execution(self) -> None:
        """Pause execution (placeholder)."""
        
        logger.info("Execution pause requested")
        # This would integrate with the execution controller
    
    def _stop_execution(self) -> None:
        """Stop execution (placeholder)."""
        
        logger.info("Execution stop requested") 
        # This would integrate with the execution controller
    
    def _clear_plan(self) -> None:
        """Clear the current plan."""
        
        self.current_plan = None
        self.step_widgets.clear()
        self.progress_animations.clear()
        
        # Clear UI
        self._clear_empty_state()
        self._show_empty_state()
        
        # Reset header
        self.title_label.configure(text="Execution Plan")
        self.plan_info_label.configure(text="No active plan")
        
        # Reset progress
        self.overall_progress_bar.set(0)
        self.overall_progress_label.configure(text="Overall Progress: 0%")
        self.steps_info_label.configure(text="Steps: 0 / 0")
        self.time_info_label.configure(text="Elapsed: --:--")
        
        logger.info("Execution plan cleared")
    
    def get_current_plan(self) -> Optional[ExecutionPlan]:
        """Get the currently loaded plan."""
        
        return self.current_plan
    
    def get_plan_summary(self) -> Dict[str, Any]:
        """Get summary of current plan status."""
        
        if not self.current_plan:
            return {"status": "no_plan"}
        
        total_steps = len(self.current_plan.steps)
        status_counts = {}
        
        for status in StepStatus:
            count = len([s for s in self.current_plan.steps if s.status == status])
            status_counts[status.value] = count
        
        progress = status_counts.get("completed", 0) / total_steps if total_steps > 0 else 0
        
        return {
            "plan_id": self.current_plan.id,
            "title": self.current_plan.title,
            "total_steps": total_steps,
            "status_counts": status_counts,
            "overall_progress": progress,
            "started_at": self.current_plan.started_at,
            "completed_at": self.current_plan.completed_at
        }