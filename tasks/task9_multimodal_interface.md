# Task 9: Multi-Modal Interface

## What This Task Is About
This task creates the "user gateway" for Kali AI-OS - multiple ways to interact with the system:
- **CLI Interface** - Professional command-line interface with intelligent autocomplete and history
- **GUI Application** - Desktop application with visual workflow editor and real-time monitoring
- **Web Interface** - Browser-based access for remote management and team collaboration
- **Mobile App** - Smartphone/tablet interface for monitoring and lightweight operations
- **Adaptive Selection** - AI automatically chooses the best interface based on context and task

## Why This Task Is Critical
- **Universal Access**: Users can work from any device, anywhere
- **Context Adaptation**: Interface adapts to user's environment and current task
- **Team Collaboration**: Web interface enables team-based security assessments
- **Mobile Monitoring**: Real-time security monitoring from mobile devices

## How to Complete This Task - Step by Step

### Phase 1: Setup Interface Environment (45 minutes)
```bash
# 1. Install interface dependencies (in VM)
sudo apt update
sudo apt install -y nodejs npm python3-tk
pip install fastapi uvicorn websockets
pip install tkinter customtkinter streamlit
pip install flask-socketio eventlet

# 2. Install web development tools
npm install -g create-react-app
npm install -g @ionic/cli

# 3. Create interface directory structure
mkdir -p src/interface/{cli,gui,web,mobile,adaptive}
mkdir -p src/interface/web/{static/{css,js,assets},templates}
mkdir -p tests/interface/{cli,gui,web,mobile}

# 4. Test interface frameworks
python -c "import tkinter; print('GUI framework ready!')"
node --version && echo "Web framework ready!"
```



