"""
MCP Server for CV Database Access
Provides standardized tools for querying PostgreSQL and Qdrant vector DB
"""

import logging
from typing import Dict, List, Any, Optional
from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue
from langchain_openai import OpenAIEmbeddings

from config import get_config
from db_manager import get_db_manager, convert_dates

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def _format_result(tool_name: str, status: str, results: Any = None, error: str = None, **extra_fields) -> Dict[str, Any]:
    """
    Format standardized response for all MCP tools.

    Args:
        tool_name: Name of the tool that was called
        status: "success" or "error"
        results: Tool results (list or dict)
        error: Error message if status is "error"
        **extra_fields: Additional fields to include (e.g., company, category, date_range)

    Returns:
        Formatted result dictionary
    """
    response = {
        "status": status,
        "tool": tool_name,
    }

    if status == "success":
        if results is not None:
            if isinstance(results, list):
                response["results_count"] = len(results)
                response["results"] = results
            elif isinstance(results, dict):
                response.update(results)
            else:
                response["results"] = results
    else:
        response["error"] = error

    # Add any extra fields (like company, category, date_range, etc.)
    response.update(extra_fields)

    return response


# ============================================================================
# DATABASE TOOLS
# ============================================================================

class DatabaseTools:
    """MCP Tools for accessing CV database"""

    def __init__(self, config=None):
        """Initialize DatabaseTools with configuration"""
        self.config = config or get_config()
        self.db = get_db_manager(self.config)
        self.embedding_model = OpenAIEmbeddings(
            api_key=self.config.get_openai_api_key(),
            model=self.config.get_embedding_model()
        )
        self.qdrant_client = QdrantClient(
            url=self.config.get_qdrant_url(),
            api_key=self.config.get_qdrant_api_key()
        )
        # Cache CV ID to avoid repeated lookups
        self._cv_id_cache: Optional[str] = None
        logger.info("DatabaseTools initialized")

    def _get_cv_id(self) -> str:
        """
        Get the CV ID from the database with caching

        Returns:
            str: CV ID or "default-cv-id" if not found
        """
        # Return cached value if available
        if self._cv_id_cache:
            return self._cv_id_cache

        try:
            results = self.db.execute_query(
                "SELECT DISTINCT cv_id FROM skills LIMIT 1",
                as_dict=False
            )

            if results:
                self._cv_id_cache = str(results[0][0])
                return self._cv_id_cache
            else:
                logger.warning("No CV ID found in database, using default")
                return "default-cv-id"
        except Exception as e:
            logger.warning(f"Could not fetch CV ID: {e}, using default")
            return "default-cv-id"

    # ========================================================================
    # TOOL 1: Get CV Summary
    # ========================================================================
    def get_cv_summary(self) -> Dict[str, Any]:
        """
        Get a summary of the CV including name, role, experience, and key stats.

        Returns:
            Dict with CV summary information
        """
        try:
            results = self.db.execute_query(
                """
                SELECT name, crole as current_role, total_years_experience,
                       total_jobs, total_degrees, total_publications,
                       domains, all_skills
                FROM cv_summary
                LIMIT 1
                """
            )

            if results:
                summary_dict = results[0]
                logger.info("CV summary retrieved successfully")
                return _format_result("get_cv_summary", "success", summary=summary_dict)
            else:
                logger.warning("CV not found in database")
                return _format_result("get_cv_summary", "error", error="CV not found")

        except Exception as e:
            logger.error(f"Error in get_cv_summary: {e}")
            return _format_result("get_cv_summary", "error", error=str(e))

    # ========================================================================
    # TOOL 2: Search Company Experience
    # ========================================================================
    def search_company_experience(self, company_name: str) -> Dict[str, Any]:
        """
        Find all jobs at a specific company.

        Args:
            company_name: Name of the company (e.g., 'KasiOss')

        Returns:
            Dict with work experience records
        """
        try:
            cv_id = self._get_cv_id()
            results = self.db.execute_query(
                """
                SELECT company, role, location, start_date, end_date, is_current,
                       technologies, skills, domain, seniority, team_size
                FROM work_experience
                WHERE cv_id = %s AND company ILIKE %s
                ORDER BY start_date DESC
                """,
                (cv_id, f"%{company_name}%")
            )

            # Convert dates to strings
            for result in results:
                convert_dates(result, ["start_date", "end_date"])

            logger.info(f"Found {len(results)} jobs at {company_name}")
            return _format_result(
                "search_company_experience",
                "success",
                results=results,
                company=company_name
            )

        except Exception as e:
            logger.error(f"Error in search_company_experience: {e}")
            return _format_result("search_company_experience", "error", error=str(e))

    # ========================================================================
    # TOOL 3: Search Technology Experience
    # ========================================================================
    def search_technology_experience(self, technology: str) -> Dict[str, Any]:
        """
        Find all jobs using a specific technology.

        Args:
            technology: Technology name (e.g., 'Python', 'TensorFlow')

        Returns:
            Dict with work experience using the technology
        """
        try:
            cv_id = self._get_cv_id()
            results = self.db.execute_query(
                """
                SELECT company, role, start_date, end_date, technologies, domain
                FROM work_experience
                WHERE cv_id = %s AND %s = ANY(technologies)
                ORDER BY start_date DESC
                """,
                (cv_id, technology)
            )

            # Convert dates
            for result in results:
                convert_dates(result, ["start_date", "end_date"])

            logger.info(f"Found {len(results)} jobs using {technology}")
            return _format_result(
                "search_technology_experience",
                "success",
                results=results,
                technology=technology
            )

        except Exception as e:
            logger.error(f"Error in search_technology_experience: {e}")
            return _format_result("search_technology_experience", "error", error=str(e))

    # ========================================================================
    # TOOL 4: Search Work by Date Range
    # ========================================================================
    def search_work_by_date(self, start_year: int, end_year: int) -> Dict[str, Any]:
        """
        Find work experience within a date range.

        Args:
            start_year: Start year (e.g., 2020)
            end_year: End year (e.g., 2024)

        Returns:
            Dict with work experience in the date range
        """
        try:
            cv_id = self._get_cv_id()
            results = self.db.execute_query(
                """
                SELECT company, role, start_date, end_date, technologies, keywords
                FROM work_experience
                WHERE cv_id = %s
                  AND start_date >= %s::date
                  AND (end_date <= %s::date OR end_date IS NULL)
                ORDER BY start_date DESC
                """,
                (cv_id, f"{start_year}-01-01", f"{end_year}-12-31")
            )

            for result in results:
                convert_dates(result, ["start_date", "end_date"])

            logger.info(f"Found {len(results)} jobs between {start_year}-{end_year}")
            return _format_result(
                "search_work_by_date",
                "success",
                results=results,
                date_range=f"{start_year}-{end_year}"
            )

        except Exception as e:
            logger.error(f"Error in search_work_by_date: {e}")
            return _format_result("search_work_by_date", "error", error=str(e))

    # ========================================================================
    # TOOL 5: Search Education
    # ========================================================================
    def search_education(self, institution: Optional[str] = None, degree: Optional[str] = None) -> Dict[str, Any]:
        """
        Find education records by institution or degree.

        Args:
            institution: University or institution name (optional)
            degree: Degree type (e.g., 'PhD', 'Master') (optional)

        Returns:
            Dict with education records
        """
        try:
            cv_id = self._get_cv_id()

            if institution:
                results = self.db.execute_query(
                    """
                    SELECT institution, degree, field, specialization, graduation_date, thesis, publications
                    FROM education
                    WHERE cv_id = %s AND institution ILIKE %s
                    """,
                    (cv_id, f"%{institution}%")
                )
                search_type = f"institution: {institution}"

            elif degree:
                results = self.db.execute_query(
                    """
                    SELECT institution, degree, field, specialization, graduation_date, thesis
                    FROM education
                    WHERE cv_id = %s AND degree ILIKE %s
                    """,
                    (cv_id, f"%{degree}%")
                )
                search_type = f"degree: {degree}"

            else:
                results = self.db.execute_query(
                    """
                    SELECT institution, degree, field, specialization, graduation_date, thesis
                    FROM education
                    WHERE cv_id = %s
                    """,
                    (cv_id,)
                )
                search_type = "all education"

            for result in results:
                convert_dates(result, ["graduation_date"])

            logger.info(f"Found {len(results)} education records for {search_type}")
            return _format_result(
                "search_education",
                "success",
                results=results,
                search_type=search_type
            )

        except Exception as e:
            logger.error(f"Error in search_education: {e}")
            return _format_result("search_education", "error", error=str(e))

    # ========================================================================
    # TOOL 6: Search Publications
    # ========================================================================
    def search_publications(self, year: Optional[int] = None) -> Dict[str, Any]:
        """
        Search publications by year.

        Args:
            year: Publication year (optional, defaults to all publications)

        Returns:
            Dict with publications
        """
        try:
            cv_id = self._get_cv_id()

            if year:
                results = self.db.execute_query(
                    """
                    SELECT title, year, conference_name, doi, keywords, content_text
                    FROM publications
                    WHERE cv_id = %s AND year = %s
                    ORDER BY year DESC
                    """,
                    (cv_id, year)
                )
                search_type = f"year: {year}"

            else:
                results = self.db.execute_query(
                    """
                    SELECT title, year, conference_name, doi, keywords, content_text
                    FROM publications
                    WHERE cv_id = %s
                    ORDER BY year DESC
                    """,
                    (cv_id,)
                )
                search_type = "all publications"

            logger.info(f"Found {len(results)} publications for {search_type}")
            return _format_result(
                "search_publications",
                "success",
                results=results,
                search_type=search_type
            )

        except Exception as e:
            logger.error(f"Error in search_publications: {e}")
            return _format_result("search_publications", "error", error=str(e))

    # ========================================================================
    # TOOL 7: Search Skills
    # ========================================================================
    def search_skills(self, category: str) -> Dict[str, Any]:
        """
        Find skills by category.

        Args:
            category: Skill category (e.g., 'AI', 'ML', 'programming', 'Tools', 'Cloud', 'Data_tools')

        Returns:
            Dict with skills in the category
        """
        try:
            cv_id = self._get_cv_id()
            results = self.db.execute_query(
                """
                SELECT skill_name
                FROM skills
                WHERE cv_id = %s AND skill_category = %s
                ORDER BY skill_name
                """,
                (cv_id, category)
            )

            logger.info(f"Found {len(results)} skills in category {category}")
            return _format_result(
                "search_skills",
                "success",
                results=results,
                category=category
            )

        except Exception as e:
            logger.error(f"Error in search_skills: {e}")
            return _format_result("search_skills", "error", error=str(e))

    # ========================================================================
    # TOOL 8: Search Awards and Certifications
    # ========================================================================
    def search_awards_certifications(self, award_type: Optional[str] = None) -> Dict[str, Any]:
        """
        Find awards and certifications records.

        Args:
            award_type: Type of award/certification to filter (optional)

        Returns:
            Dict with awards and certifications records
        """
        try:
            cv_id = self._get_cv_id()

            if award_type:
                results = self.db.execute_query(
                    """
                    SELECT title, issuing_organization, organization, issue_date, keywords
                    FROM awards_certifications
                    WHERE cv_id = %s AND (issuing_organization ILIKE %s OR organization ILIKE %s OR title ILIKE %s)
                    ORDER BY issue_date DESC
                    """,
                    (cv_id, f"%{award_type}%", f"%{award_type}%", f"%{award_type}%")
                )
                search_type = f"type: {award_type}"

            else:
                results = self.db.execute_query(
                    """
                    SELECT title, issuing_organization, organization, issue_date, keywords
                    FROM awards_certifications
                    WHERE cv_id = %s
                    ORDER BY issue_date DESC
                    """,
                    (cv_id,)
                )
                search_type = "all awards and certifications"

            for result in results:
                convert_dates(result, ["issue_date"])

            logger.info(f"Found {len(results)} awards/certifications for {search_type}")
            return _format_result(
                "search_awards_certifications",
                "success",
                results=results,
                search_type=search_type
            )

        except Exception as e:
            logger.error(f"Error in search_awards_certifications: {e}")
            return _format_result("search_awards_certifications", "error", error=str(e))

    # ========================================================================
    # TOOL 9: Semantic Search
    # ========================================================================
    def semantic_search(self, query: str, section: Optional[str] = None, top_k: int = 5) -> Dict[str, Any]:
        """
        Perform semantic search on CV content using vector embeddings.

        Args:
            query: Natural language search query
            section: Filter by section (work_experience, education, publication, all)
            top_k: Number of results to return (default: 5)

        Returns:
            Dict with semantic search results from Qdrant
        """
        try:
            query_embedding = self.embedding_model.embed_query(query)
            collection_name = self.config.get_qdrant_collection()

            # Build filter if section is specified
            query_filter = None
            if section and section != "all":
                query_filter = Filter(
                    must=[
                        FieldCondition(
                            key="section",
                            match=MatchValue(value=section)
                        )
                    ]
                )

            # Use the Qdrant query_points API (search is deprecated)
            response = self.qdrant_client.query_points(
                collection_name=collection_name,
                query=query_embedding,
                query_filter=query_filter,
                limit=top_k,
                with_payload=True
            )

            # query_points returns a QueryResponse, extract the points
            results = response.points

            formatted_results = []
            for result in results:
                # Build result with core fields
                formatted_result = {
                    "chunk_id": result.payload.get("chunk_id"),
                    "cv_id": result.payload.get("cv_id"),
                    "section": result.payload.get("section"),
                    "similarity_score": result.score
                }

                # Add section-specific metadata fields
                section_value = result.payload.get("section", "")

                # Work experience specific fields
                if section_value == "work experience":
                    if result.payload.get("company"):
                        formatted_result["company"] = result.payload.get("company")
                    if result.payload.get("role"):
                        formatted_result["role"] = result.payload.get("role")
                    if result.payload.get("domain"):
                        formatted_result["domain"] = result.payload.get("domain")
                    if result.payload.get("responsibility"):
                        formatted_result["responsibility"] = result.payload.get("responsibility")

                # Education specific fields
                elif section_value == "education":
                    if result.payload.get("institution"):
                        formatted_result["institution"] = result.payload.get("institution")
                    if result.payload.get("degree"):
                        formatted_result["degree"] = result.payload.get("degree")
                    if result.payload.get("thesis"):
                        formatted_result["thesis"] = result.payload.get("thesis")
                    if result.payload.get("graduation_date"):
                        formatted_result["graduation_date"] = result.payload.get("graduation_date")

                # Publication specific fields
                elif section_value == "publication":
                    if result.payload.get("title"):
                        formatted_result["title"] = result.payload.get("title")

                # Projects specific fields
                elif section_value == "projects":
                    if result.payload.get("project_name"):
                        formatted_result["project_name"] = result.payload.get("project_name")
                    if result.payload.get("responsibility"):
                        formatted_result["responsibility"] = result.payload.get("responsibility")
                    if result.payload.get("technologies"):
                        formatted_result["technologies"] = result.payload.get("technologies")

                # Common optional fields
                if result.payload.get("technologies"):
                    formatted_result["technologies"] = result.payload.get("technologies")
                if result.payload.get("skills"):
                    formatted_result["skills"] = result.payload.get("skills")

                formatted_results.append(formatted_result)

            logger.info(f"Semantic search found {len(formatted_results)} results for query: '{query}'")
            return {
                "status": "success",
                "tool": "semantic_search",
                "query": query,
                "section_filter": section or "all",
                "results_count": len(formatted_results),
                "results": formatted_results
            }

        except Exception as e:
            logger.error(f"Error in semantic_search: {e}")
            return {
                "status": "error",
                "tool": "semantic_search",
                "error": str(e)
            }


# ============================================================================
# MCP SERVER SETUP
# ============================================================================

def create_mcp_server():
    """Create and return configured MCP server"""
    try:
        config = get_config()
        tools = DatabaseTools(config)
        logger.info("MCP Server initialized successfully")
        return tools
    except Exception as e:
        logger.error(f"Failed to initialize MCP Server: {e}")
        raise


if __name__ == "__main__":
    logger.info("MCP Server started")
    try:
        mcp_server = create_mcp_server()
        logger.info("All tools available and ready")

        # Simple test: get CV summary
        result = mcp_server.get_cv_summary()
        if result["status"] == "success":
            print("✓ MCP Server is working correctly")
        else:
            print(f"✗ MCP Server error: {result.get('error')}")
    except Exception as e:
        print(f"✗ MCP Server initialization failed: {e}")
