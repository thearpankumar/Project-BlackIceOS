# Task 4: AI Processing Layer

## What This Task Is About
This task creates the "brain" of Kali AI-OS - the intelligent system that understands user commands and orchestrates security operations:
- **LLM Integration** - Connects to Google GenAI and Groq for natural language understanding. It uses web search to access information up to 2025 to ensure responses are current.
- **Command Intelligence** - Converts "scan example.com for vulnerabilities" into specific tool workflows
- **Memory Management** - Maintains context across conversations and remembers user preferences
- **Security-First AI** - Validates all AI responses to prevent dangerous operations
- **Multi-Provider Fallback** - Switches between AI providers for reliability

## Why This Task Is Critical
- **Natural Language Interface**: Users can speak naturally instead of memorizing command syntax
- **Intelligent Workflows**: AI chooses the right tools and parameters automatically
- **Context Awareness**: AI remembers previous scans and builds on past knowledge
- **Safety Integration**: All AI responses are validated by the safety framework

## How to Complete This Task - Step by Step

### Phase 1: Setup AI Environment (45 minutes)
```bash
# 1. Install AI processing dependencies
pip install google-generativeai groq
pip install spacy nltk sentence-transformers
pip install redis diskcache  # For caching
pip install aiohttp asyncio-throttle  # For async processing

# 2. Download language models
python -c "
import spacy
spacy.cli.download('en_core_web_sm')
"

# 3. Setup environment variables (will be provided by auth server)
# GOOGLE_API_KEY and GROQ_API_KEY will come from auth server
# Never store these in code or config files
```

### Phase 2: Write AI Tests First (1.5 hours)
```python
# tests/ai/test_llm_gateway.py
def test_basic_command_processing():
    """Test AI can process basic security commands"""
    # Input: "scan example.com"
    # Expected: Workflow with nmap scan
    
def test_cybersecurity_context_understanding():
    """Test AI understands security concepts"""
    # Input: "test web app for SQL injection"
    # Expected: Workflow with SQLMap and Burp Suite
    
def test_dangerous_command_blocking():
    """Test AI blocks dangerous operations"""
    # Input: "delete all files"
    # Expected: Command blocked by safety system
    
def test_memory_context_integration():
    """Test AI remembers previous context"""
    # First: "I'm testing example.com"
    # Then: "now scan for vulnerabilities"
    # Expected: AI remembers target is example.com
    
def test_api_key_security():
    """Test API keys are handled securely"""
    # Verify keys never written to disk
    # Verify keys are cleared on timeout
```

### Phase 3: LLM Gateway Core (2 hours)
```python
# src/ai/core/llm_gateway.py
import asyncio
from src.ai.security.key_manager import APIKeyManager
from src.ai.providers.google_genai_client import GoogleGenAIClient
from src.ai.providers.groq_client import GroqClient

class LLMGateway:
    def __init__(self, key_manager):
        self.key_manager = key_manager
        self.google_genai_client = None
        self.groq_client = None
        self.current_context = {}
        
    async def process_command(self, command, context=None):
        """Main command processing pipeline"""
        # 1. Sanitize input command
        sanitized = self._sanitize_input(command)
        
        # 2. Build full context with memory
        full_context = await self._build_context(sanitized, context)
        
        # 3. Generate AI response
        try:
            response = await self._get_ai_response(sanitized, full_context)
        except Exception as e:
            # Fallback to secondary provider
            response = await self._fallback_ai_response(sanitized, full_context)
            
        # 4. Validate response for safety
        if not self._validate_response(response):
            return {"success": False, "error": "AI response blocked by safety system"}
            
        # 5. Extract actionable workflow
        workflow = self._extract_workflow(response)
        
        return {
            "success": True,
            "response": response['content'],
            "workflow": workflow,
            "confidence": response['confidence']
        }
        
    async def _get_ai_response(self, command, context):
        """Get response from primary AI provider (Google GenAI)"""
        if not self.google_genai_client:
            api_key = self.key_manager.get_google_api_key()
            self.google_genai_client = GoogleGenAIClient(api_key)
            
        prompt = self._build_security_prompt(command, context)
        return await self.google_genai_client.generate(prompt)
    
    async def _fallback_ai_response(self, command, context):
        """Get response from fallback AI provider (Groq)"""
        if not self.groq_client:
            api_key = self.key_manager.get_groq_api_key()
            self.groq_client = GroqClient(api_key)
            
        prompt = self._build_security_prompt(command, context)
        return await self.groq_client.generate(prompt)
```

