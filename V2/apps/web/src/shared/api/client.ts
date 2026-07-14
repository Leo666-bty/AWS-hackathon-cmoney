import { z } from "zod";

const healthSchema = z.object({
  status: z.literal("ok"),
  service: z.string(),
  version: z.string(),
  model_status: z.string(),
});

export type HealthResponse = z.infer<typeof healthSchema>;

const apiBaseUrl = import.meta.env.VITE_API_BASE_URL ?? "/api/v2";

export async function getHealth(signal?: AbortSignal): Promise<HealthResponse> {
  const response = await fetch(`${apiBaseUrl}/health`, { signal });
  if (!response.ok) {
    throw new Error(`API health check failed with ${response.status}`);
  }
  return healthSchema.parse(await response.json());
}
