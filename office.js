import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';

// ============================================================
// 4 CHUYÊN VIÊN CHIBI (TẢI TỪ BLENDER assets/studio.glb)
// ============================================================
const WORKERS = [
  {
    id: 'BÀN 1',
    name: 'Minh',
    role: 'Nghiên cứu & Đề cương',
    focusPos: new THREE.Vector3(-1.05, 0.95, -1.0),
    labelAnchor: new THREE.Vector3(-1.05, 1.92, -1.28),
    orbAnchor: new THREE.Vector3(-1.05, 1.02, -0.42),
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
    role: 'Chấp bút & Soạn thảo',
    focusPos: new THREE.Vector3(1.05, 0.95, -1.0),
    labelAnchor: new THREE.Vector3(1.05, 1.92, -1.28),
    orbAnchor: new THREE.Vector3(1.05, 1.02, -0.42),
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
    role: 'Biên tập & Chuẩn NĐ30',
    focusPos: new THREE.Vector3(-1.05, 0.95, 1.0),
    labelAnchor: new THREE.Vector3(-1.05, 1.92, 1.28),
    orbAnchor: new THREE.Vector3(-1.05, 1.02, 0.42),
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
    focusPos: new THREE.Vector3(1.05, 0.95, 1.0),
    labelAnchor: new THREE.Vector3(1.05, 1.92, 1.28),
    orbAnchor: new THREE.Vector3(1.05, 1.02, 0.42),
    status: 'idle',
    task: null,
    phaseLabel: null,
    elapsedSec: 0,
    lastResultId: null,
    error: null,
  },
];

const STATUS_META = {
  idle: { label: 'Sẵn sàng', color: 0xa8998a, css: '#8c7866' },
  working: { label: 'Đang biên soạn', color: 0x2563eb, css: '#2563eb' },
  done: { label: 'Đã có văn bản', color: 0x15803d, css: '#15803d' },
  error: { label: 'Có lỗi', color: 0xb91c1c, css: '#b91c1c' },
};

// ============================================================
// THREE.JS RENDERER, CAMERA & ÁNH SÁNG STUDIO ẤM
// ============================================================
const container = document.getElementById('canvas-wrap');
const labelsLayer = document.getElementById('labels-layer');
const scene = new THREE.Scene();
scene.background = new THREE.Color(0xefe8dc);

const renderer = new THREE.WebGLRenderer({ antialias: true, powerPreference: 'high-performance' });
renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
renderer.setSize(window.innerWidth, window.innerHeight);
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFSoftShadowMap;
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure = 1.08;
container.appendChild(renderer.domElement);

const camera = new THREE.PerspectiveCamera(34, window.innerWidth / window.innerHeight, 0.1, 100);
const DEFAULT_CAM_POS = new THREE.Vector3(-0.3, 4.9, 6.9);
const DEFAULT_TARGET = new THREE.Vector3(0, 1.05, -0.35);
camera.position.copy(DEFAULT_CAM_POS);

const controls = new OrbitControls(camera, renderer.domElement);
controls.target.copy(DEFAULT_TARGET);
controls.enableDamping = true;
controls.dampingFactor = 0.06;
controls.maxPolarAngle = Math.PI / 2 - 0.05;
controls.minDistance = 3.2;
controls.maxDistance = 16;
controls.update();

scene.add(new THREE.HemisphereLight(0xfffaf2, 0xd8c8b4, 1.15));

const sunLight = new THREE.DirectionalLight(0xfff5e4, 1.72);
sunLight.position.set(5.5, 8.5, 4.5);
sunLight.castShadow = true;
sunLight.shadow.mapSize.set(2048, 2048);
sunLight.shadow.camera.near = 1;
sunLight.shadow.camera.far = 25;
sunLight.shadow.camera.left = -6.5;
sunLight.shadow.camera.right = 6.5;
sunLight.shadow.camera.top = 6.5;
sunLight.shadow.camera.bottom = -6.5;
sunLight.shadow.bias = -0.0005;
sunLight.shadow.radius = 3;
scene.add(sunLight);

const warmPendantLight = new THREE.PointLight(0xffe1a8, 2.8, 9, 1.5);
warmPendantLight.position.set(0, 2.35, 0);
scene.add(warmPendantLight);

