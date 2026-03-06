import pg from 'pg';
import { QdrantClient } from '@qdrant/js-client-rest';
import type { ConfigManager } from './config.js';
import { getConfig } from './config.js';
import {
  PostgreSQLConnectionError,
  QdrantConnectionError,
  DatabaseQueryError,
} from './exceptions.js';

// ============================================================================
// POSTGRESQL DATABASE MANAGER
// ============================================================================

export class PostgreSQLManager {
  private pool: pg.Pool;

  constructor(config?: ConfigManager) {
    const cfg = config ?? getConfig();
    this.pool = new pg.Pool({ connectionString: cfg.getPostgresqlUrl() });
  }

  async fetchOne(query: string, params?: unknown[]): Promise<Record<string, unknown> | null> {
    try {
      const result = await this.pool.query(query, params);
      return result.rows[0] ?? null;
    } catch (err) {
      throw new DatabaseQueryError(`SQL query failed: ${err}`);
    }
  }

  async fetchAll(query: string, params?: unknown[]): Promise<Record<string, unknown>[]> {
    try {
      const result = await this.pool.query(query, params);
      return result.rows;
    } catch (err) {
      throw new DatabaseQueryError(`SQL query failed: ${err}`);
    }
  }

  async execute(query: string, params?: unknown[]): Promise<number> {
    try {
      const result = await this.pool.query(query, params);
      return result.rowCount ?? 0;
    } catch (err) {
      throw new DatabaseQueryError(`SQL query failed: ${err}`);
    }
  }

  async close(): Promise<void> {
    await this.pool.end();
  }
}

// ============================================================================
// QDRANT VECTOR DATABASE MANAGER
// ============================================================================

export class QdrantManager {
  readonly client: QdrantClient;

  constructor(config?: ConfigManager) {
    const cfg = config ?? getConfig();
    try {
      // Skip SSL cert verification for self-signed certs
      process.env['NODE_TLS_REJECT_UNAUTHORIZED'] = '0';
      this.client = new QdrantClient({
        url: cfg.getQdrantUrl(),
        apiKey: cfg.getQdrantApiKey(),
      });
    } catch (err) {
      throw new QdrantConnectionError(`Failed to connect to Qdrant: ${err}`);
    }
  }
}

// ============================================================================
// SINGLETON FACTORIES
// ============================================================================

let _pgManager: PostgreSQLManager | null = null;
let _qdrantManager: QdrantManager | null = null;

export function getPostgresManager(config?: ConfigManager): PostgreSQLManager {
  if (!_pgManager) {
    _pgManager = new PostgreSQLManager(config);
  }
  return _pgManager;
}

export function getQdrantManager(config?: ConfigManager): QdrantManager {
  if (!_qdrantManager) {
    _qdrantManager = new QdrantManager(config);
  }
  return _qdrantManager;
}
