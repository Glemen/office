"""
Phòng Biên Tập & Soạn Thảo Văn Bản 3D (Editorial Document Studio 3D)
Hỗ trợ 3 nguồn AI không cần cài thư viện ngoài (chỉ dùng Python chuẩn):
  1. Antigravity Live (tự động nhận diện nếu chạy trong Antigravity)
  2. Google Gemini API (dán API key trong Cài đặt trên web)
  3. OpenAI-compatible / Ollama local (VD: http://localhost:11434/v1)

Hỗ trợ 3 chế độ giao việc:
  - auto-best   : Tự chọn 1 chuyên viên giỏi nhất cho loại văn bản
  - split-merge : Chia nhiệm vụ lớn cho 3 chuyên viên làm song song → Vy tổng hợp bản hoàn chỉnh
  - direct      : Giao đích danh 1 bàn (0..3)
"""
import json
import os
import re
import threading
import time
import urllib.error
import urllib.request
from datetime import datetime
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

HOST = "127.0.0.1"
PORT = int(os.environ.get("OFFICE_PORT", "8080"))
BASE_DIR = Path(__file__).resolve().parent
RESULTS_DIR = BASE_DIR / "results"
RESULTS_DIR.mkdir(exist_ok=True)
INDEX_FILE = RESULTS_DIR / "index.json"
CONFIG_FILE = BASE_DIR / "config.local.json"

LS_ADDRESS = os.environ.get("ANTIGRAVITY_LS_ADDRESS", "")
CSRF_TOKEN = os.environ.get("ANTIGRAVITY_CSRF_TOKEN", "")
PROJECT_ID = os.environ.get("ANTIGRAVITY_PROJECT_ID", "")
BRAIN_DIR = Path.home() / ".gemini" / "antigravity" / "brain"

SPECIALISTS = [
    {
        "index": 0,
        "id": "BÀN 1",
        "name": "Minh",
        "role": "Nghiên cứu & Lập dàn ý",
        "specialty": "Phân tích yêu cầu, xây dựng cấu trúc, dàn ý chi tiết, luận điểm, số liệu và bối cảnh.",
    },
    {
        "index": 1,
        "id": "BÀN 2",
        "name": "Lan",
        "role": "Chấp bút & Soạn thảo chính",
        "specialty": "Soạn thảo công văn, báo cáo, đề án, tờ trình, kế hoạch, thư từ, bài phát biểu mạch lạc và chuẩn mực.",
    },
    {
        "index": 2,
        "id": "BÀN 3",
        "name": "Tuấn",
        "role": "Biên tập & Chuẩn thể thức",
        "specialty": "Hiệu đính văn phong, rà soát logic, kiểm tra thể thức văn bản hành chính (Nghị định 30), pháp lý và rủi ro.",
    },
    {
        "index": 3,
        "id": "BÀN 4",
        "name": "Vy",
        "role": "Tổng hợp & Xuất bản",
        "specialty": "Tổng hợp nhiều bản thảo thành 1 văn bản hoàn chỉnh, viết tóm tắt điều hành, bảng biểu và checklist thực thi.",
    },
]

STATE_LOCK = threading.Lock()
WORKER_STATES = [
    {
        **s,
        "status": "idle",  # idle | working | done | error
        "task": None,
        "phaseLabel": None,
        "startedAt": None,
        "lastResultId": None,
        "error": None,
    }
    for s in SPECIALISTS
]

PIPELINE_STATE = {
    "active": False,
    "mode": None,
    "phase": "idle",  # idle | phase1 | phase2 | done
    "task": None,
    "message": "Phòng biên tập đang sẵn sàng nhận lệnh",
}


def load_json(path: Path, default):
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return default
    return default


