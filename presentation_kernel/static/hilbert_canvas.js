import * as THREE from "https://cdn.jsdelivr.net/npm/three@0.160/build/three.module.js";
import { OrbitControls } from "https://cdn.jsdelivr.net/npm/three@0.160/examples/jsm/controls/OrbitControls.js";

/*
  HILBERT CANVAS — INSTRUMENT VIEW (READ-ONLY)
  ------------------------------------------
  Responsibilities:
    - Fetch render spec (instrument surface)
    - Render field geometry deterministically
    - Provide pan / rotate / zoom (exploratory only)
    - Hit testing (no mutation of instrument state)
*/

const SPEC_URL = "/api/presentation/v1/render/spec";
const CAL_URL  = "/api/presentation/v1/internal/calibration";
const TB_URL   = "/api/presentation/v1/internal/timebase";

// ------------------------------------------------------------
// DOM + Canvas
// ------------------------------------------------------------
const canvas = document.getElementById("hilbert-canvas");
if (!canvas) {
  throw new Error("[HIL] hilbert_canvas.js: canvas#hilbert-canvas not found. Check index.html.");
}
const container =
  document.getElementById("hilbert-canvas-container") || canvas.parentElement || document.body;

// ------------------------------------------------------------
// Renderer
// ------------------------------------------------------------
const renderer = new THREE.WebGLRenderer({
  canvas,
  antialias: true,
  alpha: false,
  powerPreference: "high-performance",
});
renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
renderer.outputColorSpace = THREE.SRGBColorSpace;
renderer.setClearColor(0x0b0c10, 1);

// ------------------------------------------------------------
// Scene
// ------------------------------------------------------------
const scene = new THREE.Scene();
scene.background = new THREE.Color(0x0b0c10);

// Reference grid (debug + orientation; no epistemic meaning)
const grid = new THREE.GridHelper(20, 20, 0x2a2d36, 0x151820);
grid.material.transparent = true;
grid.material.opacity = 0.35;
scene.add(grid);

// ------------------------------------------------------------
// Camera
// ------------------------------------------------------------
const camera = new THREE.PerspectiveCamera(60, 1, 0.01, 2000);
camera.position.set(0, 2.2, 7);

// ------------------------------------------------------------
// Controls
// ------------------------------------------------------------
const controls = new OrbitControls(camera, canvas);
controls.enableDamping = true;
controls.dampingFactor = 0.08;
controls.enablePan = true;
controls.enableZoom = true;
controls.enableRotate = true;
controls.target.set(0, 0, 0);
controls.update();

// ------------------------------------------------------------
// Lighting (purely visual)
// ------------------------------------------------------------
scene.add(new THREE.AmbientLight(0xffffff, 0.35));
const keyLight = new THREE.PointLight(0xffffff, 0.85);
keyLight.position.set(8, 10, 8);
scene.add(keyLight);

// ------------------------------------------------------------
// Core calibration anchor (always present)
// ------------------------------------------------------------
const coreGeometry = new THREE.SphereGeometry(1.0, 64, 64);
const coreMaterial = new THREE.MeshStandardMaterial({
  color: 0x7aa2f7,
  metalness: 0.25,
  roughness: 0.45,
  emissive: 0x0b1220,
  emissiveIntensity: 0.35,
});
const calibrationCore = new THREE.Mesh(coreGeometry, coreMaterial);
calibrationCore.name = "calibration_core";
scene.add(calibrationCore);

// Optional ring shell (helps “field” readability)
const ringGeo = new THREE.TorusGeometry(1.6, 0.03, 24, 256);
const ringMat = new THREE.MeshStandardMaterial({
  color: 0xa7a7a7,
  metalness: 0.15,
  roughness: 0.7,
  emissive: 0x000000,
});
const ring = new THREE.Mesh(ringGeo, ringMat);
ring.rotation.x = Math.PI / 2.2;
ring.name = "core_shell_ring";
scene.add(ring);