### Phase 4: Security-Focused Prompt Engineering (1 hour)
```python
# src/ai/core/prompt_templates.py
class SecurityPromptTemplates:
    def __init__(self):
        self.system_prompt = """
You are a cybersecurity AI assistant for Kali AI-OS. 

CRITICAL SECURITY RULES:
1. ONLY suggest authorized security testing commands
2. NEVER suggest destructive operations (rm, del, format, etc.)
3. ALWAYS validate that targets are authorized for testing
4. Recommend appropriate security tools for each task
5. Provide step-by-step workflows for complex operations

Available security tools: nmap, nikto, dirb, burpsuite, sqlmap, wireshark, metasploit
"""
        
    def build_command_prompt(self, user_command, context):
        """Build prompt for command processing"""
        return f"""
{self.system_prompt}

User context: {context.get('target_authorization', 'Not specified')}
Previous commands: {context.get('command_history', [])}

User command: "{user_command}"

Please provide:
1. Interpretation of the user's intent
2. Recommended security tools to use
3. Specific command parameters
4. Expected outcomes
5. Safety considerations

Respond in JSON format with workflow steps.
"""
```

### Phase 5: API Key Management (1 hour)
```python
# src/ai/security/key_manager.py  
import time
from cryptography.fernet import Fernet

class APIKeyManager:
    def __init__(self):
        self.keys = {}  # Memory-only storage
        self.key_expiry = {}
        self.encryption_key = None
        
    def store_encrypted_keys(self, encrypted_keys, encryption_key):
        """Receive encrypted keys from auth server"""
        # NEVER store keys on disk - memory only
        self.encryption_key = encryption_key
        
        # Decrypt keys into memory
        fernet = Fernet(encryption_key)
        decrypted_data = fernet.decrypt(encrypted_keys.encode())
        
        import json
        self.keys = json.loads(decrypted_data.decode())
        
        # Set automatic expiry (24 hours)
        expiry_time = time.time() + (24 * 60 * 60)
        for key_name in self.keys:
            self.key_expiry[key_name] = expiry_time
            
    def get_google_api_key(self):
        """Get Google API key if valid"""
        return self._get_key_if_valid('google_api_key')
        
    def get_groq_api_key(self):
        """Get Groq API key if valid"""
        return self._get_key_if_valid('groq_api_key')
        
    def _get_key_if_valid(self, key_name):
        """Get key only if not expired"""
        if key_name not in self.keys:
            return None
            
        if time.time() > self.key_expiry.get(key_name, 0):
            # Key expired - remove from memory
            del self.keys[key_name]
            del self.key_expiry[key_name]
            return None
            
        return self.keys[key_name]
        
    def clear_all_keys(self):
        """Clear all keys from memory (on shutdown/logout)"""
        self.keys.clear()
        self.key_expiry.clear()
        self.encryption_key = None
```

### Phase 6: Intent Recognition & Command Parsing (1.5 hours)
```python
# src/ai/processing/intent_recognizer.py
import spacy
import re

class IntentRecognizer:
    def __init__(self):
        self.nlp = spacy.load("en_core_web_sm")
        self.security_intents = {
            'scan': ['scan', 'probe', 'test', 'check', 'examine'],
            'attack': ['exploit', 'attack', 'penetrate', 'break'],
            'analyze': ['analyze', 'investigate', 'review', 'inspect'],
            'configure': ['setup', 'configure', 'prepare', 'initialize']
        }
        
    def recognize_intent(self, command):
        """Extract intent and entities from command"""
        doc = self.nlp(command.lower())
        
        # Extract primary intent
        intent = self._extract_intent(doc)
        
        # Extract entities (IPs, domains, ports)
        entities = self._extract_entities(command)
        
        # Extract security tools mentioned
        tools = self._extract_tools(command)
        
        return {
            'intent': intent,
            'entities': entities,
            'tools': tools,
            'confidence': self._calculate_confidence(intent, entities)
        }
        
    def _extract_entities(self, text):
        """Extract IPs, domains, ports from text"""
        entities = {}
        
        # IP addresses
        ip_pattern = r'\b(?:\d{1,3}\.){3}\d{1,3}\b'
        entities['ips'] = re.findall(ip_pattern, text)
        
        # Domain names
        domain_pattern = r'\b[a-zA-Z0-9-]+\.[a-zA-Z]{2,}\b'
        entities['domains'] = re.findall(domain_pattern, text)
        
        # Port numbers
        port_pattern = r'\bport\s+(\d+)\b'
        entities['ports'] = [int(p) for p in re.findall(port_pattern, text)]
        
        return entities
```