### Phase 3: Command Line Interface (2.5 hours)
```python
# src/interface/cli/command_interface.py
import cmd
import shlex
import asyncio
from datetime import datetime
from typing import Dict, List, Any, Optional
from rich.console import Console
from rich.table import Table
from rich.progress import Progress
from rich.panel import Panel

class KaliAICommandInterface(cmd.Cmd):
    """Advanced CLI interface for Kali AI-OS"""
    
    def __init__(self, ai_engine, memory_manager, safety_framework):
        super().__init__()
        self.ai_engine = ai_engine
        self.memory = memory_manager
        self.safety = safety_framework
        self.console = Console()
        
        # CLI configuration
        self.intro = self._create_intro_banner()
        self.prompt = '🛡️  kali-ai > '
        self.use_rawinput = True
        
        # Command history and completion
        self.history_manager = CommandHistoryManager()
        self.autocomplete = SmartAutocomplete(ai_engine, memory_manager)
        
        # Session state
        self.current_session = {
            'session_id': self._generate_session_id(),
            'start_time': datetime.now(),
            'commands_executed': 0,
            'active_workflows': [],
            'monitoring_targets': []
        }
        
    def _create_intro_banner(self) -> str:
        """Create welcome banner"""
        return """
┌─────────────────────────────────────────────────────────────┐
│  🛡️  Kali AI-OS - Voice-Controlled Cybersecurity Platform  │
│                                                             │
│  Type 'help' for commands or 'ai <description>' for AI     │
│  assistance. Use 'teach' to demonstrate new workflows.     │
└─────────────────────────────────────────────────────────────┘
        """
        
    def do_ai(self, line: str):
        """Execute AI-powered security operations"""
        """Usage: ai <natural language description of security task>"""
        
        if not line.strip():
            self.console.print("[red]Please describe what you want to do[/red]")
            return
            
        try:
            with self.console.status("[bold blue]AI is processing your request..."):
                # Process natural language request
                ai_response = asyncio.run(
                    self.ai_engine.process_natural_language_request(line.strip())
                )
                
            if ai_response['success']:
                # Display AI's understanding
                self._display_ai_interpretation(ai_response)
                
                # Execute if user confirms
                if self._confirm_execution():
                    execution_result = asyncio.run(
                        self.ai_engine.execute_workflow(ai_response['workflow'])
                    )
                    self._display_execution_results(execution_result)
                else:
                    self.console.print("[yellow]Operation cancelled[/yellow]")
            else:
                self.console.print(f"[red]Error: {ai_response['error']}[/red]")
                
        except Exception as e:
            self.console.print(f"[red]AI processing failed: {str(e)}[/red]")
            
    def do_scan(self, line: str):
        """Perform security scans"""
        """Usage: scan <target> [options]"""
        
        args = shlex.split(line)
        if not args:
            self.console.print("[red]Please specify a target to scan[/red]")
            return
            
        target = args[0]
        options = self._parse_scan_options(args[1:])
        
        # Validate target with safety framework
        validation = self.safety.validate_target(target)
        if not validation['allowed']:
            self.console.print(f"[red]Target not authorized: {validation['reason']}[/red]")
            return
            
        # Execute scan
        try:
            with Progress() as progress:
                scan_task = progress.add_task(f"[cyan]Scanning {target}...", total=100)
                
                scan_result = asyncio.run(
                    self.ai_engine.execute_scan(target, options, progress_callback=
                        lambda p: progress.update(scan_task, completed=p)
                    )
                )
                
            self._display_scan_results(scan_result)
            
        except Exception as e:
            self.console.print(f"[red]Scan failed: {str(e)}[/red]")
            
    def do_teach(self, line: str):
        """Enter teaching mode to demonstrate workflows"""
        """Usage: teach [workflow_name]"""
        
        workflow_name = line.strip() or f"demo_{int(datetime.now().timestamp())}"
        
        self.console.print(Panel(
            f"[bold green]Teaching Mode Activated[/bold green]\n\n"
            f"Workflow: {workflow_name}\n"
            f"1. Perform your security assessment manually\n"
            f"2. AI will learn from your actions\n"
            f"3. Type 'stop_teaching' when complete",
            title="🎓 Teaching Mode"
        ))
        
        # Start recording session
        self.teaching_session = asyncio.run(
            self.ai_engine.start_teaching_session(workflow_name)
        )
        
    def do_stop_teaching(self, line: str):
        """Stop teaching mode and save learned workflow"""
        if not hasattr(self, 'teaching_session'):
            self.console.print("[red]No active teaching session[/red]")
            return
            
        # Stop recording and learn
        result = asyncio.run(
            self.ai_engine.stop_teaching_session(self.teaching_session)
        )
        
        if result['success']:
            self.console.print(Panel(
                f"[bold green]Workflow Learned Successfully![/bold green]\n\n"
                f"Name: {result['workflow_name']}\n"
                f"Steps: {result['steps_count']}\n"
                f"Tools: {', '.join(result['tools_detected'])}\n"
                f"Variations: {result['variations_created']}",
                title="✅ Learning Complete"
            ))
        else:
            self.console.print(f"[red]Teaching failed: {result['error']}[/red]")
            
        delattr(self, 'teaching_session')
        
    def do_workflows(self, line: str):
        """Manage and execute workflows"""
        """Usage: workflows [list|run|edit|delete] [name]"""
        
        args = shlex.split(line)
        action = args[0] if args else 'list'
        
        if action == 'list':
            self._list_workflows()
        elif action == 'run' and len(args) > 1:
            self._run_workflow(args[1])
        elif action == 'edit' and len(args) > 1:
            self._edit_workflow(args[1])
        elif action == 'delete' and len(args) > 1:
            self._delete_workflow(args[1])
        else:
            self.console.print("[red]Usage: workflows [list|run|edit|delete] [name][/red]")
            
    def _list_workflows(self):
        """Display available workflows"""
        workflows = self.memory.get_all_workflows()
        
        if not workflows:
            self.console.print("[yellow]No workflows available[/yellow]")
            return
            
        table = Table(title="Available Workflows")
        table.add_column("Name", style="cyan")
        table.add_column("Category", style="magenta")
        table.add_column("Tools", style="green")
        table.add_column("Success Rate", style="yellow")
        table.add_column("Last Used", style="blue")
        
        for workflow in workflows:
            table.add_row(
                workflow['name'],
                workflow.get('category', 'Unknown'),
                ', '.join(workflow.get('tools_used', [])),
                f"{workflow.get('success_rate', 0)*100:.1f}%",
                workflow.get('last_used', 'Never')
            )
            
        self.console.print(table)
        
    def _display_ai_interpretation(self, ai_response: Dict[str, Any]):
        """Display AI's interpretation of user request"""
        interpretation = ai_response.get('interpretation', {})
        
        panel_content = (
            f"[bold]Intent:[/bold] {interpretation.get('intent', 'Unknown')}\n"
            f"[bold]Target:[/bold] {interpretation.get('target', 'None')}\n"
            f"[bold]Tools:[/bold] {', '.join(interpretation.get('tools', []))}\n"
            f"[bold]Estimated Time:[/bold] {interpretation.get('estimated_duration', 'Unknown')}\n"
        )
        
        if interpretation.get('warnings'):
            panel_content += f"\n[bold red]Warnings:[/bold red]\n"
            for warning in interpretation['warnings']:
                panel_content += f"⚠️  {warning}\n"
                
        self.console.print(Panel(panel_content, title="🤖 AI Understanding"))
        
    def completenames(self, text: str, *ignored) -> List[str]:
        """Intelligent command completion"""
        return self.autocomplete.get_completions(text, self.get_names())
        
    def completedefault(self, text: str, line: str, begidx: int, endidx: int) -> List[str]:
        """Context-aware parameter completion"""
        return self.autocomplete.get_parameter_completions(text, line)
        
    def cmdloop(self, intro=None):
        """Enhanced command loop with error handling"""
        try:
            super().cmdloop(intro)
        except KeyboardInterrupt:
            self.console.print("\n[yellow]Use 'exit' to quit[/yellow]")
            self.cmdloop()
        except Exception as e:
            self.console.print(f"[red]CLI Error: {str(e)}[/red]")
            self.cmdloop()
            
    def do_exit(self, line: str):
        """Exit Kali AI-OS CLI"""
        self.console.print("[cyan]Goodbye! Stay secure! 🛡️[/cyan]")
        return True
```

