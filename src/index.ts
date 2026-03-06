import { defineAgent, cli, voice, inference, ServerOptions, type JobContext, type JobProcess } from '@livekit/agents';

// Normalize LOG_LEVEL to lowercase (CLI only accepts trace/debug/info/warn/error/fatal)
if (process.env['LOG_LEVEL']) {
  process.env['LOG_LEVEL'] = process.env['LOG_LEVEL'].toLowerCase();
}
import * as silero from '@livekit/agents-plugin-silero';
import * as livekitPlugin from '@livekit/agents-plugin-livekit';
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
    await ctx.connect();

    const vad = ctx.proc.userData['vad'] as silero.VAD;
    const mcpClient = await getMcpClient();
    const roomManager = getRoomManager();

    const session = new voice.AgentSession({
      vad,
      stt: new inference.STT({ model: 'deepgram/nova-3', language: 'multi' }),
      llm: new inference.LLM({ model: 'openai/gpt-4.1-nano' }),
      tts: new inference.TTS({ model: 'cartesia/sonic-3', voice: '9626c31c-bec5-4cca-baa8-f8ba9e84c8bc' }),
      turnDetection: new livekitPlugin.turnDetector.MultilingualModel(),
    });

    await session.start({
      agent: new Assistant(mcpClient, roomManager),
      room: ctx.room,
    });
  },
});

// Only start web server and CLI in the main process (not in forked job subprocesses)
if (process.argv[1] === fileURLToPath(import.meta.url)) {
  startWebServer({ port: 8019 });
  cli.runApp(new ServerOptions({ agent: fileURLToPath(import.meta.url) }));
}
