import OpenAI from 'openai';
import type { ConfigManager } from './config.js';
import { getConfig } from './config.js';
import { getPostgresManager, getQdrantManager, type PostgreSQLManager, type QdrantManager } from './db_manager.js';
import { CVNotFoundError } from './exceptions.js';

type ToolResult = Record<string, unknown>;

// ============================================================================
// DATABASE TOOLS
// ============================================================================

export class DatabaseTools {
  private config: ConfigManager;
  private pg: PostgreSQLManager;
  private qdrant: QdrantManager;
  private openai: OpenAI;
  private _cvId: string | null = null;

  constructor(config?: ConfigManager) {
    this.config = config ?? getConfig();
    this.pg = getPostgresManager(this.config);
    this.qdrant = getQdrantManager(this.config);
    this.openai = new OpenAI({ apiKey: this.config.getOpenaiApiKey() });
  }

  async getCvId(): Promise<string> {
    if (this._cvId === null) {
      const result = await this.pg.fetchOne('SELECT id FROM cv_metadata LIMIT 1');
      if (!result) {
        throw new CVNotFoundError('No CV data found in database. Please run db_ingestion to load data.');
      }
      this._cvId = String(result['id']);
    }
    return this._cvId;
  }

  // Tool 1: Get CV Summary
  async getCvSummary(): Promise<ToolResult> {
    try {
      const result = await this.pg.fetchOne(`
        SELECT name, crole as current_role, total_years_experience,
               total_jobs, total_degrees, total_publications,
               domains, all_skills
        FROM cv_summary
        LIMIT 1
      `);
      if (result) {
        return { status: 'success', tool: 'get_cv_summary', summary: result };
      }
      return { status: 'error', tool: 'get_cv_summary', error: 'CV not found' };
    } catch (e) {
      return { status: 'error', tool: 'get_cv_summary', error: String(e) };
    }
  }

  // Tool 2: Search Company Experience
  async searchCompanyExperience(companyName: string): Promise<ToolResult> {
    try {
      const cvId = await this.getCvId();
      const results = await this.pg.fetchAll(`
        SELECT company, role, location, start_date, end_date, is_current,
               technologies, skills, domain, seniority, team_size, content
        FROM work_experience
        WHERE cv_id = $1 AND company ILIKE $2
        ORDER BY start_date DESC
      `, [cvId, `%${companyName}%`]);

      for (const r of results) {
        for (const key of ['start_date', 'end_date']) {
          if (r[key]) r[key] = String(r[key]);
        }
      }
      return { status: 'success', tool: 'search_company_experience', company: companyName, results_count: results.length, results };
    } catch (e) {
      return { status: 'error', tool: 'search_company_experience', error: String(e) };
    }
  }

  // Tool 3: Search Technology Experience
  async searchTechnologyExperience(technology: string): Promise<ToolResult> {
    try {
      const cvId = await this.getCvId();
      const results = await this.pg.fetchAll(`
        SELECT company, role, start_date, end_date, technologies, domain
        FROM work_experience
        WHERE cv_id = $1 AND $2 = ANY(technologies)
        ORDER BY start_date DESC
      `, [cvId, technology]);

      for (const r of results) {
        for (const key of ['start_date', 'end_date']) {
          if (r[key]) r[key] = String(r[key]);
        }
      }
      return { status: 'success', tool: 'search_technology_experience', technology, results_count: results.length, results };
    } catch (e) {
      return { status: 'error', tool: 'search_technology_experience', error: String(e) };
    }
  }

  // Tool 4: Search Work by Date Range
  async searchWorkByDate(startYear: number, endYear: number): Promise<ToolResult> {
    try {
      const cvId = await this.getCvId();
      const results = await this.pg.fetchAll(`
        SELECT company, role, start_date, end_date, technologies, keywords
        FROM work_experience
        WHERE cv_id = $1
          AND start_date >= $2::date
          AND (end_date <= $3::date OR end_date IS NULL)
        ORDER BY start_date DESC
      `, [cvId, `${startYear}-01-01`, `${endYear}-12-31`]);

      for (const r of results) {
        for (const key of ['start_date', 'end_date']) {
          if (r[key]) r[key] = String(r[key]);
        }
      }
      return { status: 'success', tool: 'search_work_by_date', date_range: `${startYear}-${endYear}`, results_count: results.length, results };
    } catch (e) {
      return { status: 'error', tool: 'search_work_by_date', error: String(e) };
    }
  }

