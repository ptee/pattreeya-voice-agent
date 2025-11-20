"""
Tests for MCP Client module
Tests client wrapper for MCP database tools
"""

import pytest
import logging
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from mcp_client import MCPClient, get_mcp_client
from config import ConfigManager

logger = logging.getLogger(__name__)


@pytest.fixture
def mock_config():
    """Create a mock ConfigManager"""
    config = Mock(spec=ConfigManager)
    config.get_openai_api_key.return_value = "test-key"
    config.get_embedding_model.return_value = "text-embedding-3-small"
    config.get_qdrant_url.return_value = "http://localhost:6333"
    config.get_qdrant_api_key.return_value = "test-qdrant-key"
    config.get_postgresql_url.return_value = "postgresql://user:pass@localhost/db"
    return config


@pytest.fixture
def mock_database_tools():
    """Create a mock DatabaseTools instance"""
    tools = Mock()
    tools.get_cv_summary.return_value = {
        'status': 'success',
        'summary': {'name': 'John Doe', 'role': 'Engineer'}
    }
    tools.search_company_experience.return_value = {
        'status': 'success',
        'results': []
    }
    tools.search_technology_experience.return_value = {
        'status': 'success',
        'results': []
    }
    tools.search_education.return_value = {
        'status': 'success',
        'results': []
    }
    tools.search_publications.return_value = {
        'status': 'success',
        'results': []
    }
    tools.search_skills.return_value = {
        'status': 'success',
        'results': []
    }
    tools.search_awards_certifications.return_value = {
        'status': 'success',
        'results': []
    }
    tools.semantic_search.return_value = {
        'status': 'success',
        'results': []
    }
    return tools


class TestMCPClientInit:
    """Tests for MCPClient initialization"""

    @patch('mcp_client.DatabaseTools')
    def test_init_with_config(self, mock_db_tools_class, mock_config):
        """Test MCPClient initializes with provided config"""
        client = MCPClient(config=mock_config)

        assert client.config == mock_config
        mock_db_tools_class.assert_called_once_with(mock_config)

    @patch('mcp_client.get_config')
    @patch('mcp_client.DatabaseTools')
    def test_init_without_config(self, mock_db_tools_class, mock_get_config, mock_config):
        """Test MCPClient initializes with default config"""
        mock_get_config.return_value = mock_config

        client = MCPClient()

        assert client.config == mock_config
        mock_get_config.assert_called_once()

    @patch('mcp_client.DatabaseTools')
    def test_init_failure(self, mock_db_tools_class, mock_config):
        """Test MCPClient initialization failure"""
        mock_db_tools_class.side_effect = Exception("Connection failed")

        with pytest.raises(Exception):
            MCPClient(config=mock_config)


class TestMCPClientTools:
    """Tests for MCPClient tool methods"""

    @patch('mcp_client.DatabaseTools')
    def test_get_cv_summary(self, mock_db_tools_class, mock_config, mock_database_tools):
        """Test get_cv_summary tool"""
        mock_db_tools_class.return_value = mock_database_tools
        client = MCPClient(config=mock_config)

        result = client.get_cv_summary()

        assert result['status'] == 'success'
        mock_database_tools.get_cv_summary.assert_called_once()

    @patch('mcp_client.DatabaseTools')
    def test_search_company_experience(self, mock_db_tools_class, mock_config, mock_database_tools):
        """Test search_company_experience tool"""
        mock_db_tools_class.return_value = mock_database_tools
        client = MCPClient(config=mock_config)

        result = client.search_company_experience("TechCorp")

        assert result['status'] == 'success'
        mock_database_tools.search_company_experience.assert_called_once_with("TechCorp")

    @patch('mcp_client.DatabaseTools')
    def test_search_technology_experience(self, mock_db_tools_class, mock_config, mock_database_tools):
        """Test search_technology_experience tool"""
        mock_db_tools_class.return_value = mock_database_tools
        client = MCPClient(config=mock_config)

        result = client.search_technology_experience("Python")

        assert result['status'] == 'success'
        mock_database_tools.search_technology_experience.assert_called_once_with("Python")

    @patch('mcp_client.DatabaseTools')
    def test_search_work_by_date(self, mock_db_tools_class, mock_config, mock_database_tools):
        """Test search_work_by_date tool"""
        mock_database_tools.search_work_by_date.return_value = {
            'status': 'success',
            'results': []
        }
        mock_db_tools_class.return_value = mock_database_tools
        client = MCPClient(config=mock_config)

        result = client.search_work_by_date(2020, 2023)

        assert result['status'] == 'success'
        mock_database_tools.search_work_by_date.assert_called_once_with(2020, 2023)

    @patch('mcp_client.DatabaseTools')
    def test_search_education(self, mock_db_tools_class, mock_config, mock_database_tools):
        """Test search_education tool"""
        mock_db_tools_class.return_value = mock_database_tools
        client = MCPClient(config=mock_config)

        result = client.search_education(degree="PhD")

        assert result['status'] == 'success'
        mock_database_tools.search_education.assert_called_once_with(None, "PhD")

    @patch('mcp_client.DatabaseTools')
    def test_search_publications(self, mock_db_tools_class, mock_config, mock_database_tools):
        """Test search_publications tool"""
        mock_db_tools_class.return_value = mock_database_tools
        client = MCPClient(config=mock_config)

        result = client.search_publications(year=2023)

        assert result['status'] == 'success'
        mock_database_tools.search_publications.assert_called_once_with(2023)

    @patch('mcp_client.DatabaseTools')
    def test_search_skills(self, mock_db_tools_class, mock_config, mock_database_tools):
        """Test search_skills tool"""
        mock_db_tools_class.return_value = mock_database_tools
        client = MCPClient(config=mock_config)

        result = client.search_skills("ML")

        assert result['status'] == 'success'
        mock_database_tools.search_skills.assert_called_once_with("ML")

    @patch('mcp_client.DatabaseTools')
    def test_search_awards_certifications(self, mock_db_tools_class, mock_config, mock_database_tools):
        """Test search_awards_certifications tool"""
        mock_db_tools_class.return_value = mock_database_tools
        client = MCPClient(config=mock_config)

        result = client.search_awards_certifications()

        assert result['status'] == 'success'
        mock_database_tools.search_awards_certifications.assert_called_once_with(None)

    @patch('mcp_client.DatabaseTools')
    def test_semantic_search(self, mock_db_tools_class, mock_config, mock_database_tools):
        """Test semantic_search tool"""
        mock_db_tools_class.return_value = mock_database_tools
        client = MCPClient(config=mock_config)

        result = client.semantic_search("machine learning experience")

        assert result['status'] == 'success'
        mock_database_tools.semantic_search.assert_called_once_with("machine learning experience", None, 5)