### Phase 7: Provider Integration (1 hour)
```python
# src/ai/providers/google_genai_client.py
import google.generativeai as genai
import asyncio

class GoogleGenAIClient:
    def __init__(self, api_key):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-1.5-pro-latest')
        
    async def generate(self, prompt, context=None):
        """Generate response using Google GenAI"""
        try:
            # In a real async environment, you'd use an async library
            # but the google-generativeai library is currently synchronous.
            # We can run it in a thread pool to avoid blocking.
            loop = asyncio.get_running_loop()
            response = await loop.run_in_executor(
                None, 
                self.model.generate_content,
                [prompt['system'], prompt['user']]
            )
            
            return {
                'content': response.text,
                'confidence': 0.9,  # Calculate based on response
                'provider': 'googlegenai'
            }
            
        except Exception as e:
            raise Exception(f"Google GenAI API error: {e}")

# src/ai/providers/groq_client.py  
from groq import Groq

class GroqClient:
    def __init__(self, api_key):
        self.client = Groq(api_key=api_key)
        
    async def generate(self, prompt, context=None):
        """Generate response using Groq"""
        try:
            response = self.client.chat.completions.create(
                model="llama3-70b-8192",
                messages=[
                    {"role": "system", "content": prompt['system']},
                    {"role": "user", "content": prompt['user']}
                ],
                max_tokens=4000,
                temperature=0.1,
            )
            
            return {
                'content': response.choices[0].message.content,
                'confidence': 0.9,
                'provider': 'groq'
            }
            
        except Exception as e:
            raise Exception(f"Groq API error: {e}")
```

### Phase 8: Integration & Testing (1 hour)
```python
# Test complete AI processing pipeline
async def test_complete_ai_pipeline():
    # 1. Setup components
    key_manager = APIKeyManager()
    # Simulate receiving keys from auth server
    key_manager.store_encrypted_keys(encrypted_keys, encryption_key)
    
    # 2. Create AI gateway
    ai_gateway = LLMGateway(key_manager)
    
    # 3. Test command processing
    result = await ai_gateway.process_command(
        "scan example.com for web vulnerabilities",
        context={'authorized_targets': ['example.com']}
    )
    
    # 4. Verify results
    assert result['success'] == True
    assert 'workflow' in result
    assert 'nmap' in result['workflow']['tools']
    
    print("AI processing pipeline working correctly!")

# Run performance tests
def test_ai_performance():
    # Test response time < 3 seconds
    # Test memory usage < 512MB
    # Test concurrent request handling
    pass
```

## Overview
Build the central AI processing system that integrates LLM APIs, manages memory, processes voice/text commands, and generates intelligent responses. This system securely handles API keys received from the auth server and orchestrates all AI-driven security operations.

