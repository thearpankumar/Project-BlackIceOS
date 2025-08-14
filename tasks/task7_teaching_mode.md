# Task 7: Teaching Mode & Learning

## What This Task Is About
This task creates the "training system" for Kali AI-OS - allowing users to teach the AI by demonstration:
- **Action Recording** - Records every mouse click, keystroke, and voice command during demonstrations
- **Smart Learning** - AI analyzes demonstrations and creates reusable workflows automatically
- **Workflow Optimization** - Removes unnecessary actions and optimizes for efficiency
- **Adaptive Replay** - AI can replay learned workflows, adapting to different environments
- **Voice Annotations** - Users can narrate what they're doing to help AI understand context

## Why This Task Is Critical
- **Knowledge Transfer**: Experts can teach complex workflows to AI without programming
- **Automation Scale**: Turn any manual process into automated workflow
- **Institutional Knowledge**: Preserve expert knowledge permanently
- **Continuous Improvement**: AI learns and optimizes workflows over time

## How to Complete This Task - Step by Step

### Phase 1: Setup Teaching Environment (45 minutes)
```bash
# 1. Install action recording dependencies (in VM)
sudo apt update
sudo apt install -y xdotool scrot python3-tk
pip install pynput mss opencv-python pillow
pip install scikit-learn pandas numpy

# 2. Configure input monitoring permissions
sudo usermod -a -G input $USER
sudo chmod +r /dev/input/event*

# 3. Create teaching directory structure
mkdir -p src/teaching/{recording,analysis,learning,validation,replay,config}
mkdir -p data/recordings/{sessions,screenshots,audio}
mkdir -p tests/teaching/fixtures

# 4. Test input capture
python -c "from pynput import mouse, keyboard; print('Input capture ready!')"
```

### Phase 2: Write Teaching Tests First (1.5 hours)
```python
# tests/teaching/test_teaching_core.py
def test_action_recording_capture():
    """Test recording captures user actions"""
    # Input: Start recording, simulate clicks/typing, stop recording
    # Expected: All actions captured with timestamps and context
    
def test_workflow_analysis_pattern_detection():
    """Test AI detects patterns in recorded actions"""
    # Input: Recorded nmap scan demonstration
    # Expected: Detects command pattern, tool usage, target parameters
    
def test_workflow_optimization():
    """Test removal of redundant actions"""
    # Input: Recording with duplicate clicks, typing corrections
    # Expected: Optimized workflow with clean actions
    
def test_demonstration_learning():
    """Test AI learns complete workflow from demo"""
    # Input: Complete burpsuite setup demonstration
    # Expected: Structured workflow with steps, tools, context
    
def test_adaptive_workflow_replay():
    """Test AI replays learned workflows"""
    # Input: Learned workflow + new target parameters
    # Expected: Workflow executed with adapted parameters
```

