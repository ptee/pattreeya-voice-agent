Create a comprehensive project plan and task checklist for building a voice agent application with the following specifications:

## Project Overview ##
- The project consists of 2 phases:
    - phase I is about backend engine with Python
    - phase II is about frontend with React.
    - phase III is to do quality assurance

### Phase I: Backend ##
- Backend engine is for voice agent with Python and terminal/console.
- Voice agent using LiveKit and its plugins for real-time communication, as shown in `src/agent.py` as a template and starting point.
- It is a RAG system that restricted for personal assistent context.
- Agent prompt instructions of the RAGs read from `src/prompts.py`
- The "SYSTEM_PROMPT" in `src/prompts.py` is the instruction to the LLM model.
- The secrets e.g. api key and other are stored in `.env.local` and are loaded from a configure file under `src/config.py` which  is now empty. You look into the `.env.local` and construct the config to read this file and return the output to the required files.
- Make sure that you don't expose any secrets to the code. For accessing PostgreSQL via MCP, use `POSTGRESQL_URL` in `.env.local`.
- As for semantic_search function, we use Qdrant vector database. Read its collection from `QDRANT_VECTOR_COLLECTION` and the Qdrant URL in `QDRANT_URL` as well as its API's key from `QDRANT_API_KEY`.
- Data retrieval from Tools (PostgreSQL via MCP and Qdrant Vector DB) are used to answer the questions, we have already constructed the MCP server and client that are `src/mcp_server.py` and `src/mcp_client.py`. 

- Write simple tests at the end of each file via __main__
- Write complex tests for each module, that are agent.py, mcp_client.py and mcp_server.py.


### Phase II: Frontend  ###
- Now, instead of using "terminal/console" app from Phase I, we create a web site for it.  
- Lookinto the codebase in `/home/pt/Projects/LLMs/voice-agents/agent-starter-react-pt`   for the frontend and fork the frontend from there.
- Integrate the Python backend engine and frontend together.

### Phase III: Quality Assurance ###
- Propose testing strategies and add logging
- Deployment considerations