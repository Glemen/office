import * as THREE from 'three';
import { OrbitControls } from 'three/addons/OrbitControls.js';

// ============================================================
// 4 CHUYÊN VIÊN VĂN BẢN QUANH BÀN BIÊN TẬP GỖ ÓC CHÓ
// ============================================================
const WORKERS = [
  {
    id: 'BÀN 1',
    name: 'Minh',
    role: 'Nghiên cứu & Lập dàn ý',
    shirt: 0x1e3a5f,
    seatPos: new THREE.Vector3(-1.15, 0, -1.42),
    facingY: 0,
    laptopPos: new THREE.Vector3(-1.15, 0.79, -0.58),
    laptopRotY: Math.PI,
    status: 'idle',
    task: null,
    phaseLabel: null,
    elapsedSec: 0,
    lastResultId: null,
    error: null,
  },
  {
    id: 'BÀN 2',
    name: 'Lan',
    role: 'Chấp bút & Soạn thảo chính',
    shirt: 0x8c2d3b,
    seatPos: new THREE.Vector3(1.15, 0, -1.42),
    facingY: 0,
    laptopPos: new THREE.Vector3(1.15, 0.79, -0.58),
    laptopRotY: Math.PI,
    status: 'idle',
    task: null,
    phaseLabel: null,
    elapsedSec: 0,
    lastResultId: null,
    error: null,
  },
  {
    id: 'BÀN 3',
    name: 'Tuấn',
    role: 'Biên tập & Chuẩn thể thức',
    shirt: 0x3f4752,
    seatPos: new THREE.Vector3(-1.15, 0, 1.42),
    facingY: Math.PI,
    laptopPos: new THREE.Vector3(-1.15, 0.79, 0.58),
    laptopRotY: 0,
    status: 'idle',
    task: null,
    phaseLabel: null,
    elapsedSec: 0,
    lastResultId: null,
    error: null,
  },
  {
    id: 'BÀN 4',
    name: 'Vy',
    role: 'Tổng hợp & Xuất bản',
    shirt: 0x155e63,
    seatPos: new THREE.Vector3(1.15, 0, 1.42),
    facingY: Math.PI,
    laptopPos: new THREE.Vector3(1.15, 0.79, 0.58),
    laptopRotY: 0,
    status: 'idle',
    task: null,
    phaseLabel: null,
    elapsedSec: 0,
    lastResultId: null,
    error: null,
  },
];

const STATUS_META = {
  idle: { label: 'Đang chờ việc', color: 0xa8998a, css: '#8c7866' },
  working: { label: 'Đang biên soạn', color: 0x9a5b25, css: '#9a5b25' },
  done: { label: 'Đã có văn bản', color: 0x15803d, css: '#15803d' },
  error: { label: 'Có lỗi', color: 0xb91c1c, css: '#b91c1c' },
};

// ============================================================
// THREE.JS — PHÒNG BIÊN TẬP GỖ ẤM SANG TRỌNG (EDITORIAL STUDIO)
// ============================================================
const container = document.getElementById('canvas-wrap');
const scene = new THREE.Scene();
scene.background = new THREE.Color(0xeae3d7);

const renderer = new THREE.WebGLRenderer({ antialias: true, powerPreference: 'high-performance' });
renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
renderer.setSize(window.innerWidth, window.innerHeight);
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFSoftShadowMap;
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure = 1.06;
container.appendChild(renderer.domElement);

const camera = new THREE.PerspectiveCamera(36, window.innerWidth / window.innerHeight, 0.1, 100);
const DEFAULT_CAM_POS = new THREE.Vector3(6.8, 5.8, 7.8);
const DEFAULT_TARGET = new THREE.Vector3(0, 0.85, 0);
camera.position.copy(DEFAULT_CAM_POS);

const controls = new OrbitControls(camera, renderer.domElement);
controls.target.copy(DEFAULT_TARGET);
controls.enableDamping = true;
controls.dampingFactor = 0.06;
controls.maxPolarAngle = Math.PI / 2 - 0.06;
controls.minDistance = 4.5;
controls.maxDistance = 18;
controls.update();

// Ánh sáng ấm kiểu phòng biên tập ban ngày + đèn thả trần
scene.add(new THREE.HemisphereLight(0xfffaf0, 0xd4c3ae, 0.95));

const sunLight = new THREE.DirectionalLight(0xfff2dc, 1.55);
sunLight.position.set(7.5, 9.5, -3.5);
sunLight.castShadow = true;
sunLight.shadow.mapSize.set(2048, 2048);
sunLight.shadow.camera.near = 1;
sunLight.shadow.camera.far = 28;
sunLight.shadow.camera.left = -7.5;
sunLight.shadow.camera.right = 7.5;
sunLight.shadow.camera.top = 7.5;
sunLight.shadow.camera.bottom = -7.5;
sunLight.shadow.bias = -0.0004;
sunLight.shadow.radius = 3;
scene.add(sunLight);

const pendantLight = new THREE.PointLight(0xffe4b5, 2.2, 8.5, 1.6);
pendantLight.position.set(0, 2.55, 0);
scene.add(pendantLight);

// ============================================================
// TEXTURES & MATERIALS (SÀN GỖ XƯƠNG CÁ, GỖ ÓC CHÓ, ĐỒNG THAU, DA BÒ)
// ============================================================
function makeParquetTexture() {
  const c = document.createElement('canvas');
  c.width = 512;
  c.height = 512;
  const ctx = c.getContext('2d');
  ctx.fillStyle = '#d8be9a';
  ctx.fillRect(0, 0, 512, 512);
  const pw = 64;
  const ph = 256;
  for (let row = 0; row < 4; row++) {
    for (let col = 0; col < 8; col++) {
      const shade = ((row * 3 + col * 5) % 4) * 5 - 8;
      ctx.fillStyle = `rgb(${214 + shade}, ${184 + shade}, ${145 + shade})`;
      const x = col * pw;
      const y = (row * ph) / 2 + (col % 2) * 32;
      ctx.fillRect(x, y, pw - 2, ph / 2 - 2);
    }
  }
  const tex = new THREE.CanvasTexture(c);
  tex.wrapS = tex.wrapT = THREE.RepeatWrapping;
  tex.repeat.set(4, 4);
  tex.colorSpace = THREE.SRGBColorSpace;
  return tex;
}

function makeWalnutTexture() {
  const c = document.createElement('canvas');
  c.width = 512;
  c.height = 512;
  const ctx = c.getContext('2d');
  ctx.fillStyle = '#5c3d28';
  ctx.fillRect(0, 0, 512, 512);
  for (let y = 0; y < 512; y += 3) {
    const d = Math.sin(y * 0.06) * 10 + (Math.random() - 0.5) * 8;
    ctx.fillStyle = `rgba(${78 + d}, ${50 + d * 0.7}, ${32 + d * 0.5}, 0.45)`;
    ctx.fillRect(0, y, 512, 2);
  }
  const tex = new THREE.CanvasTexture(c);
  tex.wrapS = tex.wrapT = THREE.RepeatWrapping;
  tex.colorSpace = THREE.SRGBColorSpace;
  return tex;
}