const emblemSpotLight = new THREE.PointLight(0xffe09e, 1.9, 5, 1.6);
emblemSpotLight.position.set(0.25, 2.95, -3.55);
scene.add(emblemSpotLight);

// Tạo 4 bảng tên 3D nổi phía trên đầu nhân vật
const labelEls = WORKERS.map((w, i) => {
  const div = document.createElement('div');
  div.className = 'nameplate-3d';
  div.textContent = `${w.name} • Sẵn sàng`;
  labelsLayer.appendChild(div);
  return div;
});

// ============================================================
// TẢI MÔ HÌNH BLENDER (assets/studio.glb)
// ============================================================
const workerRigs = [];
const clickable = [];
const monitorUpdaters = [];
let clockHands = { hour: null, minute: null, second: null };

function attachLiveMonitor(screenMesh, worker) {
  const canvas = document.createElement('canvas');
  canvas.width = 320;
  canvas.height = 192;
  const ctx = canvas.getContext('2d');
  const tex = new THREE.CanvasTexture(canvas);
  tex.colorSpace = THREE.SRGBColorSpace;
  tex.flipY = true;
  screenMesh.material = new THREE.MeshBasicMaterial({ map: tex });

  function redraw(t) {
    const meta = STATUS_META[worker.status] || STATUS_META.idle;
    if (worker.status === 'idle') {
      const g = ctx.createLinearGradient(0, 0, 320, 192);
      g.addColorStop(0, '#0ea5e9');
      g.addColorStop(0.5, '#2563eb');
      g.addColorStop(1, '#1e3a8a');
      ctx.fillStyle = g;
      ctx.fillRect(0, 0, 320, 192);

      ctx.fillStyle = 'rgba(147, 197, 253, 0.35)';
      ctx.beginPath();
      ctx.arc(160, 108, 56 + Math.sin(t * 1.2) * 3, 0, Math.PI * 2);
      ctx.fill();
      ctx.fillStyle = 'rgba(219, 234, 254, 0.45)';
      ctx.beginPath();
      ctx.arc(178, 96, 36, 0, Math.PI * 2);
      ctx.fill();

      ctx.fillStyle = 'rgba(255,255,255,0.94)';
      ctx.font = 'bold 16px sans-serif';
      ctx.fillText(`${worker.name} • Sẵn sàng`, 16, 32);
    } else {
      ctx.fillStyle = '#0f172a';
      ctx.fillRect(0, 0, 320, 192);
      ctx.fillStyle = meta.css;
      ctx.fillRect(0, 0, 320, 32);
      ctx.fillStyle = '#ffffff';
      ctx.font = 'bold 14px monospace';
      ctx.fillText(`${worker.name} • ${(worker.phaseLabel || meta.label).slice(0, 20)}`, 12, 22);

      ctx.fillStyle = '#f8fafc';
      ctx.font = '15px sans-serif';
      ctx.fillText((worker.task || '').slice(0, 30), 14, 68);

      if (worker.status === 'working') {
        const barX = 14 + ((t * 120) % 200);
        ctx.fillStyle = '#334155';
        ctx.fillRect(14, 92, 292, 14);
        ctx.fillStyle = '#38bdf8';
        ctx.fillRect(barX, 92, 92, 14);
        ctx.fillStyle = '#93c5fd';
        ctx.font = '13px monospace';
        ctx.fillText(`Chuẩn hóa NĐ30 (${worker.elapsedSec}s)...`, 14, 140);
      } else if (worker.status === 'done') {
        ctx.fillStyle = '#4ade80';
        ctx.font = 'bold 16px sans-serif';
        ctx.fillText('✓ Đã xong chuẩn NĐ30', 14, 120);
      } else {
        ctx.fillStyle = '#f87171';
        ctx.font = '14px sans-serif';
        ctx.fillText('Có lỗi khi xử lý', 14, 120);
      }
    }
    tex.needsUpdate = true;
  }

  monitorUpdaters.push(redraw);
}