// ------------------------------------------------------------
// Sizing (use ResizeObserver so the WebGL backbuffer matches CSS)
// ------------------------------------------------------------
function resizeToContainer() {
  const w = Math.max(1, container.clientWidth);
  const h = Math.max(1, container.clientHeight);

  renderer.setSize(w, h, false);
  camera.aspect = w / h;
  camera.updateProjectionMatrix();
}

const ro = new ResizeObserver(() => resizeToContainer());
ro.observe(container);
window.addEventListener("resize", resizeToContainer);
resizeToContainer();

// ------------------------------------------------------------
// Deterministic PRNG from string (Mulberry32)
// ------------------------------------------------------------
function xfnv1a(str) {
  let h = 2166136261 >>> 0;
  for (let i = 0; i < str.length; i++) {
    h ^= str.charCodeAt(i);
    h = Math.imul(h, 16777619);
  }
  return h >>> 0;
}
function mulberry32(seed) {
  return function () {
    let t = (seed += 0x6D2B79F5);
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

// ------------------------------------------------------------
// Geometry builders
// ------------------------------------------------------------
let fieldGroup = new THREE.Group();
fieldGroup.name = "field_group";
scene.add(fieldGroup);

function clearFieldGroup() {
  scene.remove(fieldGroup);
  fieldGroup.traverse((obj) => {
    if (obj.geometry) obj.geometry.dispose?.();
    if (obj.material) {
      if (Array.isArray(obj.material)) obj.material.forEach((m) => m.dispose?.());
      else obj.material.dispose?.();
    }
  });
  fieldGroup = new THREE.Group();
  fieldGroup.name = "field_group";
  scene.add(fieldGroup);
}

function addPathLines(paths) {
  // Expectation: paths = [{ points: [[x,y,z], ...], id, ...}, ...]
  // If your spec uses another shape, normalize here.
  const mat = new THREE.LineBasicMaterial({ color: 0x7aa2f7, transparent: true, opacity: 0.9 });

  for (let i = 0; i < paths.length; i++) {
    const p = paths[i];
    const pts = p.points || p.path || p.vertices || [];
    if (!Array.isArray(pts) || pts.length < 2) continue;

    const geom = new THREE.BufferGeometry();
    const arr = new Float32Array(pts.length * 3);
    for (let j = 0; j < pts.length; j++) {
      const v = pts[j];
      arr[j * 3 + 0] = Number(v[0] ?? 0);
      arr[j * 3 + 1] = Number(v[1] ?? 0);
      arr[j * 3 + 2] = Number(v[2] ?? 0);
    }
    geom.setAttribute("position", new THREE.BufferAttribute(arr, 3));
    geom.computeBoundingSphere();

    const line = new THREE.Line(geom, mat);
    line.name = p.id ? `path_${p.id}` : `path_${i}`;
    fieldGroup.add(line);
  }
}

function addSeedPointCloud(seedString, count = 1200) {
  // “Seed field”: deterministic, calibration-anchored filler geometry
  // so the viewer always shows a field even when paths = [].
  const seed = xfnv1a(seedString);
  const rnd = mulberry32(seed);

  const positions = new Float32Array(count * 3);

  // Fibonacci-ish sphere distribution with slight deterministic jitter
  for (let i = 0; i < count; i++) {
    const u = (i + 0.5) / count;
    const v = (i * 0.61803398875) % 1.0;

    const theta = 2 * Math.PI * v;
    const phi = Math.acos(1 - 2 * u);

    // radius shell between ~2.2 and ~8.0 with small jitter
    const r = 2.2 + 5.8 * Math.pow(rnd(), 0.72);

    const x = r * Math.sin(phi) * Math.cos(theta) + (rnd() - 0.5) * 0.05;
    const y = r * Math.cos(phi) + (rnd() - 0.5) * 0.05;
    const z = r * Math.sin(phi) * Math.sin(theta) + (rnd() - 0.5) * 0.05;

    positions[i * 3 + 0] = x;
    positions[i * 3 + 1] = y;
    positions[i * 3 + 2] = z;
  }

  const geom = new THREE.BufferGeometry();
  geom.setAttribute("position", new THREE.BufferAttribute(positions, 3));
  geom.computeBoundingSphere();

  const mat = new THREE.PointsMaterial({
    color: 0xa7a7a7,
    size: 0.03,
    sizeAttenuation: true,
    transparent: true,
    opacity: 0.75,
  });

  const pts = new THREE.Points(geom, mat);
  pts.name = "seed_point_cloud";
  fieldGroup.add(pts);
}

function frameCameraToObject(obj) {
  // Frame camera to bounding sphere
  const box = new THREE.Box3().setFromObject(obj);
  const sphere = new THREE.Sphere();
  box.getBoundingSphere(sphere);

  if (!isFinite(sphere.radius) || sphere.radius <= 0) return;

  const radius = sphere.radius;
  const dist = radius / Math.tan((camera.fov * Math.PI) / 360);
  const newPos = new THREE.Vector3(0, 0, 1).multiplyScalar(dist * 1.25).add(sphere.center);

  camera.position.copy(newPos);
  controls.target.copy(sphere.center);
  controls.update();
}

// ------------------------------------------------------------
// Fetch + Build
// ------------------------------------------------------------
async function fetchJson(url) {
  const res = await fetch(url, { cache: "no-store" });
  if (!res.ok) throw new Error(`[HIL] fetch failed ${url}: ${res.status}`);
  return await res.json();
}

async function buildFieldOnLoad() {
  clearFieldGroup();

  let spec = null;
  try {
    spec = await fetchJson(SPEC_URL);
    console.log("[HIL] render spec:", spec);
  } catch (e) {
    console.warn("[HIL] render spec unavailable; using seed field only.", e);
  }

  // Always try to anchor seed to calibration/timebase
  let seedAnchor = "";
  try {
    const cal = await fetchJson(CAL_URL);
    seedAnchor += JSON.stringify(cal);
  } catch {}
  try {
    const tb = await fetchJson(TB_URL);
    seedAnchor += JSON.stringify(tb);
  } catch {}

  const paths = spec?.paths || [];

  if (Array.isArray(paths) && paths.length > 0) {
    addPathLines(paths);
  } else {
    // No paths yet => render calibration-anchored seed field
    // so the screen is never “empty”.
    const fallbackSeed = seedAnchor || "hil_seed_v1";
    addSeedPointCloud(fallbackSeed, 1400);
  }

  // Frame to the full group (core + field)
  const framingGroup = new THREE.Group();
  framingGroup.add(calibrationCore.clone());
  framingGroup.add(fieldGroup);
  frameCameraToObject(framingGroup);
}

buildFieldOnLoad().catch((e) => console.error("[HIL] buildFieldOnLoad error:", e));

// ------------------------------------------------------------
// Raycast click (interaction proof; no mutation)
// ------------------------------------------------------------
const raycaster = new THREE.Raycaster();
const mouseNdc = new THREE.Vector2();

function onClick(ev) {
  const rect = canvas.getBoundingClientRect();
  const x = ((ev.clientX - rect.left) / rect.width) * 2 - 1;
  const y = -(((ev.clientY - rect.top) / rect.height) * 2 - 1);

  mouseNdc.set(x, y);
  raycaster.setFromCamera(mouseNdc, camera);

  const hits = raycaster.intersectObjects([calibrationCore, ...fieldGroup.children], true);
  if (hits.length) {
    const hit = hits[0].object;
    console.log("[HIL] click hit:", hit.name || hit.type, hit);
  }
}
canvas.addEventListener("click", onClick);

// ------------------------------------------------------------
// Loop
// ------------------------------------------------------------
function animate() {
  controls.update();
  renderer.render(scene, camera);
  requestAnimationFrame(animate);
}
animate();
