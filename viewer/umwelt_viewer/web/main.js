// umwelt viewer.
//
// Draws each robot's belief from the operator's point of view. Everything in
// the scene lives under `world`, a group whose local frame is ENU (x east,
// y north, z up) so positions and quaternions from ROS can be used as they
// are. three.js itself is y-up; the group's rotation does the conversion.
//
// The viewer only draws what robots believe. It never shows simulator ground
// truth, so what you see here is what a person wearing the glasses would see.

import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';

const FREE = new THREE.Color(0x5dcaa5);
const OCC = new THREE.Color(0xe8643f);
const TRAIL_POINTS = 600;
const MAX_COLUMNS = 6000;

// ---------------------------------------------------------------- scene

const canvas = document.getElementById('scene');
const renderer = new THREE.WebGLRenderer({ canvas, antialias: true });
renderer.setPixelRatio(window.devicePixelRatio);

const scene = new THREE.Scene();
scene.background = new THREE.Color(0x1d2125);
scene.fog = new THREE.Fog(0x1d2125, 60, 160);

const camera = new THREE.PerspectiveCamera(60, 1, 0.05, 500);
const controls = new OrbitControls(camera, canvas);
controls.enableDamping = true;
controls.maxPolarAngle = Math.PI * 0.495;

scene.add(new THREE.HemisphereLight(0xffffff, 0x3a3f45, 1.6));
const sun = new THREE.DirectionalLight(0xffffff, 1.4);
sun.position.set(-20, 40, 15);
scene.add(sun);

// ENU root. Rotating -90 degrees about x maps (x, y, z) to (x, z, -y).
const world = new THREE.Group();
world.rotation.x = -Math.PI / 2;
scene.add(world);

const enuToThree = (x, y, z) => new THREE.Vector3(x, z, -y);

const ground = new THREE.Mesh(
  new THREE.PlaneGeometry(200, 200),
  new THREE.MeshStandardMaterial({ color: 0x2c3035, roughness: 1 }),
);
world.add(ground);

const grid = new THREE.GridHelper(200, 40, 0x4a4f55, 0x363a3f);
grid.rotation.x = Math.PI / 2;   // GridHelper is drawn in XZ; put it in ENU XY.
grid.position.z = 0.005;
world.add(grid);

// A small marker at the world origin (PX4 home).
const home = new THREE.Mesh(
  new THREE.RingGeometry(0.35, 0.45, 32),
  new THREE.MeshBasicMaterial({ color: 0x9a988f, side: THREE.DoubleSide }),
);
home.position.z = 0.01;
world.add(home);

// ---------------------------------------------------------------- robots

const robots = new Map();

function makeDrone() {
  const g = new THREE.Group();
  const body = new THREE.MeshStandardMaterial({ color: 0xd3d1c7, roughness: 0.6 });
  const arm = new THREE.BoxGeometry(0.9, 0.06, 0.04);
  for (const a of [Math.PI / 4, -Math.PI / 4]) {
    const m = new THREE.Mesh(arm, body);
    m.rotation.z = a;
    g.add(m);
  }
  const rotorGeo = new THREE.CylinderGeometry(0.16, 0.16, 0.01, 24);
  rotorGeo.rotateX(Math.PI / 2);   // cylinder axis from y to z
  const rotorMat = new THREE.MeshBasicMaterial({ color: 0xffffff, transparent: true, opacity: 0.35 });
  for (const [x, y] of [[0.32, 0.32], [0.32, -0.32], [-0.32, 0.32], [-0.32, -0.32]]) {
    const r = new THREE.Mesh(rotorGeo, rotorMat);
    r.position.set(x, y, 0.04);
    g.add(r);
  }
  // Heading: body +x is forward (FLU).
  g.add(new THREE.ArrowHelper(new THREE.Vector3(1, 0, 0), new THREE.Vector3(0, 0, 0), 1.1, 0x5dcaa5, 0.25, 0.14));
  return g;
}

function makeRobot(id) {
  const r = { id, lastState: 0, lastGrid: 0, state: null };

  r.model = makeDrone();
  world.add(r.model);

  // Vertical line from the robot to the ground, for depth perception.
  r.stemGeo = new THREE.BufferGeometry().setAttribute('position', new THREE.Float32BufferAttribute(new Float32Array(6), 3));
  r.stem = new THREE.Line(r.stemGeo, new THREE.LineDashedMaterial({ color: 0x9a988f, dashSize: 0.15, gapSize: 0.1 }));
  world.add(r.stem);

  // 2-sigma horizontal position uncertainty.
  r.ellipse = new THREE.Mesh(
    new THREE.RingGeometry(0.94, 1.0, 64),
    new THREE.MeshBasicMaterial({ color: 0xef9f27, transparent: true, opacity: 0.8, side: THREE.DoubleSide }),
  );
  r.ellipse.position.z = 0.04;
  r.ellipse.visible = false;
  world.add(r.ellipse);

  // Flight trail.
  r.trailPos = new Float32Array(TRAIL_POINTS * 3);
  r.trailCount = 0;
  r.trailGeo = new THREE.BufferGeometry().setAttribute('position', new THREE.BufferAttribute(r.trailPos, 3));
  r.trail = new THREE.Line(r.trailGeo, new THREE.LineBasicMaterial({ color: 0x85b7eb, transparent: true, opacity: 0.6 }));
  world.add(r.trail);

  // Belief layer: a textured plane on the ground plus columns for occupied cells.
  r.texture = null;
  r.layer = null;
  r.columns = new THREE.InstancedMesh(
    new THREE.BoxGeometry(1, 1, 1).translate(0, 0, 0.5),
    new THREE.MeshStandardMaterial({ color: 0xffffff, transparent: true, opacity: 0.8, roughness: 0.8 }),
    MAX_COLUMNS,
  );
  r.columns.count = 0;
  world.add(r.columns);

  r.hud = document.createElement('div');
  r.hud.className = 'robot';
  document.getElementById('robots').appendChild(r.hud);

  robots.set(id, r);
  return r;
}