const MAT = {
  floor: new THREE.MeshStandardMaterial({ map: makeParquetTexture(), roughness: 0.62, metalness: 0.02 }),
  rug: new THREE.MeshStandardMaterial({ color: 0xf4eee4, roughness: 0.95 }),
  wall: new THREE.MeshStandardMaterial({ color: 0xf6f2ea, roughness: 0.92 }),
  walnut: new THREE.MeshStandardMaterial({ map: makeWalnutTexture(), roughness: 0.46, metalness: 0.04 }),
  brass: new THREE.MeshStandardMaterial({ color: 0xc9a35d, roughness: 0.28, metalness: 0.82 }),
  leather: new THREE.MeshStandardMaterial({ color: 0x8f5633, roughness: 0.58 }),
  matteBlack: new THREE.MeshStandardMaterial({ color: 0x221f1c, roughness: 0.55 }),
  paper: new THREE.MeshStandardMaterial({ color: 0xffffff, roughness: 0.85 }),
  folder: new THREE.MeshStandardMaterial({ color: 0xe3c38c, roughness: 0.75 }),
  silver: new THREE.MeshStandardMaterial({ color: 0xd6d3cd, roughness: 0.28, metalness: 0.65 }),
  skin: new THREE.MeshStandardMaterial({ color: 0xe5b898, roughness: 0.65 }),
  hair: new THREE.MeshStandardMaterial({ color: 0x201914, roughness: 0.8 }),
  pants: new THREE.MeshStandardMaterial({ color: 0x292524, roughness: 0.85 }),
  leaf: new THREE.MeshStandardMaterial({ color: 0x2e6438, roughness: 0.62 }),
  pot: new THREE.MeshStandardMaterial({ color: 0xd6cdc0, roughness: 0.78 }),
  lampGlow: new THREE.MeshStandardMaterial({
    color: 0xfff3d6,
    emissive: 0xffd58a,
    emissiveIntensity: 1.5,
    roughness: 0.2,
  }),
  windowGlass: new THREE.MeshStandardMaterial({
    color: 0xfff6e5,
    emissive: 0xffeacc,
    emissiveIntensity: 0.65,
    roughness: 0.1,
  }),
};

function box(w, h, d, m, x, y, z, parent = scene, cast = true, receive = true) {
  const mesh = new THREE.Mesh(new THREE.BoxGeometry(w, h, d), m);
  mesh.position.set(x, y, z);
  mesh.castShadow = cast;
  mesh.receiveShadow = receive;
  parent.add(mesh);
  return mesh;
}

// ============================================================
// KIẾN TRÚC PHÒNG BIÊN TẬP
// ============================================================
box(13.6, 0.16, 11.2, MAT.floor, 0, -0.08, 0, scene, false, true);
// Thảm trải sàn màu kem dưới bàn họp
box(5.6, 0.015, 4.4, MAT.rug, 0, 0.008, 0, scene, false, true);

// Tường sau (-Z) và tường trái (-X) + nẹp gỗ óc chó & đồng thau
box(13.6, 4.2, 0.2, MAT.wall, 0, 2.1, -5.2, scene, false, true);
box(0.2, 4.2, 11.2, MAT.wall, -6.2, 2.1, 0, scene, false, true);
box(13.4, 0.9, 0.06, MAT.walnut, 0, 0.45, -5.08, scene, false, true);
box(13.4, 0.035, 0.07, MAT.brass, 0, 0.91, -5.07, scene, false, false);
box(0.06, 0.9, 11.0, MAT.walnut, -6.08, 0.45, 0, scene, false, true);
box(0.07, 0.035, 11.0, MAT.brass, -6.07, 0.91, 0, scene, false, false);

// Cửa sổ lớn tường sau-phải đón nắng ấm
const winGroup = new THREE.Group();
winGroup.position.set(3.2, 2.35, -5.07);
scene.add(winGroup);
box(4.4, 2.8, 0.06, MAT.windowGlass, 0, 0, 0, winGroup, false, false);
box(4.55, 0.09, 0.12, MAT.matteBlack, 0, 1.4, 0.02, winGroup, false, false);
box(4.55, 0.09, 0.12, MAT.matteBlack, 0, -1.4, 0.02, winGroup, false, false);
for (const wx of [-2.22, -0.74, 0.74, 2.22]) {
  box(0.08, 2.8, 0.12, MAT.matteBlack, wx, 0, 0.02, winGroup, false, false);
}

// Tủ thư viện hồ sơ gỗ óc chó tường sau-trái
const library = new THREE.Group();
library.position.set(-3.2, 0, -4.75);
scene.add(library);
box(3.4, 2.7, 0.48, MAT.walnut, 0, 1.35, 0, library);
const binderColors = [0x1e3a5f, 0x8c2d3b, 0x2f5d50, 0x9a5b25, 0x4b5563, 0xd6cdc0];
for (const sy of [0.95, 1.55, 2.15]) {
  box(3.22, 0.04, 0.46, MAT.walnut, 0, sy - 0.22, 0.02, library, false, true);
  for (let b = 0; b < 14; b++) {
    const bx = -1.42 + b * 0.21;
    if (b === 6 || b === 11) continue;
    box(
      0.085,
      0.34 + (b % 3) * 0.04,
      0.26,
      new THREE.MeshStandardMaterial({ color: binderColors[(b + Math.round(sy * 3)) % binderColors.length], roughness: 0.72 }),
      bx,
      sy - 0.02,
      0.08,
      library
    );
  }
}

// Bảng Quy Trình Biên Tập Live trên tường trái (CanvasTexture cập nhật trực tiếp!)
const boardCanvas = document.createElement('canvas');
boardCanvas.width = 512;
boardCanvas.height = 300;
const boardCtx = boardCanvas.getContext('2d');
const boardTex = new THREE.CanvasTexture(boardCanvas);
boardTex.colorSpace = THREE.SRGBColorSpace;

const boardGroup = new THREE.Group();
boardGroup.position.set(-6.05, 2.35, -0.2);
boardGroup.rotation.y = Math.PI / 2;
scene.add(boardGroup);
box(2.75, 1.65, 0.06, MAT.walnut, 0, 0, 0, boardGroup);
const boardScreen = new THREE.Mesh(
  new THREE.PlaneGeometry(2.58, 1.48),
  new THREE.MeshBasicMaterial({ map: boardTex })
);
boardScreen.position.z = 0.035;
boardGroup.add(boardScreen);

