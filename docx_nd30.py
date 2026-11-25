"""
Trình xuất văn bản hành chính chuẩn Nghị định 30/2020/NĐ-CP (Phụ lục I & III)
- Xuất file Word thật (.docx) bằng python-docx:
  * Khổ A4 (210x297mm), lề Trên 20mm, Dưới 20mm, Trái 30mm, Phải 15mm
  * Phông chữ Times New Roman (Unicode), màu đen thuần
  * Bảng 2 cột đầu trang (Tên cơ quan + Số/Ký hiệu | Quốc hiệu + Tiêu ngữ + Địa danh ngày tháng)
  * Số trang canh giữa lề trên (13pt), ẩn ở trang 1
  * Nội dung 14pt canh đều hai lề, lùi đầu dòng 1.27cm, cách đoạn 6pt, giãn dòng 1.15
  * Hỗ trợ bảng biểu, đậm/nghiêng sạch (không lọt ký tự Markdown thô)
  * Bảng 2 cột cuối trang (Nơi nhận 12pt/11pt | Chức vụ & Họ tên người ký 14pt)
- Xuất trang HTML chuẩn A4 để In / Lưu PDF sắc nét (render_nd30_print_html).
"""
import html
import json
import re
from datetime import datetime
from pathlib import Path

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn
from docx.shared import Cm, Mm, Pt, RGBColor

BLACK = RGBColor(0, 0, 0)


def default_date_str() -> str:
    now = datetime.now()
    d = f"{now.day:02d}" if now.day < 10 else str(now.day)
    m = f"{now.month:02d}" if now.month <= 2 else str(now.month)
    return f"Hà Nội, ngày {d} tháng {m} năm {now.year}"


def normalize_doc_data(raw_text: str, fallback_title: str = "VĂN BẢN HÀNH CHÍNH") -> dict:
    """Trích xuất JSON chuẩn NĐ30 từ phản hồi AI; nếu là Markdown thuần thì tự chuyển đổi sạch."""
    data = None
    # Tìm khối ```json ... ```
    m = re.search(r"```json\s*(\{.*?\})\s*```", raw_text, flags=re.S)
    if m:
        try:
            data = json.loads(m.group(1))
        except Exception:
            data = None
    if data is None:
        stripped = raw_text.strip()
        if stripped.startswith("{") and stripped.endswith("}"):
            try:
                data = json.loads(stripped)
            except Exception:
                data = None

    if not isinstance(data, dict):
        # Fallback: chuyển đổi văn bản Markdown sang cấu trúc NĐ30
        clean_md = re.sub(r"^```[a-zA-Z]*\n|\n```$", "", raw_text.strip())
        data = {
            "loai_van_ban": "van_ban_co_ten_loai",
            "co_quan_chu_quan": "CƠ QUAN CHỦ QUẢN",
            "co_quan_ban_hanh": "CƠ QUAN BAN HÀNH",
            "so_ky_hieu": "Số: ....../VB-...",
            "dia_danh_ngay": default_date_str(),
            "ten_loai": "VĂN BẢN",
            "trich_yeu": fallback_title,
            "kinh_gui": [],
            "can_cu": [],
            "noi_dung": clean_md,
            "quyen_han_ky": "",
            "chuc_vu_ky": "THỦ TRƯỞNG ĐƠN VỊ",
            "nguoi_ky": "",
            "noi_nhan": ["- Như trên;", "- Lưu: VT."],
        }

    # Chuẩn hóa đầy đủ các trường bắt buộc
    out = {
        "loai_van_ban": data.get("loai_van_ban") or "van_ban_co_ten_loai",
        "co_quan_chu_quan": (data.get("co_quan_chu_quan") or "").strip(),
        "co_quan_ban_hanh": (data.get("co_quan_ban_hanh") or "ĐƠN VỊ BAN HÀNH").strip(),
        "so_ky_hieu": (data.get("so_ky_hieu") or "Số: ....../...").strip(),
        "dia_danh_ngay": (data.get("dia_danh_ngay") or default_date_str()).strip(),
        "ten_loai": (data.get("ten_loai") or "").strip(),
        "trich_yeu": (data.get("trich_yeu") or fallback_title).strip(),
        "kinh_gui": data.get("kinh_gui") if isinstance(data.get("kinh_gui"), list) else [],
        "can_cu": data.get("can_cu") if isinstance(data.get("can_cu"), list) else [],
        "noi_dung": (data.get("noi_dung") or "").strip(),
        "quyen_han_ky": (data.get("quyen_han_ky") or "").strip(),
        "chuc_vu_ky": (data.get("chuc_vu_ky") or "THỦ TRƯỞNG ĐƠN VỊ").strip(),
        "nguoi_ky": (data.get("nguoi_ky") or "").strip(),
        "noi_nhan": data.get("noi_nhan") if isinstance(data.get("noi_nhan"), list) and data.get("noi_nhan") else ["- Như trên;", "- Lưu: VT."],
    }
    if not out["so_ky_hieu"].lower().startswith("số:"):
        out["so_ky_hieu"] = "Số: " + out["so_ky_hieu"]
    return out


