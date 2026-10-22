"use client";

import { useEffect, useRef, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Camera, X, RotateCcw, AlertCircle } from "lucide-react";
import { Button } from "@/components/ui/button";

interface CameraCaptureProps {
  open: boolean;
  onClose: () => void;
  onCapture: (file: File) => void;
}

export function CameraCapture({ open, onClose, onCapture }: CameraCaptureProps) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    if (!open) return;
    let cancelled = false;

    async function start() {
      setError(null);
      setReady(false);
      try {
        const stream = await navigator.mediaDevices.getUserMedia({
          video: { facingMode: "environment", width: { ideal: 1920 }, height: { ideal: 1080 } },
          audio: false,
        });
        if (cancelled) {
          stream.getTracks().forEach((t) => t.stop());
          return;
        }
        streamRef.current = stream;
        if (videoRef.current) {
          videoRef.current.srcObject = stream;
          await videoRef.current.play();
        }
        setReady(true);
      } catch (err) {
        setError(
          "Camera access denied or unavailable. Grant camera permission, or use the file uploader instead."
        );
      }
    }
    start();

    return () => {
      cancelled = true;
      streamRef.current?.getTracks().forEach((t) => t.stop());
      streamRef.current = null;
    };
  }, [open]);

  function capture() {
    const video = videoRef.current;
    if (!video) return;
    const canvas = document.createElement("canvas");
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
    canvas.toBlob(
      (blob) => {
        if (!blob) return;
        const file = new File([blob], `label-capture-${Date.now()}.jpg`, {
          type: "image/jpeg",
        });
        onCapture(file);
        onClose();
      },
      "image/jpeg",
      0.92
    );
  }

  return (
    <AnimatePresence>
      {open && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="fixed inset-0 z-50 flex items-center justify-center bg-ink-950/85 backdrop-blur-sm p-4"
          onClick={onClose}
        >
          <motion.div
            initial={{ scale: 0.94, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            exit={{ scale: 0.96, opacity: 0 }}
            transition={{ type: "spring", stiffness: 220, damping: 22 }}
            onClick={(e) => e.stopPropagation()}
            className="relative w-full max-w-2xl overflow-hidden rounded-2xl border border-white/10 bg-ink-900 shadow-glass"
          >
            <div className="flex items-center justify-between border-b border-white/10 px-5 py-3.5">
              <div className="flex items-center gap-2">
                <Camera className="h-4 w-4 text-brass-400" />
                <span className="font-display text-sm font-medium text-paper-50">
                  Live label capture
                </span>
              </div>
              <button
                onClick={onClose}
                className="rounded-lg p-1.5 text-paper-100/50 hover:bg-white/10 hover:text-paper-50"
                aria-label="Close camera"
              >
                <X className="h-4 w-4" />
              </button>
            </div>

            <div className="relative aspect-video bg-black">
              {error ? (
                <div className="flex h-full flex-col items-center justify-center gap-3 p-8 text-center">
                  <AlertCircle className="h-6 w-6 text-fail" />
                  <p className="max-w-sm text-sm text-paper-100/70">{error}</p>
                </div>
              ) : (
                <>
                  <video
                    ref={videoRef}
                    playsInline
                    muted
                    className="h-full w-full object-cover"
                  />
                  <div className="pointer-events-none absolute inset-6 rounded-xl border-2 border-dashed border-brass-400/50" />
                  {!ready && (
                    <div className="absolute inset-0 flex items-center justify-center bg-ink-950/60">
                      <RotateCcw className="h-5 w-5 animate-spin text-brass-400" />
                    </div>
                  )}
                </>
              )}
            </div>

            <div className="flex items-center justify-center gap-3 border-t border-white/10 p-4">
              <Button variant="secondary" onClick={onClose}>
                Cancel
              </Button>
              <Button onClick={capture} disabled={!ready || !!error}>
                <Camera className="h-4 w-4" />
                Capture label
              </Button>
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
