# Task 5: Security Tool Integration

## What This Task Is About
This task creates the "toolkit" of Kali AI-OS - a universal system that can control any security tool automatically:
- **Universal Tool Adapter** - Single interface to control 600+ Kali Linux security tools
- **Multi-Method Integration** - Uses CLI commands, GUI automation, or API calls as appropriate
- **Dynamic Tool Discovery** - Automatically detects and learns new security tools
- **Intelligent Execution** - AI chooses the right tool and parameters for each security task
- **Result Aggregation** - Combines outputs from multiple tools into comprehensive reports

## Why This Task Is Critical
- **Tool Unification**: Single interface for hundreds of different security tools
- **Automation**: AI can run complex multi-tool workflows automatically
- **Extensibility**: Easy to add new tools without custom coding
- **Intelligence**: Tools are chosen and configured automatically based on target and context

## How to Complete This Task - Step by Step

### Phase 1: Setup Tool Integration Environment (1 hour)
```bash
# 1. Verify Kali tools are installed (in VM)
which nmap nikto dirb gobuster sqlmap
which burpsuite wireshark metasploit

# 2. Install additional tools
sudo apt update
sudo apt install -y masscan zap nuclei subfinder httpx
sudo apt install -y amass sublist3r dirsearch wfuzz

# 3. Install Python tool integration libraries
pip install subprocess32 pexpect
pip install beautifulsoup4 lxml requests
pip install selenium webdriver-manager
pip install python-nmap

# 4. Create tool registry directory
mkdir -p src/security/tools/configs
mkdir -p src/security/tools/templates
mkdir -p src/security/tools/outputs
```

### Phase 2: Write Tool Integration Tests First (1.5 hours)
```python
# tests/security/test_tool_integration.py
def test_nmap_basic_scan():
    """Test nmap integration works"""
    # Input: target="example.com", scan_type="basic"
    # Expected: Port scan results with open ports
    
def test_nikto_web_scan():
    """Test nikto web vulnerability scanning"""
    # Input: target="https://example.com"
    # Expected: Web vulnerability findings
    
def test_burpsuite_gui_automation():
    """Test Burp Suite GUI automation"""
    # Input: target="https://example.com", mode="proxy"
    # Expected: Burp Suite configured and running
    
def test_tool_discovery():
    """Test automatic discovery of installed tools"""
    # Expected: List of available security tools
    
def test_multi_tool_workflow():
    """Test coordinated execution of multiple tools"""
    # Input: ["nmap", "nikto", "dirb"] for target
    # Expected: Results from all three tools
    
def test_unknown_tool_learning():
    """Test system learns new tools automatically"""
    # Input: Custom security script
    # Expected: Tool learned and can be executed
```

