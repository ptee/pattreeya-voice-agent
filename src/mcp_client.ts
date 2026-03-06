import type { ConfigManager } from './config.js';
import { getConfig } from './config.js';
import { DatabaseTools } from './mcp_server.js';
import { MCPServerError } from './exceptions.js';

type ToolResult = Record<string, unknown>;

export class MCPClient {
  private tools: DatabaseTools;
  cvId!: string;

  constructor(config?: ConfigManager) {
    try {
      const cfg = config ?? getConfig();
      this.tools = new DatabaseTools(cfg);
    } catch (e) {
      throw new MCPServerError(`MCP Client initialization failed: ${e}`);
    }
  }

  async init(): Promise<void> {
    this.cvId = await this.tools.getCvId();
  }

  getCvSummary(): Promise<ToolResult> { return this.tools.getCvSummary(); }
  searchCompanyExperience(companyName: string): Promise<ToolResult> { return this.tools.searchCompanyExperience(companyName); }
  searchTechnologyExperience(technology: string): Promise<ToolResult> { return this.tools.searchTechnologyExperience(technology); }
  searchWorkByDate(startYear: number, endYear: number): Promise<ToolResult> { return this.tools.searchWorkByDate(startYear, endYear); }
  searchEducation(institution?: string, degree?: string): Promise<ToolResult> { return this.tools.searchEducation(institution, degree); }
  searchPublications(year?: number): Promise<ToolResult> { return this.tools.searchPublications(year); }
  searchSkills(category: string): Promise<ToolResult> { return this.tools.searchSkills(category); }
  searchAwardsCertifications(awardType?: string): Promise<ToolResult> { return this.tools.searchAwardsCertifications(awardType); }
  semanticSearch(query: string, section?: string, topK: number = 5): Promise<ToolResult> { return this.tools.semanticSearch(query, section, topK); }
  getAllWorkExperience(): Promise<ToolResult> { return this.tools.getAllWorkExperience(); }
  searchLanguages(language?: string): Promise<ToolResult> { return this.tools.searchLanguages(language); }
  getContactInfo(): Promise<ToolResult> { return this.tools.getContactInfo(); }
  searchWorkReferences(referenceName?: string, company?: string): Promise<ToolResult> { return this.tools.searchWorkReferences(referenceName, company); }
}

let _client: MCPClient | null = null;

export async function getMcpClient(): Promise<MCPClient> {
  if (!_client) {
    _client = new MCPClient();
    await _client.init();
  }
  return _client;
}
