import logging
import os
from typing import Optional

from dotenv import load_dotenv
from livekit import rtc
from livekit.agents import (
    Agent,
    AgentServer,
    AgentSession,
    JobContext,
    JobProcess,
    cli,
    inference,
    room_io,
    function_tool,
    RunContext,
)
from livekit.plugins import noise_cancellation, silero, elevenlabs, tavus, simli, bey
from livekit.plugins.turn_detector.multilingual import MultilingualModel
import sys
is_console_mode = 'console' in sys.argv

from config import get_config
from mcp_client import get_mcp_client
from prompts import SYSTEM_PROMPT
from room_manager import get_room_manager
from web_server import run_web_server

logger = logging.getLogger("agent")
stt_logger = logging.getLogger("stt")
language_logger = logging.getLogger("language_detection")

load_dotenv()


class Assistant(Agent):
    def __init__(self, mcp_client=None, room_manager=None) -> None:
        self.mcp_client = mcp_client or get_mcp_client()
        # Lazy initialization: room_manager will be initialized when first needed
        # This avoids "no running event loop" errors during synchronous initialization
        self._room_manager = room_manager
        super().__init__(
            instructions=SYSTEM_PROMPT,
        )

    @property
    def room_manager(self):
        """Lazy initialization of room manager"""
        if self._room_manager is None:
            try:
                self._room_manager = get_room_manager()
            except RuntimeError as e:
                # If no event loop is running, defer initialization
                if "no running event loop" in str(e):
                    logger.debug("Deferring room_manager initialization until event loop is available")
                    return None
                raise
        return self._room_manager

    async def _get_room_manager(self):
        """Get room manager with event loop guarantee (for async contexts)"""
        if self._room_manager is None:
            self._room_manager = get_room_manager()
        return self._room_manager

    @function_tool
    async def get_cv_summary(self, _: RunContext) -> str:
        """Get a high-level summary of the person's CV including role, experience, and key stats."""
        try:
            result = self.mcp_client.get_cv_summary()
            if result['status'] == 'success':
                summary = result.get('summary', {})
                return f"Summary: {summary}"
            else:
                return f"Error retrieving CV summary: {result.get('error')}"
        except Exception as e:
            logger.error(f"Error in get_cv_summary: {e}")
            return f"Error: {str(e)}"

    @function_tool
    async def search_company_experience(self, _: RunContext, company_name: str) -> str:
        """Find all work experience at a specific company."""
        try:
            result = self.mcp_client.search_company_experience(company_name)
            if result['status'] == 'success':
                results = result.get('results', [])
                if results:
                    return f"Found {len(results)} job(s) at {company_name}: {results}"
                else:
                    return f"No experience found at {company_name}"
            else:
                return f"Error: {result.get('error')}"
        except Exception as e:
            logger.error(f"Error in search_company_experience: {e}")
            return f"Error: {str(e)}"

    @function_tool
    async def search_technology_experience(self, _: RunContext, technology: str) -> str:
        """Find all jobs using a specific technology."""
        try:
            result = self.mcp_client.search_technology_experience(technology)
            if result['status'] == 'success':
                results = result.get('results', [])
                if results:
                    return f"Found {len(results)} job(s) using {technology}: {results}"
                else:
                    return f"No experience found with {technology}"
            else:
                return f"Error: {result.get('error')}"
        except Exception as e:
            logger.error(f"Error in search_technology_experience: {e}")
            return f"Error: {str(e)}"

    @function_tool
    async def search_education(self, _: RunContext, institution: Optional[str] = None, degree: Optional[str] = None) -> str:
        """Find education records by institution or degree type."""
        try:
            result = self.mcp_client.search_education(institution, degree)
            if result['status'] == 'success':
                results = result.get('results', [])
                if results:
                    return f"Found {len(results)} education record(s): {results}"
                else:
                    return f"No education records found"
            else:
                return f"Error: {result.get('error')}"
        except Exception as e:
            logger.error(f"Error in search_education: {e}")
            return f"Error: {str(e)}"

    @function_tool
    async def search_publications(self, _: RunContext, year: Optional[int] = None) -> str:
        """Search publications by year or get all publications."""
        try:
            result = self.mcp_client.search_publications(year)
            if result['status'] == 'success':
                results = result.get('results', [])
                if results:
                    return f"Found {len(results)} publication(s): {results}"
                else:
                    return f"No publications found"
            else:
                return f"Error: {result.get('error')}"
        except Exception as e:
            logger.error(f"Error in search_publications: {e}")
            return f"Error: {str(e)}"

    @function_tool
    async def search_skills(self, _: RunContext, category: str) -> str:
        """Find skills by category (AI, ML, programming, Tools, Cloud, Data_tools)."""
        try:
            result = self.mcp_client.search_skills(category)
            if result['status'] == 'success':
                results = result.get('results', [])
                if results:
                    skills = [r.get('skill_name') for r in results]
                    return f"Skills in {category}: {', '.join(skills)}"
                else:
                    return f"No skills found in category {category}"
            else:
                return f"Error: {result.get('error')}"
        except Exception as e:
            logger.error(f"Error in search_skills: {e}")
            return f"Error: {str(e)}"

    @function_tool
    async def search_awards_certifications(self, _: RunContext, award_type: Optional[str] = None) -> str:
        """Find awards and certifications records."""
        try:
            result = self.mcp_client.search_awards_certifications(award_type)
            if result['status'] == 'success':
                results = result.get('results', [])
                if results:
                    return f"Found {len(results)} award(s)/certification(s): {results}"
                else:
                    return f"No awards or certifications found"
            else:
                return f"Error: {result.get('error')}"
        except Exception as e:
            logger.error(f"Error in search_awards_certifications: {e}")
            return f"Error: {str(e)}"

    @function_tool
    async def semantic_search(self, _: RunContext, query: str, section: Optional[str] = None, top_k: int = 5) -> str:
        """Perform semantic search on CV content using vector embeddings."""
        try:
            result = self.mcp_client.semantic_search(query, section, top_k)
            if result['status'] == 'success':
                results = result.get('results', [])
                if results:
                    return f"Found {len(results)} relevant result(s): {results}"
                else:
                    return f"No relevant results found for your query"
            else:
                return f"Error: {result.get('error')}"
        except Exception as e:
            logger.error(f"Error in semantic_search: {e}")
            return f"Error: {str(e)}"

    @function_tool
    async def create_pattreeya_room(self, _: RunContext, room_name_suffix: Optional[str] = None) -> str:
        """Create a new LiveKit room with 'pattreeya-' prefix for voice conversations.

        Args:
            room_name_suffix: Optional custom suffix for the room name.
                            If not provided, a timestamp will be used (e.g., 'pattreeya-20250120-143025')

        Returns a message with the created room name."""
        try:
            rm = await self._get_room_manager()
            room_name = await rm.create_pattreeya_room(
                room_name_suffix=room_name_suffix
            )
            return f"Successfully created room: {room_name}. You can now connect to this room for a voice conversation with Pattreeya."
        except Exception as e:
            logger.error(f"Error creating pattreeya room: {e}")
            return f"Failed to create room: {str(e)}"

    @function_tool
    async def list_pattreeya_rooms(self, _: RunContext) -> str:
        """List all active pattreeya rooms currently available."""
        try:
            rm = await self._get_room_manager()
            rooms = await rm.list_pattreeya_rooms()
            if rooms:
                room_list = ", ".join(rooms)
                return f"Currently active pattreeya rooms: {room_list}"
            else:
                return "No active pattreeya rooms at the moment."
        except Exception as e:
            logger.error(f"Error listing pattreeya rooms: {e}")
            return f"Failed to list rooms: {str(e)}"

    @function_tool
    async def delete_pattreeya_room(self, _: RunContext, room_name: str) -> str:
        """Delete a specific pattreeya room.

        Args:
            room_name: Name of the room to delete (should start with 'pattreeya-')

        Returns a confirmation message."""
        try:
            rm = await self._get_room_manager()
            success = await rm.delete_pattreeya_room(room_name)
            if success:
                return f"Successfully deleted room: {room_name}"
            else:
                return f"Failed to delete room: {room_name}"
        except Exception as e:
            logger.error(f"Error deleting pattreeya room: {e}")
            return f"Failed to delete room: {str(e)}"