def doc_data_to_markdown(d: dict) -> str:
    """Tạo bản Markdown sạch để xem nhanh trên giao diện web & copy."""
    lines = []
    if d["co_quan_chu_quan"]:
        lines.append(f"**{d['co_quan_chu_quan'].upper()}**")
    lines.append(f"**{d['co_quan_ban_hanh'].upper()}** | **CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM** — *Độc lập - Tự do - Hạnh phúc*")
    lines.append(f"{d['so_ky_hieu']} | *{d['dia_danh_ngay']}*")
    lines.append("")
    if d["loai_van_ban"] == "cong_van":
        lines.append(f"**V/v {d['trich_yeu']}**")
    else:
        if d["ten_loai"]:
            lines.append(f"# {d['ten_loai'].upper()}")
        if d["trich_yeu"]:
            lines.append(f"## {d['trich_yeu']}")
    lines.append("")
    if d["kinh_gui"]:
        if len(d["kinh_gui"]) == 1:
            lines.append(f"Kính gửi: {d['kinh_gui'][0]}")
        else:
            lines.append("Kính gửi:")
            for item in d["kinh_gui"]:
                lines.append(f"- {item.lstrip('- ').strip()}")
        lines.append("")
    for cc in d["can_cu"]:
        lines.append(f"*{cc}*")
    if d["can_cu"]:
        lines.append("")
    lines.append(d["noi_dung"])
    lines.append("")
    lines.append("---")
    if d["quyen_han_ky"]:
        lines.append(f"**{d['quyen_han_ky'].upper()}**")
    lines.append(f"**{d['chuc_vu_ky'].upper()}**")
    if d["nguoi_ky"]:
        lines.append(f"**{d['nguoi_ky']}**")
    lines.append("")
    lines.append("*Nơi nhận:*")
    for nn in d["noi_nhan"]:
        lines.append(nn if nn.strip().startswith("-") else f"- {nn.strip()}")
    return "\n".join(lines)


# ============================================================
# HELPER XML CHO PYTHON-DOCX
# ============================================================
def set_run_font(run, size_pt=14, bold=False, italic=False):
    run.font.name = "Times New Roman"
    run.font.size = Pt(size_pt)
    run.font.color.rgb = BLACK
    run.bold = bold
    run.italic = italic
    rPr = run._r.get_or_add_rPr()
    rFonts = rPr.find(qn("w:rFonts"))
    if rFonts is None:
        rFonts = OxmlElement("w:rFonts")
        rPr.insert(0, rFonts)
    rFonts.set(qn("w:ascii"), "Times New Roman")
    rFonts.set(qn("w:hAnsi"), "Times New Roman")
    rFonts.set(qn("w:cs"), "Times New Roman")


def remove_table_borders(table):
    tblPr = table._tbl.tblPr
    borders = parse_xml(
        f'<w:tblBorders {nsdecls("w")}>'
        '<w:top w:val="none" w:sz="0" w:space="0" w:color="auto"/>'
        '<w:left w:val="none" w:sz="0" w:space="0" w:color="auto"/>'
        '<w:bottom w:val="none" w:sz="0" w:space="0" w:color="auto"/>'
        '<w:right w:val="none" w:sz="0" w:space="0" w:color="auto"/>'
        '<w:insideH w:val="none" w:sz="0" w:space="0" w:color="auto"/>'
        '<w:insideV w:val="none" w:sz="0" w:space="0" w:color="auto"/>'
        "</w:tblBorders>"
    )
    tblPr.append(borders)


def set_table_thin_borders(table):
    tblPr = table._tbl.tblPr
    borders = parse_xml(
        f'<w:tblBorders {nsdecls("w")}>'
        '<w:top w:val="single" w:sz="4" w:space="0" w:color="000000"/>'
        '<w:left w:val="single" w:sz="4" w:space="0" w:color="000000"/>'
        '<w:bottom w:val="single" w:sz="4" w:space="0" w:color="000000"/>'
        '<w:right w:val="single" w:sz="4" w:space="0" w:color="000000"/>'
        '<w:insideH w:val="single" w:sz="4" w:space="0" w:color="000000"/>'
        '<w:insideV w:val="single" w:sz="4" w:space="0" w:color="000000"/>'
        "</w:tblBorders>"
    )
    tblPr.append(borders)


