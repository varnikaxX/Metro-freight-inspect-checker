/**
 * Types mirror `schemas.py` in the FastAPI backend 1:1 (field names,
 * optionality, and casing) so the payload from POST /api/v1/scan can be
 * consumed without any translation layer.
 */

export type ScanStatus = "PENDING" | "PROCESSING" | "COMPLETED" | "FAILED";
export type VerificationState = "verified_present" | "not_detected_needs_review" | "needs_review" | "not_applicable" | "verified_missing" | "not_assessed";

export interface FieldDetail {
  id?: string | null;
  scan_id?: string | null;
  field_name: string;
  field_value?: string | null;
  is_present: boolean;
  created_at?: string | null;
  verification_state?: VerificationState | null;
  raw_text?: string | null;
  source_line?: string | null;
  confidence?: number | null;
  candidate_status?: string | null;
}

export interface ViolationDetail {
  id?: string | null;
  scan_id?: string | null;
  rule_code: string;
  description: string;
  created_at?: string | null;
}

export interface ScanResponse {
  id: string;
  user_id?: string | null;
  raw_image_url: string;
  pdf_report_url?: string | null;
  status: ScanStatus;
  created_at: string;
  updated_at?: string | null;
  extracted_fields: FieldDetail[];
  violations: ViolationDetail[];
  full_text?: string | null;
}

export interface ScanSummary {
  id: string;
  raw_image_url: string;
  pdf_report_url?: string | null;
  status: ScanStatus;
  created_at: string;
  violation_count: number;
  is_compliant: boolean;
}

export interface ScanListResponse {
  total: number;
  scans: ScanSummary[];
}

export interface ApiErrorResponse {
  detail: string;
}

/** Derived, UI-only classification — not present on the backend payload. */
export type ComplianceVerdict = "PASS" | "VIOLATIONS" | "MANUAL_REVIEW";

export function deriveVerdict(scan: ScanResponse): ComplianceVerdict {
  const noTextDetected = scan.violations.some(
    (v) => v.rule_code === "LMR_2011_OCR_NO_TEXT_DETECTED"
  );
  if (scan.status === "FAILED" || noTextDetected) return "MANUAL_REVIEW";
  if (scan.extracted_fields.some((field) => field.verification_state === "verified_missing")) return "VIOLATIONS";
  if (scan.extracted_fields.some((field) => field.verification_state === "not_detected_needs_review" || field.verification_state === "not_assessed")) return "MANUAL_REVIEW";
  if (!scan.extracted_fields.some((field) => field.verification_state)) return scan.violations.length ? "VIOLATIONS" : "PASS";
  return "PASS";
}