### Phase 3: Universal Tool Adapter Core (2.5 hours)
```python
# src/security/tools/universal_adapter.py
import subprocess
import asyncio
import json
from typing import Dict, List, Any

class UniversalToolAdapter:
    def __init__(self):
        self.tool_registry = ToolRegistry()
        self.command_generator = CommandGenerator()
        self.output_parser = OutputParser()
        self.execution_engine = ExecutionEngine()
        
    async def execute_tool(self, tool_name: str, target: str, options: Dict = None):
        """Execute any security tool"""
        try:
            # 1. Get tool configuration
            tool_config = self.tool_registry.get_tool_config(tool_name)
            if not tool_config:
                # Try to learn tool dynamically
                tool_config = await self._learn_new_tool(tool_name)
                
            # 2. Generate appropriate command/workflow
            if tool_config['type'] == 'cli':
                command = self.command_generator.generate_cli_command(
                    tool_name, target, options, tool_config
                )
                result = await self.execution_engine.execute_cli(command)
                
            elif tool_config['type'] == 'gui':
                workflow = self.command_generator.generate_gui_workflow(
                    tool_name, target, options, tool_config
                )
                result = await self.execution_engine.execute_gui(workflow)
                
            elif tool_config['type'] == 'api':
                api_call = self.command_generator.generate_api_call(
                    tool_name, target, options, tool_config
                )
                result = await self.execution_engine.execute_api(api_call)
                
            # 3. Parse and format results
            parsed_results = self.output_parser.parse(tool_name, result['output'])
            
            return {
                'success': True,
                'tool': tool_name,
                'target': target,
                'command': result.get('command', ''),
                'raw_output': result['output'],
                'parsed_results': parsed_results,
                'execution_time': result['execution_time']
            }
            
        except Exception as e:
            return {
                'success': False,
                'tool': tool_name,
                'target': target,
                'error': str(e)
            }

# src/security/tools/tool_registry.py
class ToolRegistry:
    def __init__(self):
        self.tools = {}
        self._load_builtin_tools()
        self._discover_installed_tools()
        
    def _load_builtin_tools(self):
        """Load configurations for known security tools"""
        self.tools.update({
            'nmap': {
                'executable': 'nmap',
                'type': 'cli',
                'category': 'network_scanner',
                'common_args': {
                    'tcp_syn': ['-sS'],
                    'service_version': ['-sV'],
                    'os_detection': ['-O'],
                    'script_scan': ['-sC'],
                    'fast': ['-T4'],
                    'stealth': ['-T2']
                },
                'output_formats': ['-oN', '-oX', '-oG'],
                'typical_targets': ['ip', 'domain', 'cidr']
            },
            'nikto': {
                'executable': 'nikto',
                'type': 'cli', 
                'category': 'web_scanner',
                'common_args': {
                    'host': ['-h'],
                    'port': ['-p'],
                    'ssl': ['-ssl'],
                    'evasion': ['-evasion']
                },
                'output_formats': ['-output'],
                'typical_targets': ['url', 'domain']
            },
            'burpsuite': {
                'executable': 'burpsuite',
                'type': 'gui',
                'category': 'web_proxy',
                'startup_time': 30,
                'gui_templates': 'templates/burpsuite/',
                'automation_method': 'template_matching'
            }
        })
```

### Phase 4: CLI Tool Execution Engine (1.5 hours)
```python
# src/security/tools/execution/cli_executor.py
import asyncio
import subprocess
import time

class CLIExecutor:
    def __init__(self):
        self.active_processes = {}
        
    async def execute_command(self, command: List[str], timeout: int = 300):
        """Execute CLI command with timeout and monitoring"""
        start_time = time.time()
        
        try:
            # Start process
            process = await asyncio.create_subprocess_exec(
                *command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            # Store process for monitoring/cancellation
            process_id = f"{command[0]}_{start_time}"
            self.active_processes[process_id] = process
            
            # Wait for completion with timeout
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(), timeout=timeout
                )
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                raise Exception(f"Command timed out after {timeout} seconds")
            
            execution_time = time.time() - start_time
            
            # Clean up
            del self.active_processes[process_id]
            
            return {
                'success': process.returncode == 0,
                'command': ' '.join(command),
                'stdout': stdout.decode('utf-8', errors='ignore'),
                'stderr': stderr.decode('utf-8', errors='ignore'),
                'return_code': process.returncode,
                'execution_time': execution_time
            }
            
        except Exception as e:
            return {
                'success': False,
                'command': ' '.join(command),
                'error': str(e),
                'execution_time': time.time() - start_time
            }
```

### Phase 5: GUI Tool Automation (2 hours)
```python
# src/security/tools/execution/gui_executor.py
class GUIExecutor:
    def __init__(self, desktop_controller):
        self.desktop = desktop_controller
        
    async def execute_burpsuite_workflow(self, target: str, workflow_type: str):
        """Execute Burp Suite GUI workflow"""
        try:
            # 1. Launch Burp Suite (if not running)
            if not self._is_burpsuite_running():
                await self._launch_burpsuite()
                
            # 2. Wait for application to be ready
            await self._wait_for_burpsuite_ready()
            
            # 3. Execute specific workflow
            if workflow_type == 'proxy_setup':
                result = await self._setup_burp_proxy(target)
            elif workflow_type == 'active_scan':
                result = await self._run_active_scan(target)
            elif workflow_type == 'spider':
                result = await self._run_spider(target)
                
            return {
                'success': True,
                'tool': 'burpsuite',
                'workflow': workflow_type,
                'target': target,
                'result': result
            }
            
        except Exception as e:
            return {
                'success': False,
                'tool': 'burpsuite',
                'error': str(e)
            }
    
    async def _launch_burpsuite(self):
        """Launch Burp Suite application"""
        # Click application launcher or use command
        await self.desktop.run_command('burpsuite')
        
    async def _setup_burp_proxy(self, target: str):
        """Configure Burp Suite proxy for target"""
        # 1. Find and click Proxy tab
        proxy_tab = await self.desktop.find_element('templates/burpsuite/proxy_tab.png')
        await self.desktop.click(proxy_tab['location'])
        
        # 2. Configure target scope
        options_button = await self.desktop.find_element('templates/burpsuite/options.png')
        await self.desktop.click(options_button['location'])
        
        # 3. Add target to scope
        add_button = await self.desktop.find_element('templates/burpsuite/add_scope.png')
        await self.desktop.click(add_button['location'])
        
        # 4. Enter target URL
        await self.desktop.type_text(target)
        
        # 5. Start proxy
        start_button = await self.desktop.find_element('templates/burpsuite/start_proxy.png')
        await self.desktop.click(start_button['location'])
        
        return {'proxy_configured': True, 'target': target}
```

