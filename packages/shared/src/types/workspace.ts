import type { WorkspaceId, UserId } from "./ids.js";
import type { WorkspaceRole } from "./enums.js";

export interface WorkspaceMember {
  readonly userId: UserId;
  readonly role: WorkspaceRole;
  readonly joinedAt: string;
}

export interface Workspace {
  readonly id: WorkspaceId;
  readonly slug: string;
  readonly name: string;
  readonly description: string | null;
  readonly ownerId: UserId;
  readonly members: readonly WorkspaceMember[];
  readonly isPrivate: boolean;
  readonly createdAt: string;
  readonly updatedAt: string;
}
