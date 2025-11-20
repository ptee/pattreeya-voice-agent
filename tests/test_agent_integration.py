"""
Integration tests for Voice Agent with MCP Client
Tests agent initialization and tool integration
"""

import pytest
import logging
from unittest.mock import Mock, patch, AsyncMock, MagicMock
import sys
import os

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from agent import Assistant
from config import ConfigManager
from mcp_client import MCPClient

logger = logging.getLogger(__name__)


@pytest.fixture
def mock_mcp_client():
    """Create a mock MCP client"""
    client = Mock(spec=MCPClient)

    # Setup return values for all tools
    client.get_cv_summary.return_value = {
        'status': 'success',
        'summary': {
            'name': 'Test Person',
            'current_role': 'Engineer',
            'total_years_experience': 10,
            'total_jobs': 5,
            'total_degrees': 2,
            'total_publications': 3,
            'domains': 'Tech, AI',
            'all_skills': 'Python, ML, Leadership'
        }
    }

    client.search_company_experience.return_value = {
        'status': 'success',
        'results': [
            {
                'company': 'TechCorp',
                'role': 'Senior Engineer',
                'location': 'NYC',
                'start_date': '2020-01-01',
                'end_date': None,
                'is_current': True,
                'technologies': ['Python', 'AWS'],
                'skills': ['Leadership', 'Architecture'],
                'domain': 'Software',
                'seniority': 'Senior',
                'team_size': 5
            }
        ]
    }

    client.search_technology_experience.return_value = {
        'status': 'success',
        'results': [
            {
                'company': 'TechCorp',
                'role': 'Software Engineer',
                'start_date': '2020-01-01',
                'end_date': None,
                'technologies': ['Python', 'TensorFlow'],
                'domain': 'AI'
            }
        ]
    }

    client.search_education.return_value = {
        'status': 'success',
        'results': [
            {
                'institution': 'MIT',
                'degree': 'PhD',
                'field': 'Computer Science',
                'specialization': 'Machine Learning',
                'graduation_date': '2020-05-01',
                'thesis': 'Deep Learning for NLP'
            }
        ]
    }

    client.search_publications.return_value = {
        'status': 'success',
        'results': [
            {
                'title': 'Deep Learning Survey',
                'year': 2023,
                'conference_name': 'NeurIPS',
                'doi': 'doi:12345',
                'keywords': ['ML', 'DL']
            }
        ]
    }

    client.search_skills.return_value = {
        'status': 'success',
        'results': [
            {'skill_name': 'Python'},
            {'skill_name': 'TensorFlow'},
            {'skill_name': 'PyTorch'}
        ]
    }

    client.search_awards_certifications.return_value = {
        'status': 'success',
        'results': [
            {
                'title': 'Best Engineer Award',
                'issuing_organization': 'TechCorp',
                'organization': 'TechCorp',
                'issue_date': '2023-01-01',
                'keywords': ['Excellence']
            }
        ]
    }

    client.semantic_search.return_value = {
        'status': 'success',
        'results': [
            {
                'chunk_id': 'chunk_1',
                'cv_id': 'cv_123',
                'section': 'work_experience',
                'similarity_score': 0.95,
                'company': 'TechCorp',
                'role': 'Senior Engineer',
                'responsibility': 'Led team of engineers'
            }
        ]
    }

    return client


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


class TestAssistantInit:
    """Tests for Assistant initialization"""

    @patch('agent.get_mcp_client')
    def test_assistant_init_with_client(self, mock_get_client, mock_mcp_client):
        """Test Assistant initializes with provided MCP client"""
        assistant = Assistant(mcp_client=mock_mcp_client)

        assert assistant.mcp_client == mock_mcp_client
        mock_get_client.assert_not_called()

    @patch('agent.get_mcp_client')
    def test_assistant_init_default_client(self, mock_get_client, mock_mcp_client):
        """Test Assistant initializes with default MCP client"""
        mock_get_client.return_value = mock_mcp_client

        assistant = Assistant()

        mock_get_client.assert_called_once()
        assert assistant.mcp_client == mock_mcp_client

    @patch('agent.SYSTEM_PROMPT', 'Test prompt')
    @patch('agent.get_mcp_client')
    def test_assistant_system_prompt(self, mock_get_client, mock_mcp_client):
        """Test Assistant uses system prompt from prompts module"""
        mock_get_client.return_value = mock_mcp_client

        assistant = Assistant()

        # The instructions should be set to the SYSTEM_PROMPT
        assert hasattr(assistant, 'instructions')