### Phase 6: Output Parsing System (1.5 hours)
```python
# src/security/tools/parsing/output_parser.py
import json
import re
import xml.etree.ElementTree as ET

class OutputParser:
    def __init__(self):
        self.parsers = {
            'nmap': self._parse_nmap_output,
            'nikto': self._parse_nikto_output,
            'dirb': self._parse_dirb_output,
            'sqlmap': self._parse_sqlmap_output
        }
        
    def parse(self, tool_name: str, raw_output: str):
        """Parse tool output into structured format"""
        if tool_name in self.parsers:
            return self.parsers[tool_name](raw_output)
        else:
            # Use AI to parse unknown tool output
            return self._ai_parse_output(tool_name, raw_output)
            
    def _parse_nmap_output(self, output: str):
        """Parse nmap scan results"""
        results = {
            'tool': 'nmap',
            'hosts': [],
            'open_ports': [],
            'services': [],
            'os_info': None
        }
        
        # Parse hosts and ports
        host_pattern = r'Nmap scan report for (.+)'
        port_pattern = r'(\d+)/(tcp|udp)\s+(open|closed|filtered)\s*(.+)?'
        
        current_host = None
        for line in output.split('\n'):
            host_match = re.search(host_pattern, line)
            if host_match:
                current_host = host_match.group(1).strip()
                results['hosts'].append(current_host)
                
            port_match = re.search(port_pattern, line)
            if port_match and current_host:
                port_info = {
                    'host': current_host,
                    'port': int(port_match.group(1)),
                    'protocol': port_match.group(2),
                    'state': port_match.group(3),
                    'service': port_match.group(4).strip() if port_match.group(4) else ''
                }
                
                if port_info['state'] == 'open':
                    results['open_ports'].append(port_info)
                    results['services'].append(port_info)
                    
        return results
        
    def _parse_nikto_output(self, output: str):
        """Parse nikto web scan results"""
        results = {
            'tool': 'nikto',
            'target': '',
            'vulnerabilities': [],
            'findings': []
        }
        
        # Extract target
        target_pattern = r'Target IP:\s*(.+)'
        target_match = re.search(target_pattern, output)
        if target_match:
            results['target'] = target_match.group(1).strip()
            
        # Extract findings
        finding_pattern = r'\+\s*(.+)'
        for line in output.split('\n'):
            finding_match = re.search(finding_pattern, line)
            if finding_match:
                finding = finding_match.group(1).strip()
                results['findings'].append(finding)
                
                # Classify as vulnerability if it contains certain keywords
                vuln_keywords = ['vulnerable', 'security', 'exploit', 'injection', 'xss']
                if any(keyword in finding.lower() for keyword in vuln_keywords):
                    results['vulnerabilities'].append(finding)
                    
        return results
```