def save_json(path: Path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


RESULTS = load_json(INDEX_FILE, [])
CONFIG = load_json(
    CONFIG_FILE,
    {
        "provider": "auto",  # auto | antigravity | gemini | openai
        "geminiApiKey": os.environ.get("GEMINI_API_KEY", ""),
        "geminiModel": "gemini-2.5-flash",
        "openaiBaseUrl": "http://localhost:11434/v1",
        "openaiApiKey": os.environ.get("OPENAI_API_KEY", ""),
        "openaiModel": "qwen2.5:7b",
        "archiveAntigravity": True,
    },
)


def active_provider() -> str:
    pref = CONFIG.get("provider", "auto")
    has_agy = bool(LS_ADDRESS and CSRF_TOKEN)
    has_gemini = bool((CONFIG.get("geminiApiKey") or "").strip())
    has_openai = bool((CONFIG.get("openaiBaseUrl") or "").strip())
    if pref == "antigravity" and has_agy:
        return "antigravity"
    if pref == "gemini" and has_gemini:
        return "gemini"
    if pref == "openai" and has_openai:
        return "openai"
    # Auto fallback order
    if has_agy:
        return "antigravity"
    if has_gemini:
        return "gemini"
    if has_openai and (CONFIG.get("openaiApiKey") or "localhost" in CONFIG.get("openaiBaseUrl", "")):
        return "openai"
    return "none"


def slugify(text: str) -> str:
    s = re.sub(r"[^a-zA-Z0-9]+", "-", text.lower()).strip("-")
    return (s[:32] or "van-ban").strip("-")


def pick_best_specialist(task_text: str) -> tuple[int, str]:
    """Chọn chuyên viên phù hợp nhất dựa trên loại văn bản."""
    low = task_text.lower()
    scores = [0, 1, 0, 0]  # Lan (Chấp bút) mặc định ưu tiên nhẹ cho văn bản chung

    rules = [
        (0, ["dàn ý", "đề cương", "nghiên cứu", "phân tích", "khảo sát", "tìm hiểu", "luận điểm", "outline", "ý tưởng"]),
        (1, ["viết", "soạn", "công văn", "tờ trình", "báo cáo", "đề án", "kế hoạch", "thư", "email", "bài phát biểu", "thông báo", "biên bản", "quyết định"]),
        (2, ["biên tập", "sửa", "hiệu đính", "rà soát", "kiểm tra", "thể thức", "nghị định", "pháp lý", "hợp đồng", "rủi ro", "phản biện", "chính tả", "review"]),
        (3, ["tóm tắt", "tổng hợp", "bảng biểu", "checklist", "slide", "executive", "trình bày", "đóng gói", "tổng kết"]),
    ]
    for idx, keywords in rules:
        for kw in keywords:
            if kw in low:
                scores[idx] += 2

    # Sắp xếp ưu tiên theo điểm cao nhất, ưu tiên người đang rảnh
    ranked = sorted(range(4), key=lambda i: (scores[i], WORKER_STATES[i]["status"] != "working"), reverse=True)
    chosen = ranked[0]
    reasons = [
        "chuyên sâu về nghiên cứu & lập cấu trúc dàn ý",
        "chuyên sâu về chấp bút & soạn thảo văn bản chuẩn mực",
        "chuyên sâu về biên tập, hiệu đính & chuẩn thể thức",
        "chuyên sâu về tổng hợp, tóm tắt & trình bày bảng biểu",
    ]
    return chosen, reasons[chosen]


# ============================================================
# GỌI 3 NGUỒN AI (ANTIGRAVITY / GEMINI / OPENAI-OLLAMA)
# ============================================================
def agy_post(method: str, payload: dict) -> dict:
    url = f"http://{LS_ADDRESS}/product.v1.ConversationService/{method}"
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        method="POST",
        headers={
            "Content-Type": "application/json",
            "Connect-Protocol-Version": "1",
            "x-antigravity-csrf-token": CSRF_TOKEN,
        },
    )
    with urllib.request.urlopen(req, timeout=25) as resp:
        return json.loads(resp.read().decode("utf-8"))


