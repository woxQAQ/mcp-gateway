/**
 * Generated by orval v7.10.0 🍺
 * Do not edit manually.
 * API Server
 * OpenAPI spec version: 0.1.0
 */
import type { LoginPassword } from "./LoginPassword";
import type { LoginUsername } from "./LoginUsername";

export interface Login {
  /** The password of the user */
  password?: LoginPassword;
  /** The username of the user */
  username?: LoginUsername;
}