### Phase 3: Action Recording System (2.5 hours)
```python
# src/teaching/recording/action_recorder.py
import time
import json
from datetime import datetime
from typing import Dict, List, Any, Optional
from pynput import mouse, keyboard
import threading
import mss

class ActionRecorder:
    def __init__(self):
        self.recording = False
        self.session_id = None
        self.recorded_actions = []
        self.start_time = None
        self.screen_recorder = ScreenRecorder()
        self.voice_recorder = VoiceRecorder()
        
        # Input listeners
        self.mouse_listener = None
        self.keyboard_listener = None
        self.current_text_buffer = ""
        
    def start_recording(self, session_name: str, 
                      capture_voice: bool = True) -> Dict[str, Any]:
        """Start recording user demonstration"""
        try:
            if self.recording:
                return {'success': False, 'error': 'Already recording'}
                
            # Initialize session
            self.session_id = f"{session_name}_{int(time.time())}"
            self.recorded_actions = []
            self.start_time = time.time()
            self.recording = True
            self.current_text_buffer = ""
            
            # Start input listeners
            self._start_input_listeners()
            
            # Start screen recording
            self.screen_recorder.start_recording(self.session_id)
            
            # Start voice recording if enabled
            if capture_voice:
                self.voice_recorder.start_recording(self.session_id)
                
            # Record session start
            self._record_action({
                'type': 'session_start',
                'session_name': session_name,
                'timestamp': 0.0,
                'system_context': self._get_system_context()
            })
            
            return {
                'success': True,
                'session_id': self.session_id,
                'message': f'Recording started: {session_name}'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Failed to start recording: {str(e)}'
            }
            
    def stop_recording(self) -> Dict[str, Any]:
        """Stop recording and return captured workflow"""
        try:
            if not self.recording:
                return {'success': False, 'error': 'Not currently recording'}
                
            # Record session end
            self._record_action({
                'type': 'session_end',
                'timestamp': time.time() - self.start_time
            })
            
            self.recording = False
            
            # Stop input listeners
            self._stop_input_listeners()
            
            # Stop screen recording
            screenshots = self.screen_recorder.stop_recording()
            
            # Stop voice recording
            voice_annotations = self.voice_recorder.stop_recording()
            
            # Process and optimize recorded actions
            processed_actions = self._process_recorded_actions()
            
            # Create session summary
            session_data = {
                'session_id': self.session_id,
                'recorded_actions': processed_actions,
                'screenshots': screenshots,
                'voice_annotations': voice_annotations,
                'duration': time.time() - self.start_time,
                'action_count': len(processed_actions),
                'tools_detected': self._detect_tools_used(processed_actions)
            }
            
            # Save session to disk
            self._save_session(session_data)
            
            return {
                'success': True,
                'session_data': session_data,
                'message': f'Recording saved: {self.session_id}'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Failed to stop recording: {str(e)}'
            }
            
    def _start_input_listeners(self):
        """Start monitoring mouse and keyboard input"""
        # Mouse listener
        self.mouse_listener = mouse.Listener(
            on_click=self._on_mouse_click,
            on_move=self._on_mouse_move,
            on_scroll=self._on_mouse_scroll
        )
        
        # Keyboard listener
        self.keyboard_listener = keyboard.Listener(
            on_press=self._on_key_press,
            on_release=self._on_key_release
        )
        
        self.mouse_listener.start()
        self.keyboard_listener.start()
        
    def _on_mouse_click(self, x: int, y: int, button, pressed: bool):
        """Handle mouse click events"""
        if not self.recording or not pressed:
            return
            
        # Capture screenshot of click area
        click_screenshot = self.screen_recorder.capture_region(
            x-50, y-50, 100, 100
        )
        
        self._record_action({
            'type': 'click',
            'x': x,
            'y': y,
            'button': str(button),
            'timestamp': time.time() - self.start_time,
            'window_title': self._get_active_window_title(),
            'click_screenshot': click_screenshot,
            'ui_element': self._identify_ui_element(x, y)
        })
        
    def _on_key_press(self, key):
        """Handle keyboard press events"""
        if not self.recording:
            return
            
        timestamp = time.time() - self.start_time
        
        try:
            # Regular character
            if hasattr(key, 'char') and key.char:
                self.current_text_buffer += key.char
                
                # Record individual character for real-time tracking
                self._record_action({
                    'type': 'type_char',
                    'char': key.char,
                    'timestamp': timestamp,
                    'buffer_length': len(self.current_text_buffer)
                })
                
        except AttributeError:
            # Special key (Enter, Space, etc.)
            key_name = str(key).replace('Key.', '')
            
            # If we have accumulated text, record it as a complete typing action
            if self.current_text_buffer and key_name in ['enter', 'tab', 'space']:
                self._record_action({
                    'type': 'type_text',
                    'text': self.current_text_buffer,
                    'timestamp': timestamp - len(self.current_text_buffer) * 0.05,  # Estimate start time
                    'completion_key': key_name,
                    'window_title': self._get_active_window_title()
                })
                
                # Check if this looks like a command
                if self._is_command_pattern(self.current_text_buffer):
                    self._record_action({
                        'type': 'command_detected',
                        'command': self.current_text_buffer.strip(),
                        'timestamp': timestamp,
                        'tool': self._extract_tool_name(self.current_text_buffer)
                    })
                    
                self.current_text_buffer = ""
                
            # Record special key press
            self._record_action({
                'type': 'key_press',
                'key': key_name,
                'timestamp': timestamp
            })
            
    def _record_action(self, action: Dict[str, Any]):
        """Record an action with full context"""
        # Add universal context to every action
        action.update({
            'session_id': self.session_id,
            'application': self._get_active_application(),
            'screen_region': self._get_screen_context(),
            'system_state': self._get_system_state()
        })
        
        self.recorded_actions.append(action)
        
        # Auto-save every 50 actions for safety
        if len(self.recorded_actions) % 50 == 0:
            self._auto_save_session()
            
    def _process_recorded_actions(self) -> List[Dict[str, Any]]:
        """Process and optimize recorded actions"""
        # Remove duplicate actions
        deduplicated = self._remove_duplicate_actions(self.recorded_actions)
        
        # Combine related actions
        combined = self._combine_related_actions(deduplicated)
        
        # Add semantic context
        contextualized = self._add_semantic_context(combined)
        
        return contextualized
        
    def _remove_duplicate_actions(self, actions: List[Dict]) -> List[Dict]:
        """Remove duplicate or redundant actions"""
        cleaned = []
        prev_action = None
        
        for action in actions:
            # Skip duplicate clicks
            if (action['type'] == 'click' and prev_action and 
                prev_action['type'] == 'click' and
                abs(action['x'] - prev_action['x']) < 5 and
                abs(action['y'] - prev_action['y']) < 5 and
                action['timestamp'] - prev_action['timestamp'] < 0.5):
                continue
                
            # Skip redundant mouse movements
            if action['type'] == 'mouse_move' and len(cleaned) > 5:
                continue
                
            cleaned.append(action)
            prev_action = action
            
        return cleaned
        
    def _combine_related_actions(self, actions: List[Dict]) -> List[Dict]:
        """Combine related actions into logical groups"""
        combined = []
        i = 0
        
        while i < len(actions):
            current = actions[i]
            
            # Combine typing sequences
            if current['type'] in ['type_char', 'type_text']:
                text_sequence = self._extract_text_sequence(actions, i)
                if text_sequence['combined_text']:
                    combined.append({
                        'type': 'text_input',
                        'text': text_sequence['combined_text'],
                        'timestamp': current['timestamp'],
                        'duration': text_sequence['duration'],
                        'character_count': len(text_sequence['combined_text'])
                    })
                    i = text_sequence['end_index']
                else:
                    combined.append(current)
                    i += 1
            else:
                combined.append(current)
                i += 1
                
        return combined
```

