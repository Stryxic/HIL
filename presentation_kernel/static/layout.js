/**
 * HIL Layout Canvas
 * -----------------
 * Deterministic compositor for instrument panels.
 *
 * Responsibilities:
 * - Own exactly one <canvas>
 * - Define rectangular viewports
 * - Invoke panel renderers
 * - Route pointer events to the correct panel
 *
 * Non-responsibilities:
 * - No data fetching
 * - No semantics
 * - No prioritization logic
 * - No mutation of panel data
 */

export class LayoutCanvas {
  constructor(canvas) {
    if (!(canvas instanceof HTMLCanvasElement)) {
      throw new Error("LayoutCanvas requires a HTMLCanvasElement");
    }

    this.canvas = canvas;
    this.ctx = canvas.getContext("2d");
    this.panels = [];
    this._bindEvents();
  }

  /**
   * Register a panel with a fixed viewport.
   *
   * @param {Object} panel - implements render(ctx, viewport, data)
   * @param {Object} viewport - { x, y, w, h }
   */
  addPanel(panel, viewport) {
    if (typeof panel.render !== "function") {
      throw new Error("Panel must implement render(ctx, viewport, data)");
    }

    this.panels.push({ panel, viewport });

    if (typeof panel.init === "function") {
      panel.init(this.ctx, viewport);
    }
  }

  /**
   * Render all panels using a single immutable data snapshot.
   *
   * @param {Object} dataSnapshot
   */
  render(dataSnapshot) {
    const ctx = this.ctx;

    ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);

    for (const { panel, viewport } of this.panels) {
      ctx.save();

      // Clip to panel bounds
      ctx.beginPath();
      ctx.rect(viewport.x, viewport.y, viewport.w, viewport.h);
      ctx.clip();

      // Translate local origin
      ctx.translate(viewport.x, viewport.y);

      // Panel draws only within its own coordinate space
      panel.render(ctx, viewport, dataSnapshot);

      ctx.restore();
    }
  }

  /**
   * Route pointer events to the owning panel.
   */
  _bindEvents() {
    this.canvas.addEventListener("mousedown", e => this._routeEvent("onMouseDown", e));
    this.canvas.addEventListener("mousemove", e => this._routeEvent("onMouseMove", e));
    this.canvas.addEventListener("mouseup",   e => this._routeEvent("onMouseUp", e));
    this.canvas.addEventListener("wheel",     e => this._routeEvent("onWheel", e));
  }

  _routeEvent(handlerName, event) {
    const rect = this.canvas.getBoundingClientRect();
    const x = event.clientX - rect.left;
    const y = event.clientY - rect.top;

    for (const { panel, viewport } of this.panels) {
      if (
        x >= viewport.x &&
        x <= viewport.x + viewport.w &&
        y >= viewport.y &&
        y <= viewport.y + viewport.h
      ) {
        if (typeof panel[handlerName] === "function") {
          panel[handlerName](event, {
            x: x - viewport.x,
            y: y - viewport.y,
            viewport
          });
        }
        break;
      }
    }
  }
}