const loader = new GLTFLoader();
loader.load(
  './assets/studio.glb?v=' + Date.now(),
  (gltf) => {
    const root = gltf.scene;
    root.traverse((obj) => {
      if (obj.isMesh) {
        obj.castShadow = obj.name !== 'Floor' && obj.name !== 'Rug' && !obj.name.startsWith('Grout');
        obj.receiveShadow = true;
        if (obj.name === 'EmblemLogo') {
          obj.castShadow = false;
          if (obj.material) {
            obj.material.transparent = true;
            obj.material.alphaTest = 0.08;
            obj.material.side = THREE.DoubleSide;
          }
        }
      }
    });
    scene.add(root);

    clockHands = {
      hour: root.getObjectByName('ClockHour'),
      minute: root.getObjectByName('ClockMinute'),
      second: root.getObjectByName('ClockSecond'),
    };

    WORKERS.forEach((w, idx) => {
      const workerRoot = root.getObjectByName(`Worker${idx}`);
      const upper = root.getObjectByName(`Worker${idx}_Upper`);
      const head = root.getObjectByName(`Worker${idx}_Head`);
      const eyes = root.getObjectByName(`Worker${idx}_Eyes`);
      const armL = root.getObjectByName(`Worker${idx}_ArmL`);
      const armR = root.getObjectByName(`Worker${idx}_ArmR`);
      const badge = root.getObjectByName(`Worker${idx}_Badge`);
      const ring = root.getObjectByName(`Worker${idx}_Ring`);
      const screen = root.getObjectByName(`MonitorScreen${idx}`);

      if (ring) ring.visible = false;
      if (screen) attachLiveMonitor(screen, w);

      if (workerRoot) {
        const hit = new THREE.Mesh(
          new THREE.CylinderGeometry(0.55, 0.55, 1.7, 12),
          new THREE.MeshBasicMaterial({ visible: false })
        );
        hit.position.set(0, 0.85, 0);
        hit.userData.workerIndex = idx;
        workerRoot.add(hit);
        clickable.push(hit);
      }

      workerRigs.push({
        worker: w,
        upper,
        head,
        eyes,
        armL,
        armR,
        badge,
        ring,
        baseUpperY: upper ? upper.position.y : 0.56,
        baseBadgeY: badge ? badge.position.y : 1.72,
      });
    });
  },
  undefined,
  (err) => {
    console.error('Lỗi tải studio.glb:', err);
    showToast('Không tải được assets/studio.glb!');
  }
);

const syncOrbs = [0, 1, 2].map((srcIdx) => {
  const orb = new THREE.Mesh(
    new THREE.SphereGeometry(0.06, 14, 12),
    new THREE.MeshBasicMaterial({ color: 0x38bdf8 })
  );
  orb.visible = false;
  scene.add(orb);
  return { orb, srcIdx };
});

// ============================================================
// QUẢN LÝ UI/UX, MẪU NHANH, ĐÍNH KÈM FILE, CHỈNH SỬA NĐ30 & CÀI ĐẶT
// ============================================================
let selectedIdx = -1;
let autoOrbit = false;
let camLerpTarget = null;
let camPosTarget = null;
let allResults = [];
let currentDialogData = null;
let isEditingResult = false;
let attachedReferenceText = '';
let pipelineInfo = { active: false, phase: 'idle', message: 'Sẵn sàng nhận lệnh' };

const elSummary = document.getElementById('office-summary');
const elOrgUnitLabel = document.getElementById('org-unit-label');
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
const elFileInput = document.getElementById('file-attach-input');
const elAttachedBar = document.getElementById('attached-bar');
const elAttachedName = document.getElementById('attached-name');

const elResDialog = document.getElementById('result-dialog');
const elResWorker = document.getElementById('res-dialog-worker');
const elResTitle = document.getElementById('res-dialog-title');
const elResMeta = document.getElementById('res-dialog-meta');
const elResContent = document.getElementById('res-dialog-content');
const elResEditForm = document.getElementById('res-edit-form');
const btnToggleEdit = document.getElementById('btn-toggle-edit');
const elResFile = document.getElementById('res-dialog-file');
const btnResDocx = document.getElementById('btn-res-docx');
const btnResPdf = document.getElementById('btn-res-pdf');

const elSetDialog = document.getElementById('settings-dialog');
const elSetForm = document.getElementById('settings-form');

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

// Các chip Mẫu nhanh Nghị định 30
document.querySelectorAll('.tpl-chip').forEach((chip) => {
  chip.addEventListener('click', () => {
    elCmdInput.value = chip.dataset.tpl || '';
    elCmdInput.focus();
  });
});

