"""
Tests for MCP Server module
Tests database tools and configuration management
"""

import pytest
import logging
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from mcp_server import DatabaseTools, create_mcp_server
from config import ConfigManager

logger = logging.getLogger(__name__)


@pytest.fixture
def mock_config():
    """Create a mock ConfigManager for testing"""
    config = Mock(spec=ConfigManager)
    config.get_openai_api_key.return_value = "test-key"
    config.get_embedding_model.return_value = "text-embedding-3-small"
    config.get_qdrant_url.return_value = "http://localhost:6333"
    config.get_qdrant_api_key.return_value = "test-qdrant-key"
    config.get_postgresql_url.return_value = "postgresql://user:pass@localhost/db"
    return config


@pytest.fixture
def mock_pg_connection():
    """Create a mock PostgreSQL connection"""
    conn = Mock()
    cursor = Mock()
    conn.cursor.return_value = cursor
    return conn, cursor


@pytest.fixture
def mock_qdrant_client():
    """Create a mock Qdrant client"""
    return Mock()


class TestDatabaseToolsInit:
    """Tests for DatabaseTools initialization"""

    @patch('mcp_server.QdrantClient')
    @patch('mcp_server.OpenAIEmbeddings')
    def test_initialization_with_config(self, mock_embeddings, mock_qdrant, mock_config):
        """Test DatabaseTools initializes with provided config"""
        tools = DatabaseTools(config=mock_config)

        assert tools.config == mock_config
        mock_embeddings.assert_called_once()
        mock_qdrant.assert_called_once()

    @patch('mcp_server.get_config')
    @patch('mcp_server.QdrantClient')
    @patch('mcp_server.OpenAIEmbeddings')
    def test_initialization_without_config(self, mock_embeddings, mock_qdrant, mock_get_config, mock_config):
        """Test DatabaseTools initializes with default config"""
        mock_get_config.return_value = mock_config
        tools = DatabaseTools()

        assert tools.config == mock_config
        mock_get_config.assert_called_once()


class TestGetCVSummary:
    """Tests for get_cv_summary tool"""

    @patch('mcp_server.QdrantClient')
    @patch('mcp_server.OpenAIEmbeddings')
    def test_get_cv_summary_success(self, mock_embeddings, mock_qdrant, mock_config, mock_pg_connection):
        """Test successful CV summary retrieval"""
        conn, cursor = mock_pg_connection
        cursor.description = [('name',), ('current_role',), ('total_years_experience',),
                              ('total_jobs',), ('total_degrees',), ('total_publications',),
                              ('domains',), ('all_skills',)]
        cursor.fetchone.return_value = ('John Doe', 'Engineer', 10, 3, 2, 5,
                                       'Tech, AI', 'Python, ML')

        tools = DatabaseTools(config=mock_config)

        with patch.object(tools, 'get_pg_connection', return_value=conn):
            result = tools.get_cv_summary()

        assert result['status'] == 'success'
        assert result['tool'] == 'get_cv_summary'
        assert 'summary' in result
        assert result['summary']['name'] == 'John Doe'

    @patch('mcp_server.QdrantClient')
    @patch('mcp_server.OpenAIEmbeddings')
    def test_get_cv_summary_empty(self, mock_embeddings, mock_qdrant, mock_config, mock_pg_connection):
        """Test CV summary retrieval when no data exists"""
        conn, cursor = mock_pg_connection
        cursor.description = [('name',), ('current_role',)]
        cursor.fetchone.return_value = None

        tools = DatabaseTools(config=mock_config)

        with patch.object(tools, 'get_pg_connection', return_value=conn):
            result = tools.get_cv_summary()

        assert result['status'] == 'error'
        assert 'error' in result