def extract_transcript_reply(conv_id: str) -> str:
    log_dir = BRAIN_DIR / conv_id / ".system_generated" / "logs"
    for fname in ("transcript_full.jsonl", "transcript.jsonl"):
        p = log_dir / fname
        if not p.exists():
            continue
        last_text = ""
        try:
            for line in p.read_text(encoding="utf-8", errors="ignore").splitlines():
                line = line.strip()
                if not line:
                    continue
                obj = json.loads(line)
                role = obj.get("role") or obj.get("type") or ""
                if role in ("assistant", "model"):
                    content = obj.get("content") or obj.get("text") or ""
                    if isinstance(content, list):
                        content = "\n".join(
                            c.get("text", "") for c in content if isinstance(c, dict) and c.get("text")
                        )
                    if isinstance(content, str) and content.strip():
                        last_text = content.strip()
        except Exception:
            pass
        if last_text:
            return last_text
    return ""


def call_antigravity(title: str, prompt: str, target_file: Path) -> str:
    full_prompt = (
        f"{prompt}\n\n"
        f"Yêu cầu lưu kết quả:\n"
        f"- Ghi toàn bộ văn bản hoàn chỉnh (Markdown sạch, rõ ràng) vào file: `{target_file}` bằng công cụ `write_file` (Overwrite=true).\n"
        f"- Sau khi ghi xong, trả lời ngắn gọn xác nhận."
    )
    payload = {
        "title": title[:65],
        "model": "flash",
        "tags": ["doc-studio-3d"],
        "prompt": [{"text": full_prompt}],
    }
    if PROJECT_ID:
        payload["projectId"] = PROJECT_ID

    resp = agy_post("CreateConversation", payload)
    conv_id = resp.get("conversation", {}).get("id", "")
    started = time.time()
    seen_running = False
    time.sleep(2.5)
    while time.time() - started < 300:
        info = agy_post("GetConversation", {"conversationId": conv_id})
        run_state = info.get("state", {}).get("runState", "")
        if run_state == "RUN_STATE_RUNNING":
            seen_running = True
        elif run_state == "RUN_STATE_IDLE" and (
            seen_running or target_file.exists() or time.time() - started > 6
        ):
            break
        time.sleep(2.0)

    if CONFIG.get("archiveAntigravity", True) and conv_id:
        try:
            agy_post("UpdateConversation", {"conversationId": conv_id, "annotations": {"archived": True}})
        except Exception:
            pass

    if target_file.exists() and target_file.stat().st_size > 0:
        return target_file.read_text(encoding="utf-8", errors="replace")
    fallback = extract_transcript_reply(conv_id)
    if fallback:
        target_file.write_text(fallback, encoding="utf-8")
        return fallback
    raise RuntimeError("Antigravity hoàn tất nhưng không trả về nội dung.")


def call_gemini(prompt: str) -> str:
    api_key = (CONFIG.get("geminiApiKey") or "").strip()
    model = (CONFIG.get("geminiModel") or "gemini-2.5-flash").strip()
    if not api_key:
        raise RuntimeError("Chưa cấu hình Gemini API Key trong mục Cài đặt AI.")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
    body = json.dumps({"contents": [{"parts": [{"text": prompt}]}]}).encode("utf-8")
    req = urllib.request.Request(
        url, data=body, method="POST", headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    parts = data["candidates"][0]["content"]["parts"]
    return "\n".join(p.get("text", "") for p in parts if p.get("text")).strip()


def call_openai_compat(prompt: str) -> str:
    base = (CONFIG.get("openaiBaseUrl") or "http://localhost:11434/v1").rstrip("/")
    key = (CONFIG.get("openaiApiKey") or "ollama").strip()
    model = (CONFIG.get("openaiModel") or "qwen2.5:7b").strip()
    url = f"{base}/chat/completions"
    body = json.dumps(
        {
            "model": model,
            "messages": [
                {"role": "system", "content": "Bạn là chuyên viên soạn thảo văn bản tiếng Việt chuyên nghiệp."},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.4,
        }
    ).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=body,
        method="POST",
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {key}",
        },
    )
    with urllib.request.urlopen(req, timeout=180) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    return data["choices"][0]["message"]["content"].strip()