def add_page_number_field(paragraph):
    run = paragraph.add_run()
    set_run_font(run, size_pt=13, bold=False, italic=False)
    fld1 = OxmlElement("w:fldChar")
    fld1.set(qn("w:fldCharType"), "begin")
    instr = OxmlElement("w:instrText")
    instr.set(qn("xml:space"), "preserve")
    instr.text = " PAGE "
    fld2 = OxmlElement("w:fldChar")
    fld2.set(qn("w:fldCharType"), "separate")
    fld3 = OxmlElement("w:fldChar")
    fld3.set(qn("w:fldCharType"), "end")
    run._r.append(fld1)
    run._r.append(instr)
    run._r.append(fld2)
    run._r.append(fld3)


def add_formatted_runs(p, text: str, size_pt=14, default_bold=False, default_italic=False):
    """Tách inline **bold** và *italic* để không lọt ký tự Markdown vào Word."""
    tokens = re.split(r"(\*\*.*?\*\*|\*[^*]+\*)", text)
    for tok in tokens:
        if not tok:
            continue
        if tok.startswith("**") and tok.endswith("**") and len(tok) > 4:
            r = p.add_run(tok[2:-2])
            set_run_font(r, size_pt=size_pt, bold=True, italic=default_italic)
        elif tok.startswith("*") and tok.endswith("*") and len(tok) > 2:
            r = p.add_run(tok[1:-1])
            set_run_font(r, size_pt=size_pt, bold=default_bold, italic=True)
        else:
            r = p.add_run(tok.replace("`", ""))
            set_run_font(r, size_pt=size_pt, bold=default_bold, italic=default_italic)


def add_short_rule(container, chars="──────────────", size_pt=10, space_after=4):
    p = container.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after = Pt(space_after)
    p.paragraph_format.line_spacing = 1.0
    r = p.add_run(chars)
    set_run_font(r, size_pt=size_pt, bold=False)
    return p