let pipelineInfo = { active: false, phase: 'idle', message: 'Sẵn sàng nhận lệnh' };

function redrawEditorialBoard() {
  const ctx = boardCtx;
  ctx.fillStyle = '#fffdf9';
  ctx.fillRect(0, 0, 512, 300);
  ctx.fillStyle = '#5c3d28';
  ctx.fillRect(0, 0, 512, 46);
  ctx.fillStyle = '#fffdf9';
  ctx.font = 'bold 20px sans-serif';
  ctx.fillText('BẢNG ĐIỀU PHỐI BIÊN TẬP VĂN BẢN', 20, 30);

  WORKERS.forEach((w, i) => {
    const y = 74 + i * 44;
    const meta = STATUS_META[w.status] || STATUS_META.idle;
    ctx.fillStyle = '#f5efe6';
    ctx.fillRect(20, y - 22, 472, 34);
    ctx.fillStyle = meta.css;
    ctx.beginPath();
    ctx.arc(38, y - 5, 7, 0, Math.PI * 2);
    ctx.fill();
    ctx.fillStyle = '#1f1914';
    ctx.font = 'bold 16px sans-serif';
    ctx.fillText(`${w.name} (${w.role})`, 56, y);
    ctx.fillStyle = meta.css;
    ctx.font = '14px sans-serif';
    const stText = w.status === 'working' ? `${w.phaseLabel || 'Đang làm'} (${w.elapsedSec}s)` : meta.label;
    ctx.fillText(stText, 315, y);
  });

  ctx.fillStyle = '#6c5e52';
  ctx.font = '15px sans-serif';
  ctx.fillText((pipelineInfo.message || '').slice(0, 54), 22, 276);
  boardTex.needsUpdate = true;
}

// Góc máy in & kệ giấy A4 ở phía sau-phải
const printCorner = new THREE.Group();
printCorner.position.set(4.5, 0, -3.6);
scene.add(printCorner);
box(1.1, 0.78, 0.65, MAT.walnut, 0, 0.39, 0, printCorner);
box(0.58, 0.36, 0.48, MAT.matteBlack, 0, 0.96, 0, printCorner);
box(0.28, 0.04, 0.24, MAT.paper, 0, 1.15, 0.06, printCorner); // giấy A4 trên khay

// Cây Bàng Singapore xanh mướt
function addFiddlePlant(x, z, scale = 1) {
  const g = new THREE.Group();
  g.position.set(x, 0, z);
  scene.add(g);
  const pot = new THREE.Mesh(new THREE.CylinderGeometry(0.26 * scale, 0.21 * scale, 0.46 * scale, 18), MAT.pot);
  pot.position.y = 0.23 * scale;
  pot.castShadow = true;
  g.add(pot);
  const stem = new THREE.Mesh(new THREE.CylinderGeometry(0.03 * scale, 0.04 * scale, 0.95 * scale, 8), MAT.walnut);
  stem.position.y = 0.7 * scale;
  g.add(stem);
  for (let i = 0; i < 9; i++) {
    const a = (i / 9) * Math.PI * 2;
    const leaf = new THREE.Mesh(new THREE.SphereGeometry(0.18 * scale, 12, 10), MAT.leaf);
    leaf.scale.set(0.8, 1.4, 0.35);
    leaf.position.set(Math.cos(a) * 0.22 * scale, (0.95 + (i % 3) * 0.22) * scale, Math.sin(a) * 0.22 * scale);
    leaf.rotation.z = -Math.cos(a) * 0.5;
    leaf.rotation.x = Math.sin(a) * 0.5;
    leaf.castShadow = true;
    g.add(leaf);
  }
}
addFiddlePlant(-5.2, -4.2, 1.1);
addFiddlePlant(-5.2, 3.3, 0.95);

// ============================================================
// BÀN BIÊN TẬP GỖ ÓC CHÓ TRUNG TÂM + ĐÈN THẢ ĐỒNG THAU
// ============================================================
const tableGroup = new THREE.Group();
scene.add(tableGroup);
box(4.2, 0.07, 1.75, MAT.walnut, 0, 0.74, 0, tableGroup);
// Viền đồng thau tinh tế chạy quanh cạnh bàn
box(4.22, 0.015, 1.77, MAT.brass, 0, 0.71, 0, tableGroup, false, false);
// 2 chân bàn chữ U màu đen mờ
for (const lx of [-1.55, 1.55]) {
  box(0.08, 0.71, 1.32, MAT.matteBlack, lx, 0.355, 0, tableGroup);
}

// Đèn thả trần đồng thau thanh mảnh
const lampGroup = new THREE.Group();
lampGroup.position.set(0, 2.75, 0);
scene.add(lampGroup);
box(2.6, 0.06, 0.14, MAT.brass, 0, 0, 0, lampGroup, false, false);
box(2.5, 0.02, 0.10, MAT.lampGlow, 0, -0.035, 0, lampGroup, false, false);
for (const cx of [-0.95, 0.95]) {
  box(0.015, 1.4, 0.015, MAT.matteBlack, cx, 0.72, 0, lampGroup, false, false);
}

// Tài liệu, tập hồ sơ & lọ hoa nhỏ trên mặt bàn
box(0.24, 0.03, 0.32, MAT.paper, -0.15, 0.79, -0.1, tableGroup);
box(0.26, 0.025, 0.34, MAT.folder, 0.18, 0.79, 0.12, tableGroup);
const vase = new THREE.Mesh(new THREE.CylinderGeometry(0.06, 0.08, 0.18, 16), MAT.pot);
vase.position.set(0, 0.86, 0);
tableGroup.add(vase);
const centerpiece = new THREE.Mesh(new THREE.SphereGeometry(0.11, 12, 10), MAT.leaf);
centerpiece.position.set(0, 1.0, 0);
tableGroup.add(centerpiece);

// ============================================================
// GHẾ DA BÒ + LAPTOP + 4 CHUYÊN VIÊN + HIỆU ỨNG TRUYỀN DỮ LIỆU KHI TỔNG HỢP
// ============================================================
function createStudioChair(pos, rotY) {
  const g = new THREE.Group();
  g.position.copy(pos);
  g.rotation.y = rotY;
  scene.add(g);
  for (const [lx, lz] of [[-0.22, -0.22], [0.22, -0.22], [-0.22, 0.22], [0.22, 0.22]]) {
    box(0.04, 0.44, 0.04, MAT.walnut, lx, 0.22, lz, g);
  }
  box(0.50, 0.08, 0.48, MAT.leather, 0, 0.46, 0, g);
  box(0.48, 0.50, 0.07, MAT.leather, 0, 0.74, -0.22, g);
  for (const ax of [-0.24, 0.24]) {
    box(0.04, 0.18, 0.04, MAT.walnut, ax, 0.56, -0.02, g);
    box(0.05, 0.035, 0.30, MAT.walnut, ax, 0.66, 0.0, g);
  }
}

