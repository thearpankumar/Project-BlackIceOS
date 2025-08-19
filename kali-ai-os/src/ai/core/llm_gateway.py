import asyncio
from typing import Dict, Any, Optional
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
        try:
            sanitized_command = self.prompt_sanitizer.sanitize(command)
            full_context = await self._build_context(sanitized_command, context)
            response = await self._generate_response(sanitized_command, full_context)
            if not self._validate_response(response):
                return {'success': False, 'error': 'Invalid response generated'}
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
        try:
            return await self.provider_manager.generate_with_google_genai(command, context)
        except Exception as e:
            return await self.provider_manager.generate_with_groq(command, context)

    def _validate_response(self, response: Dict) -> bool:
        content = response.get('content', '')
        import re
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