def run_ai(title: str, prompt: str, target_file: Path) -> str:
    prov = active_provider()
    if prov == "antigravity":
        return call_antigravity(title, prompt, target_file)
    if prov == "gemini":
        text = call_gemini(prompt)
        target_file.write_text(text, encoding="utf-8")
        return text
    if prov == "openai":
        text = call_openai_compat(prompt)
        target_file.write_text(text, encoding="utf-8")
        return text
    raise RuntimeError(
        "Chưa có nguồn AI nào hoạt động. Hãy mở mục 'Cài đặt AI' ở góc trên để nhập Gemini API Key hoặc Ollama."
    )


def record_deliverable(worker_idx: int, task_text: str, filename: str, content: str, mode_label: str) -> dict:
    w = SPECIALISTS[worker_idx]
    rid = filename.rsplit(".", 1)[0]
    preview = " ".join(content.replace("#", "").replace("*", "").split())[:150]
    rec = {
        "id": rid,
        "workerIndex": worker_idx,
        "workerId": w["id"],
        "workerName": w["name"],
        "workerRole": w["role"],
        "modeLabel": mode_label,
        "task": task_text,
        "filename": filename,
        "completedAt": datetime.now().strftime("%H:%M:%S %d/%m/%Y"),
        "preview": preview,
    }
    with STATE_LOCK:
        RESULTS.insert(0, rec)
        save_json(INDEX_FILE, RESULTS)
    return rec


# ============================================================
# 2 LUỒNG THỰC THI: ĐƠN LẺ (CHỌN NGƯỜI GIỎI NHẤT) & CHIA NHỎ + TỔNG HỢP
# ============================================================
def run_single_job(worker_idx: int, task_text: str, mode_label: str):
    spec = SPECIALISTS[worker_idx]
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{ts}_b{worker_idx + 1}_{slugify(task_text)}.md"
    target = RESULTS_DIR / filename

    prompt = (
        f"Bạn là **{spec['name']}** — {spec['role']} ({spec['id']}) tại Phòng Biên Tập Văn Bản.\n"
        f"Chuyên môn của bạn: {spec['specialty']}\n\n"
        f"Nhiệm vụ người dùng giao:\n> {task_text}\n\n"
        f"Hãy soạn thảo văn bản hoàn chỉnh, trình bày Markdown đẹp, rõ ràng, sẵn sàng đưa vào Microsoft Word sử dụng ngay (tiếng Việt chuẩn mực, trừ khi yêu cầu ngôn ngữ khác)."
    )
    try:
        content = run_ai(f"[{spec['id']} - {spec['name']}] {task_text}", prompt, target)
        rec = record_deliverable(worker_idx, task_text, filename, content, mode_label)
        with STATE_LOCK:
            w = WORKER_STATES[worker_idx]
            w["status"] = "done"
            w["lastResultId"] = rec["id"]
            w["phaseLabel"] = "Hoàn thành"
            PIPELINE_STATE["active"] = False
            PIPELINE_STATE["phase"] = "done"
            PIPELINE_STATE["message"] = f"{spec['name']} đã hoàn thành văn bản!"
    except Exception as exc:
        with STATE_LOCK:
            w = WORKER_STATES[worker_idx]
            w["status"] = "error"
            w["error"] = str(exc)
            PIPELINE_STATE["active"] = False
            PIPELINE_STATE["phase"] = "idle"
            PIPELINE_STATE["message"] = f"Lỗi: {exc}"