# ============================================================
# XUẤT FILE WORD .DOCX THẬT CHUẨN NGHỊ ĐỊNH 30/2020/NĐ-CP
# ============================================================
def build_docx(doc_data: dict, out_path: Path):
    doc = Document()
    sec = doc.sections[0]
    # Khổ giấy A4 (210mm x 297mm) & định lề chuẩn NĐ30: Trên 20, Dưới 20, Trái 30, Phải 15
    sec.page_width = Mm(210)
    sec.page_height = Mm(297)
    sec.top_margin = Mm(20)
    sec.bottom_margin = Mm(20)
    sec.left_margin = Mm(30)
    sec.right_margin = Mm(15)

    # Số trang canh giữa lề trên, 13pt, ẩn trang 1 (Phụ lục I Mục I.7)
    sec.different_first_page_header_footer = True
    sec.header_distance = Mm(10)
    hp = sec.header.paragraphs[0]
    hp.alignment = WD_ALIGN_PARAGRAPH.CENTER
    add_page_number_field(hp)

    # Style mặc định
    normal = doc.styles["Normal"]
    normal.font.name = "Times New Roman"
    normal.font.size = Pt(14)
    normal.font.color.rgb = BLACK

    # 1. BẢNG 2 CỘT PHẦN ĐẦU TRANG (Ô 1, 2, 3, 4, 5b)
    hdr_tbl = doc.add_table(rows=2, cols=2)
    hdr_tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    hdr_tbl.autofit = False
    remove_table_borders(hdr_tbl)
    col_widths = [Cm(7.2), Cm(9.3)]
    for row in hdr_tbl.rows:
        for i, w in enumerate(col_widths):
            row.cells[i].width = w
            row.cells[i].vertical_alignment = WD_ALIGN_VERTICAL.TOP

    # Ô trái hàng 1: Tên CQ chủ quản + Tên CQ ban hành + gạch ngang
    c_org = hdr_tbl.cell(0, 0)
    p_org = c_org.paragraphs[0]
    p_org.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_org.paragraph_format.space_before = Pt(0)
    p_org.paragraph_format.space_after = Pt(0)
    p_org.paragraph_format.line_spacing = 1.05
    if doc_data["co_quan_chu_quan"]:
        r = p_org.add_run(doc_data["co_quan_chu_quan"].upper() + "\n")
        set_run_font(r, size_pt=12, bold=False)
    r_bh = p_org.add_run(doc_data["co_quan_ban_hanh"].upper())
    set_run_font(r_bh, size_pt=12, bold=True)
    add_short_rule(c_org, "──────────", size_pt=9, space_after=2)

    # Ô phải hàng 1: Quốc hiệu + Tiêu ngữ + gạch ngang
    c_qh = hdr_tbl.cell(0, 1)
    p_qh = c_qh.paragraphs[0]
    p_qh.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_qh.paragraph_format.space_before = Pt(0)
    p_qh.paragraph_format.space_after = Pt(0)
    p_qh.paragraph_format.line_spacing = 1.05
    r1 = p_qh.add_run("CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM\n")
    set_run_font(r1, size_pt=12, bold=True)
    r2 = p_qh.add_run("Độc lập - Tự do - Hạnh phúc")
    set_run_font(r2, size_pt=13, bold=True)
    add_short_rule(c_qh, "────────────────────", size_pt=9, space_after=2)

    # Ô trái hàng 2: Số, ký hiệu (+ V/v nếu là công văn)
    c_so = hdr_tbl.cell(1, 0)
    p_so = c_so.paragraphs[0]
    p_so.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_so.paragraph_format.space_before = Pt(4)
    p_so.paragraph_format.space_after = Pt(0)
    r_so = p_so.add_run(doc_data["so_ky_hieu"])
    set_run_font(r_so, size_pt=13, bold=False)

    if doc_data["loai_van_ban"] == "cong_van" and doc_data["trich_yeu"]:
        p_vv = c_so.add_paragraph()
        p_vv.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_vv.paragraph_format.space_before = Pt(6)
        p_vv.paragraph_format.space_after = Pt(0)
        vv_txt = doc_data["trich_yeu"]
        if not vv_txt.lower().startswith("v/v"):
            vv_txt = "V/v " + vv_txt
        r_vv = p_vv.add_run(vv_txt)
        set_run_font(r_vv, size_pt=12, bold=False)

    # Ô phải hàng 2: Địa danh, ngày tháng năm (13pt nghiêng)
    c_dt = hdr_tbl.cell(1, 1)
    p_dt = c_dt.paragraphs[0]
    p_dt.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_dt.paragraph_format.space_before = Pt(4)
    p_dt.paragraph_format.space_after = Pt(0)
    r_dt = p_dt.add_run(doc_data["dia_danh_ngay"])
    set_run_font(r_dt, size_pt=13, italic=True)

    # 2. TÊN LOẠI & TRÍCH YẾU (Ô 5a — nếu không phải Công văn)
    if doc_data["loai_van_ban"] != "cong_van":
        if doc_data["ten_loai"]:
            p_tl = doc.add_paragraph()
            p_tl.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p_tl.paragraph_format.space_before = Pt(14)
            p_tl.paragraph_format.space_after = Pt(2)
            r_tl = p_tl.add_run(doc_data["ten_loai"].upper())
            set_run_font(r_tl, size_pt=14, bold=True)
        if doc_data["trich_yeu"]:
            p_ty = doc.add_paragraph()
            p_ty.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p_ty.paragraph_format.space_before = Pt(0)
            p_ty.paragraph_format.space_after = Pt(2)
            r_ty = p_ty.add_run(doc_data["trich_yeu"])
            set_run_font(r_ty, size_pt=14, bold=True)
        add_short_rule(doc, "──────────────", size_pt=10, space_after=10)
    else:
        sp = doc.add_paragraph()
        sp.paragraph_format.space_before = Pt(6)
        sp.paragraph_format.space_after = Pt(4)

    # 3. KÍNH GỬI (Ô 9a)
    kinh_gui = [k.strip() for k in doc_data["kinh_gui"] if str(k).strip()]
    if kinh_gui:
        if len(kinh_gui) == 1:
            p_kg = doc.add_paragraph()
            p_kg.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p_kg.paragraph_format.space_before = Pt(4)
            p_kg.paragraph_format.space_after = Pt(8)
            r_kg = p_kg.add_run(f"Kính gửi: {kinh_gui[0].lstrip('- ').strip()}")
            set_run_font(r_kg, size_pt=14, bold=False)
        else:
            p_kg0 = doc.add_paragraph()
            p_kg0.paragraph_format.left_indent = Cm(2.5)
            p_kg0.paragraph_format.space_before = Pt(4)
            p_kg0.paragraph_format.space_after = Pt(2)
            r0 = p_kg0.add_run("Kính gửi:")
            set_run_font(r0, size_pt=14)
            for idx, item in enumerate(kinh_gui):
                p_kgi = doc.add_paragraph()
                p_kgi.paragraph_format.left_indent = Cm(4.2)
                p_kgi.paragraph_format.space_before = Pt(0)
                p_kgi.paragraph_format.space_after = Pt(8 if idx == len(kinh_gui) - 1 else 2)
                clean_item = item.lstrip("- ").strip()
                r_i = p_kgi.add_run(f"- {clean_item}")
                set_run_font(r_i, size_pt=14)

    # 4. CĂN CỨ BAN HÀNH (14pt nghiêng, lùi 1.27cm)
    for idx, cc in enumerate(doc_data["can_cu"]):
        cc_str = str(cc).strip()
        if not cc_str:
            continue
        p_cc = doc.add_paragraph()
        p_cc.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        p_cc.paragraph_format.first_line_indent = Cm(1.27)
        p_cc.paragraph_format.space_before = Pt(0)
        p_cc.paragraph_format.space_after = Pt(8 if idx == len(doc_data["can_cu"]) - 1 else 4)
        p_cc.paragraph_format.line_spacing = 1.15
        r_cc = p_cc.add_run(cc_str)
        set_run_font(r_cc, size_pt=14, italic=True)

    # 5. NỘI DUNG VĂN BẢN (Ô 6 — 14pt, canh đều, lùi 1.27cm, cách đoạn 6pt, hỗ trợ bảng)
    lines = doc_data["noi_dung"].splitlines()
    i = 0
    last_body_p = None
    while i < len(lines):
        raw = lines[i].rstrip()
        stripped = raw.strip()
        if not stripped or stripped == "---":
            i += 1
            continue

        # Bảng Markdown -> Bảng Word có viền mảnh đen
        if stripped.startswith("|") and "|" in stripped[1:]:
            tbl_lines = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                tbl_lines.append(lines[i].strip())
                i += 1
            rows_cells = []
            for tl in tbl_lines:
                cells = [c.strip() for c in tl.strip("|").split("|")]
                if all(re.fullmatch(r"[-:\s]+", c or "-") for c in cells):
                    continue
                rows_cells.append(cells)
            if rows_cells:
                ncols = max(len(r) for r in rows_cells)
                t = doc.add_table(rows=len(rows_cells), cols=ncols)
                t.alignment = WD_TABLE_ALIGNMENT.CENTER
                set_table_thin_borders(t)
                for r_idx, row_vals in enumerate(rows_cells):
                    for c_idx in range(ncols):
                        val = row_vals[c_idx] if c_idx < len(row_vals) else ""
                        cell = t.cell(r_idx, c_idx)
                        p = cell.paragraphs[0]
                        p.alignment = WD_ALIGN_PARAGRAPH.CENTER if r_idx == 0 else WD_ALIGN_PARAGRAPH.LEFT
                        p.paragraph_format.space_before = Pt(3)
                        p.paragraph_format.space_after = Pt(3)
                        add_formatted_runs(p, val, size_pt=13, default_bold=(r_idx == 0))
            continue

        # Tiêu đề Markdown (# / ## / ###) hoặc Chương / Phần / Mục
        hm = re.match(r"^(#{1,3})\s+(.*)$", stripped)
        if hm:
            lvl = len(hm.group(1))
            title_txt = hm.group(2).strip().replace("**", "")
            p = doc.add_paragraph()
            if lvl == 1 or re.match(r"^(PHẦN|CHƯƠNG|MỤC|QUYẾT ĐỊNH:|QUYẾT NGHỊ:)\b", title_txt, re.I):
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                p.paragraph_format.space_before = Pt(8)
                p.paragraph_format.space_after = Pt(6)
            else:
                p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
                p.paragraph_format.first_line_indent = Cm(1.27)
                p.paragraph_format.space_before = Pt(6)
                p.paragraph_format.space_after = Pt(4)
            p.paragraph_format.line_spacing = 1.15
            r = p.add_run(title_txt)
            set_run_font(r, size_pt=14, bold=True)
            last_body_p = p
            i += 1
            continue

        # Gạch đầu dòng (- / * / +)
        bm = re.match(r"^[-*+]\s+(.*)$", stripped)
        if bm:
            p = doc.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
            p.paragraph_format.first_line_indent = Cm(1.27)
            p.paragraph_format.space_before = Pt(0)
            p.paragraph_format.space_after = Pt(6)
            p.paragraph_format.line_spacing = 1.15
            add_formatted_runs(p, "- " + bm.group(1).strip(), size_pt=14)
            last_body_p = p
            i += 1
            continue

        # Đoạn văn bình thường (hoặc Điều X. / I. / 1. ...)
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        p.paragraph_format.first_line_indent = Cm(1.27)
        p.paragraph_format.space_before = Pt(0)
        p.paragraph_format.space_after = Pt(6)
        p.paragraph_format.line_spacing = 1.15

        # Kiểm tra nếu dòng bắt đầu bằng "Điều 1." thì in đậm tên Điều
        dm = re.match(r"^(Điều\s+\d+\.[^\n]*)$", stripped)
        if dm and len(stripped) < 95:
            r = p.add_run(stripped)
            set_run_font(r, size_pt=14, bold=True)
        else:
            add_formatted_runs(p, stripped, size_pt=14)
        last_body_p = p
        i += 1

    # Kết thúc văn bản bằng "./." theo chuẩn NĐ30 nếu chưa có
    if last_body_p is not None and not last_body_p.text.strip().endswith("./."):
        txt = last_body_p.text.rstrip()
        if txt.endswith("."):
            r_end = last_body_p.add_run("/.")
        else:
            r_end = last_body_p.add_run("./.")
        set_run_font(r_end, size_pt=14)

    # 6. BẢNG 2 CỘT CUỐI TRANG: NƠI NHẬN (Ô 9b) & CHỨC VỤ/CHỮ KÝ (Ô 7a, 7b)
    sp_end = doc.add_paragraph()
    sp_end.paragraph_format.space_before = Pt(8)
    sp_end.paragraph_format.space_after = Pt(4)

    ftr_tbl = doc.add_table(rows=1, cols=2)
    ftr_tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    ftr_tbl.autofit = False
    remove_table_borders(ftr_tbl)
    ftr_widths = [Cm(7.8), Cm(8.7)]
    row = ftr_tbl.rows[0]
    trPr = row._tr.get_or_add_trPr()
    trPr.append(OxmlElement("w:cantSplit"))
    for idx, w in enumerate(ftr_widths):
        row.cells[idx].width = w
        row.cells[idx].vertical_alignment = WD_ALIGN_VERTICAL.TOP

    # Cột trái: Nơi nhận (12pt nghiêng đậm) + danh sách (11pt đứng)
    c_nn = row.cells[0]
    p_nn_hdr = c_nn.paragraphs[0]
    p_nn_hdr.paragraph_format.space_before = Pt(0)
    p_nn_hdr.paragraph_format.space_after = Pt(2)
    r_nn = p_nn_hdr.add_run("Nơi nhận:")
    set_run_font(r_nn, size_pt=12, bold=True, italic=True)
    for item in doc_data["noi_nhan"]:
        item_s = str(item).strip()
        if not item_s:
            continue
        if not item_s.startswith("-"):
            item_s = "- " + item_s
        p_ni = c_nn.add_paragraph()
        p_ni.paragraph_format.space_before = Pt(0)
        p_ni.paragraph_format.space_after = Pt(1)
        p_ni.paragraph_format.line_spacing = 1.05
        r_ni = p_ni.add_run(item_s)
        set_run_font(r_ni, size_pt=11, bold=False)

    # Cột phải: Quyền hạn & Chức vụ ký (14pt IN HOA đậm) + khoảng trống ký + Họ tên (14pt đậm)
    c_ky = row.cells[1]
    p_ky = c_ky.paragraphs[0]
    p_ky.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_ky.paragraph_format.space_before = Pt(0)
    p_ky.paragraph_format.space_after = Pt(0)
    p_ky.paragraph_format.line_spacing = 1.1
    if doc_data["quyen_han_ky"]:
        r_qh_ky = p_ky.add_run(doc_data["quyen_han_ky"].upper() + "\n")
        set_run_font(r_qh_ky, size_pt=14, bold=True)
    r_cv = p_ky.add_run(doc_data["chuc_vu_ky"].upper())
    set_run_font(r_cv, size_pt=14, bold=True)

    # Khoảng trống ký & đóng dấu (4 dòng)
    for _ in range(4):
        p_sp = c_ky.add_paragraph()
        p_sp.paragraph_format.space_before = Pt(0)
        p_sp.paragraph_format.space_after = Pt(0)
        r_sp = p_sp.add_run(" ")
        set_run_font(r_sp, size_pt=14)

    if doc_data["nguoi_ky"]:
        p_ten = c_ky.add_paragraph()
        p_ten.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_ten.paragraph_format.space_before = Pt(0)
        p_ten.paragraph_format.space_after = Pt(0)
        r_ten = p_ten.add_run(doc_data["nguoi_ky"])
        set_run_font(r_ten, size_pt=14, bold=True)

    doc.save(str(out_path))


