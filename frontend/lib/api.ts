import axios, { AxiosError } from "axios";
import type { ApiErrorResponse, ScanListResponse, ScanResponse } from "./types";

export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000";

const client = axios.create({
  baseURL: `${API_BASE_URL}/api/v1`,
  timeout: 180_000,
  validateStatus: (status) => status >= 200 && status < 300,
});

export class ScanApiError extends Error {
  status?: number;
  kind: "network" | "http" | "malformed" | "unknown";
  constructor(message: string, status?: number, kind: ScanApiError["kind"] = "unknown") {
    super(message);
    this.name = "ScanApiError";
    this.status = status;
    this.kind = kind;
  }
}

function toApiError(err: unknown): ScanApiError {
  const axiosErr = err as AxiosError<ApiErrorResponse>;
  if (axiosErr?.response) {
    const body = axiosErr.response.data;
    const detail = typeof body === "string" ? body : body?.detail;
    return new ScanApiError(
      detail || `Compliance backend returned HTTP ${axiosErr.response.status}.`,
      axiosErr.response.status,
      "http"
    );
  }
  if (axiosErr?.request) {
    return new ScanApiError(
      "Could not reach the compliance backend. Confirm it is running at " +
        API_BASE_URL,
      undefined,
      "network"
    );
  }
  return new ScanApiError((err as Error)?.message ?? "Unknown error", undefined, "unknown");
}

function isScanResponse(value: unknown): value is ScanResponse {
  if (!value || typeof value !== "object") return false;
  const scan = value as Partial<ScanResponse>;
  return (
    typeof scan.id === "string" &&
    typeof scan.raw_image_url === "string" &&
    typeof scan.status === "string" &&
    typeof scan.created_at === "string" &&
    Array.isArray(scan.extracted_fields) &&
    Array.isArray(scan.violations) &&
    scan.extracted_fields.every(
      (field) =>
        field &&
        typeof field.field_name === "string" &&
        typeof field.is_present === "boolean"
    ) &&
    scan.violations.every(
      (violation) =>
        violation &&
        typeof violation.rule_code === "string" &&
        typeof violation.description === "string"
    )
  );
}

function scanResponseShape(value: unknown) {
  if (!value || typeof value !== "object") return { type: typeof value };
  const scan = value as Record<string, unknown>;
  return {
    type: "object",
    keys: Object.keys(scan),
    extractedFields: Array.isArray(scan.extracted_fields) ? scan.extracted_fields.length : "not-array",
    violations: Array.isArray(scan.violations) ? scan.violations.length : "not-array",
    statusType: typeof scan.status,
    createdAtType: typeof scan.created_at,
  };
}

/**
 * POST /api/v1/scan — multipart/form-data upload of the label image.
 * Field name must be `file` to match FastAPI's `UploadFile = File(...)`.
 */
export async function scanLabel(
  file: File,
  opts?: { userId?: string; onProgress?: (pct: number) => void; signal?: AbortSignal }
): Promise<ScanResponse> {
  const form = new FormData();
  form.append("file", file, file.name);

  try {
    const response = await client.post<string>("/scan", form, {
      params: opts?.userId ? { user_id: opts.userId } : undefined,
      signal: opts?.signal,
      // Parse once below so malformed successful bodies get a distinct error.
      responseType: "text",
      onUploadProgress: (evt) => {
        if (opts?.onProgress && evt.total) {
          opts.onProgress(Math.round((evt.loaded / evt.total) * 100));
        }
      },
    });
    if (process.env.NODE_ENV === "development") {
      console.debug("[scan] response", {
        status: response.status,
        contentType: response.headers["content-type"],
      });
    }

    let parsed: unknown;
    try {
      parsed = JSON.parse(response.data);
    } catch {
      throw new ScanApiError(
        "Scan completed but result could not be displayed.",
        response.status,
        "malformed"
      );
    }

    if (process.env.NODE_ENV === "development") {
      console.debug("[scan] parsed response shape", scanResponseShape(parsed));
    }
    if (!isScanResponse(parsed)) {
      throw new ScanApiError(
        "Scan completed but result could not be displayed.",
        response.status,
        "malformed"
      );
    }
    return parsed;
  } catch (err) {
    if (err instanceof ScanApiError) throw err;
    throw toApiError(err);
  }
}

export async function fetchScanHistory(
  limit = 50,
  offset = 0
): Promise<ScanListResponse> {
  try {
    const { data } = await client.get<ScanListResponse>("/scans", {
      params: { limit, offset },
    });
    return data;
  } catch (err) {
    throw toApiError(err);
  }
}

export async function fetchScanById(scanId: string): Promise<ScanResponse> {
  try {
    const { data } = await client.get<ScanResponse>(`/scans/${scanId}`);
    return data;
  } catch (err) {
    throw toApiError(err);
  }
}

export async function deleteAccount(accessToken: string): Promise<void> {
  try {
    await client.delete("/account", {
      headers: { Authorization: `Bearer ${accessToken}` },
    });
  } catch (err) {
    throw toApiError(err);
  }
}