### Phase 7: Multi-Tool Workflow Coordination (1 hour)
```python
# src/security/workflows/scan_workflows.py
class ScanWorkflows:
    def __init__(self, tool_adapter):
        self.tools = tool_adapter
        
    async def comprehensive_web_scan(self, target: str):
        """Execute comprehensive web application scan"""
        results = {}
        
        try:
            # 1. Network reconnaissance
            print(f"Starting network scan of {target}...")
            results['nmap'] = await self.tools.execute_tool(
                'nmap', target, {'scan_type': 'web_ports', 'timing': 'normal'}
            )
            
            # 2. Web server enumeration
            print(f"Starting web vulnerability scan...")
            results['nikto'] = await self.tools.execute_tool(
                'nikto', f"https://{target}"
            )
            
            # 3. Directory enumeration
            print(f"Starting directory enumeration...")
            results['dirb'] = await self.tools.execute_tool(
                'dirb', f"https://{target}"
            )
            
            # 4. SSL/TLS analysis
            if self._has_https(results['nmap']):
                print(f"Starting SSL analysis...")
                results['sslscan'] = await self.tools.execute_tool(
                    'sslscan', target
                )
                
            # 5. Aggregate and analyze results
            aggregated = self._aggregate_results(results)
            
            return {
                'success': True,
                'target': target,
                'individual_results': results,
                'aggregated_findings': aggregated,
                'workflow': 'comprehensive_web_scan'
            }
            
        except Exception as e:
            return {
                'success': False,
                'target': target,
                'error': str(e),
                'partial_results': results
            }
            
    def _aggregate_results(self, results):
        """Combine results from multiple tools"""
        aggregated = {
            'open_ports': [],
            'vulnerabilities': [],
            'directories': [],
            'ssl_issues': [],
            'recommendations': []
        }
        
        # Combine open ports from nmap
        if 'nmap' in results and results['nmap']['success']:
            aggregated['open_ports'] = results['nmap']['parsed_results']['open_ports']
            
        # Combine vulnerabilities from nikto
        if 'nikto' in results and results['nikto']['success']:
            aggregated['vulnerabilities'].extend(
                results['nikto']['parsed_results']['vulnerabilities']
            )
            
        # Generate recommendations
        aggregated['recommendations'] = self._generate_recommendations(aggregated)
        
        return aggregated
```

### Phase 8: Testing & Integration (1 hour)
```python
# Test complete tool integration system
async def test_complete_tool_integration():
    # 1. Initialize tool adapter
    adapter = UniversalToolAdapter()
    
    # 2. Test individual tools
    nmap_result = await adapter.execute_tool('nmap', 'scanme.nmap.org')
    assert nmap_result['success'] == True
    assert len(nmap_result['parsed_results']['open_ports']) > 0
    
    # 3. Test workflow coordination
    workflow = ScanWorkflows(adapter)
    web_scan_result = await workflow.comprehensive_web_scan('scanme.nmap.org')
    assert web_scan_result['success'] == True
    
    # 4. Test GUI automation
    burp_result = await adapter.execute_tool(
        'burpsuite', 'https://example.com', {'workflow': 'proxy_setup'}
    )
    assert burp_result['success'] == True
    
    print("Tool integration system working correctly!")

# Performance testing
def test_tool_performance():
    # Test concurrent tool execution
    # Test memory usage during scans
    # Test handling of large outputs
    pass
```

## Overview
Build a universal security tool integration system that can automate any cybersecurity tool through CLI commands, GUI automation, or API calls. This system provides a unified interface for 600+ Kali tools plus custom security software.

## Directory Structure
```
Samsung-AI-os/
├── kali-ai-os/
│   ├── src/
│   │   ├── security/
│   │   │   ├── __init__.py
│   │   │   ├── tools/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── universal_adapter.py
│   │   │   │   ├── tool_registry.py
│   │   │   │   ├── command_generator.py
│   │   │   │   ├── output_parser.py
│   │   │   │   └── execution_engine.py
│   │   │   ├── integrations/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── kali_tools/
│   │   │   │   │   ├── __init__.py
│   │   │   │   │   ├── nmap_integration.py
│   │   │   │   │   ├── burpsuite_integration.py
│   │   │   │   │   ├── metasploit_integration.py
│   │   │   │   │   ├── wireshark_integration.py
│   │   │   │   │   └── tool_templates.py
│   │   │   │   ├── custom_tools/
│   │   │   │   │   ├── __init__.py
│   │   │   │   │   ├── github_tools.py
│   │   │   │   │   ├── script_runner.py
│   │   │   │   │   └── dynamic_installer.py
│   │   │   │   ├── commercial/
│   │   │   │   │   ├── __init__.py
│   │   │   │   │   ├── nessus_integration.py
│   │   │   │   │   ├── acunetix_integration.py
│   │   │   │   │   └── gui_automation.py
│   │   │   │   └── web_tools/
│   │   │   │       ├── __init__.py
│   │   │   │       ├── shodan_api.py
│   │   │   │       ├── virustotal_api.py
│   │   │   │       └── browser_automation.py
│   │   │   ├── workflows/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── scan_workflows.py
│   │   │   │   ├── attack_workflows.py
│   │   │   │   ├── analysis_workflows.py
│   │   │   │   └── reporting_workflows.py
│   │   │   ├── results/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── result_aggregator.py
│   │   │   │   ├── evidence_manager.py
│   │   │   │   ├── report_generator.py
│   │   │   │   └── finding_correlator.py
│   │   │   └── config/
│   │   │       ├── __init__.py
│   │   │       ├── tool_configs/
│   │   │       ├── workflow_templates/
│   │   │       └── output_parsers/
│   │   └── tests/
│   │       ├── security/
│   │       │   ├── test_tool_integration.py
│   │       │   ├── test_command_generation.py
│   │       │   ├── test_output_parsing.py
│   │       │   ├── test_workflows.py
│   │       │   └── test_tool_discovery.py
│   │       └── fixtures/
│   │           ├── tool_outputs/
│   │           └── test_configs/
```