const robot = (id) => robots.get(id) ?? makeRobot(id);

function applyState(s) {
  const r = robot(s.robot_id);
  r.state = s;
  r.lastState = performance.now();
  const [x, y, z] = s.position;
  const [qx, qy, qz, qw] = s.orientation;

  r.model.position.set(x, y, z);
  r.model.quaternion.set(qx, qy, qz, qw);

  const stem = r.stemGeo.attributes.position;
  stem.setXYZ(0, x, y, z);
  stem.setXYZ(1, x, y, 0);
  stem.needsUpdate = true;
  r.stem.computeLineDistances();

  if (s.cov_xy) {
    // Principal axes of the 2x2 covariance.
    const [[a, b], [, d]] = s.cov_xy;
    const tr = (a + d) / 2;
    const disc = Math.sqrt(Math.max(0, ((a - d) / 2) ** 2 + b * b));
    const l1 = tr + disc;
    const l2 = Math.max(0, tr - disc);
    const angle = 0.5 * Math.atan2(2 * b, a - d);
    r.ellipse.scale.set(2 * Math.sqrt(l1) + 0.05, 2 * Math.sqrt(l2) + 0.05, 1);
    r.ellipse.rotation.z = angle;
    r.ellipse.position.x = x;
    r.ellipse.position.y = y;
    r.ellipse.visible = true;
    r.sigma = Math.sqrt(l1);
  } else {
    r.ellipse.visible = false;
    r.sigma = null;
  }

  // Trail: append when the robot has moved at least 10 cm.
  const n = r.trailCount;
  const last = n > 0 ? n - 1 : -1;
  const moved = last < 0 || Math.hypot(
    r.trailPos[last * 3] - x, r.trailPos[last * 3 + 1] - y, r.trailPos[last * 3 + 2] - z) > 0.1;
  if (moved) {
    if (n === TRAIL_POINTS) {
      r.trailPos.copyWithin(0, 3);
      r.trailCount = n - 1;
    }
    r.trailPos.set([x, y, z], r.trailCount * 3);
    r.trailCount += 1;
    r.trailGeo.setDrawRange(0, r.trailCount);
    r.trailGeo.attributes.position.needsUpdate = true;
  }
}

function applyGrid(header, cells) {
  const r = robot(header.robot_id);
  r.lastGrid = performance.now();
  const { width: w, height: h, resolution: res, origin: [ox, oy] } = header;

  if (!r.layer || r.layer.userData.w !== w || r.layer.userData.h !== h) {
    if (r.layer) world.remove(r.layer);
    r.rgba = new Uint8Array(w * h * 4);
    r.texture = new THREE.DataTexture(r.rgba, w, h, THREE.RGBAFormat);
    r.texture.magFilter = THREE.NearestFilter;
    r.texture.minFilter = THREE.NearestFilter;
    r.layer = new THREE.Mesh(
      new THREE.PlaneGeometry(w * res, h * res),
      new THREE.MeshBasicMaterial({ map: r.texture, transparent: true, depthWrite: false }),
    );
    r.layer.userData = { w, h };
    r.layer.position.set(ox + (w * res) / 2, oy + (h * res) / 2, 0.02);
    world.add(r.layer);
  }

  // Row 0 of the grid is the lowest y, which is v = 0 on the plane.
  const rgba = r.rgba;
  const m = new THREE.Matrix4();
  const c = new THREE.Color();
  let columns = 0;
  let known = 0;
  for (let i = 0; i < w * h; i++) {
    const p = cells[i] / 255;
    const certainty = Math.abs(p - 0.5) * 2;
    const o = i * 4;
    if (certainty < 0.1) {
      // Unknown: a faint grey wash, so the extent of the robot's map is visible.
      rgba[o] = 95;
      rgba[o + 1] = 94;
      rgba[o + 2] = 90;
      rgba[o + 3] = 22;
      continue;
    }
    known += 1;
    const col = p > 0.5 ? OCC : FREE;
    rgba[o] = col.r * 255;
    rgba[o + 1] = col.g * 255;
    rgba[o + 2] = col.b * 255;
    rgba[o + 3] = p > 0.5 ? 90 + 165 * certainty : 140 * certainty;

    if (p > 0.7 && columns < MAX_COLUMNS) {
      const ix = i % w;
      const iy = Math.floor(i / w);
      const height = 0.3 + 1.7 * certainty;
      m.makeScale(res * 0.92, res * 0.92, height);
      m.setPosition(ox + (ix + 0.5) * res, oy + (iy + 0.5) * res, 0);
      r.columns.setMatrixAt(columns, m);
      r.columns.setColorAt(columns, c.copy(FREE).lerp(OCC, certainty));
      columns += 1;
    }
  }
  r.texture.needsUpdate = true;
  r.columns.count = columns;
  r.columns.instanceMatrix.needsUpdate = true;
  if (r.columns.instanceColor) r.columns.instanceColor.needsUpdate = true;
  r.knownCells = known;
  r.occupiedCells = columns;
}