class TestAssistantTools:
    """Tests for Assistant tools"""

    def test_get_cv_summary_tool_exists(self, mock_mcp_client):
        """Test that get_cv_summary tool exists"""
        assistant = Assistant(mcp_client=mock_mcp_client)

        assert hasattr(assistant, 'get_cv_summary')
        assert callable(assistant.get_cv_summary)

    def test_search_company_experience_tool_exists(self, mock_mcp_client):
        """Test that search_company_experience tool exists"""
        assistant = Assistant(mcp_client=mock_mcp_client)

        assert hasattr(assistant, 'search_company_experience')
        assert callable(assistant.search_company_experience)

    def test_search_technology_experience_tool_exists(self, mock_mcp_client):
        """Test that search_technology_experience tool exists"""
        assistant = Assistant(mcp_client=mock_mcp_client)

        assert hasattr(assistant, 'search_technology_experience')
        assert callable(assistant.search_technology_experience)

    def test_search_education_tool_exists(self, mock_mcp_client):
        """Test that search_education tool exists"""
        assistant = Assistant(mcp_client=mock_mcp_client)

        assert hasattr(assistant, 'search_education')
        assert callable(assistant.search_education)

    def test_search_publications_tool_exists(self, mock_mcp_client):
        """Test that search_publications tool exists"""
        assistant = Assistant(mcp_client=mock_mcp_client)

        assert hasattr(assistant, 'search_publications')
        assert callable(assistant.search_publications)

    def test_search_skills_tool_exists(self, mock_mcp_client):
        """Test that search_skills tool exists"""
        assistant = Assistant(mcp_client=mock_mcp_client)

        assert hasattr(assistant, 'search_skills')
        assert callable(assistant.search_skills)

    def test_search_awards_certifications_tool_exists(self, mock_mcp_client):
        """Test that search_awards_certifications tool exists"""
        assistant = Assistant(mcp_client=mock_mcp_client)

        assert hasattr(assistant, 'search_awards_certifications')
        assert callable(assistant.search_awards_certifications)

    def test_semantic_search_tool_exists(self, mock_mcp_client):
        """Test that semantic_search tool exists"""
        assistant = Assistant(mcp_client=mock_mcp_client)

        assert hasattr(assistant, 'semantic_search')
        assert callable(assistant.semantic_search)


