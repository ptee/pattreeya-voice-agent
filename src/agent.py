import logging
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
from livekit.plugins import noise_cancellation, silero
from livekit.plugins.turn_detector.multilingual import MultilingualModel

from config import get_config
from mcp_client import get_mcp_client
from prompts import SYSTEM_PROMPT
from room_manager import get_room_manager

logger = logging.getLogger("agent")

load_dotenv(".env.local")


class Assistant(Agent):
    def __init__(self, mcp_client=None, room_manager=None) -> None:
        self.mcp_client = mcp_client or get_mcp_client()
        self.room_manager = room_manager or get_room_manager()
        super().__init__(
            instructions=SYSTEM_PROMPT,
        )

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
            room_name = await self.room_manager.create_pattreeya_room(
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
            rooms = await self.room_manager.list_pattreeya_rooms()
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
            success = await self.room_manager.delete_pattreeya_room(room_name)
            if success:
                return f"Successfully deleted room: {room_name}"
            else:
                return f"Failed to delete room: {room_name}"
        except Exception as e:
            logger.error(f"Error deleting pattreeya room: {e}")
            return f"Failed to delete room: {str(e)}"


server = AgentServer()


def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()


server.setup_fnc = prewarm


@server.rtc_session()
async def my_agent(ctx: JobContext):
    # Logging setup
    # Add any other context you want in all log entries here
    ctx.log_context_fields = {
        "room": ctx.room.name,
    }

    # Set up a voice AI pipeline with multilingual support (Deepgram Nova-3, OpenAI, Cartesia, and LiveKit Multilingual Turn Detector)
    session = AgentSession(
        # Speech-to-text (STT) is your agent's ears, turning the user's speech into text that the LLM can understand
        # Deepgram Nova-3 automatically detects language from audio (supports 99+ languages)
        # See all available models at https://docs.livekit.io/agents/models/stt/
        stt=inference.STT(model="deepgram/nova-3"),
        # A Large Language Model (LLM) is your agent's brain, processing user input and generating a response
        # See all available models at https://docs.livekit.io/agents/models/llm/
        llm=inference.LLM(model="openai/gpt-4.1-mini"),
        # Text-to-speech (TTS) is your agent's voice, turning the LLM's text into speech that the user can hear
        # See all available models as well as voice selections at https://docs.livekit.io/agents/models/tts/
        tts=inference.TTS(
            model="cartesia/sonic-3", voice="9626c31c-bec5-4cca-baa8-f8ba9e84c8bc"
        ),
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

    # Start the session, which initializes the voice pipeline and warms up the models
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

    # Run the LiveKit agent server
    cli.run_app(server)
