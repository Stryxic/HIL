/*
==============================================================================
HIL Instrument Canvas Handler (Layout-based)
==============================================================================

Principles:
- Read-only
- Deterministic
- One-shot render on load
- No polling
- No mutation
- No UI state machines

DOM = declarative structure
Canvas = instrument surface
JS = passive adapter
LayoutCanvas = spatial authority

==============================================================================
*/

"use strict";

import { LayoutCanvas } from "./layout.js";

/* --------------------------------------------------------------------------
 * Utilities
 * -------------------------------------------------------------------------- */

async function fetchJSON(url) {
  const response = await fetch(url, { cache: "no-store" });
  if (!response.ok) {
    const txt = await response.text().catch(() => "");
    throw new Error(`Failed fetch: ${url} (${response.status}) ${txt}`);
  }
  return response.json();
}

function configureCanvas(canvas) {
  const dpr = window.devicePixelRatio || 1;
  const rect = canvas.getBoundingClientRect();

  canvas.width = Math.floor(rect.width * dpr);
  canvas.height = Math.floor(rect.height * dpr);

  const ctx = canvas.getContext("2d");
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  return ctx;
}

function setFont(ctx, size = 12) {
  ctx.font = `${size}px ui-monospace, SFMono-Regular, Menlo, monospace`;
}

function drawLabel(ctx, text) {
  ctx.fillStyle = "#7aa2f7";
  setFont(ctx, 12);
  ctx.fillText(text, 10, 18);
}

function drawMutedText(ctx, text, x, y) {
  ctx.fillStyle = "#a7a7a7";
  setFont(ctx, 11);
  ctx.fillText(text, x, y);
}

function drawBlocked(ctx, reason) {
  ctx.fillStyle = "#f7768e";
  setFont(ctx, 11);
  ctx.fillText(reason, 10, 42);
  drawMutedText(ctx, "panel suppressed", 10, 64);
}

/* --------------------------------------------------------------------------
 * Panels (pure renderers)
 * -------------------------------------------------------------------------- */

class CalibrationPanel {
  render(ctx, vp, data) {
    const c = data.calibration;
    ctx.clearRect(0, 0, vp.w, vp.h);
    drawLabel(ctx, "Calibration & Integrity");

    const barX = 10, barY = 40, barW = 240, barH = 10;
    ctx.fillStyle = "#2a2d36";
    ctx.fillRect(barX, barY, barW, barH);

    ctx.fillStyle = c.status === "verified" ? "#9ece6a" : "#f7768e";
    ctx.fillRect(barX, barY, barW, barH);

    drawMutedText(
      ctx,
      `${c.status} · ${c.file_count} files`,
      barX + barW + 10,
      barY + 9
    );

    if (c.status !== "verified") {
      drawMutedText(
        ctx,
        `errors=${(c.errors || []).length}`,
        barX + barW + 10,
        barY + 28
      );
    }
  }
}

class InstrumentStatePanel {
  render(ctx, vp, data) {
    const o = data.observed;
    ctx.clearRect(0, 0, vp.w, vp.h);
    drawLabel(ctx, "Instrument State");

    ctx.fillStyle = "#e6e6e6";
    setFont(ctx, 11);
    ctx.fillText(`core=${o.versions.core_version}`, 10, 42);
    ctx.fillText(`timestamp=${o.timestamp}`, 10, 64);
  }
}

class TimebasePanel {
  render(ctx, vp, data) {
    const t = data.timebase;
    ctx.clearRect(0, 0, vp.w, vp.h);
    drawLabel(ctx, "Certified Timebase");

    if (!t || typeof t.tick_floor?.min_tick !== "number") {
      drawBlocked(ctx, "blocked: invalid or missing timebase");
      return;
    }

    const min = t.tick_floor.min_tick;
    const max = (t.recommended_band?.recommended_ticks || []).slice(-1)[0] || min * 10;
    const frac = Math.min(1, min / max);

    const barX = 10, barY = 44, barW = vp.w - 20, barH = 10;

    ctx.fillStyle = "#2a2d36";
    ctx.fillRect(barX, barY, barW, barH);

    ctx.fillStyle = "#7aa2f7";
    ctx.fillRect(barX, barY, Math.floor(barW * frac), barH);

    setFont(ctx, 11);
    ctx.fillStyle = "#e6e6e6";
    ctx.fillText(`Δt_min=${min.toFixed(6)}s`, 10, 74);
  }
}

class PathPreviewPanel {
  render(ctx, vp) {
    ctx.clearRect(0, 0, vp.w, vp.h);
    drawLabel(ctx, "Hilbert Path (Preview)");

    ctx.strokeStyle = "#7aa2f7";
    ctx.beginPath();
    ctx.moveTo(10, 60);
    ctx.lineTo(120, 40);
    ctx.lineTo(240, 55);
    ctx.lineTo(380, 35);
    ctx.stroke();

    drawMutedText(ctx, "deterministic geometric path (projection)", 10, 84);
  }
}

class CommitGatePanel {
  render(ctx, vp) {
    ctx.clearRect(0, 0, vp.w, vp.h);
    drawLabel(ctx, "Commit Gate");

    ctx.strokeStyle = "#a7a7a7";
    ctx.strokeRect(10, 42, 200, 18);
    drawMutedText(ctx, "human confirmation required", 20, 56);
  }
}

/* --------------------------------------------------------------------------
 * Bootstrap (one-shot)
 * -------------------------------------------------------------------------- */

async function initInstrument() {
  let observed, calibration, timebase;

  try {
    observed = await fetchJSON("/api/presentation/v1/observed");
    calibration = await fetchJSON("/api/presentation/v1/internal/calibration");
    if (calibration.status === "verified") {
      timebase = await fetchJSON("/api/presentation/v1/internal/timebase");
    }
  } catch (err) {
    console.error("Instrument bootstrap failed:", err);
    return;
  }

  const snapshot = { observed, calibration, timebase };

  document.querySelectorAll(".instrument-canvas").forEach(canvas => {
    const ctx = configureCanvas(canvas);
    const layout = new LayoutCanvas(canvas, ctx);

    const vp = { x: 0, y: 0, w: canvas.width, h: canvas.height };
    const role = canvas.dataset.role;

    switch (role) {
      case "calibration":
        layout.addPanel(new CalibrationPanel(), vp);
        break;
      case "instrument":
        layout.addPanel(new InstrumentStatePanel(), vp);
        break;
      case "timebase":
        layout.addPanel(
          calibration.status === "verified"
            ? new TimebasePanel()
            : { render: (c, v) => drawBlocked(c, "blocked: calibration invalid") },
          vp
        );
        break;
      case "path":
        layout.addPanel(
          calibration.status === "verified"
            ? new PathPreviewPanel()
            : { render: (c, v) => drawBlocked(c, "blocked: calibration invalid") },
          vp
        );
        break;
      case "commit":
        layout.addPanel(new CommitGatePanel(), vp);
        break;
    }

    layout.render(snapshot);
  });
}

document.addEventListener("DOMContentLoaded", initInstrument);