def configure_stt_logging():
    """Configure logging for STT and language detection."""
    # STT Logger - logs transcribed text and model info
    stt_handler = logging.StreamHandler()
    stt_handler.setFormatter(
        logging.Formatter(
            "%(asctime)s - %(name)s - STT - %(levelname)s - %(message)s"
        )
    )
    stt_logger.addHandler(stt_handler)
    stt_logger.setLevel(logging.INFO)

    # Language Detection Logger - logs detected languages
    lang_handler = logging.StreamHandler()
    lang_handler.setFormatter(
        logging.Formatter(
            "%(asctime)s - %(name)s - LANG_DETECTION - %(levelname)s - %(message)s"
        )
    )
    language_logger.addHandler(lang_handler)
    language_logger.setLevel(logging.INFO)


server = AgentServer()


def prewarm(proc: JobProcess):
    """Prewarm models and configure logging."""
    proc.userdata["vad"] = silero.VAD.load()
    # Configure STT logging
    configure_stt_logging()
    stt_logger.info("STT logging configured - ready to capture transcriptions")


server.setup_fnc = prewarm


@server.rtc_session()
async def my_agent(ctx: JobContext):
    # Logging setup with room and user context
    ctx.log_context_fields = {
        "room": ctx.room.name,
    }

    # Log session start
    logger.info(
        f"🎤 Agent session started in room: {ctx.room.name}"
    )

    # Log STT configuration
    stt_logger.info("=" * 60)
    stt_logger.info("STT Configuration")
    stt_logger.info("=" * 60)
    stt_logger.info("Model: Deepgram Nova-3")
    stt_logger.info("Language Mode: multi (automatic language detection)")
    stt_logger.info("Supported Languages: 99+ (including EN, DE, ES, FR, TH, etc.)")
    stt_logger.info("Language Detection: Automatic from audio input")
    stt_logger.info("=" * 60)

    language_logger.info(
        "Language detection initialized - ready to detect user's language from speech"
    )

    # Set up a voice AI pipeline with multilingual support (Deepgram Nova-3, OpenAI, Cartesia, and LiveKit Multilingual Turn Detector)
    session = AgentSession(
        # Speech-to-text (STT) is your agent's ears, turning the user's speech into text that the LLM can understand
        # Deepgram Nova-3 with language="multi" for automatic language detection (supports 99+ languages)
        # See all available models at https://docs.livekit.io/agents/models/stt/
        stt=inference.STT(model="deepgram/nova-3", language="multi"),
        # A Large Language Model (LLM) is your agent's brain, processing user input and generating a response
        # See all available models at https://docs.livekit.io/agents/models/llm/
        llm=inference.LLM(model="openai/gpt-4.1-nano"),
        # TTS Cartesia Sonic-3 50$/1M chars
        # 11Labs Flash v2.5 20$/1M chars 150$/1M chars 
        tts=inference.TTS(
            model="cartesia/sonic-3", voice="9626c31c-bec5-4cca-baa8-f8ba9e84c8bc"
        ),
        #tts=elevenlabs.TTS(model="eleven_flash_v2_5",
        #    voice_id="ODq5zmih8GrVes37Dizd"
        #)
        # VAD and turn detection are used to determine when the user is speaking and when the agent should respond
        # MultilingualModel() automatically detects language for proper speaker detection across languages
        # See more at https://docs.livekit.io/agents/build/turns
        turn_detection=MultilingualModel(),
        vad=ctx.proc.userdata["vad"],
        # allow the LLM to generate a response while waiting for the end of turn
        # See more at https://docs.livekit.io/agents/build/audio/#preemptive-generation
        preemptive_generation=True,
    )

    # To use a realtime model instead of a voice pipeline, use the following session setup instead.
    # (Note: This is for the OpenAI Realtime API. For other providers, see https://docs.livekit.io/agents/models/realtime/))
    # 1. Install livekit-agents[openai]
    # 2. Set OPENAI_API_KEY in .env.local
    # 3. Add `from livekit.plugins import openai` to the top of this file
    # 4. Use the following session setup instead of the version above
    # session = AgentSession(
    #     llm=openai.realtime.RealtimeModel(voice="marin")
    # )

    # # Add a virtual avatar to the session, if desired
    # # For other providers, see https://docs.livekit.io/agents/models/avatar/
    # avatar = hedra.AvatarSession(
    #   avatar_id="...",  # See https://docs.livekit.io/agents/models/avatar/plugins/hedra
    # )
    # # Start the avatar and wait for it to join
    # await avatar.start(session, room=ctx.room)

    #providers = ["tavus", "simli", "bey"]
    provider ="bey"
    
    match provider:
        case "tavus":  # Set to True to enable Tavus avatar
            avatar = tavus.AvatarSession(
                replica_id="r9d30b0e55ac",  # ID of the Tavus replica to use
                persona_id="p9cb09c3c7bc",  # ID of the Tavus persona to use (see preceding section for configuration details)
            )
        case "simli":
            avatar = simli.AvatarSession(
                simli_config=simli.SimliConfig(
                    api_key=os.getenv("SIMLI_API_KEY"),
                    face_id="cace3ef7-a4c4-425d-a8cf-a5358eb0c427",
                ),
            )
        case "bey":
            avatar = bey.AvatarSession(
                avatar_id="694c83e2-8895-4a98-bd16-56332ca3f449",
            )
        case _:
            avatar = None

    if avatar is not None and not is_console_mode:
        # Start the avatar and wait for it to join if not in console mode
        await avatar.start(session, room=ctx.room)

    # Start your agent session with the user
    await session.start(
        room=ctx.room,
        agent=Assistant()
    )

    # Start the session, which initializes the voice pipeline and warms up the models
    logger.info("Starting agent session with multilingual STT support...")
    stt_logger.info("Session starting - initializing transcription pipeline")
    language_logger.info("Listening for user input - will detect language automatically")

    await session.start(
        agent=Assistant(),
        room=ctx.room,
        room_options=room_io.RoomOptions(
            audio_input=room_io.AudioInputOptions(
                noise_cancellation=lambda params: noise_cancellation.BVCTelephony()
                if params.participant.kind == rtc.ParticipantKind.PARTICIPANT_KIND_SIP
                else noise_cancellation.BVC(),
            ),
        ),
    )

    # Join the room and connect to the user
    logger.info(f"✓ Agent connected to room {ctx.room.name} - ready to listen")
    stt_logger.info("Transcription pipeline active - waiting for user speech")
    language_logger.info(
        "Language detection active - will log detected language from user's first message"
    )
    await ctx.connect()


