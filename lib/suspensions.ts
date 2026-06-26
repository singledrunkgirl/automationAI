import "server-only";

import { api } from "@/convex/_generated/api";
import { ChatSDKError } from "@/lib/errors";
import { getConvexClient } from "@/lib/db/convex-client";
import { getSuspensionMessage } from "@/lib/suspensionMessage";
import { isLocalOnlyMode } from "@/lib/local-only";

const serviceKey = process.env.CONVEX_SERVICE_ROLE_KEY!;

export async function getActiveSuspensionForUser(userId: string) {
  // In local-only mode, there are no suspensions.
  if (isLocalOnlyMode()) return null;
  return await getConvexClient().query(api.userSuspensions.getActiveByUser, {
    serviceKey,
    userId,
  });
}

export async function assertUserCanMakeCostIncurringRequest(userId: string) {
  // In local-only mode, skip suspension check.
  if (isLocalOnlyMode()) return;
  const suspension = await getActiveSuspensionForUser(userId);
  if (!suspension) return;

  throw new ChatSDKError(
    "forbidden:chat",
    getSuspensionMessage(`${suspension.category}:${suspension.source_id}`),
    {
      suspensionCategory: suspension.category,
      suspensionSource: suspension.source,
    },
  );
}
