import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';

// ============================================================
// 4 CHUYÊN VIÊN CHIBI (TẢI TRỰC TIẾP TỪ BLENDER assets/studio.glb)
// ============================================================
const WORKERS = [
  {
    id: 'BÀN 1',
    name: 'Minh',
    role: 'Nghiên cứu & Lập dàn ý',
    focusPos: new THREE.Vector3(-1.05, 0.95, -1.0),
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
    role: 'Chấp bút & Soạn thảo chính',
    focusPos: new THREE.Vector3(1.05, 0.95, -1.0),
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
    role: 'Biên tập & Chuẩn thể thức',
    focusPos: new THREE.Vector3(-1.05, 0.95, 1.0),
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
  idle: { label: 'Đang chờ việc', color: 0xa8998a, css: '#8c7866' },
  working: { label: 'Đang biên soạn', color: 0x2563eb, css: '#2563eb' },
  done: { label: 'Đã có văn bản', color: 0x15803d, css: '#15803d' },
  error: { label: 'Có lỗi', color: 0xb91c1c, css: '#b91c1c' },
};

// ============================================================
// THREE.JS RENDERER, CAMERA & ÁNH SÁNG STUDIO ẤM
// ============================================================
const container = document.getElementById('canvas-wrap');
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
controls.minDistance = 3.5;
controls.maxDistance = 16;
controls.update();

// Ánh sáng tự nhiên ban ngày + đèn thả trần ấm giống ảnh Chibi
scene.add(new THREE.HemisphereLight(0xfffaf2, 0xd8c8b4, 1.15));

const sunLight = new THREE.DirectionalLight(0xfff5e4, 1.75);
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

const slatGlowLight = new THREE.PointLight(0xffcb77, 1.8, 6, 1.7);
slatGlowLight.position.set(-1.2, 2.2, -3.5);
scene.add(slatGlowLight);

// ============================================================
// TẢI MÔ HÌNH BLENDER (assets/studio.glb) & GẮN KHỚP ANIMATION + MÀN HÌNH SỐNG
// ============================================================
const workerRigs = [];
const clickable = [];
const monitorUpdaters = [];

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
      // Hình nền xanh Windows 11 mượt giống ảnh tham chiếu
      const g = ctx.createLinearGradient(0, 0, 320, 192);
      g.addColorStop(0, '#0ea5e9');
      g.addColorStop(0.5, '#2563eb');
      g.addColorStop(1, '#1e3a8a');
      ctx.fillStyle = g;
      ctx.fillRect(0, 0, 320, 192);

      // Sóng hoa xanh mềm
      ctx.fillStyle = 'rgba(147, 197, 253, 0.35)';
      ctx.beginPath();
      ctx.arc(160, 108, 56 + Math.sin(t * 1.2) * 3, 0, Math.PI * 2);
      ctx.fill();
      ctx.fillStyle = 'rgba(219, 234, 254, 0.45)';
      ctx.beginPath();
      ctx.arc(178, 96, 36, 0, Math.PI * 2);
      ctx.fill();

      ctx.fillStyle = 'rgba(255,255,255,0.92)';
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
        ctx.fillText(`Đang biên soạn (${worker.elapsedSec}s)...`, 14, 140);
      } else if (worker.status === 'done') {
        ctx.fillStyle = '#4ade80';
        ctx.font = 'bold 16px sans-serif';
        ctx.fillText('✓ Đã hoàn thành văn bản', 14, 120);
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

    // Liên kết 4 nhân vật Chibi & 4 màn hình từ file Blender
    WORKERS.forEach((w, idx) => {
      const workerRoot = root.getObjectByName(`Worker${idx}`);
      const upper = root.getObjectByName(`Worker${idx}_Upper`);
      const head = root.getObjectByName(`Worker${idx}_Head`);
      const armL = root.getObjectByName(`Worker${idx}_ArmL`);
      const armR = root.getObjectByName(`Worker${idx}_ArmR`);
      const badge = root.getObjectByName(`Worker${idx}_Badge`);
      const ring = root.getObjectByName(`Worker${idx}_Ring`);
      const screen = root.getObjectByName(`MonitorScreen${idx}`);

      if (ring) ring.visible = false;
      if (screen) attachLiveMonitor(screen, w);

      // Tạo hitbox trong suốt trên mỗi nhân vật để click dễ dàng
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
    showToast('Không tải được assets/studio.glb — kiểm tra lại file Blender!');
  }
);

// Quả cầu ánh sáng chuyển bản thảo sang Vy (Bàn 4) trong Pha 2
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
// QUẢN LÝ UI/UX, PHÂN CÔNG THÔNG MINH, WORD EXPORT & CÀI ĐẶT AI
// ============================================================
let selectedIdx = -1;
let autoOrbit = false;
let camLerpTarget = null;
let allResults = [];
let currentDialogData = null;
let pipelineInfo = { active: false, phase: 'idle', message: 'Sẵn sàng nhận lệnh' };

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
        showToast(`✓ ${WORKERS[i].name} đã hoàn thành văn bản! Bấm để đọc & tải Word`, () => openResult(rid));
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
  camera.position.set(0.0, 9.2, 2.8);
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

syncState();
setInterval(syncState, 2000);

// ============================================================
// VÒNG LẶP 60 FPS — ANIMATION NHÂN VẬT CHIBI TỪ BLENDER
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

    // Trong glTF Y-up: hướng nhìn nhân vật (Blender +Y) là Three.js -Z, nên cúi về trước là rotation.x âm
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
    if (rig.badge) {
      rig.badge.position.y = rig.baseBadgeY + Math.sin(t * 2.5 + i) * (isWorking ? 0.045 : 0.015);
    }
  });

  // Quả cầu ánh sáng truyền bản thảo sang Vy (Bàn 4) trong Pha 2
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