if __name__ == "__main__":
    # Simple test: verify agent initialization
    try:
        logger.info("Initializing Assistant...")
        assistant = Assistant()
        logger.info("✓ Assistant initialized successfully")
        logger.info("✓ Agent is ready to serve")
    except Exception as e:
        logger.error(f"✗ Failed to initialize Assistant: {e}")

    # Start the Flask API server on port 8019
    # This serves the /api/connection-details endpoint for the React frontend
    try:
        config = get_config()
        api_thread = run_web_server(
            host="0.0.0.0",
            port=8019,
            livekit_api_key=config.get_livekit_api_key(),
            livekit_api_secret=config.get_livekit_api_secret(),
            livekit_url=config.get_livekit_url(),
            static_files_path=None,
            debug=False,
        )
        logger.info("✓ API server started on http://0.0.0.0:8019")
    except Exception as e:
        logger.warning(f"API server initialization failed (agent will still run): {e}")

    # Start the React frontend server on port 3000
    # Run Next.js in production mode (from the web directory)
    import subprocess
    import time
    from pathlib import Path

    try:
        web_dir = Path(__file__).parent.parent / "web"
        if (web_dir / ".next").exists():
            logger.info("Starting Next.js production server on port 3000...")
            next_process = subprocess.Popen(
                ["pnpm", "start"],
                cwd=str(web_dir),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            time.sleep(3)  # Give Next.js time to start
            logger.info("✓ Next.js server started on http://0.0.0.0:3000")
        else:
            logger.warning(
                "Next.js build output not found. To build the frontend, run: cd web && pnpm build"
            )
    except Exception as e:
        logger.warning(f"Failed to start Next.js server: {e}")

    # Run the LiveKit agent server
    cli.run_app(server)
