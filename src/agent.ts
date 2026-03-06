import { voice, llm } from '@livekit/agents';
import { z } from 'zod';
import { SYSTEM_PROMPT } from './prompts.js';
import type { MCPClient } from './mcp_client.js';
import type { RoomManager } from './room_manager.js';

export class Assistant extends voice.Agent {
  constructor(mcpClient: MCPClient, roomManager: RoomManager) {
    super({
      instructions: SYSTEM_PROMPT,
      tools: {
        get_cv_summary: llm.tool({
          description: 'Get a high-level summary of the person\'s CV including role, experience, and key stats.',
          parameters: z.object({}),
          execute: async () => {
            const result = await mcpClient.getCvSummary();
            if (result['status'] === 'success') {
              return `Summary: ${JSON.stringify(result['summary'])}`;
            }
            return `Error retrieving CV summary: ${result['error']}`;
          },
        }),

        search_company_experience: llm.tool({
          description: 'Find all work experience at a specific company.',
          parameters: z.object({ company_name: z.string() }),
          execute: async ({ company_name }) => {
            const result = await mcpClient.searchCompanyExperience(company_name);
            if (result['status'] === 'success') {
              const results = result['results'] as unknown[];
              if (results.length > 0) return `Found ${results.length} job(s) at ${company_name}: ${JSON.stringify(results)}`;
              return `No experience found at ${company_name}`;
            }
            return `Error: ${result['error']}`;
          },
        }),

        search_work_by_date: llm.tool({
          description: 'Find work experience within a date range.',
          parameters: z.object({ start_year: z.number().int(), end_year: z.number().int() }),
          execute: async ({ start_year, end_year }) => {
            const result = await mcpClient.searchWorkByDate(start_year, end_year);
            if (result['status'] === 'success') {
              const results = result['results'] as unknown[];
              if (results.length > 0) return `Found ${results.length} job(s) between ${start_year}-${end_year}: ${JSON.stringify(results)}`;
              return `No work experience found between ${start_year} and ${end_year}`;
            }
            return `Error: ${result['error']}`;
          },
        }),

        search_technology_experience: llm.tool({
          description: 'Find all jobs using a specific technology.',
          parameters: z.object({ technology: z.string() }),
          execute: async ({ technology }) => {
            const result = await mcpClient.searchTechnologyExperience(technology);
            if (result['status'] === 'success') {
              const results = result['results'] as unknown[];
              if (results.length > 0) return `Found ${results.length} job(s) using ${technology}: ${JSON.stringify(results)}`;
              return `No experience found with ${technology}`;
            }
            return `Error: ${result['error']}`;
          },
        }),

        search_education: llm.tool({
          description: 'Find education records by institution or degree type.',
          parameters: z.object({
            institution: z.string().optional(),
            degree: z.string().optional(),
          }),
          execute: async ({ institution, degree }) => {
            const result = await mcpClient.searchEducation(institution, degree);
            if (result['status'] === 'success') {
              const results = result['results'] as unknown[];
              if (results.length > 0) return `Found ${results.length} education record(s): ${JSON.stringify(results)}`;
              return 'No education records found';
            }
            return `Error: ${result['error']}`;
          },
        }),

        search_publications: llm.tool({
          description: 'Search publications by year or get all publications.',
          parameters: z.object({ year: z.number().int().optional() }),
          execute: async ({ year }) => {
            const result = await mcpClient.searchPublications(year);
            if (result['status'] === 'success') {
              const results = result['results'] as unknown[];
              if (results.length > 0) return `Found ${results.length} publication(s): ${JSON.stringify(results)}`;
              return 'No publications found';
            }
            return `Error: ${result['error']}`;
          },
        }),

        search_skills: llm.tool({
          description: 'Find skills by category (AI, ML, programming, Tools, Cloud, Data_tools).',
          parameters: z.object({ category: z.string() }),
          execute: async ({ category }) => {
            const result = await mcpClient.searchSkills(category);
            if (result['status'] === 'success') {
              const results = result['results'] as Array<Record<string, string>>;
              if (results.length > 0) {
                const skills = results.map((r) => r['skill_name']).join(', ');
                return `Skills in ${category}: ${skills}`;
              }
              return `No skills found in category ${category}`;
            }
            return `Error: ${result['error']}`;
          },
        }),

        search_awards_certifications: llm.tool({
          description: 'Find awards and certifications records.',
          parameters: z.object({ award_type: z.string().optional() }),
          execute: async ({ award_type }) => {
            const result = await mcpClient.searchAwardsCertifications(award_type);
            if (result['status'] === 'success') {
              const results = result['results'] as unknown[];
              if (results.length > 0) return `Found ${results.length} award(s)/certification(s): ${JSON.stringify(results)}`;
              return 'No awards or certifications found';
            }
            return `Error: ${result['error']}`;
          },
        }),

        semantic_search: llm.tool({
          description: 'Perform semantic search on CV content using vector embeddings.',
          parameters: z.object({
            query: z.string(),
            section: z.string().optional(),
            top_k: z.number().int().optional(),
          }),
          execute: async ({ query, section, top_k }) => {
            const result = await mcpClient.semanticSearch(query, section, top_k ?? 5);
            if (result['status'] === 'success') {
              const results = result['results'] as unknown[];
              if (results.length > 0) return `Found ${results.length} relevant result(s): ${JSON.stringify(results)}`;
              return 'No relevant results found for your query';
            }
            return `Error: ${result['error']}`;
          },
        }),

        get_all_work_experience: llm.tool({
          description: 'Get complete work experience history - all jobs in chronological order. Use this for general experience, career history, or all jobs queries.',
          parameters: z.object({}),
          execute: async () => {
            const result = await mcpClient.getAllWorkExperience();
            if (result['status'] === 'success') {
              const results = result['results'] as unknown[];
              if (results.length > 0) return `Found ${results.length} work experience record(s): ${JSON.stringify(results)}`;
              return 'No work experience records found';
            }
            return `Error: ${result['error']}`;
          },
        }),

        search_languages: llm.tool({
          description: 'Find languages spoken and proficiency levels.',
          parameters: z.object({ language: z.string().optional() }),
          execute: async ({ language }) => {
            const result = await mcpClient.searchLanguages(language);
            if (result['status'] === 'success') {
              const results = result['results'] as unknown[];
              if (results.length > 0) return `Found ${results.length} language(s): ${JSON.stringify(results)}`;
              return 'No language records found';
            }
            return `Error: ${result['error']}`;
          },
        }),

        get_contact_info: llm.tool({
          description: 'Get contact information: email, LinkedIn, and GitHub.',
          parameters: z.object({}),
          execute: async () => {
            const result = await mcpClient.getContactInfo();
            if (result['status'] === 'success') {
              return `Contact info: ${JSON.stringify(result['data'])}`;
            }
            return `Error: ${result['error']}`;
          },
        }),

        search_work_references: llm.tool({
          description: 'Find professional work references by name or company.',
          parameters: z.object({
            reference_name: z.string().optional(),
            company: z.string().optional(),
          }),
          execute: async ({ reference_name, company }) => {
            const result = await mcpClient.searchWorkReferences(reference_name, company);
            if (result['status'] === 'success') {
              const results = result['results'] as unknown[];
              if (results.length > 0) return `Found ${results.length} reference(s): ${JSON.stringify(results)}`;
              return 'No work references found';
            }
            return `Error: ${result['error']}`;
          },
        }),

        create_pattreeya_room: llm.tool({
          description: "Create a new LiveKit room with 'pattreeya-' prefix for voice conversations.",
          parameters: z.object({ room_name_suffix: z.string().optional() }),
          execute: async ({ room_name_suffix }) => {
            try {
              const roomName = await roomManager.createPattreeyaRoom(room_name_suffix);
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