## Directory Structure
```
Samsung-AI-os/
├── kali-ai-os/
│   ├── src/
│   │   ├── ai/
│   │   │   ├── __init__.py
│   │   │   ├── core/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── llm_gateway.py
│   │   │   │   ├── memory_manager.py
│   │   │   │   ├── context_processor.py
│   │   │   │   ├── response_generator.py
│   │   │   │   └── session_handler.py
│   │   │   ├── providers/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── google_genai_client.py
│   │   │   │   ├── groq_client.py
│   │   │   │   ├── provider_manager.py
│   │   │   │   └── fallback_handler.py
│   │   │   ├── processing/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── intent_recognizer.py
│   │   │   │   ├── command_parser.py
│   │   │   │   ├── parameter_extractor.py
│   │   │   │   ├── workflow_planner.py
│   │   │   │   └── action_coordinator.py
│   │   │   ├── memory/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── short_term_memory.py
│   │   │   │   ├── working_memory.py
│   │   │   │   ├── context_window.py
│   │   │   │   └── memory_optimizer.py
│   │   │   ├── security/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── key_manager.py
│   │   │   │   ├── api_security.py
│   │   │   │   ├── prompt_sanitizer.py
│   │   │   │   └── response_validator.py
│   │   │   └── config/
│   │   │       ├── __init__.py
│   │   │       ├── ai_config.py
│   │   │       ├── model_settings.py
│   │   │       └── prompt_templates.py
│   │   └── tests/
│   │       ├── ai/
│   │       │   ├── __init__.py
│   │       │   ├── test_llm_gateway.py
│   │       │   ├── test_memory_manager.py
│   │       │   ├── test_intent_recognition.py
│   │       │   ├── test_command_parsing.py
│   │       │   ├── test_api_security.py
│   │       │   └── test_providers.py
│   │       └── fixtures/
│   │           ├── sample_commands.json
│   │           ├── test_contexts.json
│   │           └── mock_responses.json
│   └── requirements/
│       └── ai_requirements.txt
```

## Technology Stack
- **LLM APIs**: Google GenAI (Gemini), Groq (Llama 3)
- **Memory Management**: Redis 5.0.1, SQLite for persistence
- **Request Handling**: aiohttp 3.9.0, asyncio
- **Security**: cryptography 41.0.7, JWT validation
- **NLP Processing**: spacy 3.7.0, nltk 3.8.1
- **Caching**: diskcache 5.6.3

### 2. Memory Management Tests
```python
# tests/ai/test_memory_manager.py
def test_short_term_memory():
    """Test short-term memory operations"""
    from src.ai.memory.short_term_memory import ShortTermMemory
    
    memory = ShortTermMemory(max_size=100)
    
    # Add conversation context
    memory.add_context("user", "scan example.com")
    memory.add_context("assistant", "Running nmap scan...")
    
    # Retrieve context
    context = memory.get_recent_context(limit=2)
    assert len(context) == 2
    assert context[0]['role'] == 'user'
    assert 'example.com' in context[0]['content']

def test_working_memory():
    """Test working memory for active tasks"""
    from src.ai.memory.working_memory import WorkingMemory
    
    memory = WorkingMemory()
    
    # Start task
    task_id = memory.start_task("network_scan", {
        'target': 'example.com',
        'tools': ['nmap', 'nikto']
    })
    
    # Update task progress
    memory.update_task(task_id, {'status': 'in_progress', 'tool': 'nmap'})
    
    # Get task state
    task = memory.get_task(task_id)
    assert task['status'] == 'in_progress'
    assert task['tool'] == 'nmap'

def test_context_window_management():
    """Test context window optimization"""
    from src.ai.memory.context_window import ContextWindow
    
    window = ContextWindow(max_tokens=4000)
    
    # Add large context
    large_text = "word " * 2000  # ~2000 tokens
    window.add_text(large_text)
    
    # Should fit within window
    assert window.get_token_count() < 4000
    
    # Add more text
    window.add_text(large_text)
    
    # Should automatically trim older content
    assert window.get_token_count() < 4000
    assert window.was_trimmed() == True
```

## Implementation Requirements

### Core Components

