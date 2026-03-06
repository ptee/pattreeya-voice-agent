// Custom exceptions for CV Voice Agent

export class CVAgentException extends Error {
  constructor(message: string) {
    super(message);
    this.name = this.constructor.name;
  }
}

// Configuration exceptions
export class ConfigurationError extends CVAgentException {}
export class ConfigurationMissingError extends ConfigurationError {}
export class ConfigurationInvalidError extends ConfigurationError {}
export class StreamlitSecretsError extends ConfigurationError {}
export class EnvVarError extends ConfigurationError {}

// Database connection exceptions
export class DatabaseConnectionError extends CVAgentException {}
export class PostgreSQLConnectionError extends DatabaseConnectionError {}
export class QdrantConnectionError extends DatabaseConnectionError {}
export class DatabaseOperationError extends CVAgentException {}
export class DatabaseQueryError extends DatabaseOperationError {}
export class DatabaseInsertError extends DatabaseOperationError {}
export class DatabaseTableError extends DatabaseOperationError {}

// Data validation exceptions
export class DataValidationError extends CVAgentException {}
export class InvalidUUIDError extends DataValidationError {}
export class CVNotFoundError extends DataValidationError {}
export class InvalidDataFormatError extends DataValidationError {}

// Embedding and vector DB exceptions
export class EmbeddingError extends CVAgentException {}
export class VectorStoreError extends CVAgentException {}
export class VectorSearchError extends VectorStoreError {}

// LLM agent exceptions
export class LLMAgentError extends CVAgentException {}
export class ToolCallingError extends LLMAgentError {}
export class LLMResponseError extends LLMAgentError {}
export class NoToolsCalledError extends ToolCallingError {}

// MCP exceptions
export class MCPError extends CVAgentException {}
export class MCPClientError extends MCPError {}
export class MCPServerError extends MCPError {}
export class MCPToolError extends MCPError {}

// Error context helper
export class ErrorContext {
  constructor(
    public readonly errorType: string,
    public readonly message: string,
    public readonly suggestions: string[] = [],
    public readonly remediationSteps: string[] = [],
  ) {}

  format(): string {
    const lines = [
      `\n${'='.repeat(70)}`,
      `ERROR: ${this.errorType.toUpperCase()}`,
      '='.repeat(70),
      `\nMessage: ${this.message}\n`,
    ];
    if (this.suggestions.length > 0) {
      lines.push('Suggestions:');
      for (const s of this.suggestions) lines.push(`  - ${s}`);
    }
    if (this.remediationSteps.length > 0) {
      lines.push('\nRemediation Steps:');
      this.remediationSteps.forEach((s, i) => lines.push(`  ${i + 1}. ${s}`));
    }
    lines.push(`\n${'='.repeat(70)}\n`);
    return lines.join('\n');
  }
}

export function createContextualError(
  ExceptionClass: new (msg: string) => CVAgentException,
  ctx: ErrorContext,
): CVAgentException {
  return new ExceptionClass(ctx.format());
}