def run_split_merge_job(task_text: str):
    """Pha 1: Minh (0) + Lan (1) + Tuấn (2) chạy song song → Pha 2: Vy (3) tổng hợp 1 văn bản hoàn chỉnh."""
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    sub_tasks = [
        (
            0,
            "Lập dàn ý & luận điểm",
            f"Bạn là Minh (Nghiên cứu & Dàn ý). Với nhiệm vụ lớn sau:\n> {task_text}\n\n"
            f"Hãy xây dựng: (1) Bối cảnh & Mục tiêu cốt lõi, (2) Cấu trúc/Dàn ý chi tiết từng mục, (3) Các luận điểm, tiêu chí hoặc dữ liệu cần có. Viết súc tích, rõ ràng bằng Markdown.",
        ),
        (
            1,
            "Chấp bút nội dung chính",
            f"Bạn là Lan (Chấp bút & Soạn thảo chính). Với nhiệm vụ lớn sau:\n> {task_text}\n\n"
            f"Hãy viết phần nội dung chính chi tiết, lời văn chuyên nghiệp, mạch lạc, sẵn sàng dùng cho văn bản chính thức bằng Markdown.",
        ),
        (
            2,
            "Rà soát thể thức & rủi ro",
            f"Bạn là Tuấn (Biên tập & Chuẩn thể thức). Với nhiệm vụ lớn sau:\n> {task_text}\n\n"
            f"Hãy cung cấp: (1) Yêu cầu về thể thức/cấu trúc chuẩn văn bản, (2) Các rủi ro, điểm cần lưu ý, điều khoản/ràng buộc quan trọng, (3) Gợi ý hoàn thiện để văn bản thuyết phục nhất. Viết bằng Markdown.",
        ),
    ]

    with STATE_LOCK:
        PIPELINE_STATE.update(
            {
                "active": True,
                "mode": "split-merge",
                "phase": "phase1",
                "task": task_text,
                "message": "Pha 1: Minh, Lan, Tuấn đang xử lý song song 3 phần...",
            }
        )
        for idx, label, _ in sub_tasks:
            w = WORKER_STATES[idx]
            w["status"] = "working"
            w["task"] = task_text
            w["phaseLabel"] = label
            w["startedAt"] = time.time()
            w["error"] = None
        # Vy chuẩn bị ở chế độ chờ tổng hợp
        vy = WORKER_STATES[3]
        vy["status"] = "idle"
        vy["task"] = task_text
        vy["phaseLabel"] = "Chờ 3 phần để tổng hợp..."

    part_outputs = {}
    part_errors = {}

    def worker_part(idx, label, prompt):
        tmp_file = RESULTS_DIR / f".tmp_{ts}_p{idx}.md"
        try:
            text = run_ai(f"[Pha 1 - {SPECIALISTS[idx]['name']}] {task_text}", prompt, tmp_file)
            part_outputs[idx] = text
            with STATE_LOCK:
                WORKER_STATES[idx]["status"] = "done"
                WORKER_STATES[idx]["phaseLabel"] = "Đã chuyển cho Vy"
        except Exception as exc:
            part_errors[idx] = str(exc)
            with STATE_LOCK:
                WORKER_STATES[idx]["status"] = "error"
                WORKER_STATES[idx]["error"] = str(exc)
        finally:
            try:
                if tmp_file.exists():
                    tmp_file.unlink()
            except Exception:
                pass

    threads = [threading.Thread(target=worker_part, args=st, daemon=True) for st in sub_tasks]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    if not part_outputs:
        err_msg = "; ".join(part_errors.values()) or "Không có phần nào hoàn thành."
        with STATE_LOCK:
            PIPELINE_STATE.update({"active": False, "phase": "idle", "message": f"Lỗi Pha 1: {err_msg}"})
        return

    # Pha 2: Vy (Bàn 4) tổng hợp thành 1 văn bản hoàn chỉnh
    with STATE_LOCK:
        PIPELINE_STATE.update(
            {
                "phase": "phase2",
                "message": "Pha 2: Vy đang tổng hợp 3 bản thảo thành văn bản hoàn chỉnh...",
            }
        )
        vy = WORKER_STATES[3]
        vy["status"] = "working"
        vy["task"] = task_text
        vy["phaseLabel"] = "Tổng hợp & xuất bản"
        vy["startedAt"] = time.time()
        vy["error"] = None

    final_filename = f"{ts}_tonghop_{slugify(task_text)}.md"
    final_path = RESULTS_DIR / final_filename

    merge_prompt = (
        f"Bạn là **Vy** — Chuyên viên Tổng hợp & Xuất bản (BÀN 4).\n"
        f"Người dùng đã giao nhiệm vụ lớn:\n> {task_text}\n\n"
        f"3 đồng nghiệp đã hoàn thành các phần bổ trợ dưới đây. Hãy tổng hợp, biên tập lại thành **MỘT VĂN BẢN HOÀN CHỈNH DUY NHẤT**, "
        f"mạch lạc, không trùng lặp, trình bày Markdown chuẩn đẹp (có tiêu đề, tóm tắt điều hành, nội dung chi tiết, bảng/checklist hành động nếu phù hợp) để người dùng xuất thẳng sang Word sử dụng ngay:\n\n"
        f"--- PHẦN 1 (Minh - Nghiên cứu & Dàn ý) ---\n{part_outputs.get(0, '(Không có)')}\n\n"
        f"--- PHẦN 2 (Lan - Nội dung chính) ---\n{part_outputs.get(1, '(Không có)')}\n\n"
        f"--- PHẦN 3 (Tuấn - Thể thức & Lưu ý rủi ro) ---\n{part_outputs.get(2, '(Không có)')}\n"
    )

    try:
        final_content = run_ai(f"[Tổng hợp - Vy] {task_text}", merge_prompt, final_path)
        rec = record_deliverable(3, task_text, final_filename, final_content, "Chia 4 bàn & Tổng hợp")
        with STATE_LOCK:
            vy = WORKER_STATES[3]
            vy["status"] = "done"
            vy["lastResultId"] = rec["id"]
            vy["phaseLabel"] = "Đã xuất bản"
            PIPELINE_STATE.update(
                {
                    "active": False,
                    "phase": "done",
                    "message": "Hoàn tất! Vy đã tổng hợp xong văn bản hoàn chỉnh.",
                }
            )
    except Exception as exc:
        with STATE_LOCK:
            WORKER_STATES[3]["status"] = "error"
            WORKER_STATES[3]["error"] = str(exc)
            PIPELINE_STATE.update({"active": False, "phase": "idle", "message": f"Lỗi tổng hợp: {exc}"})