#### 1. LLM Gateway
```python
# src/ai/core/llm_gateway.py
import asyncio
from typing import Dict, Any, Optional, List
from src.ai.providers.provider_manager import ProviderManager
from src.ai.security.prompt_sanitizer import PromptSanitizer
from src.ai.memory.memory_manager import MemoryManager

class LLMGateway:
    def __init__(self, key_manager):
        self.key_manager = key_manager
        self.provider_manager = ProviderManager(key_manager)
        self.prompt_sanitizer = PromptSanitizer()
        self.memory_manager = MemoryManager()
        self.active_requests = {}
        
    async def process_command(self, command: str, context: Dict = None) -> Dict[str, Any]:
        """Process user command through LLM"""
        try:
            # Sanitize input
            sanitized_command = self.prompt_sanitizer.sanitize(command)
            
            # Build context
            full_context = await self._build_context(sanitized_command, context)
            
            # Generate response
            response = await self._generate_response(sanitized_command, full_context)
            
            # Validate response
            if not self._validate_response(response):
                return {'success': False, 'error': 'Invalid response generated'}
            
            # Update memory
            await self.memory_manager.add_interaction(sanitized_command, response)
            
            return {
                'success': True,
                'response': response['content'],
                'confidence': response['confidence'],
                'suggested_tools': response.get('tools', []),
                'workflow': response.get('workflow', [])
            }
            
        except Exception as e:
            return await self._handle_error(e, command)
    
    async def _generate_response(self, command: str, context: Dict) -> Dict:
        """Generate response using available providers"""
        # Try primary provider (Google GenAI)
        try:
            return await self.provider_manager.generate_with_google_genai(command, context)
        except Exception as e:
            # Fallback to secondary provider (Groq)
            return await self.provider_manager.generate_with_groq(command, context)
    
    def _validate_response(self, response: Dict) -> bool:
        """Validate LLM response for safety"""
        content = response.get('content', '')
        
        # Check for dangerous commands
        dangerous_patterns = [
            r'rm\s+-rf\s+/',
            r'del\s+/.*',
            r'format\s+c:',
            r'dd\s+if=.*of=/dev/.*'
        ]
        
        for pattern in dangerous_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                return False
        
        return True
```

#### 2. API Key Manager
```python
# src/ai/security/key_manager.py
import time
from typing import Optional
from cryptography.fernet import Fernet

class APIKeyManager:
    def __init__(self):
        self.keys = {}  # Memory-only storage
        self.key_expiry = {}
        self.encryption_key = None
        
    def store_encrypted_keys(self, encrypted_keys: str, encryption_key: bytes):
        """Store encrypted API keys in memory"""
        self.encryption_key = encryption_key
        
        # Decrypt keys
        fernet = Fernet(encryption_key)
        decrypted_data = fernet.decrypt(encrypted_keys.encode())
        
        # Parse and store keys
        import json
        self.keys = json.loads(decrypted_data.decode())
        
        # Set expiry (24 hours)
        expiry_time = time.time() + (24 * 60 * 60)
        for key_name in self.keys:
            self.key_expiry[key_name] = expiry_time
    
    def get_google_api_key(self) -> Optional[str]:
        """Get Google API key"""
        return self._get_key('google_api_key')
    
    def get_groq_api_key(self) -> Optional[str]:
        """Get Groq API key"""
        return self._get_key('groq_api_key')
    
    def _get_key(self, key_name: str) -> Optional[str]:
        """Get API key with expiry check"""
        if key_name not in self.keys:
            return None
            
        if time.time() > self.key_expiry.get(key_name, 0):
            # Key expired
            del self.keys[key_name]
            del self.key_expiry[key_name]
            return None
            
        return self.keys[key_name]
    
    def clear_keys(self):
        """Clear all keys from memory"""
        self.keys.clear()
        self.key_expiry.clear()
        self.encryption_key = None
```

#### 3. Intent Recognizer
```python
# src/ai/processing/intent_recognizer.py
import spacy
from typing import Dict, List

class IntentRecognizer:
    def __init__(self):
        self.nlp = spacy.load("en_core_web_sm")
        self.security_intents = {
            'scan': ['scan', 'probe', 'examine', 'check', 'test'],
            'attack': ['exploit', 'attack', 'penetrate', 'break'],
            'analyze': ['analyze', 'investigate', 'review', 'assess'],
            'configure': ['setup', 'configure', 'prepare', 'initialize'],
            'monitor': ['monitor', 'watch', 'observe', 'track']
        }
        
    def recognize_intent(self, command: str) -> Dict[str, Any]:
        """Recognize intent from user command"""
        doc = self.nlp(command.lower())
        
        # Extract intent
        intent = self._extract_intent(doc)
        
        # Extract entities
        entities = self._extract_entities(doc)
        
        # Extract security tools mentioned
        tools = self._extract_security_tools(doc)
        
        return {
            'intent': intent,
            'entities': entities,
            'tools': tools,
            'confidence': self._calculate_confidence(intent, entities, tools)
        }
    
    def _extract_intent(self, doc) -> str:
        """Extract primary intent from command"""
        for token in doc:
            for intent, keywords in self.security_intents.items():
                if token.lemma_ in keywords:
                    return intent
        return 'general'
    
    def _extract_entities(self, doc) -> Dict[str, List[str]]:
        """Extract named entities (IPs, URLs, etc.)"""
        entities = {
            'ip_addresses': [],
            'domains': [],
            'ports': [],
            'files': []
        }
        
        # Use regex patterns and NER
        import re
        text = doc.text
        
        # IP addresses
        ip_pattern = r'\b(?:\d{1,3}\.){3}\d{1,3}\b'
        entities['ip_addresses'] = re.findall(ip_pattern, text)
        
        # Domain names
        domain_pattern = r'\b[a-zA-Z0-9-]+\.[a-zA-Z]{2,}\b'
        entities['domains'] = re.findall(domain_pattern, text)
        
        # Ports
        port_pattern = r'\bport\s+(\d+)\b'
        entities['ports'] = [int(p) for p in re.findall(port_pattern, text)]
        
        return entities
```