  // Tool 5: Search Education
  async searchEducation(institution?: string, degree?: string): Promise<ToolResult> {
    try {
      const cvId = await this.getCvId();
      let results: Record<string, unknown>[];
      let searchType: string;

      if (institution) {
        results = await this.pg.fetchAll(`
          SELECT institution, degree, field, specialization, graduation_date, thesis, publications, content
          FROM education
          WHERE cv_id = $1 AND institution ILIKE $2
        `, [cvId, `%${institution}%`]);
        searchType = `institution: ${institution}`;
      } else if (degree) {
        results = await this.pg.fetchAll(`
          SELECT institution, degree, field, specialization, graduation_date, thesis, content
          FROM education
          WHERE cv_id = $1 AND degree ILIKE $2
        `, [cvId, `%${degree}%`]);
        searchType = `degree: ${degree}`;
      } else {
        results = await this.pg.fetchAll(`
          SELECT institution, degree, field, specialization, graduation_date, thesis, content
          FROM education
          WHERE cv_id = $1
        `, [cvId]);
        searchType = 'all education';
      }

      for (const r of results) {
        if (r['graduation_date']) r['graduation_date'] = String(r['graduation_date']);
      }
      return { status: 'success', tool: 'search_education', search_type: searchType, results_count: results.length, results };
    } catch (e) {
      return { status: 'error', tool: 'search_education', error: String(e) };
    }
  }

  // Tool 6: Search Publications
  async searchPublications(year?: number): Promise<ToolResult> {
    try {
      const cvId = await this.getCvId();
      let results: Record<string, unknown>[];
      let searchType: string;

      if (year) {
        results = await this.pg.fetchAll(`
          SELECT title, year, conference_name, doi, keywords, content_text
          FROM publications
          WHERE cv_id = $1 AND year = $2
          ORDER BY year DESC
        `, [cvId, year]);
        searchType = `year: ${year}`;
      } else {
        results = await this.pg.fetchAll(`
          SELECT title, year, conference_name, doi, keywords, content_text
          FROM publications
          WHERE cv_id = $1
          ORDER BY year DESC
        `, [cvId]);
        searchType = 'all publications';
      }
      return { status: 'success', tool: 'search_publications', search_type: searchType, results_count: results.length, results };
    } catch (e) {
      return { status: 'error', tool: 'search_publications', error: String(e) };
    }
  }

  // Tool 7: Search Skills
  async searchSkills(category: string): Promise<ToolResult> {
    try {
      const cvId = await this.getCvId();
      const results = await this.pg.fetchAll(`
        SELECT skill_name
        FROM skills
        WHERE cv_id = $1 AND skill_category = $2
        ORDER BY skill_name
      `, [cvId, category]);
      return { status: 'success', tool: 'search_skills', category, results_count: results.length, results };
    } catch (e) {
      return { status: 'error', tool: 'search_skills', error: String(e) };
    }
  }

  // Tool 8: Search Awards and Certifications
  async searchAwardsCertifications(awardType?: string): Promise<ToolResult> {
    try {
      const cvId = await this.getCvId();
      let results: Record<string, unknown>[];
      let searchType: string;

      if (awardType) {
        results = await this.pg.fetchAll(`
          SELECT title, issuing_organization, organization, issue_date, keywords, content
          FROM awards_certifications
          WHERE cv_id = $1 AND (issuing_organization ILIKE $2 OR organization ILIKE $2 OR title ILIKE $2)
          ORDER BY issue_date DESC
        `, [cvId, `%${awardType}%`]);
        searchType = `type: ${awardType}`;
      } else {
        results = await this.pg.fetchAll(`
          SELECT title, issuing_organization, organization, issue_date, keywords, content
          FROM awards_certifications
          WHERE cv_id = $1
          ORDER BY issue_date DESC
        `, [cvId]);
        searchType = 'all awards and certifications';
      }

      for (const r of results) {
        if (r['issue_date']) r['issue_date'] = String(r['issue_date']);
      }
      return { status: 'success', tool: 'search_awards_certifications', search_type: searchType, results_count: results.length, results };
    } catch (e) {
      return { status: 'error', tool: 'search_awards_certifications', error: String(e) };
    }
  }