function createLaptop(pos, rotY, worker) {
  const g = new THREE.Group();
  g.position.copy(pos);
  g.rotation.y = rotY;
  scene.add(g);
  box(0.36, 0.015, 0.25, MAT.silver, 0, 0, 0, g);
  box(0.30, 0.005, 0.13, MAT.matteBlack, 0, 0.01, 0.02, g, false, false);

  const lid = new THREE.Group();
  lid.position.set(0, 0.01, -0.12);
  lid.rotation.x = -0.25;
  g.add(lid);
  box(0.36, 0.24, 0.01, MAT.silver, 0, 0.12, 0, lid);

  const canvas = document.createElement('canvas');
  canvas.width = 256;
  canvas.height = 168;
  const ctx = canvas.getContext('2d');
  const tex = new THREE.CanvasTexture(canvas);
  tex.colorSpace = THREE.SRGBColorSpace;
  const screenMesh = new THREE.Mesh(
    new THREE.PlaneGeometry(0.33, 0.21),
    new THREE.MeshBasicMaterial({ map: tex })
  );
  screenMesh.position.set(0, 0.12, 0.007);
  lid.add(screenMesh);

  function redrawScreen(t) {
    const meta = STATUS_META[worker.status] || STATUS_META.idle;
    ctx.fillStyle = worker.status === 'idle' ? '#faf6f0' : '#1f1914';
    ctx.fillRect(0, 0, 256, 168);

    if (worker.status === 'idle') {
      ctx.fillStyle = '#9a5b25';
      ctx.font = 'bold 17px sans-serif';
      ctx.fillText(worker.name.toUpperCase(), 18, 44);
      ctx.fillStyle = '#6c5e52';
      ctx.font = '15px sans-serif';
      ctx.fillText('Sẵn sàng soạn thảo', 18, 84);
      ctx.fillStyle = '#e5dacb';
      ctx.fillRect(18, 108, 220, 6);
    } else {
      ctx.fillStyle = meta.css;
      ctx.fillRect(0, 0, 256, 28);
      ctx.fillStyle = '#ffffff';
      ctx.font = 'bold 13px monospace';
      ctx.fillText(`${worker.name} • ${(worker.phaseLabel || meta.label).slice(0, 18)}`, 10, 19);

      ctx.fillStyle = '#f5efe6';
      ctx.font = '14px sans-serif';
      ctx.fillText((worker.task || '').slice(0, 26), 12, 60);

      if (worker.status === 'working') {
        const barX = 12 + ((t * 95) % 160);
        ctx.fillStyle = '#3f342b';
        ctx.fillRect(12, 80, 232, 12);
        ctx.fillStyle = '#d99b52';
        ctx.fillRect(barX, 80, 72, 12);
        ctx.fillStyle = '#e6c79c';
        ctx.font = '12px monospace';
        ctx.fillText(`Đang biên soạn (${worker.elapsedSec}s)...`, 12, 122);
      } else if (worker.status === 'done') {
        ctx.fillStyle = '#4ade80';
        ctx.font = 'bold 15px sans-serif';
        ctx.fillText('✓ Đã hoàn thành văn bản', 12, 106);
      } else {
        ctx.fillStyle = '#f87171';
        ctx.font = '13px sans-serif';
        ctx.fillText('Có lỗi khi xử lý', 12, 106);
      }
    }
    tex.needsUpdate = true;
  }

  return { redrawScreen };
}

const workerRigs = [];
const clickable = [];

WORKERS.forEach((w, idx) => {
  createStudioChair(w.seatPos, w.facingY);
  const laptop = createLaptop(w.laptopPos, w.laptopRotY, w);

  const ringMat = new THREE.MeshBasicMaterial({
    color: 0x9a5b25,
    transparent: true,
    opacity: 0,
    side: THREE.DoubleSide,
  });
  const ring = new THREE.Mesh(new THREE.RingGeometry(0.54, 0.64, 32), ringMat);
  ring.rotation.x = -Math.PI / 2;
  ring.position.set(w.seatPos.x, 0.02, w.seatPos.z);
  scene.add(ring);

  const person = new THREE.Group();
  person.position.copy(w.seatPos);
  person.rotation.y = w.facingY;
  scene.add(person);

  const shirtMat = new THREE.MeshStandardMaterial({ color: w.shirt, roughness: 0.7 });
  box(0.36, 0.11, 0.40, MAT.pants, 0, 0.56, 0.12, person);
  box(0.36, 0.48, 0.11, MAT.pants, 0, 0.28, 0.30, person);

  const upperBody = new THREE.Group();
  upperBody.position.set(0, 0.60, 0);
  person.add(upperBody);

  const torso = new THREE.Mesh(new THREE.CylinderGeometry(0.17, 0.19, 0.58, 16), shirtMat);
  torso.position.y = 0.29;
  torso.castShadow = true;
  upperBody.add(torso);

  const armL = new THREE.Group();
  armL.position.set(-0.22, 0.46, 0.02);
  const armLMesh = new THREE.Mesh(new THREE.CylinderGeometry(0.048, 0.045, 0.48, 12), shirtMat);
  armLMesh.rotation.x = Math.PI / 2.2;
  armLMesh.position.set(0.02, -0.08, 0.22);
  armLMesh.castShadow = true;
  armL.add(armLMesh);
  upperBody.add(armL);

  const armR = new THREE.Group();
  armR.position.set(0.22, 0.46, 0.02);
  const armRMesh = new THREE.Mesh(new THREE.CylinderGeometry(0.048, 0.045, 0.48, 12), shirtMat);
  armRMesh.rotation.x = Math.PI / 2.2;
  armRMesh.position.set(-0.02, -0.08, 0.22);
  armRMesh.castShadow = true;
  armR.add(armRMesh);
  upperBody.add(armR);

  const headGroup = new THREE.Group();
  headGroup.position.set(0, 0.68, 0);
  upperBody.add(headGroup);

  const head = new THREE.Mesh(new THREE.SphereGeometry(0.14, 18, 14), MAT.skin);
  head.scale.set(0.95, 1.08, 0.95);
  head.castShadow = true;
  headGroup.add(head);

  const hair = new THREE.Mesh(new THREE.SphereGeometry(0.145, 16, 12), MAT.hair);
  hair.scale.set(1.0, 0.65, 1.0);
  hair.position.set(0, 0.06, -0.02);
  headGroup.add(hair);

  const badgeMat = new THREE.MeshBasicMaterial({ color: STATUS_META.idle.color });
  const badge = new THREE.Mesh(new THREE.SphereGeometry(0.065, 16, 12), badgeMat);
  badge.position.set(0, 1.66, 0);
  person.add(badge);

  const hitbox = new THREE.Mesh(
    new THREE.CylinderGeometry(0.55, 0.55, 1.65, 12),
    new THREE.MeshBasicMaterial({ visible: false })
  );
  hitbox.position.set(0, 0.85, 0.2);
  hitbox.userData.workerIndex = idx;
  clickable.push(hitbox);
  person.add(hitbox);

  workerRigs.push({
    worker: w,
    upperBody,
    headGroup,
    armL,
    armR,
    badge,
    badgeMat,
    ringMat,
    laptop,
    focusTarget: new THREE.Vector3(w.seatPos.x * 0.65, 0.85, w.seatPos.z * 0.55),
  });
});