### Phase 4: Workflow Analysis Engine (2 hours)
```python
# src/teaching/analysis/workflow_analyzer.py
import re
from typing import Dict, List, Any, Optional
from src.teaching.analysis.pattern_detector import PatternDetector

class WorkflowAnalyzer:
    def __init__(self):
        self.pattern_detector = PatternDetector()
        self.security_tools = {
            'nmap': {'category': 'scanning', 'type': 'network'},
            'burpsuite': {'category': 'web_testing', 'type': 'proxy'},
            'wireshark': {'category': 'traffic_analysis', 'type': 'capture'},
            'metasploit': {'category': 'exploitation', 'type': 'framework'},
            'nikto': {'category': 'web_scanning', 'type': 'vulnerability'},
            'dirb': {'category': 'web_enumeration', 'type': 'directory'},
            'sqlmap': {'category': 'web_testing', 'type': 'injection'}
        }
        
    def create_workflow(self, session_data: Dict[str, Any]) -> Dict[str, Any]:
        """Convert recorded session into structured workflow"""
        actions = session_data['recorded_actions']
        
        # Detect high-level patterns
        patterns = self.pattern_detector.analyze_session(actions)
        
        # Extract workflow metadata
        metadata = self._extract_workflow_metadata(actions, session_data)
        
        # Generate workflow steps
        steps = self._generate_workflow_steps(actions)
        
        # Identify reusable parameters
        parameters = self._identify_parameters(actions)
        
        # Calculate complexity and timing
        complexity_analysis = self._analyze_complexity(steps)
        
        return {
            'name': metadata['name'],
            'description': metadata['description'],
            'category': metadata['category'],
            'steps': steps,
            'parameters': parameters,
            'tools_used': metadata['tools_used'],
            'target_types': metadata['target_types'],
            'context_tags': metadata['context_tags'],
            'patterns': patterns,
            'complexity': complexity_analysis,
            'estimated_duration': metadata['duration'],
            'screenshots': session_data.get('screenshots', []),
            'voice_annotations': session_data.get('voice_annotations', []),
            'learned_from': 'demonstration',
            'demonstration_date': datetime.now().isoformat(),
            'session_id': session_data['session_id']
        }
        
    def _extract_workflow_metadata(self, actions: List[Dict], 
                                  session_data: Dict) -> Dict[str, Any]:
        """Extract metadata from recorded actions"""
        # Detect tools used
        tools_used = set()
        commands = []
        applications = set()
        
        for action in actions:
            # Extract tool names from commands
            if action['type'] == 'command_detected':
                tool = action.get('tool')
                if tool and tool in self.security_tools:
                    tools_used.add(tool)
                    commands.append(action['command'])
                    
            # Track applications used
            if 'application' in action:
                applications.add(action['application'])
                
        # Analyze command patterns to infer target types
        target_types = self._infer_target_types(commands)
        
        # Generate workflow name based on tools and patterns
        workflow_name = self._generate_workflow_name(tools_used, target_types)
        
        # Determine category
        category = self._determine_category(tools_used, commands)
        
        # Generate context tags
        context_tags = self._generate_context_tags(tools_used, commands, applications)
        
        return {
            'name': workflow_name,
            'description': self._generate_description(tools_used, commands),
            'category': category,
            'tools_used': list(tools_used),
            'target_types': target_types,
            'context_tags': context_tags,
            'duration': session_data.get('duration', 0)
        }
        
    def _generate_workflow_steps(self, actions: List[Dict]) -> List[Dict[str, Any]]:
        """Convert actions into reusable workflow steps"""
        steps = []
        current_step = None
        
        for action in actions:
            if action['type'] == 'session_start':
                continue
                
            elif action['type'] == 'command_detected':
                # Create command execution step
                step = {
                    'action': 'execute_command',
                    'tool': action.get('tool', 'unknown'),
                    'command_template': self._parameterize_command(action['command']),
                    'original_command': action['command'],
                    'timestamp': action['timestamp'],
                    'description': f"Execute {action.get('tool', 'command')}"
                }
                steps.append(step)
                
            elif action['type'] == 'click':
                # Create UI interaction step
                step = {
                    'action': 'click_element',
                    'target': action.get('ui_element', 'unknown'),
                    'coordinates': {'x': action['x'], 'y': action['y']},
                    'window': action.get('window_title', ''),
                    'timestamp': action['timestamp'],
                    'description': f"Click {action.get('ui_element', 'element')}"
                }
                steps.append(step)
                
            elif action['type'] == 'text_input':
                # Create text input step
                step = {
                    'action': 'input_text',
                    'text_template': self._parameterize_text(action['text']),
                    'original_text': action['text'],
                    'timestamp': action['timestamp'],
                    'description': f"Input text: {action['text'][:50]}..."
                }
                steps.append(step)
                
            elif action['type'] == 'key_press' and action['key'] == 'enter':
                # Add execution confirmation to previous step
                if steps and steps[-1]['action'] in ['execute_command', 'input_text']:
                    steps[-1]['requires_confirmation'] = True
                    
        return steps
        
    def _parameterize_command(self, command: str) -> str:
        """Convert command to parameterized template"""
        # Replace IP addresses with parameter
        ip_pattern = r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b'
        command = re.sub(ip_pattern, '{{target_ip}}', command)
        
        # Replace domain names with parameter
        domain_pattern = r'\b[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?\.[a-zA-Z]{2,}\b'
        command = re.sub(domain_pattern, '{{target_domain}}', command)
        
        # Replace port numbers with parameter
        port_pattern = r'-p\s+(\d+(?:,\d+)*)'
        command = re.sub(port_pattern, r'-p {{target_ports}}', command)
        
        return command
        
    def _identify_parameters(self, actions: List[Dict]) -> Dict[str, Any]:
        """Identify reusable parameters in the workflow"""
        parameters = {
            'target_ips': set(),
            'target_domains': set(),
            'target_ports': set(),
            'file_paths': set(),
            'custom_values': {}
        }
        
        for action in actions:
            if action['type'] == 'command_detected':
                command = action['command']
                
                # Extract IP addresses
                ips = re.findall(r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b', command)
                parameters['target_ips'].update(ips)
                
                # Extract domain names
                domains = re.findall(r'\b[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?\.[a-zA-Z]{2,}\b', command)
                parameters['target_domains'].update(domains)
                
                # Extract port numbers
                ports = re.findall(r'-p\s+(\d+(?:,\d+)*)', command)
                parameters['target_ports'].update(ports)
                
        # Convert sets to lists for JSON serialization
        return {
            k: list(v) if isinstance(v, set) else v 
            for k, v in parameters.items()
        }
```

