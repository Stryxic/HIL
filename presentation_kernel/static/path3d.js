// ============================================================================
// 3D Canvas Architecture for Hilbert Paths (no WebGL)
// Deterministic: no smoothing, no randomness, explicit basis, polyline only.
// ============================================================================

(function () {
  "use strict";

  // --------------------------------------------------------------------------
  // Utilities: DOM + Fetch
  // --------------------------------------------------------------------------

  function $(sel, root = document) {
    return root.querySelector(sel);
  }

  async function fetchJSON(url) {
    const res = await fetch(url, { cache: "no-store" });
    if (!res.ok) throw new Error(`${url} -> ${res.status}`);
    return await res.json();
  }

  // --------------------------------------------------------------------------
  // Math: Vec3
  // --------------------------------------------------------------------------

  class Vec3 {
    constructor(x = 0, y = 0, z = 0) {
      this.x = x; this.y = y; this.z = z;
    }
    add(b) { return new Vec3(this.x + b.x, this.y + b.y, this.z + b.z); }
    sub(b) { return new Vec3(this.x - b.x, this.y - b.y, this.z - b.z); }
    mul(s) { return new Vec3(this.x * s, this.y * s, this.z * s); }
    dot(b) { return this.x * b.x + this.y * b.y + this.z * b.z; }
    len() { return Math.sqrt(this.dot(this)); }
    norm() {
      const l = this.len();
      return l > 0 ? this.mul(1 / l) : new Vec3(0, 0, 0);
    }
  }

  function clamp(v, lo, hi) {
    return Math.max(lo, Math.min(hi, v));
  }

  // --------------------------------------------------------------------------
  // Camera: orbit around target (yaw, pitch, distance)
  // We do a simple "camera space" transform by rotating world into view.
  // --------------------------------------------------------------------------

  class OrbitCamera {
    constructor() {
      this.target = new Vec3(0, 0, 0);
      this.yaw = 0.6;          // radians
      this.pitch = -0.35;      // radians
      this.distance = 6.0;     // world units
      this.fov = 55 * Math.PI / 180; // perspective FOV
      this.near = 0.01;
      this.far = 1e6;
    }

    // Convert world point -> camera/view space
    worldToView(p) {
      // Translate to target-centered frame
      const q = p.sub(this.target);

      // Rotate by yaw around Y, then pitch around X (deterministic)
      const cy = Math.cos(this.yaw), sy = Math.sin(this.yaw);
      const cx = Math.cos(this.pitch), sx = Math.sin(this.pitch);

      // yaw (Y axis)
      const x1 =  cy * q.x + sy * q.z;
      const z1 = -sy * q.x + cy * q.z;
      const y1 =  q.y;

      // pitch (X axis)
      const y2 =  cx * y1 - sx * z1;
      const z2 =  sx * y1 + cx * z1;
      const x2 =  x1;

      // Camera is at (0,0,+distance) looking toward origin => shift z
      // We want points in front of camera to have positive depth.
      const zc = z2 + this.distance;

      return new Vec3(x2, y2, zc);
    }

    // View space -> screen space (pixels)
    viewToScreen(v, width, height) {
      // Perspective projection onto normalized device coords
      // x_ndc = (x / z) * scale, y_ndc = (y / z) * scale
      const aspect = width / height;
      const scale = 1 / Math.tan(this.fov * 0.5);

      // Guard against z<=0 (behind camera)
      if (v.z <= this.near) return null;

      const xN = (v.x * scale) / (v.z * aspect);
      const yN = (v.y * scale) / v.z;

      // Convert NDC [-1,1] -> pixels
      const xPx = (xN * 0.5 + 0.5) * width;
      const yPx = (-yN * 0.5 + 0.5) * height;

      return { x: xPx, y: yPx, z: v.z };
    }

    worldToScreen(p, width, height) {
      const v = this.worldToView(p);
      return this.viewToScreen(v, width, height);
    }

    orbit(deltaYaw, deltaPitch) {
      this.yaw += deltaYaw;
      this.pitch = clamp(this.pitch + deltaPitch, -1.35, 1.35);
    }

    zoom(delta) {
      // multiplicative zoom for stability
      const k = Math.exp(delta);
      this.distance = clamp(this.distance * k, 0.2, 1e4);
    }

    pan(dxWorld, dyWorld) {
      // Pan in camera plane: approximate by rotating a screen-plane vector into world
      // This keeps deterministic behavior without full matrix math.
      const cy = Math.cos(this.yaw), sy = Math.sin(this.yaw);
      // Right vector from yaw only (good enough for UI)
      const right = new Vec3(cy, 0, -sy);
      const up = new Vec3(0, 1, 0);

      this.target = this.target.add(right.mul(dxWorld)).add(up.mul(dyWorld));
    }
  }

  // --------------------------------------------------------------------------
  // Path model: explicit basis mapping from R^k -> R^3
  // --------------------------------------------------------------------------

  function projectRkToR3(vecK, basis) {
    // basis: [i,j,k] index into vecK
    const i = basis[0], j = basis[1], k = basis[2];
    return new Vec3(vecK[i] ?? 0, vecK[j] ?? 0, vecK[k] ?? 0);
  }

  // Compute a stable bounding box and normalization transform so the path fits view
  function computeBounds(points) {
    let minX = Infinity, minY = Infinity, minZ = Infinity;
    let maxX = -Infinity, maxY = -Infinity, maxZ = -Infinity;
    for (const p of points) {
      minX = Math.min(minX, p.x); maxX = Math.max(maxX, p.x);
      minY = Math.min(minY, p.y); maxY = Math.max(maxY, p.y);
      minZ = Math.min(minZ, p.z); maxZ = Math.max(maxZ, p.z);
    }
    const center = new Vec3((minX + maxX)/2, (minY + maxY)/2, (minZ + maxZ)/2);
    const size = new Vec3(maxX - minX, maxY - minY, maxZ - minZ);
    const radius = Math.max(size.x, size.y, size.z) * 0.5 || 1.0;
    return { center, radius, minX, maxX, minY, maxY, minZ, maxZ };
  }

  // --------------------------------------------------------------------------
  // Renderer: 2D canvas drawing of projected 3D
  // --------------------------------------------------------------------------

  class Path3DRenderer {
    constructor(canvas) {
      this.canvas = canvas;
      this.ctx = canvas.getContext("2d");
      this.camera = new OrbitCamera();

      this.state = {
        paths: [],          // [{id, points:[Vec3], meta}]
        activePathId: null,
        basis: [0, 1, 2],   // default dims
        showAxes: true,
        showPoints: true,
        showLine: true,
        hover: null,        // {idx, screen:{x,y}, world:Vec3}
      };
    }

    setPaths(paths) {
      this.state.paths = paths;
      if (!this.state.activePathId && paths.length) {
        this.state.activePathId = paths[0].id;
      }
      this.fitToActivePath();
      this.draw();
    }

    setBasis(basis) {
      this.state.basis = basis;
      this.fitToActivePath();
      this.draw();
    }

    setActivePath(id) {
      this.state.activePathId = id;
      this.fitToActivePath();
      this.draw();
    }

    fitToActivePath() {
      const p = this.getActivePath();
      if (!p) return;
      const b = computeBounds(p.points);
      this.camera.target = b.center;
      // distance scaled to radius so it fits consistently
      this.camera.distance = b.radius * 3.0;
    }

    getActivePath() {
      return this.state.paths.find(p => p.id === this.state.activePathId) || null;
    }

    clear() {
      const { ctx } = this;
      const w = this.canvas.width, h = this.canvas.height;
      ctx.clearRect(0, 0, w, h);
    }

    drawAxes() {
      const { ctx } = this;
      const w = this.canvas.width, h = this.canvas.height;

      // World axes around camera target, unit length scaled to fit
      const origin = this.camera.target;
      const L = Math.max(1.0, this.camera.distance * 0.25);

      const axes = [
        { a: origin, b: origin.add(new Vec3(L, 0, 0)), label: "x" },
        { a: origin, b: origin.add(new Vec3(0, L, 0)), label: "y" },
        { a: origin, b: origin.add(new Vec3(0, 0, L)), label: "z" },
      ];

      ctx.save();
      ctx.lineWidth = 1;

      for (const ax of axes) {
        const A = this.camera.worldToScreen(ax.a, w, h);
        const B = this.camera.worldToScreen(ax.b, w, h);
        if (!A || !B) continue;

        ctx.beginPath();
        ctx.moveTo(A.x, A.y);
        ctx.lineTo(B.x, B.y);
        ctx.stroke();

        ctx.font = "12px ui-monospace, SFMono-Regular, Menlo, monospace";
        ctx.fillText(ax.label, B.x + 4, B.y + 4);
      }

      ctx.restore();
    }

    drawPath(path) {
      const { ctx } = this;
      const w = this.canvas.width, h = this.canvas.height;

      // Project all points to screen space once (deterministic)
      const screens = [];
      for (const p of path.points) {
        const s = this.camera.worldToScreen(p, w, h);
        screens.push(s);
      }

      // Line
      if (this.state.showLine) {
        ctx.save();
        ctx.lineWidth = 2;
        ctx.beginPath();
        let started = false;
        for (let i = 0; i < screens.length; i++) {
          const s = screens[i];
          if (!s) continue;
          if (!started) {
            ctx.moveTo(s.x, s.y);
            started = true;
          } else {
            ctx.lineTo(s.x, s.y);
          }
        }
        ctx.stroke();
        ctx.restore();
      }

      // Points
      if (this.state.showPoints) {
        ctx.save();
        for (let i = 0; i < screens.length; i++) {
          const s = screens[i];
          if (!s) continue;
          const r = 2.5;
          ctx.beginPath();
          ctx.arc(s.x, s.y, r, 0, Math.PI * 2);
          ctx.fill();
        }
        ctx.restore();
      }

      return screens;
    }

    drawHover() {
      const h = this.state.hover;
      if (!h) return;

      const { ctx } = this;
      ctx.save();
      ctx.lineWidth = 2;
      ctx.beginPath();
      ctx.arc(h.screen.x, h.screen.y, 6, 0, Math.PI * 2);
      ctx.stroke();
      ctx.restore();
    }

    draw() {
      this.clear();

      // Background “panel” feel (optional)
      const { ctx } = this;
      const w = this.canvas.width, h = this.canvas.height;
      ctx.save();
      ctx.globalAlpha = 0.12;
      ctx.fillRect(0, 0, w, h);
      ctx.restore();

      if (this.state.showAxes) this.drawAxes();

      const active = this.getActivePath();
      if (!active) return;

      this._lastScreens = this.drawPath(active);
      this.drawHover();
    }

    // Hover picking: nearest point in screen-space
    updateHover(px, py) {
      const active = this.getActivePath();
      if (!active || !this._lastScreens) return;

      let best = null;
      let bestD2 = Infinity;

      for (let i = 0; i < this._lastScreens.length; i++) {
        const s = this._lastScreens[i];
        if (!s) continue;
        const dx = s.x - px;
        const dy = s.y - py;
        const d2 = dx*dx + dy*dy;
        if (d2 < bestD2) {
          bestD2 = d2;
          best = { idx: i, screen: { x: s.x, y: s.y }, world: active.points[i] };
        }
      }

      // Threshold in pixels
      if (best && bestD2 <= 18 * 18) {
        this.state.hover = best;
      } else {
        this.state.hover = null;
      }
      this.draw();
    }
  }

  // --------------------------------------------------------------------------
  // Input Controller: pointer + wheel (deterministic mapping)
  // --------------------------------------------------------------------------

  class CanvasController {
    constructor(canvas, renderer) {
      this.canvas = canvas;
      this.renderer = renderer;
      this.dragging = false;
      this.mode = "orbit"; // orbit | pan
      this.last = { x: 0, y: 0 };

      this._bind();
    }

    _bind() {
      this.canvas.addEventListener("pointerdown", (e) => {
        this.canvas.setPointerCapture(e.pointerId);
        this.dragging = true;
        this.last = { x: e.clientX, y: e.clientY };
        this.mode = e.shiftKey ? "pan" : "orbit";
      });

      this.canvas.addEventListener("pointermove", (e) => {
        const rect = this.canvas.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;

        if (!this.dragging) {
          this.renderer.updateHover(x, y);
          return;
        }

        const dx = e.clientX - this.last.x;
        const dy = e.clientY - this.last.y;
        this.last = { x: e.clientX, y: e.clientY };

        if (this.mode === "orbit") {
          const k = 0.006;
          this.renderer.camera.orbit(dx * k, dy * k);
        } else {
          // Pan scaled by distance for stable UX
          const k = 0.002 * this.renderer.camera.distance;
          this.renderer.camera.pan(-dx * k, dy * k);
        }

        this.renderer.draw();
      });

      this.canvas.addEventListener("pointerup", (e) => {
        this.dragging = false;
      });

      this.canvas.addEventListener("wheel", (e) => {
        e.preventDefault();
        // Zoom uses exp(delta) for stable scaling
        const delta = e.deltaY * 0.0015;
        this.renderer.camera.zoom(delta);
        this.renderer.draw();
      }, { passive: false });

      // Resize handling
      window.addEventListener("resize", () => this.resizeToDisplaySize());
      this.resizeToDisplaySize();
    }

    resizeToDisplaySize() {
      const rect = this.canvas.getBoundingClientRect();
      const dpr = window.devicePixelRatio || 1;
      const w = Math.max(1, Math.floor(rect.width * dpr));
      const h = Math.max(1, Math.floor(rect.height * dpr));

      if (this.canvas.width !== w || this.canvas.height !== h) {
        this.canvas.width = w;
        this.canvas.height = h;
        this.renderer.draw();
      }
    }
  }

  // --------------------------------------------------------------------------
  // Data adapter: render/spec -> Path3D points
  // You can shape this to match your /render/spec schema exactly.
  // --------------------------------------------------------------------------

  function adaptRenderSpecToPaths(spec, basis) {
    // Expected (example):
    // spec.paths = [{ id, points: [[...k],[...k],...], meta:{} }, ...]
    const out = [];
    const paths = Array.isArray(spec.paths) ? spec.paths : [];

    for (let pidx = 0; pidx < paths.length; pidx++) {
      const p = paths[pidx];
      const id = p.id ?? `path-${pidx}`;
      const ptsK = Array.isArray(p.points) ? p.points : [];
      const pts3 = ptsK.map(vk => projectRkToR3(vk, basis));
      out.push({ id, points: pts3, meta: p.meta ?? {} });
    }
    return out;
  }

  // --------------------------------------------------------------------------
  // Boot: wire into DOM
  // --------------------------------------------------------------------------

  async function bootPath3DCanvas() {
    const canvas = $("#hil-path-3d");
    if (!canvas) return;

    const renderer = new Path3DRenderer(canvas);
    const controller = new CanvasController(canvas, renderer);

    // Default basis
    renderer.setBasis([0, 1, 2]);

    // Fetch spec (or observed state). Use render/spec if you have it.
    try {
      const spec = await fetchJSON("/api/presentation/v1/render/spec");
      const paths = adaptRenderSpecToPaths(spec, renderer.state.basis);
      renderer.setPaths(paths);
    } catch (e) {
      // You can render an error overlay deterministically here.
      console.error("Failed to load render/spec", e);
    }

    // Optional: expose for debugging in dev
    window.__HIL3D = { renderer, controller };
  }

  // Run when DOM ready
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", bootPath3DCanvas);
  } else {
    bootPath3DCanvas();
  }
})();