### Phase 4: Web Interface System (2 hours)
```python
# src/interface/web/web_server.py
from fastapi import FastAPI, WebSocket, HTTPException, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import asyncio
import json
from datetime import datetime
from typing import Dict, List, Any, Optional

class KaliAIWebInterface:
    def __init__(self, ai_engine, memory_manager, safety_framework):
        self.app = FastAPI(title="Kali AI-OS Web Interface", version="1.0")
        self.ai_engine = ai_engine
        self.memory = memory_manager
        self.safety = safety_framework
        
        # Setup static files and templates
        self.app.mount("/static", StaticFiles(directory="src/interface/web/static"), name="static")
        self.templates = Jinja2Templates(directory="src/interface/web/templates")
        
        # WebSocket connections for real-time updates
        self.active_connections: List[WebSocket] = []
        
        # Setup routes
        self._setup_routes()
        
    def _setup_routes(self):
        """Setup all web routes"""
        
        @self.app.get("/")
        async def dashboard(request: Request):
            """Main dashboard page"""
            # Get system status
            system_status = await self._get_system_status()
            
            # Get recent activities
            recent_activities = self.memory.get_recent_activities(limit=10)
            
            # Get active workflows
            active_workflows = await self._get_active_workflows()
            
            return self.templates.TemplateResponse("dashboard.html", {
                "request": request,
                "system_status": system_status,
                "recent_activities": recent_activities,
                "active_workflows": active_workflows
            })
            
        @self.app.post("/api/ai/request")
        async def process_ai_request(request: AIRequestModel):
            """Process natural language AI request"""
            try:
                # Validate request with safety framework
                safety_check = self.safety.validate_request(request.query)
                if not safety_check['allowed']:
                    raise HTTPException(
                        status_code=403, 
                        detail=safety_check['reason']
                    )
                    
                # Process with AI engine
                result = await self.ai_engine.process_natural_language_request(
                    request.query
                )
                
                # Broadcast to connected clients
                await self._broadcast_update({
                    'type': 'ai_request_processed',
                    'result': result
                })
                
                return result
                
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
                
        @self.app.post("/api/workflows/execute")
        async def execute_workflow(workflow_request: WorkflowExecutionModel):
            """Execute a security workflow"""
            try:
                # Get workflow from memory
                workflow = self.memory.get_workflow(workflow_request.workflow_id)
                if not workflow:
                    raise HTTPException(status_code=404, detail="Workflow not found")
                    
                # Validate execution with safety framework
                safety_check = self.safety.validate_workflow_execution(
                    workflow, workflow_request.parameters
                )
                if not safety_check['allowed']:
                    raise HTTPException(
                        status_code=403,
                        detail=safety_check['reason']
                    )
                    
                # Execute workflow
                execution_result = await self.ai_engine.execute_workflow(
                    workflow, 
                    workflow_request.parameters,
                    progress_callback=self._workflow_progress_callback
                )
                
                return execution_result
                
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
                
        @self.app.get("/api/workflows")
        async def get_workflows():
            """Get all available workflows"""
            workflows = self.memory.get_all_workflows()
            return {
                'workflows': workflows,
                'total_count': len(workflows)
            }
            
        @self.app.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket):
            """WebSocket endpoint for real-time updates"""
            await websocket.accept()
            self.active_connections.append(websocket)
            
            try:
                while True:
                    # Keep connection alive and handle messages
                    data = await websocket.receive_text()
                    message = json.loads(data)
                    
                    if message['type'] == 'subscribe_to_workflow':
                        # Subscribe to workflow updates
                        await self._handle_workflow_subscription(websocket, message)
                    elif message['type'] == 'system_status_request':
                        # Send system status update
                        status = await self._get_system_status()
                        await websocket.send_text(json.dumps({
                            'type': 'system_status_update',
                            'data': status
                        }))
                        
            except Exception as e:
                print(f"WebSocket error: {e}")
            finally:
                self.active_connections.remove(websocket)
                
    async def _broadcast_update(self, message: Dict[str, Any]):
        """Broadcast update to all connected clients"""
        if self.active_connections:
            message_text = json.dumps(message)
            disconnected = []
            
            for connection in self.active_connections:
                try:
                    await connection.send_text(message_text)
                except Exception:
                    disconnected.append(connection)
                    
            # Remove disconnected clients
            for connection in disconnected:
                self.active_connections.remove(connection)
                
    async def _workflow_progress_callback(self, progress: Dict[str, Any]):
        """Callback for workflow execution progress"""
        await self._broadcast_update({
            'type': 'workflow_progress',
            'progress': progress
        })
        
    async def _get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status"""
        return {
            'timestamp': datetime.now().isoformat(),
            'ai_engine_status': await self.ai_engine.get_status(),
            'memory_usage': self.memory.get_memory_usage(),
            'safety_status': self.safety.get_status(),
            'active_workflows': len(await self._get_active_workflows()),
            'total_workflows': len(self.memory.get_all_workflows())
        }
        
    def run_server(self, host: str = "0.0.0.0", port: int = 8080):
        """Run the web server"""
        import uvicorn
        uvicorn.run(self.app, host=host, port=port)
```

