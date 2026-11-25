"""
Phòng Biên Tập & Tác Nhân Văn Phòng 3D (Editorial & Workspace Agent Studio 3D)
- Chuẩn thể thức Nghị định 30/2020/NĐ-CP (Word .docx thật + In/Lưu PDF khổ A4)
- Gửi Hình Ảnh Đa Phương Thức (Upload / Ctrl+V dán ảnh chụp màn hình, ảnh văn bản giấy, bảng biểu...)
- Chế độ Thư Mục Làm Việc (Workspace Folder Mode — thao tác đọc/tạo/sửa file & xuất kết quả trực tiếp trong thư mục được chọn, tương đương Antigravity)
- Lưu sẵn Hồ sơ Đơn vị + Chỉnh sửa nhanh văn bản trên trình duyệt
- 3 chế độ điều phối: Tự chọn người giỏi nhất | Chia 3 bàn & Vy tổng hợp | Giao đích danh
"""
import base64
import json
import os
import re
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request
import webbrowser
from datetime import datetime
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from docx_nd30 import (
    build_docx,
    default_date_str,
    doc_data_to_markdown,
    extract_docx_bytes,
    normalize_doc_data,
    render_nd30_print_html,
)

HOST = "127.0.0.1"
PORT = int(os.environ.get("OFFICE_PORT", "8080"))
IS_FROZEN = getattr(sys, "frozen", False)
RESOURCE_DIR = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
APP_DIR = Path(sys.executable).resolve().parent if IS_FROZEN else Path(__file__).resolve().parent
RESULTS_DIR = APP_DIR / "results"
UPLOADS_DIR = RESULTS_DIR / "_uploads"
RESULTS_DIR.mkdir(exist_ok=True)
UPLOADS_DIR.mkdir(exist_ok=True)
INDEX_FILE = RESULTS_DIR / "index.json"
CONFIG_FILE = APP_DIR / "config.local.json"

LS_ADDRESS = os.environ.get("ANTIGRAVITY_LS_ADDRESS", "")
CSRF_TOKEN = os.environ.get("ANTIGRAVITY_CSRF_TOKEN", "")
PROJECT_ID = os.environ.get("ANTIGRAVITY_PROJECT_ID", "")
BRAIN_DIR = Path.home() / ".gemini" / "antigravity" / "brain"

SPECIALISTS = [
    {
        "index": 0,
        "id": "BÀN 1",
        "name": "Minh",
        "role": "Nghiên cứu & Phân tích",
        "specialty": "Phân tích hình ảnh/tài liệu/thư mục, lập đề cương, trích xuất dữ liệu và căn cứ pháp lý.",
    },
    {
        "index": 1,
        "id": "BÀN 2",
        "name": "Lan",
        "role": "Chấp bút & Soạn thảo",
        "specialty": "Soạn thảo công văn, báo cáo, kế hoạch, tờ trình, quyết định, thông báo, biên bản chuẩn văn phong hành chính.",
    },
    {
        "index": 2,
        "id": "BÀN 3",
        "name": "Tuấn",
        "role": "Biên tập & Tác vụ Thư mục",
        "specialty": "Hiệu đính chuẩn Nghị định 30/2020/NĐ-CP, xử lý file/code/tự động hóa trực tiếp trong thư mục làm việc.",
    },
    {
        "index": 3,
        "id": "BÀN 4",
        "name": "Vy",
        "role": "Tổng hợp & Xuất bản",
        "specialty": "Tổng hợp nhiều nguồn tài liệu/hình ảnh/bản thảo thành sản phẩm hoàn chỉnh, lập bảng biểu và xuất bản.",
    },
]