// ---------------------------------------------------------------- HUD

function fmt(v, digits = 1, unit = '') {
  return v === null || v === undefined || Number.isNaN(v) ? '-' : `${v.toFixed(digits)}${unit}`;
}

function updateHud(now) {
  for (const r of robots.values()) {
    const s = r.state;
    const age = r.lastState ? (now - r.lastState) / 1000 : null;
    const stale = age === null || age > 2;
    r.hud.innerHTML = `
      <div class="name">${r.id}${stale ? ' <span class="pill off">stale</span>' : ''}</div>
      <dl>
        <dt>altitude</dt><dd>${fmt(s?.position[2], 1, ' m')}</dd>
        <dt>speed</dt><dd>${fmt(s?.speed, 1, ' m/s')}</dd>
        <dt>position 1&sigma;</dt><dd>${fmt(r.sigma, 2, ' m')}</dd>
        <dt>known cells</dt><dd>${r.knownCells ?? '-'}</dd>
        <dt>occupied</dt><dd>${r.occupiedCells ?? '-'}</dd>
        <dt>task</dt><dd>${s?.active_task_id || 'idle'}</dd>
      </dl>`;
  }
}

// ---------------------------------------------------------------- views

let operator = enuToThree(-6, -10, 1.7);
let follow = null;

function setView(name) {
  for (const b of document.querySelectorAll('.controls button')) b.classList.remove('active');
  document.getElementById(`view-${name}`).classList.add('active');
  follow = null;
  if (name === 'operator') {
    camera.position.copy(operator);
    controls.target.set(0, 1.0, 0);
  } else if (name === 'top') {
    camera.position.set(0, 70, 0.01);
    controls.target.set(0, 0, 0);
  } else if (name === 'follow') {
    follow = robots.values().next().value ?? null;
  }
  controls.update();
}

document.getElementById('view-operator').onclick = () => setView('operator');
document.getElementById('view-top').onclick = () => setView('top');
document.getElementById('view-follow').onclick = () => setView('follow');
window.addEventListener('keydown', (e) => {
  const key = { o: 'operator', t: 'top', f: 'follow' }[e.key.toLowerCase()];
  if (key) setView(key);
});

// ---------------------------------------------------------------- link

const link = document.getElementById('link');

function connect() {
  const ws = new WebSocket(`ws://${location.host}/ws`);
  ws.binaryType = 'arraybuffer';
  ws.onopen = () => { link.textContent = 'live'; link.className = 'pill on'; };
  ws.onclose = () => {
    link.textContent = 'offline';
    link.className = 'pill off';
    setTimeout(connect, 1000);
  };
  ws.onmessage = (ev) => {
    if (typeof ev.data === 'string') {
      const msg = JSON.parse(ev.data);
      if (msg.type === 'state') applyState(msg);
      return;
    }
    const view = new DataView(ev.data);
    const n = view.getUint32(0, true);
    const header = JSON.parse(new TextDecoder().decode(new Uint8Array(ev.data, 4, n)));
    if (header.type === 'grid') applyGrid(header, new Uint8Array(ev.data, 4 + n));
  };
}

// ---------------------------------------------------------------- loop

function resize() {
  const w = window.innerWidth;
  const h = window.innerHeight;
  renderer.setSize(w, h, false);
  camera.aspect = w / h;
  camera.updateProjectionMatrix();
}
window.addEventListener('resize', resize);

let lastHud = 0;
function frame(now) {
  if (follow?.state) {
    const [x, y, z] = follow.state.position;
    const target = enuToThree(x, y, z);
    camera.position.add(target.clone().sub(controls.target));
    controls.target.copy(target);
  }
  controls.update();
  renderer.render(scene, camera);
  if (now - lastHud > 250) {
    updateHud(now);
    lastHud = now;
  }
  requestAnimationFrame(frame);
}

async function start() {
  try {
    const cfg = await (await fetch('/config')).json();
    const [x, y, z] = cfg.operator_position;
    operator = enuToThree(x, y, z);
    for (const id of cfg.robots) robot(id);
  } catch (err) {
    console.warn('could not load /config, using defaults', err);
  }
  resize();
  setView('operator');
  connect();
  requestAnimationFrame(frame);
}

start();