// Đính kèm file gốc (.docx / .txt / .md)
document.getElementById('btn-attach-file').addEventListener('click', () => elFileInput.click());
elFileInput.addEventListener('change', async () => {
  const file = elFileInput.files && elFileInput.files[0];
  if (!file) return;
  try {
    const buf = await file.arrayBuffer();
    const bytes = new Uint8Array(buf);
    let binary = '';
    for (let i = 0; i < bytes.length; i++) binary += String.fromCharCode(bytes[i]);
    const resp = await fetch('/api/extract-file', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ filename: file.name, dataBase64: btoa(binary) }),
    });
    const data = await resp.json();
    if (!resp.ok) throw new Error(data.error || 'Lỗi đọc file');
    attachedReferenceText = data.text || '';
    elAttachedName.textContent = `Đính kèm: ${file.name} (${attachedReferenceText.length} ký tự)`;
    elAttachedBar.classList.remove('hidden');
    if (!elCmdInput.value.trim()) {
      elCmdInput.value = 'Rà soát, biên tập lại văn bản đính kèm theo chuẩn thể thức Nghị định 30/2020/NĐ-CP';
    }
    elCmdInput.focus();
  } catch (err) {
    showToast(`Không đọc được tài liệu: ${err.message}`);
  } finally {
    elFileInput.value = '';
  }
});

document.getElementById('btn-clear-attach').addEventListener('click', () => {
  attachedReferenceText = '';
  elAttachedBar.classList.add('hidden');
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
  let inList = false;

  for (const raw of lines) {
    const line = esc(raw)
      .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
      .replace(/\*([^*]+)\*/g, '<em>$1</em>')
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
    } else if (raw.trim() === '' || raw.trim() === '---') {
      if (inList) { html += '</ul>'; inList = false; }
    } else {
      if (inList) { html += '</ul>'; inList = false; }
      html += `<p>${line}</p>`;
    }
  }
  if (inList) html += '</ul>';
  return html || '<p><em>(Trống)</em></p>';
}

function setEditMode(editing) {
  isEditingResult = editing;
  elResContent.classList.toggle('hidden', editing);
  elResEditForm.classList.toggle('hidden', !editing);
  btnToggleEdit.textContent = editing ? 'Xem bản đọc' : 'Chỉnh sửa nhanh';
}

function populateEditForm(d) {
  document.getElementById('ed-cqcq').value = d.co_quan_chu_quan || '';
  document.getElementById('ed-cqbh').value = d.co_quan_ban_hanh || '';
  document.getElementById('ed-so').value = d.so_ky_hieu || '';
  document.getElementById('ed-ngay').value = d.dia_danh_ngay || '';
  document.getElementById('ed-loai').value = d.loai_van_ban || 'van_ban_co_ten_loai';
  document.getElementById('ed-tenloai').value = d.ten_loai || '';
  document.getElementById('ed-trichyeu').value = d.trich_yeu || '';
  document.getElementById('ed-noidung').value = d.noi_dung || '';
  document.getElementById('ed-chucvu').value = d.chuc_vu_ky || '';
  document.getElementById('ed-nguoiky').value = d.nguoi_ky || '';
  document.getElementById('ed-noinhan').value = (d.noi_nhan || []).join('\n');
}

async function openResult(resultId) {
  try {
    const resp = await fetch(`/api/result/${encodeURIComponent(resultId)}`);
    if (!resp.ok) throw new Error('Không tải được văn bản');
    const data = await resp.json();
    currentDialogData = data;
    setEditMode(false);
    elResWorker.textContent = `${data.workerId} • ${data.workerName} (${data.modeLabel || data.workerRole})`;
    elResTitle.textContent = data.task;
    elResMeta.textContent = `Hoàn thành lúc ${data.completedAt} • Chuẩn Nghị định 30/2020/NĐ-CP`;
    elResContent.innerHTML = renderMarkdownSafe(data.content || '');
    if (data.docData) populateEditForm(data.docData);

    const docxName = data.docxFilename || `${data.id}.docx`;
    elResFile.textContent = `results/${docxName}`;
    btnResDocx.href = `/api/result/${encodeURIComponent(data.id)}/docx?t=${Date.now()}`;
    btnResDocx.setAttribute('download', docxName);
    btnResPdf.href = `/api/result/${encodeURIComponent(data.id)}/print?t=${Date.now()}`;
    elResDialog.showModal();
  } catch (err) {
    showToast(`Lỗi mở văn bản: ${err.message}`);
  }
}

