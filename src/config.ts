import dotenv from 'dotenv';
import { ConfigurationError } from './exceptions.js';

dotenv.config({ path: '.env.local' });

export class ConfigManager {
  private static _instance: ConfigManager | null = null;

  readonly livekitUrl: string;
  readonly livekitApiKey: string;
  readonly livekitApiSecret: string;
  readonly openaiApiKey: string;
  readonly llmModel: string;
  readonly embeddingModel: string;
  readonly postgresqlUrl: string;
  readonly qdrantUrl: string;
  readonly qdrantApiKey: string;
  readonly qdrantCollection: string;
  readonly avatarProvider: string;

  private constructor() {
    this.livekitUrl = process.env.LIVEKIT_URL ?? '';
    this.livekitApiKey = process.env.LIVEKIT_API_KEY ?? '';
    this.livekitApiSecret = process.env.LIVEKIT_API_SECRET ?? '';
    this.openaiApiKey = process.env.OPENAI_API_KEY ?? '';
    this.llmModel = process.env.LLM_MODEL ?? 'openai/gpt-4.1-nano';
    this.embeddingModel = process.env.EMBEDDING_MODEL ?? 'text-embedding-3-small';
    this.postgresqlUrl = process.env.POSTGRESQL_URL ?? '';
    this.qdrantUrl = process.env.QDRANT_URL ?? '';
    this.qdrantApiKey = process.env.QDRANT_API_KEY ?? '';
    this.qdrantCollection = process.env.COLLECTION_NAME ?? 'pt_cv';
    this.avatarProvider = process.env.AVATAR_PROVIDER ?? 'none';
    this._validateConfig();
    this._warnOptional();
  }

  private _warnOptional(): void {
    const warned: Record<string, string> = {
      DEEPGRAM_API_KEY: process.env.DEEPGRAM_API_KEY ?? '',
      CARTESIA_API_KEY: process.env.CARTESIA_API_KEY ?? '',
    };
    for (const [key, val] of Object.entries(warned)) {
      if (!val) {
        console.warn(`[Config] Warning: ${key} is not set — STT/TTS may fail with WSServerHandshakeError (status=400)`);
      }
    }
  }

  private _validateConfig(): void {
    const required: Record<string, string> = {
      LIVEKIT_URL: this.livekitUrl,
      LIVEKIT_API_KEY: this.livekitApiKey,
      LIVEKIT_API_SECRET: this.livekitApiSecret,
      OPENAI_API_KEY: this.openaiApiKey,
      POSTGRESQL_URL: this.postgresqlUrl,
      QDRANT_URL: this.qdrantUrl,
      QDRANT_API_KEY: this.qdrantApiKey,
    };
    const missing = Object.entries(required)
      .filter(([, v]) => !v)
      .map(([k]) => k);
    if (missing.length > 0) {
      throw new ConfigurationError(
        `Missing required environment variables: ${missing.join(', ')}. Please set them in .env.local`,
      );
    }
  }

  getLivekitUrl(): string { return this.livekitUrl; }
  getLivekitApiKey(): string { return this.livekitApiKey; }
  getLivekitApiSecret(): string { return this.livekitApiSecret; }
  getOpenaiApiKey(): string { return this.openaiApiKey; }
  getLlmModel(): string { return this.llmModel; }
  getEmbeddingModel(): string { return this.embeddingModel; }
  getPostgresqlUrl(): string { return this.postgresqlUrl; }
  getQdrantUrl(): string { return this.qdrantUrl; }
  getQdrantApiKey(): string { return this.qdrantApiKey; }
  getQdrantCollection(): string { return this.qdrantCollection; }
  getAvatarProvider(): string { return this.avatarProvider; }

  static getInstance(): ConfigManager {
    if (!ConfigManager._instance) {
      ConfigManager._instance = new ConfigManager();
    }
    return ConfigManager._instance;
  }

  static resetInstance(): void {
    ConfigManager._instance = null;
  }
}

export function getConfig(): ConfigManager {
  return ConfigManager.getInstance();
}