// Quả cầu ánh sáng chuyển tài liệu sang Vy (Bàn 4) trong Pha 2
const syncOrbs = [0, 1, 2].map((srcIdx) => {
  const orb = new THREE.Mesh(
    new THREE.SphereGeometry(0.06, 14, 12),
    new THREE.MeshBasicMaterial({ color: 0xd99b52 })
  );
  orb.visible = false;
  scene.add(orb);
  return { orb, srcIdx };
});

// ============================================================
// QUẢN LÝ UI/UX, PHÂN CÔNG THÔNG MINH, WORD EXPORT & CÀI ĐẶT AI
// ============================================================
let selectedIdx = -1;
let autoOrbit = false;
let camLerpTarget = null;
let allResults = [];
let currentDialogData = null;

const elSummary = document.getElementById('office-summary');
const elOfficeDot = document.getElementById('office-dot');
const elEngineBadge = document.getElementById('engine-badge');
const elClock = document.getElementById('live-clock');
const elStationDock = document.getElementById('station-dock');
const elToastStack = document.getElementById('toast-stack');

const elResultsDrawer = document.getElementById('results-drawer');
const elGlobalResults = document.getElementById('global-results');
const elResultsCount = document.getElementById('results-count');
const btnToggleResults = document.getElementById('btn-toggle-results');

const elInspector = document.getElementById('inspector');
const elInspId = document.getElementById('insp-id');
const elInspName = document.getElementById('insp-name');
const elInspRole = document.getElementById('insp-role');
const elInspStatus = document.getElementById('insp-status');
const elInspTask = document.getElementById('insp-task');
const elInspWorkingBar = document.getElementById('insp-working-bar');
const elInspElapsed = document.getElementById('insp-elapsed');
const elInspWorkingActions = document.getElementById('insp-working-actions');
const elInspDoneActions = document.getElementById('insp-done-actions');
const btnCancelTask = document.getElementById('btn-cancel-task');
const btnViewLastResult = document.getElementById('btn-view-last-result');
const elInspAssignForm = document.getElementById('insp-assign-form');
const elInspAssignInput = document.getElementById('insp-assign-input');
const elInspDoneCount = document.getElementById('insp-done-count');
const elInspHistory = document.getElementById('insp-history');

const elCmdForm = document.getElementById('command-form');
const elCmdAssignee = document.getElementById('cmd-assignee');
const elCmdInput = document.getElementById('cmd-input');
const elModeRadios = document.querySelectorAll('input[name="dispatch-mode"]');

const elResDialog = document.getElementById('result-dialog');
const elResWorker = document.getElementById('res-dialog-worker');
const elResTitle = document.getElementById('res-dialog-title');
const elResMeta = document.getElementById('res-dialog-meta');
const elResContent = document.getElementById('res-dialog-content');
const elResFile = document.getElementById('res-dialog-file');
const btnResDownload = document.getElementById('btn-res-download');

const elSetDialog = document.getElementById('settings-dialog');
const elSetForm = document.getElementById('settings-form');
const elCfgProvider = document.getElementById('cfg-provider');
const elCfgGeminiKey = document.getElementById('cfg-gemini-key');
const elCfgGeminiModel = document.getElementById('cfg-gemini-model');
const elCfgOpenaiUrl = document.getElementById('cfg-openai-url');
const elCfgOpenaiModel = document.getElementById('cfg-openai-model');
const elCfgOpenaiKey = document.getElementById('cfg-openai-key');
const elCfgArchiveAgy = document.getElementById('cfg-archive-agy');
const elCfgStatusHint = document.getElementById('cfg-status-hint');

WORKERS.forEach((w, i) => {
  const opt = document.createElement('option');
  opt.value = String(i);
  opt.textContent = `${w.id} — ${w.name} (${w.role})`;
  elCmdAssignee.appendChild(opt);
});

elModeRadios.forEach((r) => {
  r.addEventListener('change', () => {
    elCmdAssignee.classList.toggle('hidden', r.value !== 'direct');
  });
});

function getDispatchMode() {
  const checked = document.querySelector('input[name="dispatch-mode"]:checked');
  return checked ? checked.value : 'auto-best';
}

function showToast(msg, onClick = null) {
  const t = document.createElement('div');
  t.className = 'toast';
  t.textContent = msg;
  if (onClick) {
    t.addEventListener('click', () => {
      onClick();
      t.remove();
    });
  }
  elToastStack.appendChild(t);
  setTimeout(() => t.remove(), 5500);
}

// Fallback bắt buộc cho <dialog closedby="any">
function bindDialogLightDismissFallback(dialog) {
  if ('closedBy' in HTMLDialogElement.prototype) return;
  dialog.addEventListener('click', (event) => {
    if (event.target !== dialog) return;
    const rect = dialog.getBoundingClientRect();
    const inside =
      rect.top <= event.clientY &&
      event.clientY <= rect.top + rect.height &&
      rect.left <= event.clientX &&
      event.clientX <= rect.left + rect.width;
    if (!inside) dialog.close();
  });
}
bindDialogLightDismissFallback(elResDialog);
bindDialogLightDismissFallback(elSetDialog);