#### 4. Provider Manager
```python
# src/ai/providers/provider_manager.py
from src.ai.providers.google_genai_client import GoogleGenAIClient
from src.ai.providers.groq_client import GroqClient

class ProviderManager:
    def __init__(self, key_manager):
        self.key_manager = key_manager
        self.google_genai_client = None
        self.groq_client = None
        
    async def generate_with_google_genai(self, prompt: str, context: Dict) -> Dict:
        """Generate response using Google GenAI"""
        if not self.google_genai_client:
            api_key = self.key_manager.get_google_api_key()
            if not api_key:
                raise Exception("Google GenAI API key not available")
            self.google_genai_client = GoogleGenAIClient(api_key)
        
        return await self.google_genai_client.generate(prompt, context)
    
    async def generate_with_groq(self, prompt: str, context: Dict) -> Dict:
        """Generate response using Groq"""
        if not self.groq_client:
            api_key = self.key_manager.get_groq_api_key()
            if not api_key:
                raise Exception("Groq API key not available")
            self.groq_client = GroqClient(api_key)
        
        return await self.groq_client.generate(prompt, context)
```

### Security Features

#### 1. Prompt Sanitization
```python
# src/ai/security/prompt_sanitizer.py
import re
from typing import str

class PromptSanitizer:
    def __init__(self):
        self.dangerous_patterns = [
            r'ignore\s+previous\s+instructions',
            r'system\s*:',
            r'<\s*script\s*>',
            r'javascript\s*:',
            r'eval\s*\(',
            r'exec\s*\('
        ]
        
    def sanitize(self, prompt: str) -> str:
        """Sanitize user prompt to prevent injection"""
        sanitized = prompt
        
        # Remove dangerous patterns
        for pattern in self.dangerous_patterns:
            sanitized = re.sub(pattern, '[FILTERED]', sanitized, flags=re.IGNORECASE)
        
        # Limit length
        if len(sanitized) > 10000:
            sanitized = sanitized[:10000] + "... [TRUNCATED]"
        
        return sanitized
```

#### 2. Response Validator
```python
# src/ai/security/response_validator.py
class ResponseValidator:
    def __init__(self):
        self.blocked_commands = [
            'rm -rf', 'format', 'del /s', 'shutdown',
            'reboot', 'halt', 'poweroff'
        ]
        
    def validate_response(self, response: str) -> bool:
        """Validate LLM response for safety"""
        response_lower = response.lower()
        
        # Check for blocked commands
        for cmd in self.blocked_commands:
            if cmd in response_lower:
                return False
        
        # Check for potential malware URLs
        if self._contains_malware_indicators(response):
            return False
        
        return True
    
    def _contains_malware_indicators(self, response: str) -> bool:
        """Check for malware indicators"""
        malware_indicators = [
            'curl.*|.*bash',
            'wget.*|.*sh',
            'powershell.*-enc',
            'base64.*-d.*|.*bash'
        ]
        
        for indicator in malware_indicators:
            if re.search(indicator, response, re.IGNORECASE):
                return True
        
        return False
```

## Testing Strategy

### Unit Tests (90% coverage minimum)
```bash
# Install AI testing dependencies
pip install pytest pytest-cov pytest-asyncio pytest-mock

# Run AI processing tests
cd kali-ai-os
python -m pytest tests/ai/ -v --cov=src.ai --cov-report=html

# Test categories:
# - LLM integration
# - Memory management
# - Intent recognition
# - Security validation
# - Provider fallback
# - Error handling
```

