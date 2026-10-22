"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import {
  Download,
  RotateCcw,
  Loader2,
  ListChecks,
  Image as ImageIcon,
  CheckCircle2,
  AlertTriangle,
  CircleDashed,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { ComplianceSeal } from "./compliance-seal";
import { FieldCard } from "./field-card";
import { ViolationList } from "./violation-banner";
import { deriveVerdict, type ScanResponse } from "@/lib/types";
import { downloadComplianceReport } from "@/lib/pdf-export";
import { cn, formatDateTime } from "@/lib/utils";
import { ComplianceScore } from "./compliance-score";

export function ResultsPanel({
  scan,
  previewUrl,
  onNewScan,
}: {
  scan: ScanResponse;
  previewUrl: string | null;
  onNewScan: () => void;
}) {
  const verdict = deriveVerdict(scan);
  const [exporting, setExporting] = useState(false);
  const presentCount = scan.extracted_fields.filter((f) => f.is_present).length;

  async function handleExport() {
    setExporting(true);
    try {
      await downloadComplianceReport(scan);
    } finally {
      setExporting(false);
    }
  }

  const statusInfo = {
    PASS: {
      label: "Label reading complete",
      className: "border-success/30 bg-success-surface text-accent-foreground",
      icon: CheckCircle2,
    },
    VIOLATIONS: {
      label: "Review required",
      className: "border-warning/30 bg-warning-surface text-secondary-foreground",
      icon: AlertTriangle,
    },
    MANUAL_REVIEW: {
      label: "Review required",
      className: "border-warning/30 bg-warning-surface text-secondary-foreground",
      icon: CircleDashed,
    },
  }[verdict];

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
      className="space-y-6"
    >
      <div
        className={cn(
          "glass-panel flex flex-col gap-6 p-6 sm:p-8",
          verdict === "PASS" && "border-success/30 bg-success-surface/50",
          verdict !== "PASS" && "border-warning/30 bg-warning-surface/50"
        )}
      >
        <div className="flex flex-col gap-5 lg:flex-row lg:items-center lg:justify-between">
          <div className="flex items-center gap-3">
            <ComplianceSeal verdict={verdict} />
            <div
              className={cn(
                "inline-flex items-center gap-2 rounded-full border px-3 py-2 text-xs font-medium",
                statusInfo.className
              )}
            >
              <statusInfo.icon className="h-4 w-4" />
              {statusInfo.label}
            </div>
          </div>

          <div className="flex flex-wrap items-center gap-2">
            <Badge variant="neutral">Scan ID {scan.id.slice(0, 8)}</Badge>
            <Badge variant="neutral">{formatDateTime(scan.created_at)}</Badge>
            <Badge variant={scan.status === "COMPLETED" ? "pass" : "review"}>
              {scan.status}
            </Badge>
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          <ComplianceScore
            present={presentCount}
            total={scan.extracted_fields.length}
          />
          <div className="flex items-center gap-2 text-xs text-ink-700/70 dark:text-paper-100/65">
            <span className="h-2.5 w-2.5 rounded-full bg-emerald-600" />
            Green = present
            <span className="h-2.5 w-2.5 rounded-full bg-saffron-500" />
            Amber = review
            <span className="h-2.5 w-2.5 rounded-full bg-ink-900/60 dark:bg-paper-50/60" />
            White = not applicable
            <span className="h-2.5 w-2.5 rounded-full bg-clay-600" />
            Red = issue
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-[330px_1fr]">
        <div className="glass-panel overflow-hidden">
          <div className="flex items-center gap-2 border-b border-ink-900/10 px-4 py-3 dark:border-paper-50/10">
            <ImageIcon className="h-3.5 w-3.5 text-emerald-700 dark:text-emerald-300" />
            <span className="eyebrow">Scanned label</span>
          </div>

          <div className="aspect-square w-full bg-neutral-surface">
            {previewUrl ? (
              // eslint-disable-next-line @next/next/no-img-element
              <img
                src={previewUrl}
                alt="Scanned label"
                className="h-full w-full object-contain"
              />
            ) : (
              <div className="flex h-full items-center justify-center text-ink-700/40">
                No preview available
              </div>
            )}
          </div>

          <div className="space-y-3 border-t border-border bg-card p-4 sm:p-5">
            <Button
              variant="default"
              className="w-full"
              onClick={handleExport}
              disabled={exporting}
            >
              {exporting ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Download className="h-4 w-4" />
              )}
              Download compliance report
            </Button>

            <Button
              variant="outline"
              className="w-full"
              onClick={onNewScan}
            >
              <RotateCcw className="h-4 w-4" />
              New scan
            </Button>
          </div>
        </div>

        <div className="space-y-6">
          <div className="glass-panel p-5 sm:p-6">
            <div className="mb-4 flex items-center justify-between gap-3">
              <div className="flex items-center gap-2">
                <ListChecks className="h-4 w-4 text-emerald-700 dark:text-emerald-300" />
                <h3 className="font-display text-lg font-semibold text-ink-950 dark:text-paper-50">
                  Extracted attributes
                </h3>
              </div>

              <span className="font-mono text-xs text-ink-700/70 dark:text-paper-100/60">
                {presentCount} / {scan.extracted_fields.length} present
              </span>
            </div>

            <div className="space-y-3">
              <div className="grid grid-cols-1 gap-3 xl:grid-cols-2">
                {scan.extracted_fields.map((field) => (
                  <FieldCard key={field.field_name} field={field} />
                ))}
              </div>

              {scan.extracted_fields.length === 0 && (
                <p className="text-sm text-ink-700/70 dark:text-paper-100/60">
                  No structured fields were returned for this scan.
                </p>
              )}
            </div>
          </div>

          <div className="glass-panel p-5 sm:p-6">
            <h3 className="mb-4 font-display text-lg font-semibold text-ink-950 dark:text-paper-50">
              Violations &amp; missing declarations
            </h3>
            <ViolationList violations={scan.violations} />
          </div>
        </div>
      </div>
    </motion.div>
  ); 
}