class TestSearchCompanyExperience:
    """Tests for search_company_experience tool"""

    @patch('mcp_server.QdrantClient')
    @patch('mcp_server.OpenAIEmbeddings')
    def test_search_company_success(self, mock_embeddings, mock_qdrant, mock_config, mock_pg_connection):
        """Test successful company experience search"""
        conn, cursor = mock_pg_connection
        cursor.description = [('company',), ('role',), ('location',), ('start_date',),
                             ('end_date',), ('is_current',), ('technologies',), ('skills',),
                             ('domain',), ('seniority',), ('team_size',)]
        cursor.fetchall.return_value = [
            ('TechCorp', 'Software Engineer', 'NYC', '2020-01-01', '2022-12-31', False,
             ['Python', 'JavaScript'], ['coding', 'design'], 'Software', 'Senior', 5)
        ]

        tools = DatabaseTools(config=mock_config)

        with patch.object(tools, 'get_pg_connection', return_value=conn):
            with patch.object(tools, '_get_cv_id', return_value='cv-123'):
                result = tools.search_company_experience('TechCorp')

        assert result['status'] == 'success'
        assert result['tool'] == 'search_company_experience'
        assert result['results_count'] == 1
        assert result['results'][0]['company'] == 'TechCorp'

    @patch('mcp_server.QdrantClient')
    @patch('mcp_server.OpenAIEmbeddings')
    def test_search_company_not_found(self, mock_embeddings, mock_qdrant, mock_config, mock_pg_connection):
        """Test company search with no results"""
        conn, cursor = mock_pg_connection
        cursor.description = [('company',)]
        cursor.fetchall.return_value = []

        tools = DatabaseTools(config=mock_config)

        with patch.object(tools, 'get_pg_connection', return_value=conn):
            with patch.object(tools, '_get_cv_id', return_value='cv-123'):
                result = tools.search_company_experience('NonexistentCorp')

        assert result['status'] == 'success'
        assert result['results_count'] == 0


class TestSearchTechnologyExperience:
    """Tests for search_technology_experience tool"""

    @patch('mcp_server.QdrantClient')
    @patch('mcp_server.OpenAIEmbeddings')
    def test_search_technology_success(self, mock_embeddings, mock_qdrant, mock_config, mock_pg_connection):
        """Test successful technology experience search"""
        conn, cursor = mock_pg_connection
        cursor.description = [('company',), ('role',), ('start_date',), ('end_date',),
                             ('technologies',), ('domain',)]
        cursor.fetchall.return_value = [
            ('TechCorp', 'ML Engineer', '2020-01-01', '2022-12-31',
             ['Python', 'TensorFlow'], 'AI')
        ]

        tools = DatabaseTools(config=mock_config)

        with patch.object(tools, 'get_pg_connection', return_value=conn):
            with patch.object(tools, '_get_cv_id', return_value='cv-123'):
                result = tools.search_technology_experience('Python')

        assert result['status'] == 'success'
        assert result['technology'] == 'Python'
        assert result['results_count'] == 1


class TestSearchEducation:
    """Tests for search_education tool"""

    @patch('mcp_server.QdrantClient')
    @patch('mcp_server.OpenAIEmbeddings')
    def test_search_education_by_degree(self, mock_embeddings, mock_qdrant, mock_config, mock_pg_connection):
        """Test education search by degree"""
        conn, cursor = mock_pg_connection
        cursor.description = [('institution',), ('degree',), ('field',), ('specialization',),
                             ('graduation_date',), ('thesis',)]
        cursor.fetchall.return_value = [
            ('MIT', 'PhD', 'Computer Science', 'ML', '2020-05-01', 'Deep Learning')
        ]

        tools = DatabaseTools(config=mock_config)

        with patch.object(tools, 'get_pg_connection', return_value=conn):
            with patch.object(tools, '_get_cv_id', return_value='cv-123'):
                result = tools.search_education(degree='PhD')

        assert result['status'] == 'success'
        assert result['results_count'] == 1
        assert result['results'][0]['degree'] == 'PhD'

    @patch('mcp_server.QdrantClient')
    @patch('mcp_server.OpenAIEmbeddings')
    def test_search_all_education(self, mock_embeddings, mock_qdrant, mock_config, mock_pg_connection):
        """Test getting all education records"""
        conn, cursor = mock_pg_connection
        cursor.description = [('institution',), ('degree',), ('field',), ('specialization',),
                             ('graduation_date',), ('thesis',)]
        cursor.fetchall.return_value = [
            ('MIT', 'PhD', 'Computer Science', 'ML', '2020-05-01', 'Deep Learning'),
            ('Stanford', 'BS', 'Mathematics', None, '2016-06-01', None)
        ]

        tools = DatabaseTools(config=mock_config)

        with patch.object(tools, 'get_pg_connection', return_value=conn):
            with patch.object(tools, '_get_cv_id', return_value='cv-123'):
                result = tools.search_education()

        assert result['status'] == 'success'
        assert result['results_count'] == 2