STATE_LOCK = threading.Lock()
WORKER_STATES = [
    {
        **s,
        "status": "idle",
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
    "phase": "idle",
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
DEFAULT_CONFIG = {
    "provider": "auto",
    "antigravityModel": "pro",
    "geminiApiKey": os.environ.get("GEMINI_API_KEY", ""),
    "geminiModel": "gemini-2.5-pro",
    "openaiBaseUrl": "http://localhost:11434/v1",
    "openaiApiKey": os.environ.get("OPENAI_API_KEY", ""),
    "openaiModel": "qwen2.5:7b",
    "archiveAntigravity": True,
    "orgProfile": {
        "coQuanChuQuan": "",
        "coQuanBanHanh": "",
        "kyHieuDonVi": "ĐV",
        "diaDanh": "Hà Nội",
        "chucVuKy": "THỦ TRƯỞNG ĐƠN VỊ",
        "nguoiKy": "",
    },
}
CONFIG = {**DEFAULT_CONFIG, **load_json(CONFIG_FILE, {})}
CONFIG["orgProfile"] = {**DEFAULT_CONFIG["orgProfile"], **(CONFIG.get("orgProfile") or {})}


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


def pick_best_specialist(task_text: str, has_images: bool = False, has_workspace: bool = False) -> tuple[int, str]:
    low = task_text.lower()
    scores = [0, 1, 0, 0]
    if has_images:
        scores[0] += 1  # Minh mạnh về đọc/bóc tách ảnh
    if has_workspace:
        scores[2] += 1  # Tuấn mạnh về xử lý file/code trong thư mục
    rules = [
        (0, ["dàn ý", "đề cương", "nghiên cứu", "phân tích", "khảo sát", "tìm hiểu", "bóc tách", "nhận diện", "đọc ảnh"]),
        (1, ["viết", "soạn", "công văn", "tờ trình", "báo cáo", "đề án", "kế hoạch", "thông báo", "biên bản", "quyết định", "giấy mời"]),
        (2, ["biên tập", "sửa", "hiệu đính", "rà soát", "thể thức", "nghị định 30", "nđ30", "code", "script", "python", "đổi tên", "sắp xếp", "tạo file", "thư mục"]),
        (3, ["tóm tắt", "tổng hợp", "bảng biểu", "checklist", "phụ lục", "trình bày", "tổng kết"]),
    ]
    for idx, keywords in rules:
        for kw in keywords:
            if kw in low:
                scores[idx] += 2
    ranked = sorted(range(4), key=lambda i: (scores[i], WORKER_STATES[i]["status"] != "working"), reverse=True)
    chosen = ranked[0]
    reasons = [
        "chuyên sâu nghiên cứu, bóc tách ảnh & lập đề cương",
        "chuyên sâu chấp bút văn bản hành chính",
        "chuyên sâu chuẩn Nghị định 30 & xử lý thư mục làm việc",
        "chuyên sâu tổng hợp, tóm tắt & xuất bản",
    ]
    return chosen, reasons[chosen]


# ============================================================
# HỖ TRỢ THƯ MỤC LÀM VIỆC (WORKSPACE FOLDER) & ẢNH ĐÍNH KÈM
# ============================================================
def pick_windows_folder() -> str:
    """Mở hộp thoại chọn thư mục gốc của Windows nổi lên trên trình duyệt (0 KB phụ thuộc)."""
    ps_script = (
        "[Console]::OutputEncoding = [System.Text.Encoding]::UTF8; "
        "Add-Type -AssemblyName System.Windows.Forms; "
        "$top = New-Object System.Windows.Forms.Form; $top.TopMost = $true; "
        "$dlg = New-Object System.Windows.Forms.FolderBrowserDialog; "
        "$dlg.Description = 'Chọn thư mục làm việc cho Chuyên viên AI (chỉ thao tác trong thư mục này)'; "
        "$dlg.ShowNewFolderButton = $true; "
        "if ($dlg.ShowDialog($top) -eq [System.Windows.Forms.DialogResult]::OK) { Write-Output $dlg.SelectedPath }"
    )
    res = subprocess.run(
        ["powershell", "-NoProfile", "-STA", "-Command", ps_script],
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=120,
    )
    return (res.stdout or "").strip()


def summarize_workspace_dir(ws_dir: str, include_file_snippets: bool = False) -> str:
    """Liệt kê danh sách file trong thư mục làm việc để cung cấp ngữ cảnh cho AI."""
    p = Path(ws_dir)
    if not p.is_dir():
        return ""
    lines = [f"Thư mục làm việc được chỉ định: `{p}`"]
    files_listed = 0
    snippets = []
    skip_dirs = {".git", "__pycache__", "node_modules", ".venv", "venv", "dist", "build"}
    for root, dirs, files in os.walk(p):
        dirs[:] = [d for d in dirs if d not in skip_dirs]
        rel_root = Path(root).relative_to(p)
        for fn in sorted(files):
            if files_listed >= 80:
                break
            fp = Path(root) / fn
            rel_path = fp.relative_to(p)
            try:
                sz = fp.stat().st_size
            except OSError:
                sz = 0
            lines.append(f"  - {rel_path} ({sz} bytes)")
            files_listed += 1
            if include_file_snippets and len(snippets) < 8 and sz < 300_000:
                ext = fp.suffix.lower()
                try:
                    if ext == ".docx":
                        txt = extract_docx_bytes(fp.read_bytes())[:2500]
                        snippets.append(f"### Nội dung `{rel_path}`:\n{txt}")
                    elif ext in {".txt", ".md", ".csv", ".json", ".py", ".js", ".html"}:
                        txt = fp.read_text(encoding="utf-8", errors="replace")[:2500]
                        snippets.append(f"### Nội dung `{rel_path}`:\n{txt}")
                except Exception:
                    pass
    out = "\n".join(lines)
    if snippets:
        out += "\n\nMột số nội dung tệp trong thư mục:\n" + "\n\n".join(snippets)
    return out


def stage_uploaded_images(images: list[dict], prefix: str) -> list[dict]:
    """Lưu tạm các ảnh gửi kèm ra đĩa để Antigravity dùng read_file đọc trực tiếp, hoặc gửi inline sang Gemini/OpenAI."""
    staged = []
    for idx, img in enumerate(images or []):
        b64 = (img.get("dataBase64") or "").strip()
        if not b64:
            continue
        mime = (img.get("mimeType") or "image/png").strip()
        ext = ".png"
        if "jpeg" in mime or "jpg" in mime:
            ext = ".jpg"
        elif "webp" in mime:
            ext = ".webp"
        elif "gif" in mime:
            ext = ".gif"
        safe_name = re.sub(r"[^a-zA-Z0-9._-]+", "_", img.get("name") or f"image_{idx}{ext}")
        if not safe_name.lower().endswith((".png", ".jpg", ".jpeg", ".webp", ".gif")):
            safe_name += ext
        fpath = UPLOADS_DIR / f"{prefix}_{idx}_{safe_name}"
        fpath.write_bytes(base64.b64decode(b64))
        staged.append(
            {
                "name": img.get("name") or safe_name,
                "mimeType": mime,
                "dataBase64": b64,
                "path": fpath,
            }
        )
    return staged


def cleanup_staged_images(staged: list[dict]):
    for item in staged:
        p = item.get("path")
        if isinstance(p, Path) and p.exists():
            try:
                p.unlink()
            except Exception:
                pass


def build_nd30_schema_prompt(workspace_dir: str = "") -> str:
    org = CONFIG.get("orgProfile") or {}
    cqcq = org.get("coQuanChuQuan") or "(Tên cơ quan chủ quản cấp trên nếu phù hợp, hoặc để rỗng)"
    cqbh = org.get("coQuanBanHanh") or "ĐƠN VỊ BAN HÀNH"
    kh = org.get("kyHieuDonVi") or "ĐV"
    place = org.get("diaDanh") or "Hà Nội"
    cv = org.get("chucVuKy") or "THỦ TRƯỞNG ĐƠN VỊ"
    nk = org.get("nguoiKy") or ""
    date_example = default_date_str(place)

    ws_rule = ""
    if workspace_dir:
        ws_rule = (
            f"\nCHẾ ĐỘ THƯ MỤC LÀM VIỆC ĐANG BẬT (`{workspace_dir}`):\n"
            f"- Bạn đóng vai trò Tác nhân Antigravity làm việc trực tiếp trên thư mục `{workspace_dir}`.\n"
            f"- Bạn ĐƯỢC PHÉP đọc các file trong `{workspace_dir}`, tạo/chỉnh sửa file code/dữ liệu/tài liệu hoặc chạy lệnh **CHỈ BÊN TRONG phạm vi thư mục `{workspace_dir}`** (tuyệt đối không sửa các thư mục khác ngoài `{workspace_dir}`).\n"
            f"- Sau khi hoàn tất thao tác trong thư mục (hoặc khi soạn văn bản từ dữ liệu của thư mục), vẫn trả về khối JSON chuẩn dưới đây để hệ thống xuất báo cáo/văn bản `.docx` lưu vào cả `{workspace_dir}` và Kho văn bản.\n"
        )

    return f"""{ws_rule}
Thông tin đơn vị mặc định của người dùng (ưu tiên áp dụng nếu yêu cầu không nêu tên đơn vị khác):
- Cơ quan chủ quản: "{cqcq}"
- Cơ quan/Đơn vị ban hành: "{cqbh}"
- Chữ viết tắt đơn vị: "{kh}"
- Địa danh & ngày tháng: "{date_example}"
- Chức vụ người ký: "{cv}" | Họ tên người ký: "{nk}"

BẮT BUỘC trả về kết quả cuối cùng dưới dạng 1 khối ```json ... ``` hợp lệ theo đúng Nghị định 30/2020/NĐ-CP:
```json
{{
  "loai_van_ban": "van_ban_co_ten_loai hoặc cong_van (dùng cong_van cho Công văn V/v...; dùng van_ban_co_ten_loai cho Báo cáo, Kế hoạch, Tờ trình, Quyết định, Thông báo, Đề án, Biên bản...)",
  "co_quan_chu_quan": "TÊN CƠ QUAN CHỦ QUẢN IN HOA (hoặc chuỗi rỗng)",
  "co_quan_ban_hanh": "TÊN CƠ QUAN BAN HÀNH IN HOA",
  "so_ky_hieu": "Số: .../(BC, KH, TTr, QĐ, TB, BB...)-{kh}",
  "dia_danh_ngay": "{date_example}",
  "ten_loai": "TÊN LOẠI VĂN BẢN IN HOA (VD: KẾ HOẠCH, BÁO CÁO, TỜ TRÌNH, QUYẾT ĐỊNH; để rỗng nếu là cong_van)",
  "trich_yeu": "Trích yếu nội dung ngắn gọn, chuẩn xác",
  "kinh_gui": ["Danh sách nơi Kính gửi (nếu có; để [] nếu không cần)"],
  "can_cu": ["Căn cứ ...; (nếu là Quyết định, Kế hoạch; để [] nếu không cần)"],
  "noi_dung": "Toàn bộ nội dung chi tiết, đầy đủ, sâu sắc, chuẩn văn phong hành chính (hoặc báo cáo chi tiết kết quả xử lý thư mục/hình ảnh). Dùng \\n xuống dòng giữa các đoạn; dùng ## cho các mục lớn; dùng - cho các ý liệt kê; có thể kẻ bảng Markdown |...|. KHÔNG lặp lại Quốc hiệu, Số ký hiệu, Nơi nhận hay Chữ ký trong noi_dung.",
  "quyen_han_ky": "",
  "chuc_vu_ky": "{cv}",
  "nguoi_ky": "{nk}",
  "noi_nhan": ["- Như trên;", "- Lưu: VT, {kh}."]
}}
```
Chỉ xuất duy nhất 1 khối ```json ... ``` hợp lệ cho phần trả lời cuối.
"""


# ============================================================
# GỌI 3 NGUỒN AI (CÓ ĐA PHƯƠNG THỨC HÌNH ẢNH + THƯ MỤC LÀM VIỆC)
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


def call_antigravity(title: str, prompt: str, target_file: Path, staged_images: list[dict] | None = None) -> str:
    img_block = ""
    if staged_images:
        img_paths = "\n".join(f"  - `{item['path']}` ({item['name']})" for item in staged_images)
        img_block = (
            f"\nNGƯỜI DÙNG GỬI KÈM {len(staged_images)} HÌNH ẢNH:\n{img_paths}\n"
            f"-> BẮT BUỘC gọi công cụ `read_file` trên từng đường dẫn ảnh ở trên NGAY ĐẦU TIÊN để quan sát trực tiếp toàn bộ chữ, số liệu, bố cục trong ảnh rồi mới thực hiện yêu cầu!\n"
        )

    full_prompt = (
        f"{img_block}\n{prompt}\n\n"
        f"Yêu cầu lưu kết quả cuối:\n"
        f"- Ghi nguyên văn khối JSON kết quả vào file: `{target_file}` bằng công cụ `write_file` (Overwrite=true).\n"
        f"- Sau khi ghi xong, trả lời ngắn gọn xác nhận."
    )
    agy_model = (CONFIG.get("antigravityModel") or "pro").strip()
    payload = {
        "title": title[:65],
        "model": agy_model,
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
    while time.time() - started < 420:
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


def call_gemini(prompt: str, staged_images: list[dict] | None = None) -> str:
    api_key = (CONFIG.get("geminiApiKey") or "").strip()
    model = (CONFIG.get("geminiModel") or "gemini-2.5-pro").strip()
    if not api_key:
        raise RuntimeError("Chưa cấu hình Gemini API Key trong mục Cài đặt.")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
    parts = []
    for img in staged_images or []:
        parts.append({"inline_data": {"mime_type": img["mimeType"], "data": img["dataBase64"]}})
    parts.append({"text": prompt})
    body = json.dumps({"contents": [{"parts": parts}]}).encode("utf-8")
    req = urllib.request.Request(
        url, data=body, method="POST", headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=180) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    out_parts = data["candidates"][0]["content"]["parts"]
    return "\n".join(p.get("text", "") for p in out_parts if p.get("text")).strip()


def call_openai_compat(prompt: str, staged_images: list[dict] | None = None) -> str:
    base = (CONFIG.get("openaiBaseUrl") or "http://localhost:11434/v1").rstrip("/")
    key = (CONFIG.get("openaiApiKey") or "ollama").strip()
    model = (CONFIG.get("openaiModel") or "qwen2.5:7b").strip()
    url = f"{base}/chat/completions"
    if staged_images:
        user_content = [{"type": "text", "text": prompt}]
        for img in staged_images:
            user_content.append(
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:{img['mimeType']};base64,{img['dataBase64']}"},
                }
            )
    else:
        user_content = prompt

    body = json.dumps(
        {
            "model": model,
            "messages": [
                {"role": "system", "content": "Bạn là chuyên viên cao cấp về công tác văn thư theo Nghị định 30/2020/NĐ-CP."},
                {"role": "user", "content": user_content},
            ],
            "temperature": 0.35,
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
    with urllib.request.urlopen(req, timeout=240) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    return data["choices"][0]["message"]["content"].strip()


def run_ai(title: str, prompt: str, target_file: Path, staged_images: list[dict] | None = None) -> str:
    prov = active_provider()
    if prov == "antigravity":
        return call_antigravity(title, prompt, target_file, staged_images)
    if prov == "gemini":
        text = call_gemini(prompt, staged_images)
        target_file.write_text(text, encoding="utf-8")
        return text
    if prov == "openai":
        text = call_openai_compat(prompt, staged_images)
        target_file.write_text(text, encoding="utf-8")
        return text
    raise RuntimeError("Chưa có nguồn AI hoạt động. Hãy mở mục 'Cài đặt' góc trên để cấu hình.")


def save_deliverable_files(base_name: str, doc_data: dict, workspace_dir: str = "") -> tuple[str, str, str, str, str]:
    md_content = doc_data_to_markdown(doc_data)
    md_filename = f"{base_name}.md"
    docx_filename = f"{base_name}.docx"
    json_filename = f"{base_name}.json"

    (RESULTS_DIR / md_filename).write_text(md_content, encoding="utf-8")
    save_json(RESULTS_DIR / json_filename, doc_data)
    build_docx(doc_data, RESULTS_DIR / docx_filename)

    # Nếu người dùng chọn Thư mục làm việc, xuất luôn bản .docx trực tiếp vào thư mục đó!
    ws_saved_path = ""
    if workspace_dir:
        ws_p = Path(workspace_dir)
        if ws_p.is_dir():
            try:
                ws_docx = ws_p / docx_filename
                build_docx(doc_data, ws_docx)
                ws_saved_path = str(ws_docx)
            except Exception:
                pass
    return md_filename, docx_filename, json_filename, md_content, ws_saved_path


def record_deliverable(
    worker_idx: int,
    task_text: str,
    base_name: str,
    raw_output: str,
    mode_label: str,
    workspace_dir: str = "",
) -> dict:
    w = SPECIALISTS[worker_idx]
    doc_data = normalize_doc_data(
        raw_output,
        fallback_title=task_text,
        org_profile=CONFIG.get("orgProfile"),
    )
    md_fn, docx_fn, json_fn, _, ws_saved = save_deliverable_files(base_name, doc_data, workspace_dir)
    preview = " ".join(doc_data["noi_dung"].replace("#", "").replace("*", "").split())[:155]
    rec = {
        "id": base_name,
        "workerIndex": worker_idx,
        "workerId": w["id"],
        "workerName": w["name"],
        "workerRole": w["role"],
        "modeLabel": mode_label,
        "task": task_text,
        "filename": md_fn,
        "docxFilename": docx_fn,
        "jsonFilename": json_fn,
        "workspaceDir": workspace_dir,
        "workspaceSavedDocx": ws_saved,
        "completedAt": datetime.now().strftime("%H:%M:%S %d/%m/%Y"),
        "preview": preview,
    }
    with STATE_LOCK:
        RESULTS.insert(0, rec)
        save_json(INDEX_FILE, RESULTS)
    return rec


# ============================================================
# LUỒNG THỰC THI CÔNG VIỆC
# ============================================================
def run_single_job(
    worker_idx: int,
    task_text: str,
    mode_label: str,
    ref_text: str = "",
    images: list[dict] | None = None,
    workspace_dir: str = "",
):
    spec = SPECIALISTS[worker_idx]
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    base_name = f"{ts}_b{worker_idx + 1}_{slugify(task_text)}"
    target = RESULTS_DIR / f".raw_{base_name}.txt"
    staged_imgs = stage_uploaded_images(images or [], base_name)

    ws_summary = ""
    if workspace_dir:
        include_snips = active_provider() != "antigravity"
        ws_summary = summarize_workspace_dir(workspace_dir, include_file_snippets=include_snips)

    ref_section = (
        f"\n--- TÀI LIỆU THAM KHẢO ĐÍNH KÈM ---\n{ref_text[:18000]}\n--- HẾT TÀI LIỆU ---\n"
        if ref_text.strip()
        else ""
    )
    ws_section = f"\n--- THÔNG TIN THƯ MỤC LÀM VIỆC ---\n{ws_summary}\n---\n" if ws_summary else ""

    prompt = (
        f"Bạn là **{spec['name']}** — {spec['role']} ({spec['id']}) tại Phòng Biên Tập Văn Bản.\n"
        f"Chuyên môn: {spec['specialty']}\n\n"
        f"Yêu cầu của người dùng:\n> {task_text}\n"
        f"{ws_section}{ref_section}\n"
        f"Hãy thực hiện thật sâu sắc, chính xác (nếu có ảnh gửi kèm thì đọc kỹ nội dung trong ảnh; nếu có thư mục làm việc thì thao tác đúng trong phạm vi thư mục đó) và xuất kết quả chuẩn Nghị định 30/2020/NĐ-CP.\n"
        f"{build_nd30_schema_prompt(workspace_dir)}"
    )
    try:
        raw_out = run_ai(f"[{spec['id']} - {spec['name']}] {task_text}", prompt, target, staged_imgs)
        rec = record_deliverable(worker_idx, task_text, base_name, raw_out, mode_label, workspace_dir)
        with STATE_LOCK:
            w = WORKER_STATES[worker_idx]
            w["status"] = "done"
            w["lastResultId"] = rec["id"]
            w["phaseLabel"] = "Hoàn thành"
            PIPELINE_STATE["active"] = False
            PIPELINE_STATE["phase"] = "done"
            PIPELINE_STATE["message"] = f"{spec['name']} đã hoàn thành nhiệm vụ!"
    except Exception as exc:
        with STATE_LOCK:
            w = WORKER_STATES[worker_idx]
            w["status"] = "error"
            w["error"] = str(exc)
            PIPELINE_STATE["active"] = False
            PIPELINE_STATE["phase"] = "idle"
            PIPELINE_STATE["message"] = f"Lỗi: {exc}"
    finally:
        cleanup_staged_images(staged_imgs)
        try:
            if target.exists():
                target.unlink()
        except Exception:
            pass


def run_split_merge_job(
    task_text: str,
    ref_text: str = "",
    images: list[dict] | None = None,
    workspace_dir: str = "",
):
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    base_name = f"{ts}_tonghop_{slugify(task_text)}"
    staged_imgs = stage_uploaded_images(images or [], base_name)

    ws_summary = ""
    if workspace_dir:
        include_snips = active_provider() != "antigravity"
        ws_summary = summarize_workspace_dir(workspace_dir, include_file_snippets=include_snips)

    extra_ctx = ""
    if ws_summary:
        extra_ctx += f"\nThư mục làm việc được giao (`{workspace_dir}` — chỉ thao tác trong thư mục này):\n{ws_summary}\n"
    if ref_text.strip():
        extra_ctx += f"\nTài liệu tham khảo đính kèm:\n{ref_text[:14000]}\n"

    sub_tasks = [
        (
            0,
            "Phân tích & Đề cương",
            f"Bạn là Minh (Nghiên cứu & Phân tích). Với nhiệm vụ lớn:\n> {task_text}\n{extra_ctx}\n"
            f"Hãy đọc kỹ hình ảnh/thư mục/tài liệu (nếu có) và xây dựng: (1) Dữ liệu, căn cứ thực tiễn & pháp lý, (2) Đề cương chi tiết từng mục, (3) Các chỉ tiêu/mốc tiến độ cốt lõi.",
        ),
        (
            1,
            "Chấp bút nội dung",
            f"Bạn là Lan (Chấp bút & Soạn thảo). Với nhiệm vụ lớn:\n> {task_text}\n{extra_ctx}\n"
            f"Hãy viết phần nội dung chi tiết, đầy đủ giải pháp và phân công thực hiện với văn phong hành chính công vụ chuẩn mực Việt Nam.",
        ),
        (
            2,
            "Thư mục & Thể thức NĐ30",
            f"Bạn là Tuấn (Biên tập & Tác vụ Thư mục). Với nhiệm vụ lớn:\n> {task_text}\n{extra_ctx}\n"
            f"Nếu có yêu cầu tạo/cập nhật file phụ trợ trong thư mục `{workspace_dir}` thì thực hiện chỉ trong thư mục đó; đồng thời xác định chuẩn thể thức Phụ lục I & III Nghị định 30/2020/NĐ-CP, Kính gửi, Nơi nhận và các lưu ý quan trọng.",
        ),
    ]

    with STATE_LOCK:
        PIPELINE_STATE.update(
            {
                "active": True,
                "mode": "split-merge",
                "phase": "phase1",
                "task": task_text,
                "message": "Pha 1: Minh, Lan, Tuấn đang xử lý song song...",
            }
        )
        for idx, label, _ in sub_tasks:
            w = WORKER_STATES[idx]
            w["status"] = "working"
            w["task"] = task_text
            w["phaseLabel"] = label
            w["startedAt"] = time.time()
            w["error"] = None
        vy = WORKER_STATES[3]
        vy["status"] = "idle"
        vy["task"] = task_text
        vy["phaseLabel"] = "Chờ 3 phần để tổng hợp..."

    part_outputs = {}
    part_errors = {}

    def worker_part(idx, label, prompt):
        tmp_file = RESULTS_DIR / f".tmp_{ts}_p{idx}.md"
        try:
            text = run_ai(f"[Pha 1 - {SPECIALISTS[idx]['name']}] {task_text}", prompt, tmp_file, staged_imgs)
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
        cleanup_staged_images(staged_imgs)
        err_msg = "; ".join(part_errors.values()) or "Không có phần nào hoàn thành."
        with STATE_LOCK:
            PIPELINE_STATE.update({"active": False, "phase": "idle", "message": f"Lỗi Pha 1: {err_msg}"})
        return

    with STATE_LOCK:
        PIPELINE_STATE.update(
            {
                "phase": "phase2",
                "message": "Pha 2: Vy đang tổng hợp 3 phần thành văn bản chuẩn NĐ30...",
            }
        )
        vy = WORKER_STATES[3]
        vy["status"] = "working"
        vy["task"] = task_text
        vy["phaseLabel"] = "Tổng hợp & chuẩn hóa NĐ30"
        vy["startedAt"] = time.time()
        vy["error"] = None

    raw_final_path = RESULTS_DIR / f".raw_{base_name}.txt"
    merge_prompt = (
        f"Bạn là **Vy** — Chuyên viên Tổng hợp & Xuất bản (BÀN 4).\n"
        f"Nhiệm vụ lớn của người dùng:\n> {task_text}\n\n"
        f"Hãy hợp nhất 3 phần dưới đây thành **MỘT VĂN BẢN HOÀN CHỈNH DUY NHẤT**, "
        f"chặt chẽ, không trùng lặp và chuẩn Nghị định 30/2020/NĐ-CP:\n\n"
        f"--- PHẦN 1 (Minh) ---\n{part_outputs.get(0, '(Không có)')}\n\n"
        f"--- PHẦN 2 (Lan) ---\n{part_outputs.get(1, '(Không có)')}\n\n"
        f"--- PHẦN 3 (Tuấn) ---\n{part_outputs.get(2, '(Không có)')}\n\n"
        f"{build_nd30_schema_prompt(workspace_dir)}"
    )

    try:
        final_raw = run_ai(f"[Tổng hợp - Vy] {task_text}", merge_prompt, raw_final_path, staged_imgs)
        rec = record_deliverable(3, task_text, base_name, final_raw, "Chia 4 bàn & Tổng hợp", workspace_dir)
        with STATE_LOCK:
            vy = WORKER_STATES[3]
            vy["status"] = "done"
            vy["lastResultId"] = rec["id"]
            vy["phaseLabel"] = "Đã xuất bản chuẩn NĐ30"
            PIPELINE_STATE.update(
                {
                    "active": False,
                    "phase": "done",
                    "message": "Hoàn tất! Vy đã tổng hợp xong văn bản chuẩn Nghị định 30.",
                }
            )
    except Exception as exc:
        with STATE_LOCK:
            WORKER_STATES[3]["status"] = "error"
            WORKER_STATES[3]["error"] = str(exc)
            PIPELINE_STATE.update({"active": False, "phase": "idle", "message": f"Lỗi tổng hợp: {exc}"})
    finally:
        cleanup_staged_images(staged_imgs)
        try:
            if raw_final_path.exists():
                raw_final_path.unlink()
        except Exception:
            pass


# ============================================================
# HTTP SERVER
# ============================================================
class StudioHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(RESOURCE_DIR), **kwargs)

    def send_json(self, data, status=200):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _load_doc_data(self, rec: dict) -> dict:
        rid = rec["id"]
        json_p = RESULTS_DIR / rec.get("jsonFilename", f"{rid}.json")
        md_p = RESULTS_DIR / rec["filename"]
        if json_p.exists():
            loaded = load_json(json_p, None)
            if isinstance(loaded, dict):
                return loaded
        raw_md = md_p.read_text(encoding="utf-8", errors="replace") if md_p.exists() else ""
        return normalize_doc_data(raw_md, fallback_title=rec.get("task", "Văn bản"), org_profile=CONFIG.get("orgProfile"))

    def do_GET(self):
        if self.path.startswith("/results/"):
            fname = urllib.request.unquote(self.path.split("/results/", 1)[1].split("?", 1)[0])
            target = (RESULTS_DIR / Path(fname).name).resolve()
            if target.parent == RESULTS_DIR.resolve() and target.is_file():
                data = target.read_bytes()
                self.send_response(200)
                self.send_header("Content-Type", "application/octet-stream")
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)
                return
            self.send_json({"error": "File not found"}, 404)
            return

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
                        "orgUnit": (CONFIG.get("orgProfile") or {}).get("coQuanBanHanh") or "",
                        "pipeline": dict(PIPELINE_STATE),
                        "workers": workers_out,
                        "results": RESULTS[:50],
                    }
                )
            return

        if self.path == "/api/config":
            safe_cfg = {
                "provider": CONFIG.get("provider", "auto"),
                "antigravityModel": CONFIG.get("antigravityModel", "pro"),
                "geminiModel": CONFIG.get("geminiModel", "gemini-2.5-pro"),
                "hasGeminiKey": bool((CONFIG.get("geminiApiKey") or "").strip()),
                "openaiBaseUrl": CONFIG.get("openaiBaseUrl", "http://localhost:11434/v1"),
                "openaiModel": CONFIG.get("openaiModel", "qwen2.5:7b"),
                "hasOpenaiKey": bool((CONFIG.get("openaiApiKey") or "").strip()),
                "archiveAntigravity": CONFIG.get("archiveAntigravity", True),
                "hasAntigravity": bool(LS_ADDRESS and CSRF_TOKEN),
                "activeProvider": active_provider(),
                "orgProfile": CONFIG.get("orgProfile") or DEFAULT_CONFIG["orgProfile"],
            }
            self.send_json(safe_cfg)
            return

        if self.path.startswith("/api/result/"):
            rest = self.path.split("/api/result/", 1)[1].split("?", 1)[0]
            parts = rest.split("/")
            rid = urllib.request.unquote(parts[0])
            action = parts[1] if len(parts) > 1 else ""
            with STATE_LOCK:
                rec = next((r for r in RESULTS if r["id"] == rid), None)
            if not rec:
                self.send_json({"error": "Không tìm thấy văn bản"}, 404)
                return

            doc_data = self._load_doc_data(rec)
            docx_name = rec.get("docxFilename") or f"{rid}.docx"
            docx_p = RESULTS_DIR / docx_name

            if action == "docx":
                build_docx(doc_data, docx_p)
                raw_bytes = docx_p.read_bytes()
                self.send_response(200)
                self.send_header(
                    "Content-Type",
                    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                )
                self.send_header("Content-Disposition", f'attachment; filename="{docx_name}"')
                self.send_header("Content-Length", str(len(raw_bytes)))
                self.end_headers()
                self.wfile.write(raw_bytes)
                return

            if action == "print":
                html_bytes = render_nd30_print_html(doc_data).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(html_bytes)))
                self.end_headers()
                self.wfile.write(html_bytes)
                return

            md_p = RESULTS_DIR / rec["filename"]
            content = md_p.read_text(encoding="utf-8", errors="replace") if md_p.exists() else doc_data_to_markdown(doc_data)
            self.send_json({**rec, "content": content, "docxFilename": docx_name, "docData": doc_data})
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

        if self.path == "/api/pick-folder":
            try:
                selected = pick_windows_folder()
                if not selected:
                    self.send_json({"ok": False, "cancelled": True})
                    return
                p = Path(selected)
                file_count = sum(1 for _ in p.iterdir()) if p.is_dir() else 0
                self.send_json({"ok": True, "path": str(p), "itemCount": file_count})
            except Exception as exc:
                self.send_json({"error": f"Không mở được hộp chọn thư mục: {exc}"}, 500)
            return

        if self.path == "/api/open-folder":
            folder = (body.get("path") or "").strip()
            p = Path(folder)
            if p.is_dir():
                try:
                    os.startfile(str(p))
                    self.send_json({"ok": True})
                    return
                except Exception as exc:
                    self.send_json({"error": str(exc)}, 500)
                    return
            self.send_json({"error": "Thư mục không tồn tại"}, 404)
            return

        if self.path == "/api/validate-folder":
            folder = (body.get("path") or "").strip()
            p = Path(folder)
            if p.is_dir():
                cnt = sum(1 for _ in p.iterdir())
                self.send_json({"ok": True, "path": str(p.resolve()), "itemCount": cnt})
            else:
                self.send_json({"error": "Đường dẫn thư mục không tồn tại trên máy."}, 400)
            return

        if self.path == "/api/extract-file":
            fname = (body.get("filename") or "").lower()
            b64 = body.get("dataBase64") or ""
            try:
                raw_bytes = base64.b64decode(b64)
                if fname.endswith(".docx"):
                    text = extract_docx_bytes(raw_bytes)
                else:
                    text = raw_bytes.decode("utf-8", errors="replace")
                self.send_json({"ok": True, "text": text[:25000]})
            except Exception as exc:
                self.send_json({"error": f"Không đọc được file: {exc}"}, 400)
            return

        if self.path == "/api/config":
            if "provider" in body:
                CONFIG["provider"] = body["provider"]
            if body.get("antigravityModel"):
                CONFIG["antigravityModel"] = body["antigravityModel"].strip()
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
            if isinstance(body.get("orgProfile"), dict):
                CONFIG["orgProfile"] = {
                    **CONFIG.get("orgProfile", {}),
                    **{k: str(v).strip() for k, v in body["orgProfile"].items()},
                }
            save_json(CONFIG_FILE, CONFIG)
            self.send_json({"ok": True, "activeProvider": active_provider()})
            return

        if self.path.startswith("/api/result/") and self.path.endswith("/update"):
            rid = urllib.request.unquote(self.path.split("/api/result/", 1)[1].rsplit("/update", 1)[0])
            with STATE_LOCK:
                rec = next((r for r in RESULTS if r["id"] == rid), None)
            if not rec:
                self.send_json({"error": "Không tìm thấy văn bản"}, 404)
                return
            cur = self._load_doc_data(rec)
            patch = body.get("docData") or {}
            for k in (
                "loai_van_ban",
                "co_quan_chu_quan",
                "co_quan_ban_hanh",
                "so_ky_hieu",
                "dia_danh_ngay",
                "ten_loai",
                "trich_yeu",
                "noi_dung",
                "quyen_han_ky",
                "chuc_vu_ky",
                "nguoi_ky",
            ):
                if k in patch and patch[k] is not None:
                    cur[k] = str(patch[k]).strip()
            if "noi_nhan" in patch and isinstance(patch["noi_nhan"], list):
                cur["noi_nhan"] = [str(x).strip() for x in patch["noi_nhan"] if str(x).strip()]
            if "kinh_gui" in patch and isinstance(patch["kinh_gui"], list):
                cur["kinh_gui"] = [str(x).strip() for x in patch["kinh_gui"] if str(x).strip()]

            _, docx_fn, json_fn, md_content, ws_saved = save_deliverable_files(
                rid, cur, rec.get("workspaceDir") or ""
            )
            with STATE_LOCK:
                rec["docxFilename"] = docx_fn
                rec["jsonFilename"] = json_fn
                if ws_saved:
                    rec["workspaceSavedDocx"] = ws_saved
                rec["preview"] = " ".join(cur["noi_dung"].replace("#", "").replace("*", "").split())[:155]
                save_json(INDEX_FILE, RESULTS)
            self.send_json({"ok": True, "content": md_content, "docData": cur})
            return

        if self.path.startswith("/api/result/") and self.path.endswith("/delete"):
            rid = urllib.request.unquote(self.path.split("/api/result/", 1)[1].rsplit("/delete", 1)[0])
            with STATE_LOCK:
                idx = next((i for i, r in enumerate(RESULTS) if r["id"] == rid), -1)
                if idx == -1:
                    self.send_json({"error": "Không tìm thấy"}, 404)
                    return
                rec = RESULTS.pop(idx)
                save_json(INDEX_FILE, RESULTS)
            for fn in (rec.get("filename"), rec.get("docxFilename"), rec.get("jsonFilename")):
                if fn:
                    p = RESULTS_DIR / fn
                    if p.exists():
                        try:
                            p.unlink()
                        except Exception:
                            pass
            self.send_json({"ok": True})
            return

        if self.path == "/api/assign":
            task_text = (body.get("task") or "").strip()
            ref_text = (body.get("referenceText") or "").strip()
            images = body.get("images") if isinstance(body.get("images"), list) else []
            workspace_dir = (body.get("workspaceDir") or "").strip()
            mode = body.get("mode", "auto-best")
            worker_idx = body.get("workerIndex")

            if not task_text and images:
                task_text = "Phân tích hình ảnh gửi kèm và soạn thảo văn bản hành chính phù hợp"
            if not task_text:
                self.send_json({"error": "Vui lòng nhập nội dung yêu cầu hoặc đính kèm hình ảnh."}, 400)
                return
            if workspace_dir and not Path(workspace_dir).is_dir():
                self.send_json({"error": f"Thư mục làm việc không tồn tại: {workspace_dir}"}, 400)
                return
            if active_provider() == "none":
                self.send_json(
                    {"error": "Chưa cấu hình nguồn AI. Hãy bấm 'Cài đặt' góc trên để thêm Gemini API Key hoặc Ollama."},
                    400,
                )
                return

            if mode == "split-merge":
                with STATE_LOCK:
                    if any(w["status"] == "working" for w in WORKER_STATES):
                        self.send_json(
                            {"error": "Đang có chuyên viên bận. Vui lòng chờ xong rồi chạy chế độ Chia 4 bàn & Tổng hợp!"},
                            409,
                        )
                        return
                threading.Thread(
                    target=run_split_merge_job,
                    args=(task_text, ref_text, images, workspace_dir),
                    daemon=True,
                ).start()
                self.send_json({"ok": True, "mode": "split-merge"})
                return

            with STATE_LOCK:
                reason = ""
                if mode == "auto-best":
                    chosen, reason = pick_best_specialist(
                        task_text, has_images=bool(images), has_workspace=bool(workspace_dir)
                    )
                    mode_label = f"Tự chọn giỏi nhất ({SPECIALISTS[chosen]['name']})"
                else:
                    chosen = int(worker_idx)
                    mode_label = f"Giao trực tiếp ({SPECIALISTS[chosen]['id']})"
                w = WORKER_STATES[chosen]
                w["status"] = "working"
                w["task"] = task_text
                phase_lbl = "Đang xử lý thư mục..." if workspace_dir else ("Đang đọc ảnh & soạn..." if images else "Đang soạn chuẩn NĐ30...")
                w["phaseLabel"] = phase_lbl
                w["startedAt"] = time.time()
                w["error"] = None
                PIPELINE_STATE.update(
                    {
                        "active": True,
                        "mode": mode,
                        "phase": "phase1",
                        "task": task_text,
                        "message": f"Đã giao {w['name']} ({w['role']}) xử lý",
                    }
                )

            threading.Thread(
                target=run_single_job,
                args=(chosen, task_text, mode_label, ref_text, images, workspace_dir),
                daemon=True,
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
    srv = None
    chosen_port = PORT
    for p in range(PORT, PORT + 15):
        try:
            srv = ThreadingHTTPServer((HOST, p), StudioHandler)
            srv.daemon_threads = True
            chosen_port = p
            break
        except OSError:
            continue
    if srv is None:
        raise RuntimeError(f"Không tìm thấy cổng trống từ {PORT} đến {PORT + 14}")
    url = f"http://{HOST}:{chosen_port}"
    print("=" * 64)
    print("  PHONG BIEN TAP VAN BAN & TAC NHAN THU MUC 3D")
    print(f"  Dia chi truy cap : {url}")
    print(f"  Nguon AI         : {active_provider().upper()} (Model: {CONFIG.get('antigravityModel', 'pro').upper()})")
    print(f"  Thu muc luu tru  : {RESULTS_DIR}")
    print("  (Giu cua so nay mo khi su dung; dong cua so de thoat)")
    print("=" * 64)
    if IS_FROZEN:
        threading.Timer(0.8, lambda: webbrowser.open(url)).start()
    srv.serve_forever()