### Phase 5: Demonstration Learning System (2 hours)
```python
# src/teaching/learning/demonstration_learner.py
from typing import Dict, List, Any
from datetime import datetime

class DemonstrationLearner:
    def __init__(self, memory_manager):
        self.memory = memory_manager
        self.workflow_analyzer = WorkflowAnalyzer()
        self.variation_creator = WorkflowVariationCreator()
        
    def learn_from_demonstration(self, session_data: Dict[str, Any]) -> Dict[str, Any]:
        """Learn comprehensive workflow from user demonstration"""
        try:
            # Analyze session and create structured workflow
            workflow = self.workflow_analyzer.create_workflow(session_data)
            
            # Validate workflow makes sense
            validation_result = self._validate_workflow(workflow)
            if not validation_result['valid']:
                return {
                    'success': False,
                    'error': f"Invalid workflow: {validation_result['reason']}"
                }
                
            # Store primary workflow in memory
            workflow_id = self.memory.store_workflow(workflow)
            
            # Create useful variations of the workflow
            variations = self.variation_creator.create_variations(workflow)
            variation_ids = []
            
            for variation in variations:
                variation['parent_workflow_id'] = workflow_id
                var_id = self.memory.store_workflow(variation)
                variation_ids.append(var_id)
                
            # Generate learning summary
            learning_summary = self._generate_learning_summary(
                workflow, variations, session_data
            )
            
            return {
                'success': True,
                'workflow_id': workflow_id,
                'workflow_name': workflow['name'],
                'category': workflow['category'],
                'tools_learned': workflow['tools_used'],
                'steps_count': len(workflow['steps']),
                'variations_created': len(variations),
                'variation_ids': variation_ids,
                'learning_summary': learning_summary,
                'session_duration': session_data.get('duration', 0)
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f"Failed to learn from demonstration: {str(e)}"
            }
            
    def _validate_workflow(self, workflow: Dict[str, Any]) -> Dict[str, Any]:
        """Validate that learned workflow is sensible"""
        # Check minimum requirements
        if not workflow.get('steps'):
            return {'valid': False, 'reason': 'No actionable steps detected'}
            
        if len(workflow['steps']) < 2:
            return {'valid': False, 'reason': 'Workflow too simple (less than 2 steps)'}
            
        # Check for dangerous patterns
        dangerous_patterns = ['rm -rf', 'dd if=', 'mkfs', '> /dev/sda']
        for step in workflow['steps']:
            if step.get('action') == 'execute_command':
                command = step.get('original_command', '')
                for pattern in dangerous_patterns:
                    if pattern in command:
                        return {
                            'valid': False, 
                            'reason': f'Potentially dangerous command detected: {pattern}'
                        }
                        
        # Check workflow coherence
        if not workflow.get('tools_used'):
            return {'valid': False, 'reason': 'No security tools detected'}
            
        return {'valid': True, 'reason': 'Workflow validated successfully'}
        
    def _generate_learning_summary(self, workflow: Dict, variations: List[Dict],
                                 session_data: Dict) -> Dict[str, Any]:
        """Generate summary of what was learned"""
        return {
            'workflow_type': workflow['category'],
            'primary_tool': workflow['tools_used'][0] if workflow['tools_used'] else 'unknown',
            'complexity_level': self._assess_complexity(workflow),
            'automation_potential': self._assess_automation_potential(workflow),
            'parameter_count': len(workflow.get('parameters', {})),
            'reusability_score': self._calculate_reusability_score(workflow),
            'learning_confidence': self._calculate_learning_confidence(workflow, session_data),
            'suggested_improvements': self._suggest_improvements(workflow),
            'security_considerations': self._identify_security_considerations(workflow)
        }
        
    def _assess_complexity(self, workflow: Dict) -> str:
        """Assess workflow complexity level"""
        step_count = len(workflow['steps'])
        tool_count = len(workflow['tools_used'])
        
        if step_count <= 3 and tool_count == 1:
            return 'beginner'
        elif step_count <= 8 and tool_count <= 2:
            return 'intermediate'
        else:
            return 'advanced'
            
    def _calculate_reusability_score(self, workflow: Dict) -> float:
        """Calculate how reusable this workflow is"""
        score = 0.5  # Base score
        
        # Higher score for parameterized workflows
        if workflow.get('parameters'):
            param_count = sum(len(v) for v in workflow['parameters'].values() if isinstance(v, list))
            score += min(0.3, param_count * 0.1)
            
        # Higher score for common security tools
        common_tools = ['nmap', 'burpsuite', 'nikto', 'dirb']
        common_tool_count = sum(1 for tool in workflow['tools_used'] if tool in common_tools)
        score += common_tool_count * 0.1
        
        # Lower score for very specific workflows
        if len(workflow['steps']) > 15:
            score -= 0.2
            
        return min(1.0, max(0.0, score))
```

