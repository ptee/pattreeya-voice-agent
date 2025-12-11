import logging
import os
import asyncio
from typing import Optional
from pathlib import Path
from dotenv import load_dotenv
from livekit import rtc
from livekit.agents import (
    Agent,
    AgentSession,
    JobContext,
    JobProcess,
    cli,
    inference,
    room_io,
    function_tool,
    RunContext,
)
from livekit.plugins import (
    noise_cancellation, 
    silero, 
)
from livekit.plugins.turn_detector.multilingual import MultilingualModel

from config import get_config
from mcp_client import get_mcp_client
from prompts import SYSTEM_PROMPT
from room_manager import get_room_manager
from web_server import run_web_server

logger = logging.getLogger("agent")
stt_logger = logging.getLogger("stt")
language_logger = logging.getLogger("language_detection")

load_dotenv()

ROOT = Path(__file__).resolve().parents[2]


class Assistant(Agent):
    def __init__(self, mcp_client=None, room_manager=None) -> None:
        if mcp_client is not None:
            self._mcp_client = mcp_client
        else:
            try:
                self._mcp_client = get_mcp_client()
            except Exception as e:
                logger.warning(f"Failed to initialize MCP client in __init__: {e}")
                self._mcp_client = None

        if room_manager is not None:
            self._room_manager = room_manager
        else:
            try:
                self._room_manager = get_room_manager()
            except Exception as e:
                logger.warning(f"Failed to initialize room_manager in __init__: {e}")
                self._room_manager = None

        super().__init__(
            instructions=SYSTEM_PROMPT,
        )

    @property
    def mcp_client(self):
        if self._mcp_client is None:
            try:
                self._mcp_client = get_mcp_client()
            except Exception as e:
                logger.warning(f"Failed to initialize MCP client on demand: {e}")
                return None
        return self._mcp_client    

    @property
    def room_manager(self):
        if self._room_manager is None:
            try:
                self._room_manager = get_room_manager()
            except RuntimeError as e:
                if "no running event loop" in str(e):
                    logger.debug("Deferring room_manager initialization until event loop is available")
                    return None
                raise
        return self._room_manager

    async def _get_room_manager(self):
        if self._room_manager is None:
            self._room_manager = get_room_manager()
        return self._room_manager

    # =========================================================================
    # NON-BLOCKING MCP TOOL CALLS - Use asyncio.to_thread() for all sync calls
    # =========================================================================

    @function_tool
    async def get_cv_summary(self, _: RunContext) -> str:
        """Get a high-level summary of the person's CV including role, experience, and key stats."""
        try:
            # Run synchronous MCP call in a thread pool to avoid blocking
            result = await asyncio.to_thread(self._mcp_client.get_cv_summary)
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
            result = await asyncio.to_thread(
                self._mcp_client.search_company_experience, company_name
            )
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
            result = await asyncio.to_thread(
                self._mcp_client.search_technology_experience, technology
            )
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
            result = await asyncio.to_thread(
                self._mcp_client.search_education, institution, degree
            )
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
            result = await asyncio.to_thread(
                self._mcp_client.search_publications, year
            )
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
            result = await asyncio.to_thread(
                self._mcp_client.search_skills, category
            )
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
            result = await asyncio.to_thread(
                self._mcp_client.search_awards_certifications, award_type
            )
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
            result = await asyncio.to_thread(
                self._mcp_client.semantic_search, query, section, top_k
            )
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

    # =========================================================================
    # ROOM MANAGEMENT TOOLS - Already async, no changes needed
    # =========================================================================

    @function_tool
    async def create_pattreeya_room(self, _: RunContext, room_name_suffix: Optional[str] = None) -> str:
        """Create a new LiveKit room with 'pattreeya-' prefix for voice conversations."""
        try:
            rm = await self._get_room_manager()
            room_name = await rm.create_pattreeya_room(room_name_suffix=room_name_suffix)
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
        """Delete a specific pattreeya room."""
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


# =========================================================================
# SERVER SETUP - Lazy load avatar plugins to save memory
# =========================================================================

def configure_stt_logging():
    """Configure logging for STT and language detection."""
    stt_handler = logging.StreamHandler()
    stt_handler.setFormatter(
        logging.Formatter("%(asctime)s - %(name)s - STT - %(levelname)s - %(message)s")
    )
    stt_logger.addHandler(stt_handler)
    stt_logger.setLevel(logging.INFO)

    lang_handler = logging.StreamHandler()
    lang_handler.setFormatter(
        logging.Formatter("%(asctime)s - %(name)s - LANG_DETECTION - %(levelname)s - %(message)s")
    )
    language_logger.addHandler(lang_handler)
    language_logger.setLevel(logging.INFO)


from livekit.agents import AgentServer
server = AgentServer()


def prewarm(proc: JobProcess):
    """Prewarm models and configure logging."""
    proc.userdata["vad"] = silero.VAD.load()
    #proc.userdata["turn_detector"] = MultilingualModel()
    configure_stt_logging()
    stt_logger.info("STT logging configured - ready to capture transcriptions")


server.setup_fnc = prewarm


async def cleanup_avatar(avatar):
    """Safely cleanup avatar session"""
    if avatar:
        try:
            await avatar.stop()
            logger.debug("Avatar stopped")
        except Exception as e:
            logger.debug(f"Avatar cleanup error: {e}")


