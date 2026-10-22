"use client";

import { useCallback, useRef, useState } from "react";
import { motion } from "framer-motion";
import {
  UploadCloud,
  Camera,
  ImageIcon,
  X,
  ScanSearch,
  AlertCircle,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { ScanningOverlay } from "./scanning-overlay";
import { CameraCapture } from "./camera-capture";
import { cn } from "@/lib/utils";
import { InfoTooltip } from "@/components/ui/info-tooltip";

const ACCEPTED_TYPES = [
  "image/jpeg",
  "image/png",
  "image/jpg",
  "image/webp",
];

const MAX_SIZE_BYTES = 10 * 1024 * 1024;

interface UploadPanelProps {
  onSubmit: (file: File) => void;
  isScanning: boolean;
  scanStep: number;
  errorMessage?: string | null;
}

export function UploadPanel({
  onSubmit,
  isScanning,
  scanStep,
  errorMessage,
}: UploadPanelProps) {
  const [file, setFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [validationError, setValidationError] = useState<string | null>(null);
  const [cameraOpen, setCameraOpen] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const acceptFile = useCallback((candidate: File) => {
    setValidationError(null);

    if (!ACCEPTED_TYPES.includes(candidate.type)) {
      setValidationError(
        "Unsupported file type. Upload a JPG, PNG, or WEBP image."
      );
      return;
    }

    if (candidate.size > MAX_SIZE_BYTES) {
      setValidationError(
        "File too large — the backend accepts images up to 10 MB."
      );
      return;
    }

    setFile(candidate);
    setPreviewUrl(URL.createObjectURL(candidate));
  }, []);

  function handleDrop(e: React.DragEvent<HTMLDivElement>) {
    e.preventDefault();
    setIsDragging(false);

    const dropped = e.dataTransfer.files?.[0];
    if (dropped) acceptFile(dropped);
  }

  function handleReset() {
    setFile(null);
    setPreviewUrl(null);
    setValidationError(null);

    if (inputRef.current) {
      inputRef.current.value = "";
    }
  }

  return (
    <div className="space-y-4">
      <div
        onDragOver={(e) => {
          e.preventDefault();
          setIsDragging(true);
        }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={handleDrop}
        className={cn(
          "glass-panel relative overflow-hidden transition-all duration-300",
          isDragging && "border-primary bg-success-surface shadow-card-hover"
        )}
      >
        {!previewUrl ? (
          <div className="relative overflow-hidden px-6 py-16 text-center sm:px-10 sm:py-20">
            <div
              aria-hidden="true"
              className="pointer-events-none absolute inset-0 bg-inspection-grid bg-[size:28px_28px] opacity-35 dark:opacity-20"
            />

            <div
              aria-hidden="true"
              className="pointer-events-none absolute inset-4 rounded-[1.4rem] border border-border"
            />

            <div
              aria-hidden="true"
              className="pointer-events-none absolute inset-0"
            >
              {[
                "top-6 left-6 border-t-2 border-l-2",
                "top-6 right-6 border-t-2 border-r-2",
                "bottom-6 left-6 border-b-2 border-l-2",
                "bottom-6 right-6 border-b-2 border-r-2",
              ].map((pos, index) => (
                <div
                  key={index}
                  className={cn(
                    "absolute h-10 w-10 rounded-[0.5rem] border-emerald-600/60 dark:border-emerald-300/60",
                    pos
                  )}
                />
              ))}
            </div>

            <div className="relative z-10 flex flex-col items-center justify-center gap-4">
              <motion.div
                animate={isDragging ? { scale: 1.08 } : { scale: 1 }}
                className="flex h-16 w-16 items-center justify-center rounded-[1.2rem] border border-emerald-600/20 bg-emerald-50 text-emerald-700 shadow-sm dark:border-emerald-300/20 dark:bg-emerald-500/10 dark:text-emerald-300"
              >
                <UploadCloud className="h-7 w-7" />
              </motion.div>

              <div>
                <p className="font-display text-2xl font-semibold tracking-tight text-card-foreground">
                  Drop a label here
                </p>

                <p className="mt-2 text-sm text-muted-foreground">
                  JPG, PNG, or camera capture
                </p>
              </div>

              <div className="mt-2 flex flex-wrap items-center justify-center gap-3">
                <Button
                  size="lg"
                  variant="default"
                  onClick={() => inputRef.current?.click()}
                >
                  <ImageIcon className="h-4 w-4" />
                  Choose photo
                </Button>

                <Button
                  size="lg"
                  variant="outline"
                  onClick={() => setCameraOpen(true)}
                >
                  <Camera className="h-4 w-4" />
                  Use camera
                </Button>
              </div>
            </div>

            <input
              ref={inputRef}
              type="file"
              accept={ACCEPTED_TYPES.join(",")}
              className="hidden"
              onChange={(e) => {
                const picked = e.target.files?.[0];
                if (picked) acceptFile(picked);
              }}
            />
          </div>
        ) : (
          <div className="relative">
            <div className="relative aspect-[4/3] w-full overflow-hidden bg-neutral-surface sm:aspect-video">
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img
                src={previewUrl}
                alt="Selected label preview"
                className="h-full w-full object-contain"
              />

              {isScanning && <ScanningOverlay step={scanStep} />}
            </div>

            {!isScanning && (
              <button
                onClick={handleReset}
                className="absolute right-3 top-3 flex h-9 w-9 items-center justify-center rounded-full bg-ink-950/80 text-paper-100/80 backdrop-blur hover:bg-ink-950/90 hover:text-paper-50"
                aria-label="Remove image"
              >
                <X className="h-4 w-4" />
              </button>
            )}
          </div>
        )}
      </div>

      {(validationError || errorMessage) && (
        <div className="flex items-start gap-2.5 rounded-xl border border-clay-500/30 bg-clay-50 px-4 py-3 text-sm text-clay-600 dark:border-clay-500/50 dark:bg-clay-500/10 dark:text-clay-500">
          <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" />
          <span>{validationError ?? errorMessage}</span>
        </div>
      )}

      {file && !isScanning && (
        <div className="flex flex-col items-stretch justify-between gap-4 rounded-[1.3rem] border border-border bg-card p-4 text-card-foreground shadow-sm sm:flex-row sm:items-center">
          <div className="min-w-0 text-xs text-muted-foreground">
            <span className="block truncate font-mono sm:inline">
              {file.name}
            </span>

            <span className="mx-1.5 hidden sm:inline">·</span>

            <span className="block sm:inline">
              {(file.size / 1024).toFixed(0)} KB
            </span>
          </div>

          <div className="flex items-center justify-end gap-2">
            <Button
              size="lg"
              onClick={() => onSubmit(file)}
              className="min-h-12 shrink-0"
            >
              <ScanSearch className="h-4 w-4" />
              Run compliance scan
            </Button>

            <InfoTooltip label="About compliance scan">
              OCR extracts the visible declarations, then checks them against
              the Legal Metrology Rules, 2011.
            </InfoTooltip>
          </div>
        </div>
      )}

      <CameraCapture
        open={cameraOpen}
        onClose={() => setCameraOpen(false)}
        onCapture={(captured) => acceptFile(captured)}
      />
    </div>
  );
}