function renderMarkdownSafe(md) {
  const esc = (s) => s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
  const lines = md.split(/\r?\n/);
  let html = '';
  let inCode = false;
  let inList = false;

  for (const raw of lines) {
    if (raw.trim().startsWith('```')) {
      if (inList) { html += '</ul>'; inList = false; }
      html += inCode ? '</code></pre>' : '<pre><code>';
      inCode = !inCode;
      continue;
    }
    if (inCode) { html += esc(raw) + '\n'; continue; }
    const line = esc(raw)
      .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
      .replace(/`([^`]+)`/g, '<code>$1</code>');

    if (/^###\s+/.test(raw)) {
      if (inList) { html += '</ul>'; inList = false; }
      html += `<h3>${line.replace(/^###\s+/, '')}</h3>`;
    } else if (/^##\s+/.test(raw)) {
      if (inList) { html += '</ul>'; inList = false; }
      html += `<h2>${line.replace(/^##\s+/, '')}</h2>`;
    } else if (/^#\s+/.test(raw)) {
      if (inList) { html += '</ul>'; inList = false; }
      html += `<h1>${line.replace(/^#\s+/, '')}</h1>`;
    } else if (/^\s*[-*]\s+/.test(raw)) {
      if (!inList) { html += '<ul>'; inList = true; }
      html += `<li>${line.replace(/^\s*[-*]\s+/, '')}</li>`;
    } else if (raw.trim() === '') {
      if (inList) { html += '</ul>'; inList = false; }
    } else {
      if (inList) { html += '</ul>'; inList = false; }
      html += `<p>${line}</p>`;
    }
  }
  if (inList) html += '</ul>';
  if (inCode) html += '</code></pre>';
  return html || '<p><em>(Trống)</em></p>';
}

async function openResult(resultId) {
  try {
    const resp = await fetch(`/api/result/${encodeURIComponent(resultId)}`);
    if (!resp.ok) throw new Error('Không tải được văn bản');
    const data = await resp.json();
    currentDialogData = data;
    elResWorker.textContent = `${data.workerId} • ${data.workerName} (${data.modeLabel || data.workerRole})`;
    elResTitle.textContent = data.task;
    elResMeta.textContent = `Hoàn thành lúc ${data.completedAt}`;
    elResContent.innerHTML = renderMarkdownSafe(data.content || '');
    elResFile.textContent = `results/${data.filename}`;
    btnResDownload.href = `/results/${encodeURIComponent(data.filename)}`;
    btnResDownload.setAttribute('download', data.filename);
    elResDialog.showModal();
  } catch (err) {
    showToast(`Lỗi mở văn bản: ${err.message}`);
  }
}

document.getElementById('btn-res-close').addEventListener('click', () => elResDialog.close());
document.getElementById('btn-res-copy').addEventListener('click', async () => {
  if (!currentDialogData) return;
  await navigator.clipboard.writeText(currentDialogData.content || '');
  showToast('Đã copy toàn bộ văn bản!');
});

