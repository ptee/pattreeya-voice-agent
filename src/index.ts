import { defineAgent, cli, voice, ServerOptions, type JobContext, type JobProcess } from '@livekit/agents';

// Normalize LOG_LEVEL to lowercase (CLI only accepts trace/debug/info/warn/error/fatal)
if (process.env['LOG_LEVEL']) {
  process.env['LOG_LEVEL'] = process.env['LOG_LEVEL'].toLowerCase();
}
import * as silero from '@livekit/agents-plugin-silero';
import * as livekitPlugin from '@livekit/agents-plugin-livekit';
import * as deepgramPlugin from '@livekit/agents-plugin-deepgram';
import * as openaiPlugin from '@livekit/agents-plugin-openai';
import * as cartesiaPlugin from '@livekit/agents-plugin-cartesia';
import { fileURLToPath } from 'node:url';
import { Assistant } from './agent.js';
import { getMcpClient } from './mcp_client.js';
import { getRoomManager } from './room_manager.js';
import { startWebServer } from './web_server.js';

export default defineAgent({
  prewarm: async (proc: JobProcess) => {
    proc.userData['vad'] = await silero.VAD.load();
  },

  entry: async (ctx: JobContext) => {
    // ── Step 1: Connect ───────────────────────────────────────────────────────
    try {
      await ctx.connect();
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : String(e);
      if (msg.includes('handshake') || msg.includes('Handshake') || msg.includes('status=400')) {
        console.error('[INIT] WSServerHandshakeError: ctx.connect() failed — check LIVEKIT_URL, LIVEKIT_API_KEY, LIVEKIT_API_SECRET', e);
      } else {
        console.error('[INIT] ctx.connect() failed:', e);
      }
      throw e;
    }
    console.info(`[AGENT] >>> [1] Connected to room: ${ctx.room.name}`);

    // ── Room-level event hooks ─────────────────────────────────────────────
    ctx.room.on('reconnecting', () => console.warn('[ROOM] Reconnecting to LiveKit...'));
    ctx.room.on('reconnected', () => console.info('[ROOM] Reconnected successfully'));
    ctx.room.on('connectionStateChanged', (state: string) =>
      console.info(`[ROOM] connectionStateChanged: ${state}`),
    );
    ctx.room.on('participantConnected', (p: { identity: string; kind: number }) =>
      console.info(`[ROOM] participantConnected: identity=${p.identity}, kind=${p.kind}`),
    );
    ctx.room.on('participantDisconnected', (p: { identity: string }) =>
      console.info(`[ROOM] participantDisconnected: identity=${p.identity}`),
    );
    ctx.room.on(
      'trackSubscribed',
      (track: { kind: string; sid: string }, _pub: unknown, p: { identity: string }) =>
        console.info(`[ROOM] trackSubscribed: kind=${track.kind}, sid=${track.sid}, from=${p.identity}`),
    );
    ctx.room.on('trackUnsubscribed', (track: { kind: string }, _pub: unknown, p: { identity: string }) =>
      console.info(`[ROOM] trackUnsubscribed: kind=${track.kind}, from=${p.identity}`),
    );
    ctx.room.on('activeSpeakersChanged', (speakers: Array<{ identity: string }>) =>
      console.info(
        `[ROOM] activeSpeakersChanged: [${speakers.map((s) => s.identity).join(', ') || 'none'}]`,
      ),
    );

    // ── Step 2: MCP client — fire in background so session.start() is never delayed ─
    const mcpRef: { client: Awaited<ReturnType<typeof getMcpClient>> | null } = { client: null };
    getMcpClient()
      .then((c) => {
        mcpRef.client = c;
        console.info(`[AGENT] >>> [5a] MCP client ready, cvId: ${c.cvId}`);
      })
      .catch((e: unknown) => {
        const msg = e instanceof Error ? e.message : String(e);
        if (msg.includes('handshake') || msg.includes('status=400')) {
          console.error('[INIT] WSServerHandshakeError: MCP client connection failed — check DB credentials', e);
        } else {
          console.error('[INIT] MCP client init failed (non-fatal):', e);
        }
      });
    console.info('[AGENT] >>> [5a] MCP init started in background');

    const roomManager = getRoomManager();
    console.info('[AGENT] >>> [5b] Room manager ready');

    // ── Step 3: Create session ────────────────────────────────────────────────
    console.info('[AGENT] >>> [2] Creating AgentSession...');
    const vad = ctx.proc.userData['vad'] as silero.VAD;
    const session = new voice.AgentSession({
      vad,
      stt: new deepgramPlugin.STT({ model: 'nova-3' }),
      llm: new openaiPlugin.LLM({ model: 'gpt-4.1-nano' }),
      tts: new cartesiaPlugin.TTS({ model: 'sonic-3', voice: '9626c31c-bec5-4cca-baa8-f8ba9e84c8bc' }),
      turnDetection: new livekitPlugin.turnDetector.MultilingualModel(),
    });

    // ── Session-level event hooks (must be registered before session.start()) ─
    session.on('agent_state_changed', (e: { oldState: string; newState: string }) =>
      console.info(`[SESSION] agentState: ${e.oldState} → ${e.newState}`),
    );
    session.on('user_state_changed', (e: { oldState: string; newState: string }) =>
      console.info(`[SESSION] userState: ${e.oldState} → ${e.newState}`),
    );
    session.on(
      'user_input_transcribed',
      (e: { transcript: string; isFinal: boolean; language: string | null }) =>
        console.info(
          `[SESSION] userTranscript [final=${e.isFinal}, lang=${e.language ?? 'unknown'}]: "${e.transcript}"`,
        ),
    );
    session.on(
      'speech_created',
      (e: { userInitiated: boolean; source: string }) =>
        console.info(`[SESSION] speechCreated: source=${e.source}, userInitiated=${e.userInitiated}`),
    );
    session.on(
      'function_tools_executed',
      (e: { functionCalls: Array<{ name: string; arguments: string }> }) => {
        const names = e.functionCalls.map((c) => c.name).join(', ');
        console.info(`[SESSION] toolsExecuted: [${names}]`);
      },
    );
    session.on('conversation_item_added', (e: { item: { type: string; role?: string } }) =>
      console.info(`[SESSION] conversationItemAdded: type=${e.item.type}, role=${e.item.role ?? '-'}`),
    );
    session.on('error', (e: { error: unknown; source: string }) =>
      console.error(`[SESSION] error from ${e.source}:`, e.error),
    );
    session.on('close', (e: { reason: string; error: unknown }) =>
      console.info(`[SESSION] closed: reason=${e.reason}`, e.error ?? ''),
    );

    // Log participants already in the room before session.start()
    const existing = [...ctx.room.remoteParticipants.values()];
    console.info(
      `[AGENT] >>> [8] Pre-start participants: [${existing.map((p) => p.identity).join(', ') || 'none'}]`,
    );

    // ── Step 4: Start session ─────────────────────────────────────────────────
    console.info('[AGENT] >>> [9] Starting session.start()...');
    try {
      await session.start({
        agent: new Assistant(mcpRef, roomManager),
        room: ctx.room,
      });
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : String(e);
      const name = e instanceof Error ? e.constructor.name : '';
      if (msg.includes('handshake') || msg.includes('status=400')) {
        console.error('[INIT] WSServerHandshakeError: session.start() failed — check DEEPGRAM_API_KEY/CARTESIA_API_KEY:', e);
      } else if (msg.toLowerCase().includes('timeout') || name.includes('TimeoutError')) {
        console.error('[INIT] Running init timeout: session.start() timed out:', e);
      } else {
        console.error('[INIT] session.start() failed:', e);
      }
      throw e;
    }

    // Log the room state immediately after session.start() resolves
    const postParticipants = [...ctx.room.remoteParticipants.values()];
    console.info(`[AGENT] >>> [10] session.start() resolved — agentState=${(session as any)._agentState ?? 'unknown'}`);
    console.info(
      `[AGENT] >>> [10] Remote participants now: [${postParticipants.map((p) => p.identity).join(', ') || 'none'}]`,
    );
    console.info(`[AGENT] Agent ready to listen in room: ${ctx.room.name}`);

    // ── Step 5: Greet the user by name ────────────────────────────────────────
    // Wait briefly for the human participant if they haven't appeared yet
    let participants = [...ctx.room.remoteParticipants.values()];
    if (participants.length === 0) {
      await new Promise<void>((resolve) => {
        const t = setTimeout(resolve, 3000);
        ctx.room.once('participantConnected', () => { clearTimeout(t); resolve(); });
      });
      participants = [...ctx.room.remoteParticipants.values()];
    }
    // Use .name (set from JWT); never fall back to the identity which is a random ID
    const userName = participants[0]?.name?.trim() || 'there';
    console.info(`[AGENT] >>> [11] Greeting user: "${userName}" (identity=${participants[0]?.identity ?? 'none'})`);
    try {
      await session.say(
        `Hello ${userName}! I'm Pattreeya's assistant, here to help you learn about her career, education, skills, and achievements. Und bei weiteren Fragen zu ihrem Profil stehe ich Ihnen gern zur Verfügung.`,
        { allowInterruptions: true, addToChatCtx: true }
      );
      console.info('[AGENT] >>> [11] Greeting delivered');
    } catch (e) {
      console.warn('[AGENT] >>> [11] Greeting failed (non-fatal):', e);
    }
  },
});

// Only start web server and CLI in the main process (not in forked job subprocesses)
if (process.argv[1] === fileURLToPath(import.meta.url)) {
  startWebServer({ port: 8019 });
  cli.runApp(new ServerOptions({ agent: fileURLToPath(import.meta.url) }));
}
