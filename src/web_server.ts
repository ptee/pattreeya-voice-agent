import express from 'express';
import cors from 'cors';
import { SignJWT } from 'jose';
import { getConfig } from './config.js';

export function startWebServer({ port = 8019 }: { port?: number } = {}): void {
  const app = express();
  app.use(cors({ origin: '*' }));
  app.use(express.json());

  app.post('/api/connection-details', async (_req, res) => {
    try {
      const config = getConfig();
      const roomName = `voice_assistant_room_${crypto.randomUUID().slice(0, 4)}`;
      const participantIdentity = `voice_assistant_user_${crypto.randomUUID().slice(0, 4)}`;
      const participantName = 'user';

      const now = Math.floor(Date.now() / 1000);
      const ttl = 15 * 60;

      const payload = {
        iss: config.getLivekitApiKey(),
        sub: participantIdentity,
        name: participantName,
        iat: now,
        exp: now + ttl,
        nbf: now,
        video: {
          canPublish: true,
          canPublishData: true,
          canSubscribe: true,
          room: roomName,
          roomJoin: true,
        },
      };

      const secret = new TextEncoder().encode(config.getLivekitApiSecret());
      const participantToken = await new SignJWT(payload as unknown as Record<string, unknown>)
        .setProtectedHeader({ alg: 'HS256' })
        .sign(secret);

      res.json({
        serverUrl: config.getLivekitUrl(),
        roomName,
        participantToken,
        participantName,
      });
    } catch (e) {
      console.error('Error generating connection details:', e);
      res.status(500).json({ error: String(e) });
    }
  });

  app.get('/health', (_req, res) => {
    res.json({ status: 'ok' });
  });

  app.listen(port, () => {
    console.log(`Web server listening on port ${port}`);
  });
}