// Xuất trực tiếp sang file Word (.doc) mở đẹp ngay trên Microsoft Word
document.getElementById('btn-res-word').addEventListener('click', () => {
  if (!currentDialogData) return;
  const htmlBody = renderMarkdownSafe(currentDialogData.content || '');
  const wordDoc = `<!DOCTYPE html>
<html xmlns:o="urn:schemas-microsoft-com:office:office" xmlns:w="urn:schemas-microsoft-com:office:word" lang="vi">
<head><meta charset="utf-8"><title>${currentDialogData.task}</title>
<style>
  body { font-family: "Times New Roman", serif; font-size: 13pt; line-height: 1.5; color: #111; margin: 2cm; }
  h1 { font-size: 16pt; margin-bottom: 10pt; }
  h2 { font-size: 14pt; margin-top: 14pt; }
  h3 { font-size: 13pt; margin-top: 10pt; }
  p, li { margin: 5pt 0; }
</style></head>
<body>${htmlBody}</body></html>`;
  const blob = new Blob(['\ufeff', wordDoc], { type: 'application/msword;charset=utf-8' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = currentDialogData.filename.replace(/\.md$/, '.doc');
  a.click();
  URL.revokeObjectURL(url);
  showToast('Đã tải file Word (.doc) — mở trực tiếp bằng Microsoft Word!');
});

// Cài đặt AI cho máy tính khác
async function openSettings() {
  try {
    const resp = await fetch('/api/config');
    const cfg = await resp.json();
    elCfgProvider.value = cfg.provider || 'auto';
    elCfgGeminiKey.value = '';
    elCfgGeminiKey.placeholder = cfg.hasGeminiKey ? 'Đã lưu key (nhập mới để thay)' : 'AIza...';
    elCfgGeminiModel.value = cfg.geminiModel || 'gemini-2.5-flash';
    elCfgOpenaiUrl.value = cfg.openaiBaseUrl || 'http://localhost:11434/v1';
    elCfgOpenaiModel.value = cfg.openaiModel || 'qwen2.5:7b';
    elCfgOpenaiKey.value = '';
    elCfgArchiveAgy.checked = cfg.archiveAntigravity !== false;
    elCfgStatusHint.textContent = `Đang dùng: ${cfg.activeProvider.toUpperCase()}`;
    elSetDialog.showModal();
  } catch {
    showToast('Không tải được cấu hình AI');
  }
}

document.getElementById('btn-open-settings').addEventListener('click', openSettings);
document.getElementById('btn-set-close').addEventListener('click', () => elSetDialog.close());
document.getElementById('btn-set-cancel').addEventListener('click', () => elSetDialog.close());

elSetForm.addEventListener('submit', async (e) => {
  e.preventDefault();
  const payload = {
    provider: elCfgProvider.value,
    geminiApiKey: elCfgGeminiKey.value.trim(),
    geminiModel: elCfgGeminiModel.value.trim(),
    openaiBaseUrl: elCfgOpenaiUrl.value.trim(),
    openaiModel: elCfgOpenaiModel.value.trim(),
    openaiApiKey: elCfgOpenaiKey.value.trim(),
    archiveAntigravity: elCfgArchiveAgy.checked,
  };
  const resp = await fetch('/api/config', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  const data = await resp.json();
  showToast(`Đã lưu cài đặt! Nguồn AI hiện tại: ${(data.activeProvider || 'none').toUpperCase()}`);
  elSetDialog.close();
  syncState();
});

const PROVIDER_LABELS = {
  antigravity: 'Antigravity Live',
  gemini: 'Gemini API',
  openai: 'Ollama / OpenAI',
  none: 'Chưa cấu hình AI',
};

function updateSummary() {
  const working = WORKERS.filter((w) => w.status === 'working').length;
  const idle = WORKERS.length - working;
  if (working === 0) {
    elSummary.textContent = `${idle}/4 chuyên viên đang chờ việc`;
    elOfficeDot.classList.remove('active');
  } else if (pipelineInfo.active && pipelineInfo.mode === 'split-merge') {
    elSummary.textContent = pipelineInfo.message || `${working} chuyên viên đang phối hợp`;
    elOfficeDot.classList.add('active');
  } else {
    elSummary.textContent = `${working}/4 đang soạn thảo • ${idle} sẵn sàng`;
    elOfficeDot.classList.add('active');
  }
}

function renderStationDock() {
  elStationDock.innerHTML = '';
  WORKERS.forEach((w, i) => {
    const btn = document.createElement('button');
    btn.type = 'button';
    btn.className = `station-pill${i === selectedIdx ? ' selected' : ''}`;
    const sub =
      w.status === 'working'
        ? `${w.phaseLabel || 'Đang làm'} (${w.elapsedSec}s)`
        : w.status === 'done'
        ? '✓ Đã xong — bấm xem'
        : w.role;
    btn.innerHTML = `
      <span class="pill-dot ${w.status}"></span>
      <span>
        <strong>${w.name}</strong>
        <span class="pill-sub">${sub}</span>
      </span>
    `;
    btn.addEventListener('click', () => selectWorker(i, true));
    elStationDock.appendChild(btn);
  });
}

function renderGlobalResults() {
  elResultsCount.textContent = String(allResults.length);
  elGlobalResults.innerHTML = '';
  if (allResults.length === 0) {
    elGlobalResults.innerHTML =
      '<li class="empty-state">Chưa có văn bản nào. Hãy nhập yêu cầu ở thanh bên dưới để giao việc.</li>';
    return;
  }
  allResults.forEach((r) => {
    const li = document.createElement('li');
    li.className = 'result-item';
    li.innerHTML = `
      <div class="result-item-title">${r.task}</div>
      <div class="result-item-meta">${r.workerName} • ${r.modeLabel || r.workerRole} • ${r.completedAt}</div>
      <div class="result-item-preview">${r.preview || ''}</div>
    `;
    li.addEventListener('click', () => openResult(r.id));
    elGlobalResults.appendChild(li);
  });
}

function renderInspector() {
  if (selectedIdx < 0) return;
  const w = WORKERS[selectedIdx];
  const meta = STATUS_META[w.status] || STATUS_META.idle;

  elInspId.textContent = w.id;
  elInspName.textContent = w.name;
  elInspRole.textContent = w.role;
  elInspStatus.textContent = meta.label;
  elInspStatus.className = `state-badge ${w.status}`;

  elInspWorkingBar.classList.toggle('hidden', w.status !== 'working');
  elInspWorkingActions.classList.toggle('hidden', w.status !== 'working');
  elInspDoneActions.classList.toggle('hidden', !(w.status === 'done' && w.lastResultId));

  if (w.status === 'idle') {
    elInspTask.textContent = 'Chưa được giao việc — sẵn sàng nhận lệnh.';
  } else if (w.status === 'working') {
    elInspTask.textContent = w.task;
    elInspElapsed.textContent = `${w.phaseLabel || 'Đang xử lý'} (${w.elapsedSec}s)...`;
  } else if (w.status === 'done') {
    elInspTask.textContent = `✓ Đã hoàn thành: ${w.task}`;
  } else {
    elInspTask.textContent = `Lỗi: ${w.error || 'Không xác định'}`;
  }

  const mine = allResults.filter((r) => r.workerIndex === selectedIdx);
  elInspDoneCount.textContent = String(mine.length);
  elInspHistory.innerHTML = '';
  if (mine.length === 0) {
    elInspHistory.innerHTML = '<li class="empty-state">Chưa có văn bản nào.</li>';
  } else {
    mine.slice(0, 6).forEach((r) => {
      const li = document.createElement('li');
      li.className = 'result-item';
      li.innerHTML = `
        <div class="result-item-title">${r.task}</div>
        <div class="result-item-meta">${r.completedAt} • Bấm mở văn bản</div>
      `;
      li.addEventListener('click', () => openResult(r.id));
      elInspHistory.appendChild(li);
    });
  }
}

function selectWorker(idx, focusCam = false) {
  selectedIdx = idx;
  elInspector.classList.remove('hidden');
  workerRigs.forEach((r, i) => { r.ringMat.opacity = i === idx ? 0.78 : 0; });
  renderInspector();
  renderStationDock();
  if (focusCam) camLerpTarget = workerRigs[idx].focusTarget.clone();
}

function closeInspector() {
  selectedIdx = -1;
  elInspector.classList.add('hidden');
  workerRigs.forEach((r) => { r.ringMat.opacity = 0; });
  renderStationDock();
}

async function syncState() {
  try {
    const resp = await fetch('/api/state', { cache: 'no-store' });
    if (!resp.ok) return;
    const data = await resp.json();

    const prov = data.provider || 'none';
    elEngineBadge.textContent = PROVIDER_LABELS[prov] || prov;
    elEngineBadge.classList.toggle('offline', prov === 'none');

    pipelineInfo = data.pipeline || pipelineInfo;
    allResults = data.results || [];

    (data.workers || []).forEach((sw, i) => {
      const prevStatus = WORKERS[i].status;
      WORKERS[i].status = sw.status;
      WORKERS[i].task = sw.task;
      WORKERS[i].phaseLabel = sw.phaseLabel;
      WORKERS[i].elapsedSec = sw.elapsedSec || 0;
      WORKERS[i].lastResultId = sw.lastResultId;
      WORKERS[i].error = sw.error;

      const meta = STATUS_META[sw.status] || STATUS_META.idle;
      workerRigs[i].badgeMat.color.setHex(meta.color);

      if (prevStatus === 'working' && sw.status === 'done' && sw.lastResultId) {
        const rid = sw.lastResultId;
        showToast(`✓ ${WORKERS[i].name} đã hoàn thành văn bản! Bấm để đọc & tải Word`, () => openResult(rid));
      }
    });

    updateSummary();
    renderStationDock();
    renderGlobalResults();
    redrawEditorialBoard();
    if (selectedIdx >= 0) renderInspector();
  } catch {
    elEngineBadge.textContent = 'Mất kết nối server';
    elEngineBadge.classList.add('offline');
  }
}

async function dispatchTask(mode, taskText, workerIndex = null) {
  try {
    const resp = await fetch('/api/assign', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ mode, task: taskText, workerIndex }),
    });
    const data = await resp.json();
    if (!resp.ok) {
      showToast(data.error || 'Không thể giao việc');
      return;
    }
    if (mode === 'split-merge') {
      showToast('Đã chia nhiệm vụ lớn: Minh, Lan, Tuấn làm song song → Vy tổng hợp!');
      camLerpTarget = DEFAULT_TARGET.clone();
    } else if (mode === 'auto-best') {
      showToast(`Đã chọn ${data.workerName} (${data.reason})`);
      selectWorker(data.workerIndex, true);
    } else {
      showToast(`Đã giao trực tiếp cho ${WORKERS[data.workerIndex].name}`);
      selectWorker(data.workerIndex, true);
    }
    await syncState();
  } catch (err) {
    showToast(`Lỗi kết nối server: ${err.message}`);
  }
}

elCmdForm.addEventListener('submit', async (e) => {
  e.preventDefault();
  const text = elCmdInput.value.trim();
  if (!text) return;
  const mode = getDispatchMode();
  const idx = mode === 'direct' ? Number(elCmdAssignee.value) : null;
  elCmdInput.value = '';
  await dispatchTask(mode, text, idx);
});