### Phase 6: Workflow Replay System (1.5 hours)
```python
# src/teaching/replay/workflow_executor.py
import asyncio
import time
from typing import Dict, List, Any, Optional

class WorkflowExecutor:
    def __init__(self, desktop_controller):
        self.desktop = desktop_controller
        self.execution_log = []
        self.current_execution = None
        self.error_handler = WorkflowErrorHandler()
        
    async def execute_workflow(self, workflow: Dict[str, Any], 
                             execution_params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute learned workflow with adaptive capabilities"""
        execution_id = f"exec_{int(time.time())}"
        self.current_execution = {
            'id': execution_id,
            'workflow': workflow,
            'params': execution_params or {},
            'start_time': time.time(),
            'status': 'running',
            'completed_steps': [],
            'errors': []
        }
        
        try:
            # Prepare execution environment
            prep_result = await self._prepare_execution_environment(workflow)
            if not prep_result['success']:
                return self._create_execution_result(False, prep_result['error'])
                
            # Process workflow parameters
            resolved_params = self._resolve_parameters(
                workflow.get('parameters', {}), execution_params or {}
            )
            
            # Execute each step
            step_results = []
            for i, step in enumerate(workflow['steps']):
                try:
                    print(f"Executing step {i+1}/{len(workflow['steps'])}: {step.get('description', 'Unknown step')}")
                    
                    # Apply parameters to step
                    parameterized_step = self._apply_parameters_to_step(step, resolved_params)
                    
                    # Execute step with adaptive timing
                    step_result = await self._execute_step_with_adaptation(parameterized_step)
                    step_results.append(step_result)
                    
                    if step_result['success']:
                        self.current_execution['completed_steps'].append(i)
                    else:
                        # Attempt error recovery
                        recovery_result = await self.error_handler.attempt_recovery(
                            step, step_result['error'], self.desktop
                        )
                        
                        if recovery_result['success']:
                            step_results[-1] = recovery_result
                            self.current_execution['completed_steps'].append(i)
                        else:
                            # Stop execution on unrecoverable error
                            break
                            
                except Exception as e:
                    error_msg = f"Step {i+1} failed: {str(e)}"
                    self.current_execution['errors'].append(error_msg)
                    break
                    
            # Calculate execution summary
            success_rate = len(self.current_execution['completed_steps']) / len(workflow['steps'])
            execution_time = time.time() - self.current_execution['start_time']
            
            # Update workflow success statistics
            await self._update_workflow_statistics(workflow, success_rate, execution_time)
            
            return {
                'success': success_rate >= 0.8,  # 80% success threshold
                'execution_id': execution_id,
                'steps_completed': len(self.current_execution['completed_steps']),
                'total_steps': len(workflow['steps']),
                'success_rate': success_rate,
                'execution_time': execution_time,
                'errors': self.current_execution['errors'],
                'step_results': step_results,
                'workflow_name': workflow['name']
            }
            
        except Exception as e:
            return self._create_execution_result(False, str(e))
            
    async def _execute_step_with_adaptation(self, step: Dict[str, Any]) -> Dict[str, Any]:
        """Execute individual step with environmental adaptation"""
        action = step['action']
        
        try:
            if action == 'execute_command':
                return await self._execute_command_step(step)
            elif action == 'click_element':
                return await self._execute_click_step(step)
            elif action == 'input_text':
                return await self._execute_text_input_step(step)
            elif action == 'wait':
                return await self._execute_wait_step(step)
            else:
                return {
                    'success': False,
                    'error': f'Unknown action type: {action}'
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f'Step execution failed: {str(e)}'
            }
            
    async def _execute_command_step(self, step: Dict[str, Any]) -> Dict[str, Any]:
        """Execute command with adaptive terminal handling"""
        command = step.get('command_template', step.get('original_command', ''))
        
        # Ensure terminal is open and ready
        terminal_ready = await self.desktop.ensure_terminal_ready()
        if not terminal_ready:
            return {'success': False, 'error': 'Could not access terminal'}
            
        # Type command
        type_result = await self.desktop.safe_type(command)
        if not type_result['success']:
            return {'success': False, 'error': 'Failed to type command'}
            
        # Press Enter
        await asyncio.sleep(0.2)  # Small delay for command to be visible
        enter_result = await self.desktop.safe_key_press('Return')
        if not enter_result['success']:
            return {'success': False, 'error': 'Failed to execute command'}
            
        # Wait for command completion (adaptive timing)
        wait_time = self._calculate_command_wait_time(command)
        await asyncio.sleep(wait_time)
        
        return {
            'success': True,
            'action': 'execute_command',
            'command': command,
            'wait_time': wait_time
        }
        
    def _apply_parameters_to_step(self, step: Dict[str, Any], 
                                params: Dict[str, Any]) -> Dict[str, Any]:
        """Apply resolved parameters to workflow step"""
        step_copy = step.copy()
        
        # Apply parameters to command templates
        if 'command_template' in step_copy:
            template = step_copy['command_template']
            for param_name, param_value in params.items():
                placeholder = f'{{{{{param_name}}}}}'
                template = template.replace(placeholder, str(param_value))
            step_copy['command_template'] = template
            
        # Apply parameters to text templates
        if 'text_template' in step_copy:
            template = step_copy['text_template']
            for param_name, param_value in params.items():
                placeholder = f'{{{{{param_name}}}}}'
                template = template.replace(placeholder, str(param_value))
            step_copy['text_template'] = template
            
        return step_copy
        
    def _resolve_parameters(self, workflow_params: Dict[str, Any], 
                          execution_params: Dict[str, Any]) -> Dict[str, Any]:
        """Resolve workflow parameters with execution-time values"""
        resolved = {}
        
        # Use execution parameters if provided
        for key, value in execution_params.items():
            resolved[key] = value
            
        # Use default values from workflow for missing parameters
        for param_type, param_values in workflow_params.items():
            if param_type == 'target_ips' and 'target_ip' not in resolved:
                if param_values:
                    resolved['target_ip'] = param_values[0]
            elif param_type == 'target_domains' and 'target_domain' not in resolved:
                if param_values:
                    resolved['target_domain'] = param_values[0]
            elif param_type == 'target_ports' and 'target_ports' not in resolved:
                if param_values:
                    resolved['target_ports'] = param_values[0]
                    
        return resolved
```