## Technology Stack
- **CLI Execution**: subprocess, asyncio, pexpect
- **GUI Automation**: PyAutoGUI, selenium, playwright
- **API Integration**: requests, aiohttp
- **Output Parsing**: BeautifulSoup, lxml, regex
- **Process Management**: psutil, signal handling

## Implementation Requirements

### Core Components

#### 1. Universal Tool Adapter
```python
# src/security/tools/universal_adapter.py
import subprocess
import asyncio
from typing import Dict, List, Any, Optional

class UniversalToolAdapter:
    def __init__(self):
        self.tool_registry = ToolRegistry()
        self.command_generator = CommandGenerator()
        self.output_parser = OutputParser()
        self.execution_engine = ExecutionEngine()
        
    async def execute_tool(self, tool_name: str, target: str, 
                          options: Dict = None) -> Dict[str, Any]:
        """Execute any security tool"""
        try:
            # Get tool configuration
            tool_config = self.tool_registry.get_tool_config(tool_name)
            
            # Generate command
            command = self.command_generator.generate(
                tool_name, target, options, tool_config
            )
            
            # Execute command
            result = await self.execution_engine.execute(command)
            
            # Parse output
            parsed_output = self.output_parser.parse(tool_name, result['output'])
            
            return {
                'success': True,
                'tool': tool_name,
                'command': command,
                'raw_output': result['output'],
                'findings': parsed_output,
                'execution_time': result['execution_time']
            }
            
        except Exception as e:
            return {
                'success': False,
                'tool': tool_name,
                'error': str(e)
            }
```

#### 2. Tool Registry
```python
# src/security/tools/tool_registry.py
class ToolRegistry:
    def __init__(self):
        self.tools = {}
        self.load_builtin_tools()
        
    def load_builtin_tools(self):
        """Load configurations for built-in Kali tools"""
        self.tools.update({
            'nmap': {
                'executable': 'nmap',
                'type': 'cli',
                'category': 'scanner',
                'common_args': {
                    'tcp_syn': '-sS',
                    'udp': '-sU',
                    'version': '-sV',
                    'os_detection': '-O',
                    'script_scan': '-sC'
                },
                'output_format': 'nmap_xml'
            },
            'burpsuite': {
                'executable': 'burpsuite',
                'type': 'gui',
                'category': 'web_scanner',
                'automation_method': 'gui_elements',
                'startup_time': 10
            }
            # ... 600+ more tools
        })
```

#### 3. Command Generator
```python
# src/security/tools/command_generator.py
class CommandGenerator:
    def __init__(self):
        self.llm_gateway = None  # Injected from AI layer
        
    def generate(self, tool_name: str, target: str, 
                options: Dict, tool_config: Dict) -> List[str]:
        """Generate appropriate command for tool"""
        
        if tool_config['type'] == 'cli':
            return self._generate_cli_command(tool_name, target, options, tool_config)
        elif tool_config['type'] == 'gui':
            return self._generate_gui_workflow(tool_name, target, options, tool_config)
        elif tool_config['type'] == 'api':
            return self._generate_api_call(tool_name, target, options, tool_config)
    
    def _generate_cli_command(self, tool_name: str, target: str, 
                             options: Dict, config: Dict) -> List[str]:
        """Generate CLI command"""
        cmd = [config['executable']]
        
        # Add common arguments based on intent
        if options.get('scan_type') == 'stealth':
            cmd.extend(['-sS', '-T2'])
        elif options.get('scan_type') == 'fast':
            cmd.extend(['-T4', '--min-rate=1000'])
        
        # Add target
        cmd.append(target)
        
        return cmd
```