# ============================================================
# HTTP SERVER
# ============================================================
class StudioHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(BASE_DIR), **kwargs)

    def send_json(self, data, status=200):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/api/state":
            with STATE_LOCK:
                now = time.time()
                workers_out = []
                for w in WORKER_STATES:
                    item = dict(w)
                    item["elapsedSec"] = (
                        int(now - w["startedAt"])
                        if w["status"] == "working" and w["startedAt"]
                        else 0
                    )
                    workers_out.append(item)
                self.send_json(
                    {
                        "provider": active_provider(),
                        "hasAntigravity": bool(LS_ADDRESS and CSRF_TOKEN),
                        "pipeline": dict(PIPELINE_STATE),
                        "workers": workers_out,
                        "results": RESULTS[:40],
                    }
                )
            return

        if self.path == "/api/config":
            safe_cfg = {
                "provider": CONFIG.get("provider", "auto"),
                "geminiModel": CONFIG.get("geminiModel", "gemini-2.5-flash"),
                "hasGeminiKey": bool((CONFIG.get("geminiApiKey") or "").strip()),
                "openaiBaseUrl": CONFIG.get("openaiBaseUrl", "http://localhost:11434/v1"),
                "openaiModel": CONFIG.get("openaiModel", "qwen2.5:7b"),
                "hasOpenaiKey": bool((CONFIG.get("openaiApiKey") or "").strip()),
                "archiveAntigravity": CONFIG.get("archiveAntigravity", True),
                "hasAntigravity": bool(LS_ADDRESS and CSRF_TOKEN),
                "activeProvider": active_provider(),
            }
            self.send_json(safe_cfg)
            return

        if self.path.startswith("/api/result/"):
            rid = self.path.split("/api/result/", 1)[1].split("?", 1)[0]
            with STATE_LOCK:
                rec = next((r for r in RESULTS if r["id"] == rid), None)
            if not rec:
                self.send_json({"error": "Không tìm thấy văn bản"}, 404)
                return
            p = RESULTS_DIR / rec["filename"]
            content = p.read_text(encoding="utf-8", errors="replace") if p.exists() else ""
            self.send_json({**rec, "content": content})
            return

        super().do_GET()

    def do_POST(self):
        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length).decode("utf-8") if length else "{}"
        try:
            body = json.loads(raw)
        except Exception:
            self.send_json({"error": "JSON không hợp lệ"}, 400)
            return

        if self.path == "/api/config":
            if "provider" in body:
                CONFIG["provider"] = body["provider"]
            if body.get("geminiApiKey"):
                CONFIG["geminiApiKey"] = body["geminiApiKey"].strip()
            if body.get("geminiModel"):
                CONFIG["geminiModel"] = body["geminiModel"].strip()
            if body.get("openaiBaseUrl") is not None:
                CONFIG["openaiBaseUrl"] = body["openaiBaseUrl"].strip()
            if body.get("openaiApiKey"):
                CONFIG["openaiApiKey"] = body["openaiApiKey"].strip()
            if body.get("openaiModel"):
                CONFIG["openaiModel"] = body["openaiModel"].strip()
            if "archiveAntigravity" in body:
                CONFIG["archiveAntigravity"] = bool(body["archiveAntigravity"])
            save_json(CONFIG_FILE, CONFIG)
            self.send_json({"ok": True, "activeProvider": active_provider()})
            return

        if self.path == "/api/assign":
            task_text = (body.get("task") or "").strip()
            mode = body.get("mode", "auto-best")  # auto-best | split-merge | direct
            worker_idx = body.get("workerIndex")
            if not task_text:
                self.send_json({"error": "Vui lòng nhập nội dung văn bản cần làm."}, 400)
                return
            if active_provider() == "none":
                self.send_json(
                    {"error": "Chưa cấu hình nguồn AI. Hãy bấm 'Cài đặt AI' ở góc trên để thêm Gemini API Key hoặc Ollama."},
                    400,
                )
                return

            if mode == "split-merge":
                with STATE_LOCK:
                    if any(w["status"] == "working" for w in WORKER_STATES):
                        self.send_json(
                            {"error": "Đang có nhân viên bận. Chờ hoàn tất rồi chạy chế độ Chia 4 bàn & Tổng hợp nhé!"},
                            409,
                        )
                        return
                threading.Thread(target=run_split_merge_job, args=(task_text,), daemon=True).start()
                self.send_json({"ok": True, "mode": "split-merge"})
                return

            with STATE_LOCK:
                reason = ""
                if mode == "auto-best":
                    chosen, reason = pick_best_specialist(task_text)
                    mode_label = f"Tự chọn giỏi nhất ({SPECIALISTS[chosen]['name']})"
                else:
                    chosen = int(worker_idx)
                    mode_label = f"Giao trực tiếp ({SPECIALISTS[chosen]['id']})"
                w = WORKER_STATES[chosen]
                w["status"] = "working"
                w["task"] = task_text
                w["phaseLabel"] = "Đang soạn thảo..."
                w["startedAt"] = time.time()
                w["error"] = None
                PIPELINE_STATE.update(
                    {
                        "active": True,
                        "mode": mode,
                        "phase": "phase1",
                        "task": task_text,
                        "message": f"Đã chọn {w['name']} ({w['role']}) xử lý văn bản",
                    }
                )

            threading.Thread(
                target=run_single_job, args=(chosen, task_text, mode_label), daemon=True
            ).start()
            self.send_json(
                {
                    "ok": True,
                    "mode": mode,
                    "workerIndex": chosen,
                    "workerName": SPECIALISTS[chosen]["name"],
                    "reason": reason,
                }
            )
            return

        if self.path == "/api/cancel":
            idx = int(body.get("workerIndex", -1))
            with STATE_LOCK:
                if 0 <= idx < len(WORKER_STATES):
                    w = WORKER_STATES[idx]
                    w["status"] = "idle"
                    w["task"] = None
                    w["phaseLabel"] = None
                    w["startedAt"] = None
                    w["error"] = None
                    self.send_json({"ok": True})
                    return
            self.send_json({"error": "Bàn không hợp lệ"}, 400)
            return

        self.send_json({"error": "Not found"}, 404)

    def log_message(self, fmt, *args):
        pass


if __name__ == "__main__":
    srv = ThreadingHTTPServer((HOST, PORT), StudioHandler)
    print(f"Editorial Document Studio 3D running at http://{HOST}:{PORT} | AI Provider: {active_provider()}")
    srv.serve_forever()