### Phase 7: Error Recovery System (1 hour)
```python
# src/teaching/replay/error_handler.py
class WorkflowErrorHandler:
    def __init__(self):
        self.recovery_strategies = {
            'command_not_found': self._recover_missing_command,
            'permission_denied': self._recover_permission_error,
            'network_timeout': self._recover_network_timeout,
            'application_not_responding': self._recover_app_freeze,
            'click_target_not_found': self._recover_missing_ui_element
        }
        
    async def attempt_recovery(self, failed_step: Dict, error_msg: str, 
                             desktop_controller) -> Dict[str, Any]:
        """Attempt to recover from step execution errors"""
        error_type = self._classify_error(error_msg)
        
        if error_type in self.recovery_strategies:
            try:
                recovery_func = self.recovery_strategies[error_type]
                recovery_result = await recovery_func(failed_step, error_msg, desktop_controller)
                
                if recovery_result['success']:
                    return {
                        'success': True,
                        'action': failed_step['action'],
                        'recovery_applied': error_type,
                        'original_error': error_msg,
                        'recovery_method': recovery_result['method']
                    }
                    
            except Exception as e:
                print(f"Recovery attempt failed: {e}")
                
        return {
            'success': False,
            'error': f'No recovery available for: {error_type}',
            'original_error': error_msg
        }
        
    async def _recover_missing_command(self, step: Dict, error_msg: str, 
                                     desktop) -> Dict[str, Any]:
        """Recover from command not found errors"""
        command = step.get('command_template', step.get('original_command', ''))
        tool_name = command.split()[0] if command else ''
        
        # Try common installation commands
        install_commands = [
            f'sudo apt install -y {tool_name}',
            f'which {tool_name}',  # Check if it's in PATH
            f'locate {tool_name}'   # Find if installed elsewhere
        ]
        
        for install_cmd in install_commands:
            print(f"Attempting recovery with: {install_cmd}")
            await desktop.safe_type(install_cmd)
            await desktop.safe_key_press('Return')
            await asyncio.sleep(5)  # Wait for command
            
            # Try original command again
            await desktop.safe_type(command)
            await desktop.safe_key_press('Return')
            await asyncio.sleep(2)
            
            # If no error this time, consider it recovered
            # (In real implementation, would check command output)
            return {
                'success': True,
                'method': f'tool_installation_attempt: {install_cmd}'
            }
            
        return {'success': False, 'method': 'tool_installation_failed'}
```

### Phase 8: Integration & Testing (1 hour)
```python
# Test complete teaching system
async def test_complete_teaching_system():
    # 1. Initialize teaching components
    recorder = ActionRecorder()
    analyzer = WorkflowAnalyzer()
    learner = DemonstrationLearner(memory_manager)
    executor = WorkflowExecutor(desktop_controller)
    
    # 2. Simulate recorded demonstration
    demo_session = {
        'session_id': 'test_nmap_demo',
        'recorded_actions': [
            {'type': 'command_detected', 'command': 'nmap -sS example.com', 'tool': 'nmap'},
            {'type': 'key_press', 'key': 'enter'},
            {'type': 'wait', 'duration': 10},
            {'type': 'command_detected', 'command': 'nmap -sV example.com', 'tool': 'nmap'}
        ],
        'duration': 20.0,
        'screenshots': [],
        'voice_annotations': []
    }
    
    # 3. Learn workflow from demonstration
    learning_result = learner.learn_from_demonstration(demo_session)
    assert learning_result['success'] == True
    assert 'nmap' in learning_result['tools_learned']
    
    # 4. Execute learned workflow
    workflow_id = learning_result['workflow_id']
    learned_workflow = memory_manager.get_workflow(workflow_id)
    
    execution_result = await executor.execute_workflow(
        learned_workflow,
        {'target_domain': 'testsite.com'}
    )
    
    assert execution_result['success'] == True
    assert execution_result['steps_completed'] > 0
    
    print("Teaching system working correctly!")

# Performance testing
def test_teaching_performance():
    recorder = ActionRecorder()
    
    # Test recording overhead
    start_time = time.time()
    recorder.start_recording("performance_test")
    
    # Simulate 1000 actions
    for i in range(1000):
        recorder._record_action({
            'type': 'test_action',
            'id': i,
            'timestamp': time.time() - start_time
        })
        
    stop_result = recorder.stop_recording()
    recording_time = time.time() - start_time
    
    print(f"Recorded 1000 actions in {recording_time:.2f}s")
    assert recording_time < 5.0  # Should record 1000 actions in under 5 seconds
    assert len(stop_result['session_data']['recorded_actions']) == 1000
```

## Overview
Build an advanced teaching mode system that allows users to demonstrate security workflows to the AI, which then learns and reproduces these workflows autonomously. This system records actions, optimizes workflows, and enables continuous learning.

## Directory Structure
```
Samsung-AI-os/
├── kali-ai-os/
│   ├── src/
│   │   ├── teaching/
│   │   │   ├── __init__.py
│   │   │   ├── recording/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── action_recorder.py
│   │   │   │   ├── screen_recorder.py
│   │   │   │   ├── input_tracker.py
│   │   │   │   ├── voice_annotator.py
│   │   │   │   └── context_capture.py
│   │   │   ├── analysis/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── workflow_analyzer.py
│   │   │   │   ├── pattern_detector.py
│   │   │   │   ├── action_optimizer.py
│   │   │   │   ├── dependency_mapper.py
│   │   │   │   └── error_predictor.py
│   │   │   ├── learning/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── demonstration_learner.py
│   │   │   │   ├── workflow_generator.py
│   │   │   │   ├── variation_creator.py
│   │   │   │   ├── feedback_processor.py
│   │   │   │   └── knowledge_integrator.py
│   │   │   ├── validation/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── workflow_validator.py
│   │   │   │   ├── safety_checker.py
│   │   │   │   ├── consistency_verifier.py
│   │   │   │   └── performance_tester.py
│   │   │   ├── replay/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── workflow_executor.py
│   │   │   │   ├── adaptive_player.py
│   │   │   │   ├── error_handler.py
│   │   │   │   └── real_time_adjuster.py
│   │   │   └── config/
│   │   │       ├── __init__.py
│   │   │       ├── teaching_config.py
│   │   │       └── recording_settings.py
│   │   └── tests/
│   │       ├── teaching/
│   │       │   ├── test_action_recording.py
│   │       │   ├── test_workflow_analysis.py
│   │       │   ├── test_learning_engine.py
│   │       │   ├── test_workflow_replay.py
│   │       │   └── test_teaching_integration.py
│   │       └── fixtures/
│   │           ├── recorded_sessions/
│   │           ├── test_workflows/
│   │           └── sample_demonstrations/
```

## Technology Stack
- **Input Tracking**: pynput 1.7.6, keyboard, mouse
- **Screen Recording**: opencv-python, Pillow, mss
- **Audio Recording**: pyaudio, wave, speech_recognition
- **ML Analysis**: scikit-learn, numpy, pandas
- **Workflow Generation**: Jinja2 templates, AST parsing

## Implementation Requirements

### Core Components