### Integration Modules

#### 1. Nmap Integration
```python
# src/security/integrations/kali_tools/nmap_integration.py
class NmapIntegration:
    def __init__(self):
        self.xml_parser = NmapXMLParser()
        
    async def port_scan(self, target: str, ports: str = None) -> Dict:
        """Perform port scan"""
        cmd = ['nmap', '-sS', '-oX', '-']
        if ports:
            cmd.extend(['-p', ports])
        cmd.append(target)
        
        result = await self._execute_command(cmd)
        return self.xml_parser.parse(result['output'])
    
    async def service_detection(self, target: str) -> Dict:
        """Detect services and versions"""
        cmd = ['nmap', '-sV', '-sC', '-oX', '-', target]
        result = await self._execute_command(cmd)
        return self.xml_parser.parse(result['output'])
```

#### 2. Burp Suite GUI Integration
```python
# src/security/integrations/kali_tools/burpsuite_integration.py
class BurpSuiteIntegration:
    def __init__(self, desktop_controller):
        self.desktop = desktop_controller
        
    async def setup_proxy(self, target_url: str, proxy_port: int = 8080) -> Dict:
        """Setup Burp Suite proxy for target"""
        # Launch Burp Suite
        await self.desktop.open_application('burpsuite')
        await asyncio.sleep(10)  # Wait for startup
        
        # Navigate to Proxy tab
        proxy_tab = await self.desktop.find_element('burp_proxy_tab.png')
        await self.desktop.click(proxy_tab)
        
        # Configure target scope
        scope_button = await self.desktop.find_element('burp_scope_button.png')
        await self.desktop.click(scope_button)
        
        # Add target URL to scope
        await self.desktop.type_text(target_url)
        
        return {'proxy_configured': True, 'port': proxy_port}
```

### Workflow System

#### 1. Scan Workflows
```python
# src/security/workflows/scan_workflows.py
class ScanWorkflows:
    def __init__(self, tool_adapter):
        self.tools = tool_adapter
        
    async def comprehensive_web_scan(self, target: str) -> Dict:
        """Comprehensive web application scan"""
        results = {}
        
        # 1. Port scan
        results['nmap'] = await self.tools.execute_tool(
            'nmap', target, {'scan_type': 'web_ports'}
        )
        
        # 2. Web server enumeration
        results['nikto'] = await self.tools.execute_tool(
            'nikto', target
        )
        
        # 3. Directory enumeration
        results['dirb'] = await self.tools.execute_tool(
            'dirb', target
        )
        
        # 4. SSL/TLS testing
        results['sslscan'] = await self.tools.execute_tool(
            'sslscan', target
        )
        
        return self._aggregate_results(results)
```

## Testing Strategy

### Unit Tests (80% coverage minimum)
```bash
cd kali-ai-os
python -m pytest tests/security/ -v --cov=src.security --cov-report=html

# Test categories:
# - Tool discovery and registration
# - Command generation
# - Output parsing
# - Workflow execution
# - Error handling
```

### Integration Tests
```bash
# Test with real tools (if available)
python -m pytest tests/security/test_tool_integration.py -v -k "integration"

# Test GUI automation
python -m pytest tests/security/test_gui_tools.py -v

# Test API integrations
python -m pytest tests/security/test_api_tools.py -v
```

## Deployment & Validation

### Setup Commands
```bash
# 1. Install security tool dependencies
sudo apt update
sudo apt install -y nmap nikto dirb gobuster
sudo apt install -y burpsuite zaproxy wireshark

# 2. Install Python dependencies
pip install -r requirements/security_requirements.txt

# 3. Initialize tool registry
python -c "
from src.security.tools.tool_registry import ToolRegistry
registry = ToolRegistry()
tools = registry.discover_installed_tools()
print(f'Found {len(tools)} security tools')
"

# 4. Test tool integration
python -m pytest tests/security/ -v
```

### Success Metrics
- ✅ 50+ security tools integrated
- ✅ CLI and GUI automation working
- ✅ Workflow execution functional
- ✅ Output parsing accurate (90%+)
- ✅ Ready for memory system integration