### Phase 5: GUI Application (1.5 hours)
```python
# src/interface/gui/main_window.py
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import customtkinter as ctk
import asyncio
import threading
from datetime import datetime
from typing import Dict, List, Any, Optional

class KaliAIGUIApp:
    def __init__(self, ai_engine, memory_manager, safety_framework):
        self.ai_engine = ai_engine
        self.memory = memory_manager
        self.safety = safety_framework
        
        # Setup main window
        self.root = ctk.CTk()
        self.root.title("🛡️ Kali AI-OS")
        self.root.geometry("1200x800")
        
        # Configure theme
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        # Initialize components
        self.setup_ui()
        self.setup_event_handlers()
        
        # Background task management
        self.running_tasks = {}
        self.update_thread = None
        
    def setup_ui(self):
        """Setup the user interface"""
        
        # Main container
        self.main_frame = ctk.CTkFrame(self.root)
        self.main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Top toolbar
        self.toolbar = ctk.CTkFrame(self.main_frame, height=60)
        self.toolbar.pack(fill="x", pady=(0, 10))
        
        # AI input section
        self.ai_label = ctk.CTkLabel(self.toolbar, text="🤖 AI Assistant:", font=("Arial", 16, "bold"))
        self.ai_label.pack(side="left", padx=10, pady=15)
        
        self.ai_entry = ctk.CTkEntry(self.toolbar, placeholder_text="Describe your security task...", height=30)
        self.ai_entry.pack(side="left", fill="x", expand=True, padx=10, pady=15)
        
        self.ai_button = ctk.CTkButton(self.toolbar, text="Execute", command=self.execute_ai_request, height=30)
        self.ai_button.pack(side="right", padx=10, pady=15)
        
        # Main content area with tabs
        self.notebook = ttk.Notebook(self.main_frame)
        self.notebook.pack(fill="both", expand=True)
        
        # Dashboard tab
        self.setup_dashboard_tab()
        
        # Workflows tab
        self.setup_workflows_tab()
        
        # Monitoring tab
        self.setup_monitoring_tab()
        
        # Results tab
        self.setup_results_tab()
        
        # Settings tab
        self.setup_settings_tab()
        
    def setup_dashboard_tab(self):
        """Setup dashboard tab"""
        self.dashboard_frame = ctk.CTkFrame(self.notebook)
        self.notebook.add(self.dashboard_frame, text="📊 Dashboard")
        
        # System status panel
        self.status_frame = ctk.CTkFrame(self.dashboard_frame)
        self.status_frame.pack(fill="x", padx=10, pady=10)
        
        self.status_label = ctk.CTkLabel(self.status_frame, text="System Status", font=("Arial", 18, "bold"))
        self.status_label.pack(pady=10)
        
        # Status indicators
        self.status_indicators = ctk.CTkFrame(self.status_frame)
        self.status_indicators.pack(fill="x", padx=10, pady=10)
        
        self.ai_status = self.create_status_indicator("AI Engine", "🟢 Online")
        self.memory_status = self.create_status_indicator("Memory System", "🟢 Active")
        self.safety_status = self.create_status_indicator("Safety Framework", "🟢 Monitoring")
        
        # Recent activities
        self.activities_frame = ctk.CTkFrame(self.dashboard_frame)
        self.activities_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.activities_label = ctk.CTkLabel(self.activities_frame, text="Recent Activities", font=("Arial", 16, "bold"))
        self.activities_label.pack(pady=10)
        
        self.activities_list = tk.Listbox(self.activities_frame, height=10)
        self.activities_list.pack(fill="both", expand=True, padx=10, pady=10)
        
    def setup_workflows_tab(self):
        """Setup workflows management tab"""
        self.workflows_frame = ctk.CTkFrame(self.notebook)
        self.notebook.add(self.workflows_frame, text="⚙️ Workflows")
        
        # Workflow list
        self.workflow_list_frame = ctk.CTkFrame(self.workflows_frame)
        self.workflow_list_frame.pack(side="left", fill="both", expand=True, padx=10, pady=10)
        
        self.workflow_list_label = ctk.CTkLabel(self.workflow_list_frame, text="Available Workflows", font=("Arial", 16, "bold"))
        self.workflow_list_label.pack(pady=10)
        
        self.workflow_listbox = tk.Listbox(self.workflow_list_frame)
        self.workflow_listbox.pack(fill="both", expand=True, padx=10, pady=10)
        self.workflow_listbox.bind("<<ListboxSelect>>", self.on_workflow_select)
        
        # Workflow details panel
        self.workflow_details_frame = ctk.CTkFrame(self.workflows_frame)
        self.workflow_details_frame.pack(side="right", fill="both", expand=True, padx=10, pady=10)
        
        self.workflow_details_label = ctk.CTkLabel(self.workflow_details_frame, text="Workflow Details", font=("Arial", 16, "bold"))
        self.workflow_details_label.pack(pady=10)
        
        self.workflow_details_text = tk.Text(self.workflow_details_frame, height=15, state="disabled")
        self.workflow_details_text.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Workflow action buttons
        self.workflow_buttons_frame = ctk.CTkFrame(self.workflow_details_frame)
        self.workflow_buttons_frame.pack(fill="x", padx=10, pady=10)
        
        self.run_workflow_btn = ctk.CTkButton(self.workflow_buttons_frame, text="Run Workflow", command=self.run_selected_workflow)
        self.run_workflow_btn.pack(side="left", padx=5)
        
        self.edit_workflow_btn = ctk.CTkButton(self.workflow_buttons_frame, text="Edit Workflow", command=self.edit_selected_workflow)
        self.edit_workflow_btn.pack(side="left", padx=5)
        
    def execute_ai_request(self):
        """Execute AI request from the input field"""
        query = self.ai_entry.get().strip()
        if not query:
            messagebox.showwarning("Warning", "Please enter a request")
            return
            
        # Clear input
        self.ai_entry.delete(0, tk.END)
        
        # Execute in background thread
        thread = threading.Thread(target=self._execute_ai_request_async, args=(query,))
        thread.daemon = True
        thread.start()
        
    def _execute_ai_request_async(self, query: str):
        """Execute AI request asynchronously"""
        try:
            # Show processing indicator
            self.root.after(0, lambda: self.ai_button.configure(text="Processing...", state="disabled"))
            
            # Process request
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            result = loop.run_until_complete(
                self.ai_engine.process_natural_language_request(query)
            )
            
            # Update UI with result
            self.root.after(0, lambda: self._handle_ai_result(result))
            
        except Exception as e:
            error_msg = f"AI request failed: {str(e)}"
            self.root.after(0, lambda: messagebox.showerror("Error", error_msg))
        finally:
            self.root.after(0, lambda: self.ai_button.configure(text="Execute", state="normal"))
            
    def _handle_ai_result(self, result: Dict[str, Any]):
        """Handle AI processing result"""
        if result['success']:
            # Show interpretation dialog
            dialog = AIResultDialog(self.root, result)
            if dialog.result:
                # User confirmed execution
                self._execute_workflow_async(result['workflow'])
        else:
            messagebox.showerror("AI Error", result.get('error', 'Unknown error'))
            
    def run(self):
        """Run the GUI application"""
        # Start background update thread
        self.start_background_updates()
        
        # Run main loop
        self.root.mainloop()
        
    def start_background_updates(self):
        """Start background thread for UI updates"""
        def update_loop():
            while True:
                try:
                    # Update workflow list
                    self.root.after(0, self.update_workflow_list)
                    
                    # Update system status
                    self.root.after(0, self.update_system_status)
                    
                    # Update activities
                    self.root.after(0, self.update_recent_activities)
                    
                    time.sleep(5)  # Update every 5 seconds
                    
                except Exception as e:
                    print(f"Background update error: {e}")
                    
        self.update_thread = threading.Thread(target=update_loop)
        self.update_thread.daemon = True
        self.update_thread.start()
```