elInspAssignForm.addEventListener('submit', async (e) => {
  e.preventDefault();
  if (selectedIdx < 0) return;
  const text = elInspAssignInput.value.trim();
  if (!text) return;
  elInspAssignInput.value = '';
  await dispatchTask('direct', text, selectedIdx);
});

btnCancelTask.addEventListener('click', async () => {
  if (selectedIdx < 0) return;
  await fetch('/api/cancel', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ workerIndex: selectedIdx }),
  });
  showToast(`Đã hủy tác vụ của ${WORKERS[selectedIdx].name}`);
  await syncState();
});

btnViewLastResult.addEventListener('click', () => {
  if (selectedIdx >= 0 && WORKERS[selectedIdx].lastResultId) {
    openResult(WORKERS[selectedIdx].lastResultId);
  }
});

// Góc nhìn & Drawer
const btnViewDefault = document.getElementById('btn-view-default');
const btnViewTop = document.getElementById('btn-view-top');
const btnOrbit = document.getElementById('btn-orbit');

btnViewDefault.addEventListener('click', () => {
  camera.position.copy(DEFAULT_CAM_POS);
  camLerpTarget = DEFAULT_TARGET.clone();
  btnViewDefault.classList.add('active');
  btnViewTop.classList.remove('active');
});
btnViewTop.addEventListener('click', () => {
  camera.position.set(0.1, 10.2, 3.2);
  camLerpTarget = DEFAULT_TARGET.clone();
  btnViewTop.classList.add('active');
  btnViewDefault.classList.remove('active');
});
btnOrbit.addEventListener('click', () => {
  autoOrbit = !autoOrbit;
  controls.autoRotate = autoOrbit;
  controls.autoRotateSpeed = 0.65;
  btnOrbit.setAttribute('aria-pressed', String(autoOrbit));
  btnOrbit.classList.toggle('active', autoOrbit);
});

btnToggleResults.addEventListener('click', () => {
  const hidden = elResultsDrawer.classList.toggle('hidden');
  btnToggleResults.setAttribute('aria-expanded', String(!hidden));
  btnToggleResults.classList.toggle('active', !hidden);
});
document.getElementById('btn-close-results').addEventListener('click', () => {
  elResultsDrawer.classList.add('hidden');
  btnToggleResults.setAttribute('aria-expanded', 'false');
  btnToggleResults.classList.remove('active');
});
document.getElementById('btn-close-insp').addEventListener('click', closeInspector);

// Raycasting
const raycaster = new THREE.Raycaster();
const pointer = new THREE.Vector2();
let downPos = { x: 0, y: 0 };
renderer.domElement.addEventListener('pointerdown', (e) => { downPos = { x: e.clientX, y: e.clientY }; });
renderer.domElement.addEventListener('pointerup', (e) => {
  if (Math.hypot(e.clientX - downPos.x, e.clientY - downPos.y) > 6) return;
  pointer.x = (e.clientX / window.innerWidth) * 2 - 1;
  pointer.y = -(e.clientY / window.innerHeight) * 2 + 1;
  raycaster.setFromCamera(pointer, camera);
  const hits = raycaster.intersectObjects(clickable, false);
  if (hits.length > 0) {
    const idx = hits[0].object.userData.workerIndex;
    if (typeof idx === 'number') selectWorker(idx, true);
  }
});

window.addEventListener('resize', () => {
  camera.aspect = window.innerWidth / window.innerHeight;
  camera.updateProjectionMatrix();
  renderer.setSize(window.innerWidth, window.innerHeight);
});

redrawEditorialBoard();
syncState();
setInterval(syncState, 2000);

// ============================================================
// VÒNG LẶP 60 FPS
// ============================================================
const clock = new THREE.Clock();
let screenAccum = 0;
let clockAccum = 0;

function animate() {
  requestAnimationFrame(animate);
  const dt = Math.min(clock.getDelta(), 0.1);
  const t = clock.elapsedTime;

  workerRigs.forEach((rig, i) => {
    const w = rig.worker;
    const isWorking = w.status === 'working';

    if (isWorking) {
      rig.upperBody.rotation.x = THREE.MathUtils.lerp(rig.upperBody.rotation.x, 0.16, 0.1);
      rig.armL.rotation.x = Math.sin(t * 11 + i) * 0.14;
      rig.armR.rotation.x = Math.sin(t * 11 + i + Math.PI) * 0.14;
      rig.headGroup.rotation.y = Math.sin(t * 1.1 + i) * 0.08;
      rig.headGroup.rotation.x = 0.15 + Math.sin(t * 2.5 + i) * 0.03;
    } else {
      rig.upperBody.rotation.x = THREE.MathUtils.lerp(rig.upperBody.rotation.x, -0.05, 0.08);
      rig.armL.rotation.x = THREE.MathUtils.lerp(rig.armL.rotation.x, -0.34, 0.08);
      rig.armR.rotation.x = THREE.MathUtils.lerp(rig.armR.rotation.x, -0.34, 0.08);
      rig.headGroup.rotation.y = Math.sin(t * 0.45 + i * 2.1) * 0.25;
      rig.headGroup.rotation.x = THREE.MathUtils.lerp(rig.headGroup.rotation.x, -0.02, 0.08);
    }

    rig.upperBody.position.y = 0.60 + Math.sin(t * 1.8 + i) * 0.008;
    rig.badge.position.y = 1.66 + Math.sin(t * 2.4 + i) * (isWorking ? 0.045 : 0.015);
  });

  // Hiệu ứng quả cầu truyền bản thảo sang Vy (Bàn 4) trong Pha 2
  const isPhase2 = pipelineInfo.active && pipelineInfo.phase === 'phase2';
  const vyPos = WORKERS[3].laptopPos;
  syncOrbs.forEach(({ orb, srcIdx }, k) => {
    orb.visible = isPhase2;
    if (isPhase2) {
      const p = (t * 0.75 + k * 0.33) % 1;
      const from = WORKERS[srcIdx].laptopPos;
      orb.position.lerpVectors(from, vyPos, p);
      orb.position.y += Math.sin(p * Math.PI) * 0.45 + 0.18;
    }
  });

  screenAccum += dt;
  if (screenAccum >= 0.12) {
    screenAccum = 0;
    workerRigs.forEach((rig) => rig.laptop.redrawScreen(t));
  }

  clockAccum += dt;
  if (clockAccum >= 0.5) {
    clockAccum = 0;
    elClock.textContent = new Date().toLocaleTimeString('vi-VN', { hour12: false });
  }

  if (camLerpTarget) {
    controls.target.lerp(camLerpTarget, 0.08);
    if (controls.target.distanceTo(camLerpTarget) < 0.02) camLerpTarget = null;
  }

  controls.update();
  renderer.render(scene, camera);
}

animate();
