import pytest
from src.modules.documentation.services.documentation_service import DocumentationService

@pytest.mark.asyncio
async def test_documentation_service_initialization():
    """Тест инициализации сервиса документации."""
    service = DocumentationService()
    assert service.generator is not None

@pytest.mark.asyncio
async def test_generate_documentation_validation():
    """Тест валидации входных данных."""
    service = DocumentationService()
    
    # Empty code
    with pytest.raises(ValueError, match="Code cannot be empty"):
        await service.generate("", "python")
        
    # Unsupported language
    with pytest.raises(ValueError, match="Unsupported language"):
        await service.generate("print('hello')", "ruby")