#### 1. Action Recorder
```python
# src/teaching/recording/action_recorder.py
import time
import threading
from typing import Dict, List, Any, Optional
from pynput import mouse, keyboard
from src.teaching.recording.screen_recorder import ScreenRecorder

class ActionRecorder:
    def __init__(self):
        self.recording = False
        self.session_id = None
        self.recorded_actions = []
        self.start_time = None
        self.screen_recorder = ScreenRecorder()
        
        # Input listeners
        self.mouse_listener = None
        self.keyboard_listener = None
        
    def start_recording(self, session_name: str) -> Dict[str, Any]:
        """Start recording user actions"""
        if self.recording:
            return {'success': False, 'error': 'Already recording'}
        
        self.session_id = f"{session_name}_{int(time.time())}"
        self.recorded_actions = []
        self.start_time = time.time()
        self.recording = True
        
        # Start input listeners
        self._start_input_listeners()
        
        # Start screen recording
        self.screen_recorder.start_recording()
        
        return {
            'success': True,
            'session_id': self.session_id,
            'message': f'Recording started for: {session_name}'
        }
    
    def stop_recording(self) -> Dict[str, Any]:
        """Stop recording and return captured workflow"""
        if not self.recording:
            return {'success': False, 'error': 'Not currently recording'}
        
        self.recording = False
        
        # Stop input listeners
        self._stop_input_listeners()
        
        # Stop screen recording
        screenshots = self.screen_recorder.stop_recording()
        
        # Process recorded actions
        processed_actions = self._process_recorded_actions()
        
        return {
            'success': True,
            'session_id': self.session_id,
            'recorded_actions': processed_actions,
            'screenshots': screenshots,
            'duration': time.time() - self.start_time
        }
    
    def _start_input_listeners(self):
        """Start mouse and keyboard listeners"""
        self.mouse_listener = mouse.Listener(
            on_click=self._on_mouse_click,
            on_move=self._on_mouse_move,
            on_scroll=self._on_mouse_scroll
        )
        
        self.keyboard_listener = keyboard.Listener(
            on_press=self._on_key_press,
            on_release=self._on_key_release
        )
        
        self.mouse_listener.start()
        self.keyboard_listener.start()
    
    def _on_mouse_click(self, x: int, y: int, button, pressed: bool):
        """Handle mouse click events"""
        if self.recording and pressed:
            self._record_action({
                'type': 'click',
                'x': x,
                'y': y,
                'button': str(button),
                'timestamp': time.time() - self.start_time,
                'screenshot': self.screen_recorder.capture_current()
            })
    
    def _on_key_press(self, key):
        """Handle keyboard press events"""
        if not self.recording:
            return
        
        try:
            # Regular character
            char = key.char
            self._record_action({
                'type': 'type',
                'text': char,
                'timestamp': time.time() - self.start_time
            })
        except AttributeError:
            # Special key
            self._record_action({
                'type': 'key',
                'key': str(key),
                'timestamp': time.time() - self.start_time
            })
    
    def _record_action(self, action: Dict[str, Any]):
        """Record an action with context"""
        # Add window context
        action['window_context'] = self._get_window_context()
        
        # Add application context
        action['application'] = self._get_active_application()
        
        self.recorded_actions.append(action)
```

#### 2. Workflow Analyzer
```python
# src/teaching/analysis/workflow_analyzer.py
import re
from typing import Dict, List, Any
from src.teaching.analysis.pattern_detector import PatternDetector

class WorkflowAnalyzer:
    def __init__(self):
        self.pattern_detector = PatternDetector()
        
    def create_workflow(self, recorded_actions: List[Dict]) -> Dict[str, Any]:
        """Convert recorded actions into structured workflow"""
        # Detect patterns
        patterns = self.pattern_detector.analyze_actions(recorded_actions)
        
        # Optimize action sequence
        optimized_actions = self.optimize_actions(recorded_actions)
        
        # Extract metadata
        metadata = self._extract_metadata(optimized_actions)
        
        # Generate workflow steps
        steps = self._convert_to_steps(optimized_actions)
        
        return {
            'name': metadata['inferred_name'],
            'description': metadata['description'],
            'steps': steps,
            'tools_used': metadata['tools_used'],
            'patterns': patterns,
            'category': metadata['category'],
            'complexity': len(steps),
            'estimated_duration': metadata['duration']
        }
    
    def optimize_actions(self, actions: List[Dict]) -> List[Dict]:
        """Optimize recorded actions by removing redundancy"""
        optimized = []
        i = 0
        
        while i < len(actions):
            current_action = actions[i]
            
            # Combine consecutive typing actions
            if current_action['type'] == 'type':
                combined_text = current_action['text']
                j = i + 1
                
                while j < len(actions) and actions[j]['type'] == 'type':
                    combined_text += actions[j]['text']
                    j += 1
                
                optimized.append({
                    'type': 'type',
                    'text': combined_text,
                    'timestamp': current_action['timestamp']
                })
                i = j
                
            # Remove duplicate clicks
            elif current_action['type'] == 'click':
                if not self._is_duplicate_click(current_action, optimized):
                    optimized.append(current_action)
                i += 1
                
            else:
                optimized.append(current_action)
                i += 1
        
        return optimized
    
    def _extract_metadata(self, actions: List[Dict]) -> Dict[str, Any]:
        """Extract metadata from actions"""
        # Detect tools used
        tools_used = set()
        commands = []
        
        for action in actions:
            if action['type'] == 'type':
                text = action['text']
                
                # Detect command line tools
                tool_match = re.match(r'^(\w+)', text)
                if tool_match:
                    potential_tool = tool_match.group(1)
                    if self._is_security_tool(potential_tool):
                        tools_used.add(potential_tool)
                        commands.append(text)
        
        # Infer workflow name and category
        category = self._infer_category(tools_used, commands)
        name = self._generate_workflow_name(tools_used, category)
        
        return {
            'tools_used': list(tools_used),
            'category': category,
            'inferred_name': name,
            'description': self._generate_description(tools_used, commands),
            'duration': self._calculate_duration(actions)
        }
```