class TestSearchPublications:
    """Tests for search_publications tool"""

    @patch('mcp_server.QdrantClient')
    @patch('mcp_server.OpenAIEmbeddings')
    def test_search_publications_by_year(self, mock_embeddings, mock_qdrant, mock_config, mock_pg_connection):
        """Test publication search by year"""
        conn, cursor = mock_pg_connection
        cursor.description = [('title',), ('year',), ('conference_name',), ('doi',),
                             ('keywords',), ('content_text',)]
        cursor.fetchall.return_value = [
            ('Deep Learning Survey', 2023, 'NeurIPS', 'doi:12345', ['ML', 'DL'], 'Abstract...')
        ]

        tools = DatabaseTools(config=mock_config)

        with patch.object(tools, 'get_pg_connection', return_value=conn):
            with patch.object(tools, '_get_cv_id', return_value='cv-123'):
                result = tools.search_publications(year=2023)

        assert result['status'] == 'success'
        assert result['results_count'] == 1
        assert result['results'][0]['year'] == 2023


class TestSearchSkills:
    """Tests for search_skills tool"""

    @patch('mcp_server.QdrantClient')
    @patch('mcp_server.OpenAIEmbeddings')
    def test_search_skills_by_category(self, mock_embeddings, mock_qdrant, mock_config, mock_pg_connection):
        """Test skill search by category"""
        conn, cursor = mock_pg_connection
        cursor.description = [('skill_name',)]
        cursor.fetchall.return_value = [('Python',), ('TensorFlow',), ('PyTorch',)]

        tools = DatabaseTools(config=mock_config)

        with patch.object(tools, 'get_pg_connection', return_value=conn):
            with patch.object(tools, '_get_cv_id', return_value='cv-123'):
                result = tools.search_skills('ML')

        assert result['status'] == 'success'
        assert result['category'] == 'ML'
        assert result['results_count'] == 3


class TestCreateMCPServer:
    """Tests for create_mcp_server function"""

    @patch('mcp_server.get_config')
    @patch('mcp_server.DatabaseTools')
    def test_create_mcp_server_success(self, mock_db_tools, mock_get_config, mock_config):
        """Test successful MCP server creation"""
        mock_get_config.return_value = mock_config

        result = create_mcp_server()

        assert result is not None
        mock_get_config.assert_called_once()

    @patch('mcp_server.get_config')
    def test_create_mcp_server_config_error(self, mock_get_config):
        """Test MCP server creation with config error"""
        mock_get_config.side_effect = ValueError("Missing required env vars")

        with pytest.raises(ValueError):
            create_mcp_server()


class TestDatabaseToolsRowConversion:
    """Tests for row to dict conversion"""

    @patch('mcp_server.QdrantClient')
    @patch('mcp_server.OpenAIEmbeddings')
    def test_rows_to_dicts_empty(self, mock_embeddings, mock_qdrant, mock_config):
        """Test conversion of empty rows"""
        tools = DatabaseTools(config=mock_config)
        result = tools._rows_to_dicts(Mock(), [])

        assert result == []

    @patch('mcp_server.QdrantClient')
    @patch('mcp_server.OpenAIEmbeddings')
    def test_rows_to_dicts_conversion(self, mock_embeddings, mock_qdrant, mock_config):
        """Test conversion of rows to dictionaries"""
        tools = DatabaseTools(config=mock_config)
        cursor = Mock()
        cursor.description = [('id',), ('name',), ('value',)]
        rows = [(1, 'test', 100), (2, 'test2', 200)]

        result = tools._rows_to_dicts(cursor, rows)

        assert len(result) == 2
        assert result[0] == {'id': 1, 'name': 'test', 'value': 100}
        assert result[1] == {'id': 2, 'name': 'test2', 'value': 200}


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