btnToggleEdit.addEventListener('click', () => setEditMode(!isEditingResult));

elResEditForm.addEventListener('submit', async (e) => {
  e.preventDefault();
  if (!currentDialogData) return;
  const patch = {
    co_quan_chu_quan: document.getElementById('ed-cqcq').value,
    co_quan_ban_hanh: document.getElementById('ed-cqbh').value,
    so_ky_hieu: document.getElementById('ed-so').value,
    dia_danh_ngay: document.getElementById('ed-ngay').value,
    loai_van_ban: document.getElementById('ed-loai').value,
    ten_loai: document.getElementById('ed-tenloai').value,
    trich_yeu: document.getElementById('ed-trichyeu').value,
    noi_dung: document.getElementById('ed-noidung').value,
    chuc_vu_ky: document.getElementById('ed-chucvu').value,
    nguoi_ky: document.getElementById('ed-nguoiky').value,
    noi_nhan: document.getElementById('ed-noinhan').value.split(/\r?\n/).filter((x) => x.trim()),
  };
  const resp = await fetch(`/api/result/${encodeURIComponent(currentDialogData.id)}/update`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ docData: patch }),
  });
  const res = await resp.json();
  if (resp.ok) {
    currentDialogData.content = res.content;
    currentDialogData.docData = res.docData;
    elResContent.innerHTML = renderMarkdownSafe(res.content || '');
    btnResDocx.href = `/api/result/${encodeURIComponent(currentDialogData.id)}/docx?t=${Date.now()}`;
    btnResPdf.href = `/api/result/${encodeURIComponent(currentDialogData.id)}/print?t=${Date.now()}`;
    setEditMode(false);
    showToast('Đã lưu chỉnh sửa & cập nhật lại file Word (.docx) + PDF!');
    syncState();
  } else {
    showToast(res.error || 'Lỗi khi lưu chỉnh sửa');
  }
});

document.getElementById('btn-res-close').addEventListener('click', () => elResDialog.close());
document.getElementById('btn-res-copy').addEventListener('click', async () => {
  if (!currentDialogData) return;
  await navigator.clipboard.writeText(currentDialogData.content || '');
  showToast('Đã copy toàn bộ văn bản!');
});

// Cài đặt Hồ sơ Đơn vị & AI
async function openSettings() {
  try {
    const resp = await fetch('/api/config');
    const cfg = await resp.json();
    const org = cfg.orgProfile || {};
    document.getElementById('org-cqcq').value = org.coQuanChuQuan || '';
    document.getElementById('org-cqbh').value = org.coQuanBanHanh || '';
    document.getElementById('org-kh').value = org.kyHieuDonVi || 'ĐV';
    document.getElementById('org-diadanh').value = org.diaDanh || 'Hà Nội';
    document.getElementById('org-chucvu').value = org.chucVuKy || 'THỦ TRƯỞNG ĐƠN VỊ';
    document.getElementById('org-nguoiky').value = org.nguoiKy || '';

    document.getElementById('cfg-provider').value = cfg.provider || 'auto';
    document.getElementById('cfg-agy-model').value = cfg.antigravityModel || 'pro';
    const gKey = document.getElementById('cfg-gemini-key');
    gKey.value = '';
    gKey.placeholder = cfg.hasGeminiKey ? 'Đã lưu key (nhập mới để thay)' : 'AIza...';
    document.getElementById('cfg-gemini-model').value = cfg.geminiModel || 'gemini-2.5-pro';
    document.getElementById('cfg-openai-url').value = cfg.openaiBaseUrl || 'http://localhost:11434/v1';
    document.getElementById('cfg-openai-model').value = cfg.openaiModel || 'qwen2.5:7b';
    document.getElementById('cfg-archive-agy').checked = cfg.archiveAntigravity !== false;
    document.getElementById('cfg-status-hint').textContent =
      `Đang kết nối: ${cfg.activeProvider.toUpperCase()} (${(cfg.antigravityModel || 'pro').toUpperCase()})`;
    elSetDialog.showModal();
  } catch {
    showToast('Không tải được cấu hình');
  }
}

document.getElementById('btn-open-settings').addEventListener('click', openSettings);
document.getElementById('btn-set-close').addEventListener('click', () => elSetDialog.close());
document.getElementById('btn-set-cancel').addEventListener('click', () => elSetDialog.close());