#### 3. Demonstration Learner
```python
# src/teaching/learning/demonstration_learner.py
class DemonstrationLearner:
    def __init__(self, memory_manager):
        self.memory = memory_manager
        self.workflow_analyzer = WorkflowAnalyzer()
        
    def learn_from_demonstration(self, recorded_session: Dict) -> Dict[str, Any]:
        """Learn workflow from user demonstration"""
        # Analyze recorded actions
        workflow = self.workflow_analyzer.create_workflow(
            recorded_session['recorded_actions']
        )
        
        # Enhance with screenshots and context
        workflow['screenshots'] = recorded_session['screenshots']
        workflow['learned_from'] = 'demonstration'
        workflow['demonstration_date'] = datetime.now()
        
        # Store in memory
        workflow_id = self.memory.store_workflow(workflow)
        
        # Create variations
        variations = self._create_workflow_variations(workflow)
        
        return {
            'success': True,
            'workflow_id': workflow_id,
            'workflow_name': workflow['name'],
            'tools_detected': workflow['tools_used'],
            'variations_created': len(variations)
        }
    
    def _create_workflow_variations(self, base_workflow: Dict) -> List[Dict]:
        """Create variations of the learned workflow"""
        variations = []
        
        # Create variation with different scan types
        if 'nmap' in base_workflow['tools_used']:
            # Fast scan variation
            fast_variation = self._create_speed_variation(base_workflow, 'fast')
            variations.append(fast_variation)
            
            # Stealth scan variation
            stealth_variation = self._create_speed_variation(base_workflow, 'stealth')
            variations.append(stealth_variation)
        
        # Create variation with additional tools
        enhanced_variation = self._create_enhanced_variation(base_workflow)
        if enhanced_variation:
            variations.append(enhanced_variation)
        
        return variations
```

#### 4. Workflow Executor
```python
# src/teaching/replay/workflow_executor.py
class WorkflowExecutor:
    def __init__(self, desktop_controller):
        self.desktop = desktop_controller
        self.execution_log = []
        
    async def execute_workflow(self, workflow: Dict) -> Dict[str, Any]:
        """Execute learned workflow"""
        start_time = time.time()
        errors = []
        steps_completed = 0
        
        try:
            for i, step in enumerate(workflow['steps']):
                try:
                    # Execute step
                    step_result = await self._execute_step(step)
                    
                    if step_result['success']:
                        steps_completed += 1
                    else:
                        errors.append({
                            'step': i,
                            'error': step_result['error']
                        })
                        
                        # Attempt recovery
                        recovery_result = await self._attempt_recovery(step, step_result['error'])
                        if not recovery_result['success']:
                            break
                    
                except Exception as e:
                    errors.append({
                        'step': i,
                        'error': str(e)
                    })
                    break
            
            execution_time = time.time() - start_time
            
            return {
                'success': len(errors) == 0,
                'steps_completed': steps_completed,
                'total_steps': len(workflow['steps']),
                'execution_time': execution_time,
                'errors': errors
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'steps_completed': steps_completed
            }
    
    async def _execute_step(self, step: Dict) -> Dict[str, Any]:
        """Execute individual workflow step"""
        action = step['action']
        params = step.get('params', {})
        
        if action == 'click':
            return await self.desktop.safe_click(params['x'], params['y'])
        elif action == 'type':
            return await self.desktop.safe_type(params['text'])
        elif action == 'open_application':
            return await self.desktop.open_application(params['app_name'])
        elif action == 'wait':
            await asyncio.sleep(params['duration'])
            return {'success': True}
        else:
            return {'success': False, 'error': f'Unknown action: {action}'}
```

## Testing Strategy

### Unit Tests (80% coverage minimum)
```bash
cd kali-ai-os
python -m pytest tests/teaching/ -v --cov=src.teaching --cov-report=html

# Test categories:
# - Action recording accuracy
# - Workflow analysis and optimization
# - Learning from demonstrations
# - Workflow replay accuracy
# - Error handling and recovery
# - Voice annotation integration
```

### Integration Tests
```bash
# Test complete teaching workflow
python -m pytest tests/teaching/test_teaching_integration.py -v

# Test with real applications
python -m pytest tests/teaching/test_real_app_learning.py -v
```

## Deployment & Validation

### Setup Commands
```bash
# 1. Install teaching dependencies
pip install pynput mss opencv-python scikit-learn

# 2. Configure permissions for input monitoring
# On Linux: Add user to input group
sudo usermod -a -G input $USER

# 3. Test teaching mode
python -c "
from src.teaching.recording.action_recorder import ActionRecorder
recorder = ActionRecorder()
print('Teaching mode ready!')
"

# 4. Run teaching tests
python -m pytest tests/teaching/ -v
```

### Success Metrics
- ✅ Action recording accuracy >95%
- ✅ Workflow optimization functional
- ✅ Learning from demonstrations working
- ✅ Workflow replay accuracy >90%
- ✅ Voice annotation integration working
- ✅ Ready for safety framework integration

## Configuration Files

### teaching_config.py
```python
TEACHING_CONFIG = {
    'recording': {
        'screenshot_interval': 2.0,  # seconds
        'max_session_duration': 3600,  # 1 hour
        'auto_optimize': True,
        'capture_voice': True
    },
    'learning': {
        'min_actions_for_workflow': 5,
        'similarity_threshold': 0.8,
        'auto_create_variations': True,
        'feedback_learning_enabled': True
    },
    'replay': {
        'execution_speed': 1.0,  # 1x speed
        'error_retry_attempts': 3,
        'adaptive_timing': True,
        'safety_checks': True
    }
}
```

## Next Steps
After completing this task:
1. Integrate with memory system for permanent learning
2. Connect to safety framework for validation
3. Optimize for complex workflow learning
4. Proceed to Task 8: Safety & Ethics Framework