### Phase 6: Adaptive Interface Selection (1 hour)
```python
# src/interface/adaptive/interface_selector.py
from typing import Dict, List, Any, Optional
from datetime import datetime

class AdaptiveInterfaceSelector:
    def __init__(self, ai_engine):
        self.ai_engine = ai_engine
        self.user_preferences = {}
        self.context_history = []
        
        # Interface capabilities matrix
        self.interface_capabilities = {
            'cli': {
                'automation': 'excellent',
                'speed': 'excellent', 
                'precision': 'excellent',
                'learning_curve': 'steep',
                'mobile_friendly': 'poor',
                'collaborative': 'poor'
            },
            'gui': {
                'automation': 'good',
                'speed': 'good',
                'precision': 'excellent',
                'learning_curve': 'moderate',
                'mobile_friendly': 'poor',
                'collaborative': 'moderate'
            },
            'web': {
                'automation': 'good',
                'speed': 'good',
                'precision': 'good',
                'learning_curve': 'easy',
                'mobile_friendly': 'excellent',
                'collaborative': 'excellent'
            },
            'mobile': {
                'automation': 'limited',
                'speed': 'moderate',
                'precision': 'moderate',
                'learning_curve': 'easy',
                'mobile_friendly': 'excellent',
                'collaborative': 'good'
            }
        }
        
    def select_optimal_interface(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Select the optimal interface based on context"""
        
        # Analyze context factors
        factors = self._analyze_context_factors(context)
        
        # Score each interface
        interface_scores = {}
        for interface, capabilities in self.interface_capabilities.items():
            score = self._calculate_interface_score(interface, capabilities, factors)
            interface_scores[interface] = score
            
        # Select best interface
        optimal_interface = max(interface_scores, key=interface_scores.get)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(interface_scores, factors)
        
        return {
            'recommended_interface': optimal_interface,
            'confidence_score': interface_scores[optimal_interface],
            'all_scores': interface_scores,
            'reasoning': recommendations,
            'fallback_interfaces': self._get_fallback_interfaces(interface_scores)
        }
        
    def _analyze_context_factors(self, context: Dict[str, Any]) -> Dict[str, float]:
        """Analyze context factors that influence interface selection"""
        factors = {
            'task_complexity': 0.5,
            'user_mobility': 0.5,
            'collaboration_needed': 0.5,
            'time_sensitivity': 0.5,
            'device_capability': 0.5,
            'user_expertise': 0.5
        }
        
        # Task complexity
        if context.get('workflow_steps', 0) > 10:
            factors['task_complexity'] = 0.9
        elif context.get('workflow_steps', 0) > 5:
            factors['task_complexity'] = 0.7
            
        # User mobility
        if context.get('location') == 'mobile':
            factors['user_mobility'] = 0.9
        elif context.get('device_type') in ['tablet', 'phone']:
            factors['user_mobility'] = 0.8
            
        # Collaboration needs
        if context.get('team_members', 0) > 1:
            factors['collaboration_needed'] = 0.8
            
        # Time sensitivity
        if context.get('urgency') == 'high':
            factors['time_sensitivity'] = 0.9
            
        # Device capability
        device_type = context.get('device_type', 'desktop')
        if device_type == 'phone':
            factors['device_capability'] = 0.3
        elif device_type == 'tablet':
            factors['device_capability'] = 0.6
            
        return factors
```

### Phase 7: Cross-Interface Integration (1 hour)
```python
# Test complete multi-modal interface system
async def test_complete_interface_system():
    # 1. Initialize interface components
    cli_interface = KaliAICommandInterface(ai_engine, memory_manager, safety_framework)
    web_interface = KaliAIWebInterface(ai_engine, memory_manager, safety_framework)
    gui_interface = KaliAIGUIApp(ai_engine, memory_manager, safety_framework)
    adaptive_selector = AdaptiveInterfaceSelector(ai_engine)
    
    # 2. Test CLI functionality
    cli_result = cli_interface.onecmd("ai scan example.com for vulnerabilities")
    assert cli_result is not None
    
    # 3. Test web API
    web_result = await web_interface.process_ai_request({
        "query": "analyze network security for 192.168.1.0/24"
    })
    assert web_result['success'] == True
    
    # 4. Test adaptive selection
    mobile_context = {
        'device_type': 'phone',
        'location': 'mobile',
        'task_complexity': 'monitoring'
    }
    
    selection = adaptive_selector.select_optimal_interface(mobile_context)
    assert selection['recommended_interface'] in ['web', 'mobile']
    
    print("Multi-modal interface system working correctly!")

# Performance testing
def test_interface_performance():
    # Test interface switching speed
    start_time = time.time()
    
    # Simulate rapid interface switches
    for i in range(100):
        context = {
            'device_type': 'desktop' if i % 2 == 0 else 'mobile',
            'task_complexity': 'simple' if i % 3 == 0 else 'complex'
        }
        selection = adaptive_selector.select_optimal_interface(context)
        
    selection_time = time.time() - start_time
    
    print(f"100 interface selections in {selection_time:.2f}s")
    assert selection_time < 1.0  # Should select interfaces in under 1 second
```

