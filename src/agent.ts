import { voice, llm } from '@livekit/agents';
import { z } from 'zod';
import { SYSTEM_PROMPT } from './prompts.js';
import type { MCPClient } from './mcp_client.js';
import type { RoomManager } from './room_manager.js';

const toolLog = {
  info: (tool: string, msg: string) => console.info(`[TOOL] ${tool}: ${msg}`),
  error: (tool: string, msg: string, err?: unknown) =>
    console.error(`[TOOL] ${tool} error: ${msg}`, err ?? ''),
};

export class Assistant extends voice.Agent {
  constructor(mcpRef: { client: MCPClient | null }, roomManager: RoomManager) {
    console.info(`[AGENT] Assistant constructor: mcpRef=${mcpRef.client ? 'ready' : 'pending'}, roomManager=${roomManager ? 'ready' : 'null'}`);
    const unavailable = () => {
      console.warn('[TOOL] MCP client unavailable — voice-only mode');
      return 'CV database is currently unavailable (voice-only mode).';
    };
    super({
      instructions: SYSTEM_PROMPT,
      tools: {
        get_cv_summary: llm.tool({
          description: 'Get a high-level summary of the person\'s CV including role, experience, and key stats.',
          parameters: z.object({}),
          execute: async () => {
            if (!mcpRef.client) return unavailable();
            try {
              const result = await mcpRef.client.getCvSummary();
              if (result['status'] === 'success') {
                toolLog.info('get_cv_summary', 'success');
                return `Summary: ${JSON.stringify(result['summary'])}`;
              }
              toolLog.error('get_cv_summary', String(result['error']));
              return `Error retrieving CV summary: ${result['error']}`;
            } catch (e) {
              toolLog.error('get_cv_summary', 'threw', e);
              return `Error: ${e}`;
            }
          },
        }),

        search_company_experience: llm.tool({
          description: 'Find all work experience at a specific company.',
          parameters: z.object({ company_name: z.string() }),
          execute: async ({ company_name }) => {
            if (!mcpRef.client) return unavailable();
            const result = await mcpRef.client.searchCompanyExperience(company_name);
            if (result['status'] === 'success') {
              const results = result['results'] as unknown[];
              if (results.length > 0) return `Found ${results.length} job(s) at ${company_name}: ${JSON.stringify(results)}`;
              return `No experience found at ${company_name}`;
            }
            toolLog.error('tool', String(result['error']));
            return `Error: ${result['error']}`;
          },
        }),

        search_work_by_date: llm.tool({
          description: 'Find work experience within a date range.',
          parameters: z.object({ start_year: z.number().int(), end_year: z.number().int() }),
          execute: async ({ start_year, end_year }) => {
            if (!mcpRef.client) return unavailable();
            const result = await mcpRef.client.searchWorkByDate(start_year, end_year);
            if (result['status'] === 'success') {
              const results = result['results'] as unknown[];
              if (results.length > 0) return `Found ${results.length} job(s) between ${start_year}-${end_year}: ${JSON.stringify(results)}`;
              return `No work experience found between ${start_year} and ${end_year}`;
            }
            toolLog.error('tool', String(result['error']));
            return `Error: ${result['error']}`;
          },
        }),

        search_technology_experience: llm.tool({
          description: 'Find all jobs using a specific technology.',
          parameters: z.object({ technology: z.string() }),
          execute: async ({ technology }) => {
            if (!mcpRef.client) return unavailable();
            const result = await mcpRef.client.searchTechnologyExperience(technology);
            if (result['status'] === 'success') {
              const results = result['results'] as unknown[];
              if (results.length > 0) return `Found ${results.length} job(s) using ${technology}: ${JSON.stringify(results)}`;
              return `No experience found with ${technology}`;
            }
            toolLog.error('tool', String(result['error']));
            return `Error: ${result['error']}`;
          },
        }),

        search_education: llm.tool({
          description: 'Find education records by institution or degree type.',
          parameters: z.object({
            institution: z.string().nullish(),
            degree: z.string().nullish(),
          }),
          execute: async ({ institution, degree }) => {
            if (!mcpRef.client) return unavailable();
            const result = await mcpRef.client.searchEducation(institution ?? undefined, degree ?? undefined);
            if (result['status'] === 'success') {
              const results = result['results'] as unknown[];
              if (results.length > 0) return `Found ${results.length} education record(s): ${JSON.stringify(results)}`;
              return 'No education records found';
            }
            toolLog.error('tool', String(result['error']));
            return `Error: ${result['error']}`;
          },
        }),

        search_publications: llm.tool({
          description: 'Search publications by year or get all publications.',
          parameters: z.object({ year: z.number().int().nullish() }),
          execute: async ({ year }) => {
            if (!mcpRef.client) return unavailable();
            const result = await mcpRef.client.searchPublications(year ?? undefined);
            if (result['status'] === 'success') {
              const results = result['results'] as unknown[];
              if (results.length > 0) return `Found ${results.length} publication(s): ${JSON.stringify(results)}`;
              return 'No publications found';
            }
            toolLog.error('tool', String(result['error']));
            return `Error: ${result['error']}`;
          },
        }),

        search_skills: llm.tool({
          description: 'Find skills by category (AI, ML, programming, Tools, Cloud, Data_tools).',
          parameters: z.object({ category: z.string() }),
          execute: async ({ category }) => {
            if (!mcpRef.client) return unavailable();
            const result = await mcpRef.client.searchSkills(category);
            if (result['status'] === 'success') {
              const results = result['results'] as Array<Record<string, string>>;
              if (results.length > 0) {
                const skills = results.map((r) => r['skill_name']).join(', ');
                return `Skills in ${category}: ${skills}`;
              }
              return `No skills found in category ${category}`;
            }
            toolLog.error('tool', String(result['error']));
            return `Error: ${result['error']}`;
          },
        }),

        search_awards_certifications: llm.tool({
          description: 'Find awards and certifications records.',
          parameters: z.object({ award_type: z.string().nullish() }),
          execute: async ({ award_type }) => {
            if (!mcpRef.client) return unavailable();
            const result = await mcpRef.client.searchAwardsCertifications(award_type ?? undefined);
            if (result['status'] === 'success') {
              const results = result['results'] as unknown[];
              if (results.length > 0) return `Found ${results.length} award(s)/certification(s): ${JSON.stringify(results)}`;
              return 'No awards or certifications found';
            }
            toolLog.error('tool', String(result['error']));
            return `Error: ${result['error']}`;
          },
        }),

        semantic_search: llm.tool({
          description: 'Perform semantic search on CV content using vector embeddings.',
          parameters: z.object({
            query: z.string(),
            section: z.string().nullish(),
            top_k: z.number().int().nullish(),
          }),
          execute: async ({ query, section, top_k }) => {
            if (!mcpRef.client) return unavailable();
            const result = await mcpRef.client.semanticSearch(query, section ?? undefined, top_k ?? 5);
            if (result['status'] === 'success') {
              const results = result['results'] as unknown[];
              if (results.length > 0) return `Found ${results.length} relevant result(s): ${JSON.stringify(results)}`;
              return 'No relevant results found for your query';
            }
            toolLog.error('tool', String(result['error']));
            return `Error: ${result['error']}`;
          },
        }),

        get_all_work_experience: llm.tool({
          description: 'Get complete work experience history - all jobs in chronological order. Use this for general experience, career history, or all jobs queries.',
          parameters: z.object({}),
          execute: async () => {
            if (!mcpRef.client) return unavailable();
            const result = await mcpRef.client.getAllWorkExperience();
            if (result['status'] === 'success') {
              const results = result['results'] as unknown[];
              if (results.length > 0) return `Found ${results.length} work experience record(s): ${JSON.stringify(results)}`;
              return 'No work experience records found';
            }
            toolLog.error('tool', String(result['error']));
            return `Error: ${result['error']}`;
          },
        }),

        search_languages: llm.tool({
          description: 'Find languages spoken and proficiency levels.',
          parameters: z.object({ language: z.string().nullish() }),
          execute: async ({ language }) => {
            if (!mcpRef.client) return unavailable();
            const result = await mcpRef.client.searchLanguages(language ?? undefined);
            if (result['status'] === 'success') {
              const results = result['results'] as unknown[];
              if (results.length > 0) return `Found ${results.length} language(s): ${JSON.stringify(results)}`;
              return 'No language records found';
            }
            toolLog.error('tool', String(result['error']));
            return `Error: ${result['error']}`;
          },
        }),

        get_contact_info: llm.tool({
          description: 'Get contact information: email, LinkedIn, and GitHub.',
          parameters: z.object({}),
          execute: async () => {
            if (!mcpRef.client) return unavailable();
            const result = await mcpRef.client.getContactInfo();
            if (result['status'] === 'success') {
              return `Contact info: ${JSON.stringify(result['data'])}`;
            }
            toolLog.error('tool', String(result['error']));
            return `Error: ${result['error']}`;
          },
        }),

        search_work_references: llm.tool({
          description: 'Find professional work references by name or company.',
          parameters: z.object({
            reference_name: z.string().nullish(),
            company: z.string().nullish(),
          }),
          execute: async ({ reference_name, company }) => {
            if (!mcpRef.client) return unavailable();
            const result = await mcpRef.client.searchWorkReferences(reference_name ?? undefined, company ?? undefined);
            if (result['status'] === 'success') {
              const results = result['results'] as unknown[];
              if (results.length > 0) return `Found ${results.length} reference(s): ${JSON.stringify(results)}`;
              return 'No work references found';
            }
            toolLog.error('tool', String(result['error']));
            return `Error: ${result['error']}`;
          },
        }),

        create_pattreeya_room: llm.tool({
          description: "Create a new LiveKit room with 'pattreeya-' prefix for voice conversations.",
          parameters: z.object({ room_name_suffix: z.string().nullish() }),
          execute: async ({ room_name_suffix }) => {
            try {
              const roomName = await roomManager.createPattreeyaRoom(room_name_suffix ?? undefined);
              return `Successfully created room: ${roomName}. You can now connect to this room for a voice conversation with Pattreeya.`;
            } catch (e) {
              return `Failed to create room: ${e}`;
            }
          },
        }),

        list_pattreeya_rooms: llm.tool({
          description: 'List all active pattreeya rooms currently available.',
          parameters: z.object({}),
          execute: async () => {
            try {
              const rooms = await roomManager.listPattreeyaRooms();
              if (rooms.length > 0) return `Currently active pattreeya rooms: ${rooms.join(', ')}`;
              return 'No active pattreeya rooms at the moment.';
            } catch (e) {
              return `Failed to list rooms: ${e}`;
            }
          },
        }),

        delete_pattreeya_room: llm.tool({
          description: 'Delete a specific pattreeya room.',
          parameters: z.object({ room_name: z.string() }),
          execute: async ({ room_name }) => {
            try {
              await roomManager.deletePattreeyaRoom(room_name);
              return `Successfully deleted room: ${room_name}`;
            } catch (e) {
              return `Failed to delete room: ${e}`;
            }
          },
        }),
      },
    });
  }

}
