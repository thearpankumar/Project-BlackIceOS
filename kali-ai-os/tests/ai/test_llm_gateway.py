
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.ai.core.llm_gateway import LLMGateway

@pytest.fixture
def mock_key_manager():
    km = MagicMock()
    km.get_google_api_key.return_value = 'fake-google-key'
    km.get_groq_api_key.return_value = 'fake-groq-key'
    return km

@pytest.fixture
def mock_provider_manager():
    pm = MagicMock()
    pm.generate_with_google_genai = AsyncMock()
    pm.generate_with_groq = AsyncMock()
    return pm

@pytest.fixture
def mock_prompt_sanitizer():
    sanitizer = MagicMock()
    sanitizer.sanitize.side_effect = lambda x: x
    return sanitizer

@pytest.fixture
def mock_memory_manager():
    mm = MagicMock()
    mm.add_interaction = AsyncMock()
    mm.get_recent_context = MagicMock(return_value=[{'role': 'user', 'content': "I'm testing example.com"}])
    return mm

@pytest.mark.asyncio
async def test_basic_command_processing(mock_key_manager, mock_provider_manager, mock_prompt_sanitizer, mock_memory_manager):
    # Setup
    response = {'content': 'Scan complete', 'confidence': 0.95, 'tools': ['nmap'], 'workflow': ['nmap scan']}
    mock_provider_manager.generate_with_google_genai.return_value = response
    with patch('src.ai.core.llm_gateway.ProviderManager', return_value=mock_provider_manager), \
         patch('src.ai.core.llm_gateway.PromptSanitizer', return_value=mock_prompt_sanitizer), \
         patch('src.ai.core.llm_gateway.MemoryManager', return_value=mock_memory_manager):
        gateway = LLMGateway(mock_key_manager)
        result = await gateway.process_command('scan example.com')
        assert result['success']
        assert 'nmap' in result['suggested_tools']
        assert any('nmap' in step for step in result['workflow'])

@pytest.mark.asyncio
async def test_cybersecurity_context_understanding(mock_key_manager, mock_provider_manager, mock_prompt_sanitizer, mock_memory_manager):
    response = {'content': 'SQL injection test', 'confidence': 0.92, 'tools': ['SQLMap', 'Burp Suite'], 'workflow': ['SQLMap scan', 'Burp Suite intercept']}
    mock_provider_manager.generate_with_google_genai.return_value = response
    with patch('src.ai.core.llm_gateway.ProviderManager', return_value=mock_provider_manager), \
         patch('src.ai.core.llm_gateway.PromptSanitizer', return_value=mock_prompt_sanitizer), \
         patch('src.ai.core.llm_gateway.MemoryManager', return_value=mock_memory_manager):
        gateway = LLMGateway(mock_key_manager)
        result = await gateway.process_command('test web app for SQL injection')
        assert result['success']
        assert 'SQLMap' in result['suggested_tools']
        assert 'Burp Suite' in result['suggested_tools']

@pytest.mark.asyncio
async def test_dangerous_command_blocking(mock_key_manager, mock_provider_manager, mock_prompt_sanitizer, mock_memory_manager):
    dangerous_response = {'content': 'rm -rf /', 'confidence': 0.99, 'tools': [], 'workflow': ['rm -rf /']}
    mock_provider_manager.generate_with_google_genai.return_value = dangerous_response
    with patch('src.ai.core.llm_gateway.ProviderManager', return_value=mock_provider_manager), \
         patch('src.ai.core.llm_gateway.PromptSanitizer', return_value=mock_prompt_sanitizer), \
         patch('src.ai.core.llm_gateway.MemoryManager', return_value=mock_memory_manager):
        gateway = LLMGateway(mock_key_manager)
        result = await gateway.process_command('delete all files')
        assert not result['success']
        assert 'error' in result

@pytest.mark.asyncio
async def test_memory_context_integration(mock_key_manager, mock_provider_manager, mock_prompt_sanitizer, mock_memory_manager):
    # Simulate context retention
    first_response = {'content': 'Context set', 'confidence': 0.9, 'tools': [], 'workflow': []}
    second_response = {'content': 'Scan example.com', 'confidence': 0.95, 'tools': ['nmap'], 'workflow': ['nmap scan example.com']}
    mock_provider_manager.generate_with_google_genai.side_effect = [first_response, second_response]
    with patch('src.ai.core.llm_gateway.ProviderManager', return_value=mock_provider_manager), \
         patch('src.ai.core.llm_gateway.PromptSanitizer', return_value=mock_prompt_sanitizer), \
         patch('src.ai.core.llm_gateway.MemoryManager', return_value=mock_memory_manager):
        gateway = LLMGateway(mock_key_manager)
        await gateway.process_command("I'm testing example.com")
        result = await gateway.process_command('now scan for vulnerabilities')
        assert result['success']
        assert any('example.com' in step for step in result['workflow'])

def test_api_key_security(mock_key_manager):
    # Keys should only be in memory
    assert hasattr(mock_key_manager, 'keys')
    assert isinstance(mock_key_manager.keys, dict)
    # Simulate expiry
    mock_key_manager.key_expiry = {'google_api_key': 0}
    key = mock_key_manager.get_google_api_key()
    assert key is None