## Overview
Build a comprehensive multi-modal interface system that provides CLI, GUI, web, and mobile access to the Kali AI-OS. This system adapts intelligently to user context, device capabilities, and environmental factors.

## Directory Structure
```
Samsung-AI-os/
├── kali-ai-os/
│   ├── src/
│   │   ├── interface/
│   │   │   ├── __init__.py
│   │   │   ├── cli/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── command_interface.py
│   │   │   │   ├── autocomplete.py
│   │   │   │   ├── history_manager.py
│   │   │   │   ├── output_formatter.py
│   │   │   │   └── session_handler.py
│   │   │   ├── gui/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── main_window.py
│   │   │   │   ├── dashboard.py
│   │   │   │   ├── workflow_editor.py
│   │   │   │   ├── results_viewer.py
│   │   │   │   └── settings_panel.py
│   │   │   ├── web/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── web_server.py
│   │   │   │   ├── api_routes.py
│   │   │   │   ├── websocket_handler.py
│   │   │   │   ├── static/
│   │   │   │   │   ├── css/
│   │   │   │   │   ├── js/
│   │   │   │   │   └── assets/
│   │   │   │   └── templates/
│   │   │   │       ├── dashboard.html
│   │   │   │       ├── workflow.html
│   │   │   │       └── monitoring.html
│   │   │   ├── mobile/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── mobile_api.py
│   │   │   │   ├── push_notifications.py
│   │   │   │   ├── responsive_ui.py
│   │   │   │   └── offline_sync.py
│   │   │   ├── adaptive/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── context_detector.py
│   │   │   │   ├── interface_selector.py
│   │   │   │   ├── preference_learner.py
│   │   │   │   └── accessibility_manager.py
│   │   │   ├── integration/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── command_processor.py
│   │   │   │   ├── response_formatter.py
│   │   │   │   ├── session_synchronizer.py
│   │   │   │   └── state_manager.py
│   │   │   └── config/
│   │   │       ├── __init__.py
│   │   │       ├── interface_config.py
│   │   │       └── theme_manager.py
│   │   └── tests/
│   │       ├── interface/
│   │       │   ├── test_cli_interface.py
│   │       │   ├── test_gui_components.py
│   │       │   ├── test_web_interface.py
│   │       │   ├── test_mobile_interface.py
│   │       │   ├── test_adaptive_selection.py
│   │       │   └── test_interface_integration.py
│   │       └── fixtures/
│   │           ├── test_commands.json
│   │           └── mock_responses.json
```

## Technology Stack
- **CLI**: Click 8.1.0, Rich 13.0.0, prompt_toolkit 3.0.0
- **GUI**: Tkinter, PyQt6, customtkinter
- **Web**: FastAPI 0.104.1, WebSockets, Jinja2 templates
- **Mobile**: PWA, responsive design, service workers
- **Real-time**: WebSocket connections, Server-Sent Events

## Test-First Development