  // Tool 9: Semantic Search
  async semanticSearch(query: string, section?: string, topK: number = 5): Promise<ToolResult> {
    try {
      const embeddingResponse = await this.openai.embeddings.create({
        model: 'text-embedding-3-small',
        input: query,
      });
      const vector = embeddingResponse.data[0].embedding;

      const searchParams: Record<string, unknown> = { limit: topK, with_payload: true };
      if (section && section !== 'all') {
        searchParams['filter'] = {
          must: [{ key: 'section', match: { value: section } }],
        };
      }

      const results = await this.qdrant.client.search(
        this.config.getQdrantCollection(),
        { vector, ...searchParams } as Parameters<typeof this.qdrant.client.search>[1],
      );

      const formattedResults = results.map((result) => {
        const payload = result.payload ?? {};
        const sectionValue = String(payload['section'] ?? '');
        const fr: Record<string, unknown> = {
          chunk_id: payload['chunk_id'],
          cv_id: payload['cv_id'],
          section: sectionValue,
          similarity_score: result.score,
        };

        if (sectionValue === 'work experience') {
          if (payload['company']) fr['company'] = payload['company'];
          if (payload['role']) fr['role'] = payload['role'];
          if (payload['domain']) fr['domain'] = payload['domain'];
          if (payload['responsibility']) fr['responsibility'] = payload['responsibility'];
        } else if (sectionValue === 'education') {
          if (payload['institution']) fr['institution'] = payload['institution'];
          if (payload['degree']) fr['degree'] = payload['degree'];
          if (payload['thesis']) fr['thesis'] = payload['thesis'];
          if (payload['graduation_date']) fr['graduation_date'] = payload['graduation_date'];
          if (payload['description']) fr['description'] = payload['description'];
        } else if (sectionValue === 'publication') {
          if (payload['title']) fr['title'] = payload['title'];
          if (payload['description']) fr['description'] = payload['description'];
        } else if (sectionValue === 'projects') {
          if (payload['project_name']) fr['project_name'] = payload['project_name'];
          if (payload['responsibility']) fr['responsibility'] = payload['responsibility'];
          if (payload['technologies']) fr['technologies'] = payload['technologies'];
          if (payload['description']) fr['description'] = payload['description'];
        }

        if (payload['technologies']) fr['technologies'] = payload['technologies'];
        if (payload['skills']) fr['skills'] = payload['skills'];
        if (payload['description'] && !fr['description']) fr['description'] = payload['description'];

        return fr;
      });

      return { status: 'success', tool: 'semantic_search', query, section_filter: section ?? 'all', results_count: formattedResults.length, results: formattedResults };
    } catch (e) {
      return { status: 'error', tool: 'semantic_search', error: String(e) };
    }
  }

  // Tool 10: Get All Work Experience
  async getAllWorkExperience(): Promise<ToolResult> {
    try {
      const cvId = await this.getCvId();
      const results = await this.pg.fetchAll(`
        SELECT company, role, location, start_date, end_date, is_current,
               technologies, skills, domain, seniority, team_size, content
        FROM work_experience
        WHERE cv_id = $1
        ORDER BY start_date DESC
      `, [cvId]);

      for (const r of results) {
        for (const key of ['start_date', 'end_date']) {
          if (r[key]) r[key] = String(r[key]);
        }
      }
      return { status: 'success', tool: 'get_all_work_experience', results_count: results.length, results };
    } catch (e) {
      return { status: 'error', tool: 'get_all_work_experience', error: String(e) };
    }
  }

  // Tool 11: Search Languages
  async searchLanguages(language?: string): Promise<ToolResult> {
    try {
      const cvId = await this.getCvId();
      let results: Record<string, unknown>[];
      let searchType: string;

      if (language) {
        results = await this.pg.fetchAll(`
          SELECT language, proficiency_level
          FROM languages
          WHERE cv_id = $1 AND language ILIKE $2
          ORDER BY language
        `, [cvId, `%${language}%`]);
        searchType = `language: ${language}`;
      } else {
        results = await this.pg.fetchAll(`
          SELECT language, proficiency_level
          FROM languages
          WHERE cv_id = $1
          ORDER BY language
        `, [cvId]);
        searchType = 'all languages';
      }
      return { status: 'success', tool: 'search_languages', search_type: searchType, results_count: results.length, results };
    } catch (e) {
      return { status: 'error', tool: 'search_languages', error: String(e) };
    }
  }

  // Tool 12: Get Contact Info
  async getContactInfo(): Promise<ToolResult> {
    try {
      const cvId = await this.getCvId();
      const result = await this.pg.fetchOne(`
        SELECT name, email, email_alt, linkedin, github
        FROM cv_metadata
        WHERE id = $1
      `, [cvId]);
      if (result) {
        return { status: 'success', tool: 'get_contact_info', data: result };
      }
      return { status: 'error', tool: 'get_contact_info', error: 'Contact information not found' };
    } catch (e) {
      return { status: 'error', tool: 'get_contact_info', error: String(e) };
    }
  }

  // Tool 13: Search Work References
  async searchWorkReferences(referenceName?: string, company?: string): Promise<ToolResult> {
    try {
      const cvId = await this.getCvId();
      let results: Record<string, unknown>[];
      let searchType: string;

      if (referenceName) {
        results = await this.pg.fetchAll(`
          SELECT name, position, company, email, note
          FROM work_references
          WHERE cv_id = $1 AND name ILIKE $2
          ORDER BY name
        `, [cvId, `%${referenceName}%`]);
        searchType = `name: ${referenceName}`;
      } else if (company) {
        results = await this.pg.fetchAll(`
          SELECT name, position, company, email, note
          FROM work_references
          WHERE cv_id = $1 AND company ILIKE $2
          ORDER BY name
        `, [cvId, `%${company}%`]);
        searchType = `company: ${company}`;
      } else {
        results = await this.pg.fetchAll(`
          SELECT name, position, company, email, note
          FROM work_references
          WHERE cv_id = $1
          ORDER BY name
        `, [cvId]);
        searchType = 'all references';
      }
      return { status: 'success', tool: 'search_work_references', search_type: searchType, results_count: results.length, results };
    } catch (e) {
      return { status: 'error', tool: 'search_work_references', error: String(e) };
    }
  }
}