class TestMCPClientToolRegistry:
    """Tests for MCPClient tool registry"""

    @patch('mcp_client.DatabaseTools')
    def test_get_available_tools(self, mock_db_tools_class, mock_config, mock_database_tools):
        """Test getting available tools list"""
        mock_db_tools_class.return_value = mock_database_tools
        client = MCPClient(config=mock_config)

        tools = client.get_available_tools()

        assert isinstance(tools, list)
        assert len(tools) == 9  # Total number of tools
        tool_names = [t['name'] for t in tools]
        assert 'get_cv_summary' in tool_names
        assert 'search_company_experience' in tool_names
        assert 'semantic_search' in tool_names

    @patch('mcp_client.DatabaseTools')
    def test_tool_has_required_fields(self, mock_db_tools_class, mock_config, mock_database_tools):
        """Test that tools have required fields"""
        mock_db_tools_class.return_value = mock_database_tools
        client = MCPClient(config=mock_config)

        tools = client.get_available_tools()

        for tool in tools:
            assert 'name' in tool
            assert 'description' in tool
            assert 'parameters' in tool


class TestMCPClientExecuteTool:
    """Tests for MCPClient execute_tool method"""

    @patch('mcp_client.DatabaseTools')
    def test_execute_cv_summary(self, mock_db_tools_class, mock_config, mock_database_tools):
        """Test executing cv_summary tool"""
        mock_db_tools_class.return_value = mock_database_tools
        client = MCPClient(config=mock_config)

        result = client.execute_tool("get_cv_summary")

        assert result['status'] == 'success'

    @patch('mcp_client.DatabaseTools')
    def test_execute_search_company(self, mock_db_tools_class, mock_config, mock_database_tools):
        """Test executing search_company_experience tool"""
        mock_db_tools_class.return_value = mock_database_tools
        client = MCPClient(config=mock_config)

        result = client.execute_tool("search_company_experience", company_name="TechCorp")

        assert result['status'] == 'success'

    @patch('mcp_client.DatabaseTools')
    def test_execute_unknown_tool(self, mock_db_tools_class, mock_config, mock_database_tools):
        """Test executing unknown tool"""
        mock_db_tools_class.return_value = mock_database_tools
        client = MCPClient(config=mock_config)

        result = client.execute_tool("unknown_tool")

        assert result['status'] == 'error'
        assert 'Unknown tool' in result['error']


class TestGetMCPClient:
    """Tests for get_mcp_client singleton function"""

    def teardown_method(self):
        """Reset global client after each test"""
        from mcp_client import MCPClient
        MCPClient._MCPClient__instance = None

    @patch('mcp_client.MCPClient')
    def test_get_mcp_client_creates_once(self, mock_client_class):
        """Test that get_mcp_client creates only one instance"""
        mock_instance = Mock()
        mock_client_class.return_value = mock_instance

        # Reset the global client
        import mcp_client
        mcp_client._client = None

        client1 = get_mcp_client()
        client2 = get_mcp_client()

        assert client1 is client2
        mock_client_class.assert_called_once()


class TestMCPClientIntegration:
    """Integration tests for MCPClient"""

    @patch('mcp_client.DatabaseTools')
    def test_client_workflow(self, mock_db_tools_class, mock_config, mock_database_tools):
        """Test a typical client workflow"""
        mock_db_tools_class.return_value = mock_database_tools
        mock_database_tools.get_cv_summary.return_value = {
            'status': 'success',
            'summary': {'name': 'John Doe', 'role': 'Senior Engineer', 'total_years': 10}
        }

        client = MCPClient(config=mock_config)
        summary = client.get_cv_summary()

        assert summary['status'] == 'success'
        assert summary['summary']['name'] == 'John Doe'

        # Execute with tool registry
        available = client.get_available_tools()
        assert len(available) > 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