@pytest.mark.asyncio
class TestAssistantToolInvocations:
    """Tests for invoking Assistant tools"""

    async def test_get_cv_summary_invocation(self, mock_mcp_client):
        """Test invoking get_cv_summary tool"""
        assistant = Assistant(mcp_client=mock_mcp_client)
        context = Mock()

        result = await assistant.get_cv_summary(context)

        assert 'Summary:' in result
        mock_mcp_client.get_cv_summary.assert_called_once()

    async def test_search_company_experience_invocation(self, mock_mcp_client):
        """Test invoking search_company_experience tool"""
        assistant = Assistant(mcp_client=mock_mcp_client)
        context = Mock()

        result = await assistant.search_company_experience(context, "TechCorp")

        assert 'TechCorp' in result
        mock_mcp_client.search_company_experience.assert_called_once_with("TechCorp")

    async def test_search_technology_experience_invocation(self, mock_mcp_client):
        """Test invoking search_technology_experience tool"""
        assistant = Assistant(mcp_client=mock_mcp_client)
        context = Mock()

        result = await assistant.search_technology_experience(context, "Python")

        assert 'Python' in result
        mock_mcp_client.search_technology_experience.assert_called_once_with("Python")

    async def test_search_education_invocation(self, mock_mcp_client):
        """Test invoking search_education tool"""
        assistant = Assistant(mcp_client=mock_mcp_client)
        context = Mock()

        result = await assistant.search_education(context, degree="PhD")

        assert 'education' in result
        mock_mcp_client.search_education.assert_called_once()

    async def test_search_publications_invocation(self, mock_mcp_client):
        """Test invoking search_publications tool"""
        assistant = Assistant(mcp_client=mock_mcp_client)
        context = Mock()

        result = await assistant.search_publications(context, year=2023)

        assert 'publication' in result
        mock_mcp_client.search_publications.assert_called_once_with(2023)

    async def test_search_skills_invocation(self, mock_mcp_client):
        """Test invoking search_skills tool"""
        assistant = Assistant(mcp_client=mock_mcp_client)
        context = Mock()

        result = await assistant.search_skills(context, "ML")

        assert 'Skills in' in result
        mock_mcp_client.search_skills.assert_called_once_with("ML")

    async def test_search_awards_certifications_invocation(self, mock_mcp_client):
        """Test invoking search_awards_certifications tool"""
        assistant = Assistant(mcp_client=mock_mcp_client)
        context = Mock()

        result = await assistant.search_awards_certifications(context)

        assert 'award' in result.lower() or 'certification' in result.lower()
        mock_mcp_client.search_awards_certifications.assert_called_once()

    async def test_semantic_search_invocation(self, mock_mcp_client):
        """Test invoking semantic_search tool"""
        assistant = Assistant(mcp_client=mock_mcp_client)
        context = Mock()

        result = await assistant.semantic_search(context, "machine learning expertise")

        assert 'result' in result.lower()
        mock_mcp_client.semantic_search.assert_called_once()


@pytest.mark.asyncio
class TestAssistantErrorHandling:
    """Tests for error handling in Assistant tools"""

    async def test_tool_error_handling(self, mock_mcp_client):
        """Test error handling in tools"""
        mock_mcp_client.get_cv_summary.side_effect = Exception("DB Error")
        assistant = Assistant(mcp_client=mock_mcp_client)
        context = Mock()

        result = await assistant.get_cv_summary(context)

        assert 'Error' in result

    async def test_tool_failure_response(self, mock_mcp_client):
        """Test tool handling of failure responses"""
        mock_mcp_client.search_company_experience.return_value = {
            'status': 'error',
            'error': 'Connection failed'
        }
        assistant = Assistant(mcp_client=mock_mcp_client)
        context = Mock()

        result = await assistant.search_company_experience(context, "Unknown")

        assert 'Error' in result or 'error' in result.lower()

    async def test_tool_no_results_response(self, mock_mcp_client):
        """Test tool handling when no results found"""
        mock_mcp_client.search_company_experience.return_value = {
            'status': 'success',
            'results': []
        }
        assistant = Assistant(mcp_client=mock_mcp_client)
        context = Mock()

        result = await assistant.search_company_experience(context, "NonexistentCorp")

        assert 'No experience found' in result


class TestAssistantIntegration:
    """Integration tests for Assistant with MCP Client"""

    @patch('agent.get_mcp_client')
    def test_full_initialization_workflow(self, mock_get_client, mock_mcp_client):
        """Test full Assistant initialization workflow"""
        mock_get_client.return_value = mock_mcp_client

        assistant = Assistant()

        assert assistant.mcp_client is not None
        assert hasattr(assistant, 'get_cv_summary')
        assert hasattr(assistant, 'search_company_experience')
        assert hasattr(assistant, 'semantic_search')

    def test_assistant_is_agent_subclass(self, mock_mcp_client):
        """Test that Assistant is an Agent subclass"""
        from livekit.agents import Agent
        assistant = Assistant(mcp_client=mock_mcp_client)

        assert isinstance(assistant, Agent)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