### Integration Tests
```bash
# Test with auth server
python -m pytest tests/ai/test_auth_integration.py -v

# Test memory persistence
python -m pytest tests/ai/test_memory_integration.py -v

# Test provider switching
python -m pytest tests/ai/test_provider_fallback.py -v
```

### Performance Tests
```python
def test_response_latency():
    """Test AI response speed"""
    import time
    
    start_time = time.time()
    result = llm_gateway.process_command("scan example.com")
    response_time = time.time() - start_time
    
    assert response_time < 3.0  # Under 3 seconds

def test_memory_efficiency():
    """Test memory usage optimization"""
    import psutil
    import os
    
    process = psutil.Process(os.getpid())
    initial_memory = process.memory_info().rss
    
    # Process 100 commands
    for i in range(100):
        llm_gateway.process_command(f"test command {i}")
    
    final_memory = process.memory_info().rss
    memory_increase = final_memory - initial_memory
    
    # Memory increase should be reasonable
    assert memory_increase < 100 * 1024 * 1024  # Under 100MB
```

## Deployment & Testing

### Setup Commands
```bash
# 1. Install dependencies
pip install -r requirements/ai_requirements.txt

# 2. Download language models
python -c "
import spacy
spacy.cli.download('en_core_web_sm')
"

# 3. Initialize AI system
python -c "
from src.ai.core.llm_gateway import LLMGateway
from src.ai.security.key_manager import APIKeyManager
key_manager = APIKeyManager()
gateway = LLMGateway(key_manager)
print('AI processing layer initialized!')
"

# 4. Run comprehensive tests
python -m pytest tests/ai/ -v --cov=src.ai
```

### Validation Criteria
✅ **Must pass before considering task complete:**

1. **Functionality Tests**
   - LLM integration working with both providers
   - Memory management operational
   - Intent recognition accurate (85%+)
   - Security validation blocking dangerous commands

2. **Performance Tests**
   - Response time < 3 seconds
   - Memory usage optimized
   - Concurrent request handling
   - Provider fallback under 5 seconds

3. **Security Tests**
   - API keys never stored on disk
   - Prompt injection prevented
   - Response validation working
   - All dangerous commands blocked

4. **Integration Tests**
   - Auth server communication working
   - Memory persistence functional
   - Error recovery operational
   - Provider switching seamless

### Success Metrics
- ✅ 85%+ intent recognition accuracy
- ✅ <3 second response time
- ✅ 100% dangerous command blocking
- ✅ Memory usage under 512MB
- ✅ Ready for security tool integration

## Configuration Files

### ai_requirements.txt
```txt
# LLM APIs
openai==1.12.0
anthropic==0.8.1

# Memory Management
redis==5.0.1
diskcache==5.6.3

# Async Processing
aiohttp==3.9.0
asyncio-throttle==1.0.2

# NLP Processing
spacy==3.7.0
nltk==3.8.1

# Security
cryptography==41.0.7
PyJWT==2.8.0

# Testing
pytest==7.4.0
pytest-asyncio==0.21.1
pytest-mock==3.11.1
pytest-cov==4.1.0
```

### AI Configuration
```python
# src/ai/config/ai_config.py
AI_CONFIG = {
    'openai': {
        'model': 'gpt-4-turbo-preview',
        'max_tokens': 4000,
        'temperature': 0.1,
        'timeout': 30
    },
    'anthropic': {
        'model': 'claude-3-sonnet-20240229',
        'max_tokens': 4000,
        'temperature': 0.1,
        'timeout': 30
    },
    'memory': {
        'max_context_tokens': 8000,
        'session_timeout': 3600,
        'cache_size': 1000
    },
    'security': {
        'enable_validation': True,
        'block_dangerous_commands': True,
        'sanitize_prompts': True,
        'log_all_interactions': True
    }
}
```

## Next Steps
After completing this task:
1. Integrate with voice and desktop automation
2. Create cybersecurity-specific prompts
3. Optimize for security use cases
4. Proceed to Task 5: Security Tool Integration

## Troubleshooting
Common issues and solutions:
- **API key errors**: Check auth server connection and key format
- **Slow responses**: Optimize prompts and enable caching
- **Memory issues**: Tune context window and garbage collection
- **Provider failures**: Verify fallback configuration