/**
 * Generated by orval v7.10.0 🍺
 * Do not edit manually.
 * API Server
 * OpenAPI spec version: 0.1.0
 */
import type { Policy } from "./Policy";
import type { McpServerType } from "./McpServerType";

export interface McpServer {
  args: string[];
  command: string;
  description: string;
  name: string;
  policy: Policy;
  preinstalled: boolean;
  type: McpServerType;
  url: string;
}