```python
# tests/interface/test_cli_interface.py
import pytest
from unittest.mock import Mock, patch
from src.interface.cli.command_interface import CLIInterface
from src.interface.adaptive.context_detector import ContextDetector

class TestMultiModalInterface:
    
    @pytest.fixture
    def cli_interface(self):
        return CLIInterface()
    
    @pytest.fixture
    def context_detector(self):
        return ContextDetector()

    def test_cli_command_processing(self, cli_interface):
        """Test CLI command processing and response"""
        test_commands = [
            {
                'input': 'scan example.com',
                'expected_action': 'security_scan',
                'expected_target': 'example.com'
            },
            {
                'input': 'teach workflow "nmap setup"',
                'expected_action': 'start_teaching',
                'expected_workflow': 'nmap setup'
            },
            {
                'input': 'show status',
                'expected_action': 'get_status',
                'expected_target': None
            }
        ]
        
        for test in test_commands:
            result = cli_interface.process_command(test['input'])
            
            assert result['success'] == True
            assert result['action'] == test['expected_action']
            if test['expected_target']:
                assert result['target'] == test['expected_target']

    def test_cli_autocomplete(self, cli_interface):
        """Test CLI autocompletion functionality"""
        # Test command completion
        completions = cli_interface.get_completions('sca')
        assert 'scan' in completions
        
        # Test tool name completion
        completions = cli_interface.get_completions('scan with nm')
        assert 'nmap' in completions
        
        # Test parameter completion
        completions = cli_interface.get_completions('scan example.com --')
        assert any('--ports' in c for c in completions)

    def test_cli_history_management(self, cli_interface):
        """Test command history functionality"""
        # Execute commands
        commands = [
            'scan example.com',
            'teach workflow "test setup"',
            'show results'
        ]
        
        for cmd in commands:
            cli_interface.process_command(cmd)
        
        # Test history retrieval
        history = cli_interface.get_command_history()
        assert len(history) == 3
        assert history[-1] == 'show results'
        
        # Test history search
        scan_commands = cli_interface.search_history('scan')
        assert len(scan_commands) == 1
        assert 'example.com' in scan_commands[0]

    def test_gui_dashboard_components(self):
        """Test GUI dashboard component functionality"""
        from src.interface.gui.dashboard import Dashboard
        
        dashboard = Dashboard()
        
        # Test component initialization
        assert dashboard.is_initialized() == True
        
        # Test real-time updates
        test_data = {
            'active_scans': 2,
            'completed_workflows': 15,
            'system_status': 'operational'
        }
        
        dashboard.update_status(test_data)
        
        # Verify updates
        status = dashboard.get_current_status()
        assert status['active_scans'] == 2
        assert status['system_status'] == 'operational'

    def test_web_interface_api(self):
        """Test web interface API endpoints"""
        from src.interface.web.api_routes import APIRoutes
        from fastapi.testclient import TestClient
        
        api_routes = APIRoutes()
        client = TestClient(api_routes.app)
        
        # Test status endpoint
        response = client.get('/api/status')
        assert response.status_code == 200
        assert 'system_status' in response.json()
        
        # Test command execution endpoint
        response = client.post('/api/execute', json={
            'command': 'scan example.com',
            'context': {'user_id': 'test_user'}
        })
        assert response.status_code == 200
        assert response.json()['success'] == True

    def test_websocket_real_time_updates(self):
        """Test WebSocket real-time updates"""
        from src.interface.web.websocket_handler import WebSocketHandler
        
        handler = WebSocketHandler()
        
        # Simulate client connections
        mock_websocket = Mock()
        handler.connect_client(mock_websocket, client_id='test_client')
        
        # Send update
        update_data = {
            'type': 'scan_progress',
            'scan_id': 'scan_001',
            'progress': 50,
            'status': 'running'
        }
        
        handler.broadcast_update(update_data)
        
        # Verify client received update
        mock_websocket.send.assert_called_once()
        sent_data = mock_websocket.send.call_args[0][0]
        assert 'scan_progress' in sent_data

    def test_mobile_responsive_interface(self):
        """Test mobile responsive interface adaptation"""
        from src.interface.mobile.responsive_ui import ResponsiveUI
        
        responsive_ui = ResponsiveUI()
        
        # Test different screen sizes
        mobile_layout = responsive_ui.get_layout(screen_width=375)
        tablet_layout = responsive_ui.get_layout(screen_width=768)
        desktop_layout = responsive_ui.get_layout(screen_width=1920)
        
        # Mobile should have simplified layout
        assert mobile_layout['sidebar'] == 'collapsed'
        assert mobile_layout['navigation'] == 'bottom'
        
        # Desktop should have full layout
        assert desktop_layout['sidebar'] == 'expanded'
        assert desktop_layout['navigation'] == 'top'

    def test_context_adaptive_interface_selection(self, context_detector):
        """Test adaptive interface selection based on context"""
        test_contexts = [
            {
                'environment': 'quiet_office',
                'device': 'laptop',
                'task_complexity': 'high',
                'expected_interface': 'gui'
            },
            {
                'environment': 'noisy_coffeeshop',
                'device': 'laptop',
                'task_complexity': 'simple',
                'expected_interface': 'cli'
            },
            {
                'environment': 'mobile',
                'device': 'phone',
                'task_complexity': 'monitoring',
                'expected_interface': 'mobile_web'
            },
            {
                'environment': 'presentation',
                'device': 'laptop',
                'task_complexity': 'demo',
                'expected_interface': 'gui_fullscreen'
            }
        ]
        
        for context in test_contexts:
            recommended = context_detector.recommend_interface(context)
            assert recommended['primary_interface'] == context['expected_interface']

    def test_cross_interface_session_sync(self):
        """Test session synchronization across interfaces"""
        from src.interface.integration.session_synchronizer import SessionSynchronizer
        
        sync = SessionSynchronizer()
        
        # Start session in CLI
        cli_session = sync.create_session('cli', user_id='test_user')
        
        # Execute command in CLI
        sync.record_action(cli_session['session_id'], {
            'interface': 'cli',
            'action': 'scan_started',
            'details': {'target': 'example.com'}
        })
        
        # Switch to web interface
        web_session = sync.get_or_create_session('web', user_id='test_user')
        
        # Should have access to CLI session data
        session_state = sync.get_session_state(web_session['session_id'])
        assert 'scan_started' in session_state['recent_actions']
        assert session_state['recent_actions']['scan_started']['details']['target'] == 'example.com'

    def test_accessibility_features(self):
        """Test accessibility features across interfaces"""
        from src.interface.adaptive.accessibility_manager import AccessibilityManager
        
        accessibility = AccessibilityManager()
        
        # Test screen reader support
        cli_accessible = accessibility.make_cli_accessible({
            'use_screen_reader': True,
            'high_contrast': True
        })
        
        assert cli_accessible['output_format'] == 'screen_reader_friendly'
        assert cli_accessible['color_scheme'] == 'high_contrast'
        
        # Test motor impairment support
        gui_accessible = accessibility.make_gui_accessible({
            'motor_impairment': True,
            'large_targets': True
        })
        
        assert gui_accessible['button_size'] == 'large'
        assert gui_accessible['click_assistance'] == True

    def test_voice_integration_with_interfaces(self):
        """Test voice command integration across interfaces"""
        from src.interface.integration.command_processor import CommandProcessor
        
        processor = CommandProcessor()
        
        # Test voice command routing
        voice_command = {
            'text': 'scan example.com for vulnerabilities',
            'confidence': 0.95,
            'interface': 'voice'
        }
        
        result = processor.process_voice_command(voice_command)
        
        assert result['success'] == True
        assert result['action'] == 'vulnerability_scan'
        assert result['target'] == 'example.com'
        
        # Should work consistently across interfaces
        cli_result = processor.process_text_command('scan example.com for vulnerabilities')
        assert cli_result['action'] == result['action']

    def test_interface_performance_optimization(self):
        """Test interface performance under load"""
        from src.interface.web.web_server import WebServer
        import asyncio
        import time
        
        web_server = WebServer()
        
        async def simulate_concurrent_requests():
            tasks = []
            for i in range(100):
                task = web_server.handle_request({
                    'endpoint': '/api/status',
                    'method': 'GET',
                    'client_id': f'client_{i}'
                })
                tasks.append(task)
            
            start_time = time.time()
            results = await asyncio.gather(*tasks)
            end_time = time.time()
            
            # Should handle 100 concurrent requests in under 2 seconds
            assert (end_time - start_time) < 2.0
            assert all(r['success'] for r in results)
        
        asyncio.run(simulate_concurrent_requests())

    def test_offline_capability(self):
        """Test offline functionality for mobile interface"""
        from src.interface.mobile.offline_sync import OfflineSync
        
        offline_sync = OfflineSync()
        
        # Store data for offline use
        offline_data = {
            'workflow_templates': ['nmap_scan', 'web_test'],
            'recent_results': [{'scan_id': '001', 'status': 'completed'}],
            'cached_responses': {'status': 'offline_mode'}
        }
        
        offline_sync.store_offline_data(offline_data)
        
        # Simulate offline mode
        offline_sync.enable_offline_mode()
        
        # Should be able to access cached data
        cached_workflows = offline_sync.get_offline_workflows()
        assert 'nmap_scan' in cached_workflows
        
        # Should queue actions for later sync
        offline_sync.queue_action({
            'action': 'scan_request',
            'target': 'example.com',
            'timestamp': time.time()
        })
        
        queued_actions = offline_sync.get_queued_actions()
        assert len(queued_actions) == 1

    def test_multi_language_support(self):
        """Test multi-language interface support"""
        from src.interface.adaptive.language_manager import LanguageManager
        
        lang_manager = LanguageManager()
        
        # Test different languages
        languages = ['en', 'es', 'fr', 'de', 'zh']
        
        for lang in languages:
            translations = lang_manager.get_translations(lang)
            
            # Should have basic UI translations
            assert 'scan' in translations
            assert 'status' in translations
            assert 'settings' in translations
            
            # Test command translation
            english_command = 'scan example.com'
            localized_command = lang_manager.localize_command(english_command, lang)
            
            # Should maintain functionality regardless of language
            normalized = lang_manager.normalize_command(localized_command, lang)
            assert normalized == english_command

    def test_theme_and_customization(self):
        """Test theme and UI customization"""
        from src.interface.config.theme_manager import ThemeManager
        
        theme_manager = ThemeManager()
        
        # Test built-in themes
        dark_theme = theme_manager.get_theme('dark')
        light_theme = theme_manager.get_theme('light')
        hacker_theme = theme_manager.get_theme('hacker')
        
        assert dark_theme['background'] != light_theme['background']
        assert hacker_theme['font_family'] == 'monospace'
        
        # Test custom theme creation
        custom_theme = {
            'name': 'custom_blue',
            'colors': {
                'primary': '#0066cc',
                'secondary': '#004499',
                'background': '#001122'
            }
        }
        
        theme_manager.create_custom_theme(custom_theme)
        retrieved_theme = theme_manager.get_theme('custom_blue')
        
        assert retrieved_theme['colors']['primary'] == '#0066cc'
```



