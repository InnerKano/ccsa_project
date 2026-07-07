"use client";

import { useEffect, useMemo, useState } from "react";

import { cn } from "@/lib/cn";
import { formatCurrency } from "@/lib/format";

export type DonutSegment = {
  id: string;
  value: number;
  color: string;
  label: string;
};

type DonutChartProps = {
  segments: DonutSegment[];
  total: number;
  currency?: string;
  className?: string;
  size?: number;
  strokeWidth?: number;
};

const DEFAULT_SIZE = 220;
const DEFAULT_STROKE = 22;
const DRAW_DURATION_MS = 800;
const COUNT_DURATION_MS = 750;

function usePrefersReducedMotion(): boolean {
  const [reduced, setReduced] = useState(
    () =>
      typeof window !== "undefined" &&
      window.matchMedia("(prefers-reduced-motion: reduce)").matches,
  );

  useEffect(() => {
    const media = window.matchMedia("(prefers-reduced-motion: reduce)");
    const update = () => setReduced(media.matches);
    media.addEventListener("change", update);
    return () => media.removeEventListener("change", update);
  }, []);

  return reduced;
}

function useAnimatedNumber(target: number, animate: boolean, durationMs: number): number {
  const [value, setValue] = useState(animate ? 0 : target);

  useEffect(() => {
    if (!animate) {
      setValue(target);
      return;
    }

    setValue(0);
    const start = performance.now();
    let frame = 0;

    const tick = (now: number) => {
      const progress = Math.min((now - start) / durationMs, 1);
      const eased = 1 - (1 - progress) ** 3;
      setValue(target * eased);
      if (progress < 1) {
        frame = requestAnimationFrame(tick);
      }
    };

    frame = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(frame);
  }, [target, animate, durationMs]);

  return value;
}

export function DonutChart({
  segments,
  total,
  currency = "USD",
  className,
  size = DEFAULT_SIZE,
  strokeWidth = DEFAULT_STROKE,
}: DonutChartProps) {
  const reducedMotion = usePrefersReducedMotion();
  const [ready, setReady] = useState(() => reducedMotion);

  useEffect(() => {
    if (reducedMotion) {
      setReady(true);
      return;
    }
    const frame = requestAnimationFrame(() => setReady(true));
    return () => cancelAnimationFrame(frame);
  }, [reducedMotion]);

  const displayTotal = useAnimatedNumber(
    total,
    ready && !reducedMotion,
    COUNT_DURATION_MS,
  );

  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const center = size / 2;

  const arcs = useMemo(() => {
    const visible = segments.filter((segment) => segment.value > 0);
    const sum = visible.reduce((acc, segment) => acc + segment.value, 0);
    if (sum <= 0) {
      return [];
    }

    let offset = 0;
    return visible.map((segment) => {
      const dash = (segment.value / sum) * circumference;
      const arc = {
        ...segment,
        dash,
        dashOffset: -offset,
      };
      offset += dash;
      return arc;
    });
  }, [segments, circumference]);

  const ariaLabel = `Total ${formatCurrency(total, currency)}`;

  return (
    <div
      className={cn("relative shrink-0", className)}
      style={{ width: size, height: size }}
    >
      <svg width={size} height={size} role="img" aria-label={ariaLabel}>
        <circle
          cx={center}
          cy={center}
          r={radius}
          fill="none"
          stroke="var(--color-border)"
          strokeWidth={strokeWidth}
        />
        <g transform={`rotate(-90 ${center} ${center})`}>
          {arcs.map((arc, index) => (
            <circle
              key={arc.id}
              cx={center}
              cy={center}
              r={radius}
              fill="none"
              stroke={arc.color}
              strokeWidth={strokeWidth}
              strokeLinecap="butt"
              strokeDasharray={
                ready
                  ? `${arc.dash} ${circumference - arc.dash}`
                  : `0 ${circumference}`
              }
              strokeDashoffset={arc.dashOffset}
              style={{
                opacity: ready ? 1 : 0,
                transition: reducedMotion
                  ? undefined
                  : `stroke-dasharray ${DRAW_DURATION_MS + index * 80}ms ease-out, opacity 600ms ease-out`,
              }}
            />
          ))}
        </g>
      </svg>
      <div className="pointer-events-none absolute inset-0 flex flex-col items-center justify-center text-center">
        <span className="text-lg font-semibold tabular-nums text-foreground">
          {formatCurrency(displayTotal, currency)}
        </span>
        <span className="text-[10px] font-medium uppercase tracking-wider text-muted">
          Total
        </span>
      </div>
    </div>
  );
}