async def try_start_avatar(provider: str, session, room, is_console: bool):
    """Try to start avatar, return None on failure - lazy load plugins"""
    logger.debug(f">>> [8] Attempting to start avatar with provider: {provider}")

    if provider == "none" or is_console:
        return None
    
    avatar = None
    
    try:
        match provider:
            case "tavus":
                from livekit.plugins import tavus
                avatar = tavus.AvatarSession(
                    replica_id="r9d30b0e55ac",
                    persona_id="p9cb09c3c7bc",
                )
            case "simli":
                from livekit.plugins import simli
                avatar = simli.AvatarSession(
                    simli_config=simli.SimliConfig(
                        api_key=os.getenv("SIMLI_API_KEY"),
                        face_id="cace3ef7-a4c4-425d-a8cf-a5358eb0c427",
                    ),
                )
            case "bey":
                from livekit.plugins import bey
                avatar = bey.AvatarSession(
                    avatar_id="694c83e2-8895-4a98-bd16-56332ca3f449",
                )
            case "bit":
                from livekit.plugins import bithuman
                avatar = bithuman.AvatarSession(
                    model_path=os.path.join(ROOT, "assets", "min_tech_art_dir.imx")
                )
            case _:
                return None
        
        await asyncio.wait_for(avatar.start(session, room=room), timeout=5.0)
        logger.info(f"✓ Avatar started: {provider}")
        return avatar
        
    except asyncio.TimeoutError:
        logger.warning("Avatar timed out. Using voice-only.")
        return None
    except Exception as e:
        logger.warning(f"Avatar failed: {e}. Using voice-only.")
        return None    


@server.rtc_session()
async def my_agent(ctx: JobContext):
    ctx.log_context_fields = {"room": ctx.room.name}
    logger.info(f">>> [1] Agent connected to room: {ctx.room.name}")

    # Add connection monitoring
    @ctx.room.on("reconnecting")
    def on_reconnecting():
        logger.warning("[Connection] Reconnecting...")

    @ctx.room.on("reconnected")
    def on_reconnected():
        logger.debug("[Connection] Reconnected successfully ✓")

    # Initialize MCP client and room manager
    mcp_client = None
    room_manager = None

    try:
        mcp_client = get_mcp_client()
        logger.debug(">>> [5a] MCP client ready")
    except Exception as e:
        logger.warning(f"MCP client failed (will continue without): {e}")

    try:
        room_manager = get_room_manager()
        logger.debug(">>> [5b] Room manager ready")
    except Exception as e:
        logger.warning(f"Room manager failed (will continue without): {e}")

    logger.debug(">>> [2] Creating AgentSession...")
    session = AgentSession(
        stt=inference.STT(model="deepgram/nova-3", language="multi"),
        llm=inference.LLM(model="openai/gpt-4.1-nano"),
        tts=inference.TTS(
            model="cartesia/sonic-3", voice="9626c31c-bec5-4cca-baa8-f8ba9e84c8bc"
        ),
        turn_detection=MultilingualModel(),
        vad=ctx.proc.userdata["vad"],
        preemptive_generation=True,
    )

    logger.debug(">>> [7] Checking avatar provider...")
    config = get_config()

    avatar_task = asyncio.create_task(
        try_start_avatar(
            provider=config.get_avatar_provider(),
            session=session,
            room=ctx.room,
            is_console='console' in __import__('sys').argv
        )
    )

    logger.debug(">>> [9] Starting session.start()...")
    avatar = None
    try:
        await session.start(
            agent=Assistant(mcp_client=mcp_client, room_manager=room_manager),
            room=ctx.room,
            room_options=room_io.RoomOptions(
                audio_input=room_io.AudioInputOptions(
                    noise_cancellation=lambda params: noise_cancellation.BVCTelephony()
                    if params.participant.kind == rtc.ParticipantKind.PARTICIPANT_KIND_SIP
                    else noise_cancellation.BVC(),
                ),
            ),
        )
    except Exception as e:
        logger.error(f">>> [ERROR] session.start() failed: {e}")
        raise
    finally:
        logger.debug(">>> [11] Cleanup starting...")
        try:
            avatar = await asyncio.wait_for(avatar_task, timeout=5.0)
        except asyncio.TimeoutError:
            logger.warning("Avatar task timeout during cleanup, cancelling...")
            avatar_task.cancel()
            avatar = None
        except asyncio.CancelledError:
            avatar = None
        except Exception as e:
            logger.debug(f"Avatar task error during cleanup: {e}")
            avatar = None

        await cleanup_avatar(avatar)

    logger.info(f"✓ Agent connected to room {ctx.room.name} - ready to listen")


if __name__ == "__main__":
    try:
        logger.info("Initializing Assistant...")
        assistant = Assistant()
        logger.info("✓ Assistant initialized successfully")
        logger.info("✓ Agent is ready to serve")
    except Exception as e:
        logger.error(f"✗ Failed to initialize Assistant: {e}")

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
            time.sleep(3)
            logger.info("✓ Next.js server started on http://0.0.0.0:3000")
        else:
            logger.warning(
                "Next.js build output not found. To build the frontend, run: cd web && pnpm build"
            )
    except Exception as e:
        logger.warning(f"Failed to start Next.js server: {e}")

    cli.run_app(server)