elSetForm.addEventListener('submit', async (e) => {
  e.preventDefault();
  const payload = {
    provider: document.getElementById('cfg-provider').value,
    antigravityModel: document.getElementById('cfg-agy-model').value,
    geminiApiKey: document.getElementById('cfg-gemini-key').value.trim(),
    geminiModel: document.getElementById('cfg-gemini-model').value.trim(),
    openaiBaseUrl: document.getElementById('cfg-openai-url').value.trim(),
    openaiModel: document.getElementById('cfg-openai-model').value.trim(),
    archiveAntigravity: document.getElementById('cfg-archive-agy').checked,
    orgProfile: {
      coQuanChuQuan: document.getElementById('org-cqcq').value.trim(),
      coQuanBanHanh: document.getElementById('org-cqbh').value.trim(),
      kyHieuDonVi: document.getElementById('org-kh').value.trim(),
      diaDanh: document.getElementById('org-diadanh').value.trim(),
      chucVuKy: document.getElementById('org-chucvu').value.trim(),
      nguoiKy: document.getElementById('org-nguoiky').value.trim(),
    },
  };
  const resp = await fetch('/api/config', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  const data = await resp.json();
  showToast(`Đã lưu Hồ sơ Đơn vị & Cài đặt AI (${(data.activeProvider || 'none').toUpperCase()})!`);
  elSetDialog.close();
  syncState();
});

const PROVIDER_LABELS = {
  antigravity: 'Antigravity Pro',
  gemini: 'Gemini Pro',
  openai: 'Ollama / OpenAI',
  none: 'Chưa cấu hình AI',
};

function updateSummary() {
  const working = WORKERS.filter((w) => w.status === 'working').length;
  const idle = WORKERS.length - working;
  if (working === 0) {
    elSummary.textContent = `${idle}/4 chuyên viên sẵn sàng`;
    elOfficeDot.classList.remove('active');
  } else if (pipelineInfo.active && pipelineInfo.mode === 'split-merge') {
    elSummary.textContent = pipelineInfo.message || `${working} chuyên viên đang phối hợp`;
    elOfficeDot.classList.add('active');
  } else {
    elSummary.textContent = `${working}/4 đang biên soạn • ${idle} sẵn sàng`;
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

    // Cập nhật nhãn 3D nổi
    const lbl = labelEls[i];
    if (lbl) {
      lbl.className = `nameplate-3d ${w.status}`;
      lbl.textContent =
        w.status === 'working'
          ? `${w.name} • ${w.elapsedSec}s`
          : w.status === 'done'
          ? `✓ ${w.name} • Đã xong`
          : `${w.name} • ${w.role.split('&')[0].trim()}`;
    }
  });
}