# ============================================================
# XUẤT TRANG HTML A4 CHUẨN NĐ30 ĐỂ IN / LƯU PDF SẮC NÉT
# ============================================================
def _inline_html(text: str) -> str:
    s = html.escape(text)
    s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"\*([^*]+)\*", r"<em>\1</em>", s)
    return s.replace("`", "")


def render_nd30_print_html(doc_data: dict) -> str:
    body_html = []
    lines = doc_data["noi_dung"].splitlines()
    i = 0
    while i < len(lines):
        s = lines[i].strip()
        if not s or s == "---":
            i += 1
            continue
        if s.startswith("|") and "|" in s[1:]:
            trows = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                cells = [c.strip() for c in lines[i].strip().strip("|").split("|")]
                if not all(re.fullmatch(r"[-:\s]+", c or "-") for c in cells):
                    trows.append(cells)
                i += 1
            if trows:
                body_html.append('<table class="nd-table">')
                for r_idx, r in enumerate(trows):
                    tag = "th" if r_idx == 0 else "td"
                    body_html.append("<tr>" + "".join(f"<{tag}>{_inline_html(c)}</{tag}>" for c in r) + "</tr>")
                body_html.append("</table>")
            continue
        hm = re.match(r"^(#{1,3})\s+(.*)$", s)
        if hm:
            lvl = len(hm.group(1))
            t = hm.group(2).strip().replace("**", "")
            cls = "nd-center-bold" if lvl == 1 else "nd-indent-bold"
            body_html.append(f'<p class="{cls}">{html.escape(t)}</p>')
            i += 1
            continue
        bm = re.match(r"^[-*+]\s+(.*)$", s)
        if bm:
            body_html.append(f'<p class="nd-p">- {_inline_html(bm.group(1).strip())}</p>')
            i += 1
            continue
        body_html.append(f'<p class="nd-p">{_inline_html(s)}</p>')
        i += 1

    if body_html and not body_html[-1].rstrip("</p>").endswith("./."):
        body_html[-1] = body_html[-1][:-4] + "./.</p>"

    kg_html = ""
    kg = [k.strip() for k in doc_data["kinh_gui"] if str(k).strip()]
    if len(kg) == 1:
        kg_html = f'<p class="nd-kg-single">Kính gửi: {html.escape(kg[0].lstrip("- ").strip())}</p>'
    elif len(kg) > 1:
        items = "".join(f'<div>- {html.escape(k.lstrip("- ").strip())}</div>' for k in kg)
        kg_html = f'<div class="nd-kg-multi"><div>Kính gửi:</div><div class="nd-kg-list">{items}</div></div>'

    cc_html = "".join(f'<p class="nd-cc">{html.escape(str(c).strip())}</p>' for c in doc_data["can_cu"] if str(c).strip())
    nn_html = "".join(
        f'<div>{html.escape(str(n).strip() if str(n).strip().startswith("-") else "- " + str(n).strip())}</div>'
        for n in doc_data["noi_nhan"]
        if str(n).strip()
    )

    vv_block = ""
    title_block = ""
    if doc_data["loai_van_ban"] == "cong_van":
        vv = doc_data["trich_yeu"]
        if vv and not vv.lower().startswith("v/v"):
            vv = "V/v " + vv
        vv_block = f'<div class="nd-vv">{html.escape(vv)}</div>'
    else:
        tl = f'<div class="nd-tenloai">{html.escape(doc_data["ten_loai"].upper())}</div>' if doc_data["ten_loai"] else ""
        ty = f'<div class="nd-trichyeu">{html.escape(doc_data["trich_yeu"])}</div>' if doc_data["trich_yeu"] else ""
        title_block = f'<div class="nd-title-wrap">{tl}{ty}<div class="nd-rule-mid"></div></div>'

    cq_cq = f'<div class="nd-cqcq">{html.escape(doc_data["co_quan_chu_quan"].upper())}</div>' if doc_data["co_quan_chu_quan"] else ""
    qh_ky = f'<div>{html.escape(doc_data["quyen_han_ky"].upper())}</div>' if doc_data["quyen_han_ky"] else ""

    return f"""<!DOCTYPE html>
<html lang="vi">
<head>
<meta charset="utf-8" />
<title>{html.escape(doc_data["trich_yeu"] or "Văn bản chuẩn Nghị định 30")}</title>
<style>
  @page {{ size: A4; margin: 20mm 15mm 20mm 30mm; }}
  * {{ box-sizing: border-box; }}
  body {{
    margin: 0;
    background: #e5e7eb;
    font-family: "Times New Roman", Times, serif;
    font-size: 14pt;
    color: #000;
    line-height: 1.35;
  }}
  .toolbar {{
    position: sticky; top: 0; z-index: 10;
    background: #1f1914; color: #fff;
    padding: 10px 20px; display: flex; justify-content: space-between; align-items: center;
    font-family: system-ui, sans-serif; font-size: 13px;
  }}
  .toolbar button {{
    background: #9a5b25; color: #fff; border: none; padding: 8px 16px;
    border-radius: 8px; font-weight: 600; cursor: pointer; font-size: 13px;
  }}
  .page {{
    width: 210mm; min-height: 297mm;
    margin: 18px auto; padding: 20mm 15mm 20mm 30mm;
    background: #fff; box-shadow: 0 8px 28px rgba(0,0,0,0.16);
  }}
  .hdr {{ width: 100%; border-collapse: collapse; margin-bottom: 10pt; }}
  .hdr td {{ vertical-align: top; text-align: center; padding: 0 4pt; }}
  .hdr .left {{ width: 43%; }}
  .hdr .right {{ width: 57%; }}
  .nd-cqcq {{ font-size: 12pt; }}
  .nd-cqbh {{ font-size: 12pt; font-weight: bold; }}
  .nd-qh {{ font-size: 12pt; font-weight: bold; }}
  .nd-tn {{ font-size: 13pt; font-weight: bold; }}
  .nd-rule-sm {{ width: 42%; border-bottom: 1px solid #000; margin: 3pt auto 5pt; }}
  .nd-rule-lg {{ width: 72%; border-bottom: 1px solid #000; margin: 3pt auto 5pt; }}
  .nd-rule-mid {{ width: 32%; border-bottom: 1px solid #000; margin: 4pt auto 12pt; }}
  .nd-so {{ font-size: 13pt; margin-top: 2pt; }}
  .nd-vv {{ font-size: 12pt; margin-top: 6pt; }}
  .nd-date {{ font-size: 13pt; font-style: italic; margin-top: 2pt; }}
  .nd-title-wrap {{ text-align: center; margin-top: 12pt; }}
  .nd-tenloai {{ font-size: 14pt; font-weight: bold; }}
  .nd-trichyeu {{ font-size: 14pt; font-weight: bold; margin-top: 2pt; }}
  .nd-kg-single {{ text-align: center; margin: 8pt 0 10pt; }}
  .nd-kg-multi {{ margin: 8pt 0 10pt 2.2cm; display: flex; gap: 6pt; }}
  .nd-cc {{ text-align: justify; text-indent: 1.27cm; font-style: italic; margin: 0 0 5pt; }}
  .nd-p {{ text-align: justify; text-indent: 1.27cm; margin: 0 0 6pt; }}
  .nd-center-bold {{ text-align: center; font-weight: bold; margin: 8pt 0 6pt; }}
  .nd-indent-bold {{ text-align: justify; text-indent: 1.27cm; font-weight: bold; margin: 6pt 0 4pt; }}
  .nd-table {{ width: 100%; border-collapse: collapse; margin: 8pt 0; font-size: 13pt; }}
  .nd-table th, .nd-table td {{ border: 1px solid #000; padding: 4pt 6pt; }}
  .ftr {{ width: 100%; border-collapse: collapse; margin-top: 14pt; page-break-inside: avoid; }}
  .ftr td {{ vertical-align: top; }}
  .ftr .nn {{ width: 48%; font-size: 11pt; line-height: 1.25; }}
  .ftr .nn-title {{ font-size: 12pt; font-weight: bold; font-style: italic; margin-bottom: 2pt; }}
  .ftr .ky {{ width: 52%; text-align: center; font-size: 14pt; font-weight: bold; }}
  .ky-space {{ height: 74pt; }}
  @media print {{
    body {{ background: #fff; }}
    .toolbar {{ display: none; }}
    .page {{ width: auto; min-height: auto; margin: 0; padding: 0; box-shadow: none; }}
  }}
</style>
</head>
<body>
  <div class="toolbar">
    <span>Bản xem trước khổ A4 chuẩn Nghị định 30/2020/NĐ-CP (Times New Roman 14pt, lề 20/20/30/15mm)</span>
    <button onclick="window.print()">In / Lưu PDF ngay</button>
  </div>
  <div class="page">
    <table class="hdr">
      <tr>
        <td class="left">
          {cq_cq}
          <div class="nd-cqbh">{html.escape(doc_data["co_quan_ban_hanh"].upper())}</div>
          <div class="nd-rule-sm"></div>
          <div class="nd-so">{html.escape(doc_data["so_ky_hieu"])}</div>
          {vv_block}
        </td>
        <td class="right">
          <div class="nd-qh">CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM</div>
          <div class="nd-tn">Độc lập - Tự do - Hạnh phúc</div>
          <div class="nd-rule-lg"></div>
          <div class="nd-date">{html.escape(doc_data["dia_danh_ngay"])}</div>
        </td>
      </tr>
    </table>
    {title_block}
    {kg_html}
    {cc_html}
    {"".join(body_html)}
    <table class="ftr">
      <tr>
        <td class="nn">
          <div class="nn-title">Nơi nhận:</div>
          {nn_html}
        </td>
        <td class="ky">
          {qh_ky}
          <div>{html.escape(doc_data["chuc_vu_ky"].upper())}</div>
          <div class="ky-space"></div>
          <div>{html.escape(doc_data["nguoi_ky"])}</div>
        </td>
      </tr>
    </table>
  </div>
</body>
</html>"""