## Testing Strategy

### Unit Tests (85% coverage minimum)
```bash
cd kali-ai-os
python -m pytest tests/interface/ -v --cov=src.interface --cov-report=html

# Test categories:
# - CLI functionality and autocomplete
# - GUI component behavior
# - Web API endpoints and WebSockets
# - Mobile responsive design
# - Interface adaptation logic
# - Cross-interface synchronization
```

### UI/UX Tests
```bash
# Test interface responsiveness
python scripts/test_interface_performance.py

# Test accessibility compliance
python scripts/test_accessibility.py

# Test cross-browser compatibility
python scripts/test_browser_compatibility.py
```

## Deployment & Validation

### Setup Commands
```bash
# 1. Install interface dependencies
pip install click rich prompt-toolkit fastapi uvicorn
pip install customtkinter tkinter websockets

# 2. Setup web assets
mkdir -p src/interface/web/static/{css,js,assets}
mkdir -p src/interface/web/templates

# 3. Test all interfaces
python -c "
from src.interface.cli.command_interface import CLIInterface
from src.interface.gui.dashboard import Dashboard
from src.interface.web.web_server import WebServer

cli = CLIInterface()
print('CLI interface ready!')

# Test web server
web = WebServer()
print('Web interface ready!')
"

# 4. Run interface tests
python -m pytest tests/interface/ -v
```

### Success Metrics
- ✅ All interface modes functional
- ✅ Cross-interface session sync working
- ✅ Adaptive interface selection accurate
- ✅ Accessibility compliance verified
- ✅ Performance under load tested
- ✅ Ready for system integration

## Configuration Files

### interface_config.py
```python
INTERFACE_CONFIG = {
    'cli': {
        'prompt': 'kali-ai> ',
        'history_size': 1000,
        'autocomplete': True,
        'color_output': True
    },
    'gui': {
        'theme': 'dark',
        'window_size': '1200x800',
        'real_time_updates': True,
        'animation_enabled': True
    },
    'web': {
        'host': '0.0.0.0',
        'port': 8080,
        'websocket_enabled': True,
        'compression': True
    },
    'mobile': {
        'pwa_enabled': True,
        'offline_mode': True,
        'push_notifications': True,
        'responsive_breakpoints': {
            'mobile': 480,
            'tablet': 768,
            'desktop': 1024
        }
    },
    'adaptive': {
        'context_learning': True,
        'preference_tracking': True,
        'automatic_switching': False,
        'fallback_enabled': True
    }
}
```

## Next Steps
After completing this task:
1. Integrate all interface modes with core system
2. Optimize performance and user experience
3. Create comprehensive user documentation
4. Proceed to Task 10: System Integration & Testing