function renderGlobalResults() {
  elResultsCount.textContent = String(allResults.length);
  elGlobalResults.innerHTML = '';
  if (allResults.length === 0) {
    elGlobalResults.innerHTML =
      '<li class="empty-state">Chưa có văn bản nào. Hãy chọn mẫu hoặc nhập yêu cầu ở thanh bên dưới.</li>';
    return;
  }
  allResults.forEach((r) => {
    const li = document.createElement('li');
    li.className = 'result-item';
    li.innerHTML = `
      <div class="result-item-title">${r.task}</div>
      <div class="result-item-meta">${r.workerName} • ${r.modeLabel || r.workerRole} • ${r.completedAt}</div>
      <div class="result-item-preview">${r.preview || ''}</div>
      <button type="button" class="del-item-btn" title="Xóa văn bản này" aria-label="Xóa văn bản">✕</button>
    `;
    li.addEventListener('click', (ev) => {
      if (ev.target.closest('.del-item-btn')) return;
      openResult(r.id);
    });
    li.querySelector('.del-item-btn').addEventListener('click', async (ev) => {
      ev.stopPropagation();
      await fetch(`/api/result/${encodeURIComponent(r.id)}/delete`, { method: 'POST' });
      showToast('Đã xóa văn bản khỏi kho.');
      syncState();
    });
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
        <div class="result-item-meta">${r.completedAt} • Bấm mở Word / PDF</div>
      `;
      li.addEventListener('click', () => openResult(r.id));
      elInspHistory.appendChild(li);
    });
  }
}

function selectWorker(idx, focusCam = false) {
  selectedIdx = idx;
  elInspector.classList.remove('hidden');
  workerRigs.forEach((r, i) => {
    if (r.ring) r.ring.visible = i === idx;
  });
  renderInspector();
  renderStationDock();
  if (focusCam) camLerpTarget = WORKERS[idx].focusPos.clone();
}

function closeInspector() {
  selectedIdx = -1;
  elInspector.classList.add('hidden');
  workerRigs.forEach((r) => {
    if (r.ring) r.ring.visible = false;
  });
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
    elOrgUnitLabel.textContent = data.orgUnit || 'Chuẩn Nghị định 30/2020/NĐ-CP';

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
      const rig = workerRigs[i];
      if (rig && rig.badge && rig.badge.material) {
        rig.badge.material.color.setHex(meta.color);
        if (rig.badge.material.emissive) rig.badge.material.emissive.setHex(meta.color);
      }

      if (prevStatus === 'working' && sw.status === 'done' && sw.lastResultId) {
        const rid = sw.lastResultId;
        showToast(`✓ ${WORKERS[i].name} đã xuất xong văn bản chuẩn NĐ30! Bấm tải Word / PDF`, () =>
          openResult(rid)
        );
      }
    });

    updateSummary();
    renderStationDock();
    renderGlobalResults();
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
      body: JSON.stringify({
        mode,
        task: taskText,
        workerIndex,
        referenceText: attachedReferenceText,
      }),
    });
    const data = await resp.json();
    if (!resp.ok) {
      showToast(data.error || 'Không thể giao việc');
      return;
    }
    attachedReferenceText = '';
    elAttachedBar.classList.add('hidden');

    if (mode === 'split-merge') {
      showToast('Đã chia nhiệm vụ lớn: Minh, Lan, Tuấn làm song song → Vy tổng hợp chuẩn NĐ30!');
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

// Góc nhìn Camera
const btnViewDefault = document.getElementById('btn-view-default');
const btnViewEmblem = document.getElementById('btn-view-emblem');
const btnViewTop = document.getElementById('btn-view-top');
const btnOrbit = document.getElementById('btn-orbit');

function setViewButtons(activeBtn) {
  [btnViewDefault, btnViewEmblem, btnViewTop].forEach((b) => b.classList.toggle('active', b === activeBtn));
}

btnViewDefault.addEventListener('click', () => {
  camPosTarget = DEFAULT_CAM_POS.clone();
  camLerpTarget = DEFAULT_TARGET.clone();
  setViewButtons(btnViewDefault);
});
btnViewEmblem.addEventListener('click', () => {
  camPosTarget = new THREE.Vector3(0.2, 2.5, 4.4);
  camLerpTarget = new THREE.Vector3(0.2, 1.85, -3.2);
  setViewButtons(btnViewEmblem);
});
btnViewTop.addEventListener('click', () => {
  camPosTarget = new THREE.Vector3(0.0, 9.2, 2.8);
  camLerpTarget = DEFAULT_TARGET.clone();
  setViewButtons(btnViewTop);
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

// Raycasting (click + hover đổi con trỏ chuột)
const raycaster = new THREE.Raycaster();
const pointer = new THREE.Vector2();
let downPos = { x: 0, y: 0 };

renderer.domElement.addEventListener('pointermove', (e) => {
  pointer.x = (e.clientX / window.innerWidth) * 2 - 1;
  pointer.y = -(e.clientY / window.innerHeight) * 2 + 1;
  raycaster.setFromCamera(pointer, camera);
  const hits = raycaster.intersectObjects(clickable, false);
  container.style.cursor = hits.length > 0 ? 'pointer' : 'grab';
});

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

syncState();
setInterval(syncState, 2000);

// ============================================================
// VÒNG LẶP 60 FPS — ANIMATION NHÂN VẬT CHIBI, ĐỒNG HỒ THẬT & BẢNG TÊN 3D
// ============================================================
const clock = new THREE.Clock();
const projVec = new THREE.Vector3();
let screenAccum = 0;
let clockAccum = 0;

function animate() {
  requestAnimationFrame(animate);
  const dt = Math.min(clock.getDelta(), 0.1);
  const t = clock.elapsedTime;

  // Đồng hồ treo tường chạy giờ thực trên máy
  const now = new Date();
  if (clockHands.second) {
    const sec = now.getSeconds() + now.getMilliseconds() / 1000;
    const min = now.getMinutes() + sec / 60;
    const hr = (now.getHours() % 12) + min / 60;
    clockHands.second.rotation.z = -(sec / 60) * Math.PI * 2;
    clockHands.minute.rotation.z = -(min / 60) * Math.PI * 2;
    clockHands.hour.rotation.z = -(hr / 12) * Math.PI * 2;
  }

  workerRigs.forEach((rig, i) => {
    const w = rig.worker;
    const isWorking = w.status === 'working';

    if (rig.upper) {
      const targetLean = isWorking ? -0.14 : 0.04;
      rig.upper.rotation.x = THREE.MathUtils.lerp(rig.upper.rotation.x, targetLean, 0.1);
      rig.upper.position.y = rig.baseUpperY + Math.sin(t * 2.0 + i) * 0.008;
    }
    if (rig.armL && rig.armR) {
      if (isWorking) {
        rig.armL.rotation.x = Math.sin(t * 12 + i) * 0.14;
        rig.armR.rotation.x = Math.sin(t * 12 + i + Math.PI) * 0.14;
      } else {
        rig.armL.rotation.x = THREE.MathUtils.lerp(rig.armL.rotation.x, 0.25, 0.08);
        rig.armR.rotation.x = THREE.MathUtils.lerp(rig.armR.rotation.x, 0.25, 0.08);
      }
    }
    if (rig.head) {
      if (isWorking) {
        rig.head.rotation.y = Math.sin(t * 1.1 + i) * 0.09;
        rig.head.rotation.x = -0.10 + Math.sin(t * 2.6 + i) * 0.03;
      } else {
        rig.head.rotation.y = Math.sin(t * 0.55 + i * 2.1) * 0.28;
        rig.head.rotation.x = THREE.MathUtils.lerp(rig.head.rotation.x, 0.02, 0.08);
      }
    }
    // Nháy mắt Chibi tự nhiên mỗi ~4 giây
    if (rig.eyes) {
      const blinkCycle = (t + i * 1.37) % 4.2;
      rig.eyes.scale.y = blinkCycle > 4.06 ? 0.12 : 1.0;
    }
    if (rig.badge) {
      rig.badge.position.y = rig.baseBadgeY + Math.sin(t * 2.5 + i) * (isWorking ? 0.045 : 0.015);
    }
  });

  // Chiếu tọa độ 3D ra màn hình cho 4 bảng tên nổi
  WORKERS.forEach((w, i) => {
    const lbl = labelEls[i];
    if (!lbl) return;
    projVec.copy(w.labelAnchor).project(camera);
    if (projVec.z > 1) {
      lbl.style.display = 'none';
    } else {
      lbl.style.display = 'block';
      const x = (projVec.x * 0.5 + 0.5) * window.innerWidth;
      const y = (-projVec.y * 0.5 + 0.5) * window.innerHeight;
      lbl.style.left = `${x}px`;
      lbl.style.top = `${y}px`;
    }
  });

  const isPhase2 = pipelineInfo.active && pipelineInfo.phase === 'phase2';
  const vyAnchor = WORKERS[3].orbAnchor;
  syncOrbs.forEach(({ orb, srcIdx }, k) => {
    orb.visible = isPhase2;
    if (isPhase2) {
      const p = (t * 0.75 + k * 0.33) % 1;
      const from = WORKERS[srcIdx].orbAnchor;
      orb.position.lerpVectors(from, vyAnchor, p);
      orb.position.y += Math.sin(p * Math.PI) * 0.45 + 0.15;
    }
  });

  screenAccum += dt;
  if (screenAccum >= 0.12) {
    screenAccum = 0;
    monitorUpdaters.forEach((fn) => fn(t));
  }

  clockAccum += dt;
  if (clockAccum >= 0.5) {
    clockAccum = 0;
    elClock.textContent = now.toLocaleTimeString('vi-VN', { hour12: false });
  }

  if (camPosTarget) {
    camera.position.lerp(camPosTarget, 0.08);
    if (camera.position.distanceTo(camPosTarget) < 0.05) camPosTarget = null;
  }
  if (camLerpTarget) {
    controls.target.lerp(camLerpTarget, 0.08);
    if (controls.target.distanceTo(camLerpTarget) < 0.02) camLerpTarget = null;
  }

  controls.update();
  renderer.render(scene, camera);
}

animate();
