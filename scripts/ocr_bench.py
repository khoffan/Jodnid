"""
เครื่องมือวัดคุณภาพ OCR pipeline แบบออฟไลน์ (ไม่ยุ่งกับ LINE)

ใช้เทียบว่าการปรับ pipeline แต่ละแบบทำให้อ่านใบเสร็จได้ดีขึ้นจริงไหม
โดยวิ่งรูปชุดเดียวกันผ่านหลาย variant แล้วเทียบกับเฉลยที่ label ไว้

วิธีใช้
-------
1) สร้างไฟล์เฉลยเปล่าจากโฟลเดอร์รูป แล้วกรอกยอดจริงเอง
   python scripts/ocr_bench.py --images uploads --init-labels bench_labels.json

2) วัดเฉพาะชั้น OCR (ถูก เร็ว ไม่เรียก LLM สกัด)
   python scripts/ocr_bench.py --images uploads --labels bench_labels.json \
       --variants legacy,vlm

3) วัดทั้ง pipeline (เรียก LLM สกัดรายการด้วย ต้องมี DB + user_id ที่มีอยู่จริง)
   python scripts/ocr_bench.py --images uploads --labels bench_labels.json \
       --variants legacy,vlm --stage full --user-id U1234...

หมายเหตุ: ทุก variant ยิง API จริง การรัน 30 รูป x 3 variant = 90 requests
"""

import argparse
import json
import statistics
import sys
import time
from pathlib import Path
from typing import Any, Optional

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ai.ocr import is_financial_document, run_ocr, summarize_extraction  # noqa: E402
from ai.text_nlp import extract_transactions  # noqa: E402
from core.config_settings import settings  # noqa: E402
from helper.utils import Utilities  # noqa: E402

IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".webp"}

# preprocess: โหมดที่ส่งให้ pre_process_image_file (None = ส่งไฟล์ดิบไม่แตะเลย)
# force_split: True = บังคับแบ่งชิ้น, False = ส่งเต็มใบ, None = ให้ระบบตัดสินจาก aspect ratio
VARIANTS: dict[str, dict[str, Any]] = {
    "legacy": {"preprocess": "legacy", "force_split": True},
    "vlm": {"preprocess": "vlm", "force_split": False},
    "vlm-auto": {"preprocess": "vlm", "force_split": None},
    "vlm-split": {"preprocess": "vlm", "force_split": True},
    "raw": {"preprocess": None, "force_split": False},
}


def find_images(root: Path, limit: Optional[int] = None) -> list[Path]:
    """หารูปทั้งหมดใต้โฟลเดอร์ที่ระบุ เรียงตามชื่อเพื่อให้ผลลัพธ์ซ้ำได้"""
    files = sorted(p for p in root.rglob("*") if p.suffix.lower() in IMAGE_SUFFIXES)
    return files[:limit] if limit else files


def init_labels(images: list[Path], root: Path, out_path: Path) -> None:
    """สร้างไฟล์เฉลยเปล่าให้กรอกยอดจริงจากรูปทีละใบ"""
    payload = {
        "_readme": "กรอก grand_total (ยอดที่จ่ายจริง) และ item_count (จำนวนรายการ) จากรูปแต่ละใบ",
        "images": [
            {
                "file": str(image.relative_to(root)).replace("\\", "/"),
                "grand_total": None,
                "item_count": None,
                "keywords": [],
                "note": "",
            }
            for image in images
        ],
    }
    out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"สร้างไฟล์เฉลยแล้ว: {out_path} ({len(images)} รูป)")
    print("กรอก grand_total ให้ครบก่อนรันวัดผลจริง")


def load_labels(path: Optional[Path]) -> dict[str, dict[str, Any]]:
    if not path:
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    return {item["file"]: item for item in data.get("images", [])}


def normalize_text(text: str) -> str:
    """ตัด comma / ช่องว่างออก เพื่อให้เทียบตัวเลขได้ไม่ว่า OCR จะจัดรูปแบบมายังไง"""
    return text.replace(",", "").replace(" ", "").replace(" ", "")


def total_in_text(total: Optional[float], text: str) -> Optional[bool]:
    """
    เช็คว่า 'ยอดจริง' โผล่ในข้อความที่ OCR อ่านได้หรือไม่

    เป็น metric ที่ตัดสินชั้น OCR ล้วนๆ โดยไม่ต้องเรียก LLM เลย
    ถ้ายอดไม่โผล่ตรงนี้ ต่อให้ LLM เก่งแค่ไหนก็สกัดยอดถูกไม่ได้
    """
    if total is None:
        return None
    haystack = normalize_text(text)
    candidates = {f"{total:.2f}", f"{total:.1f}", f"{total:g}"}
    if float(total).is_integer():
        candidates.add(str(int(total)))
    return any(candidate in haystack for candidate in candidates)


def keywords_in_text(keywords: list[str], text: str) -> Optional[bool]:
    if not keywords:
        return None
    haystack = normalize_text(text)
    return all(normalize_text(keyword) in haystack for keyword in keywords)


def run_one(
    image_bytes: bytes,
    filename: str,
    variant: dict[str, Any],
    stage: str,
    user_id: Optional[str],
    db_session: Any,
) -> dict[str, Any]:
    """วิ่งรูปหนึ่งใบผ่าน variant หนึ่งแบบ แล้วคืนผลดิบไว้สรุปทีหลัง"""
    started_at = time.monotonic()

    if variant["preprocess"]:
        prepared = Utilities.pre_process_image_file(image_bytes, mode=variant["preprocess"])
    else:
        prepared = image_bytes

    ocr_result = run_ocr(
        image_bytes=prepared,
        filename=filename,
        api_key=settings.TYPHOON_API_KEY,
        force_split=variant["force_split"],
    )

    row: dict[str, Any] = {
        "ok": ocr_result["success"],
        "error": None if ocr_result["success"] else ocr_result.get("error"),
        "text": ocr_result.get("text", ""),
        "prepared_bytes": len(prepared),
        **ocr_result["meta"],
    }

    if ocr_result["success"] and stage == "full":
        row["is_financial"] = is_financial_document(settings.TYPHOON_API_KEY, ocr_result["text"])
        if row["is_financial"]:
            extracted = extract_transactions(
                settings.TYPHOON_API_KEY, ocr_result["text"], user_id, db_session
            )
            if extracted is None:
                row["ok"] = False
                row["error"] = "extraction returned none"
            else:
                row.update(summarize_extraction(extracted))
        else:
            row["ok"] = False
            row["error"] = "not a financial document"

    row["latency_ms"] = int((time.monotonic() - started_at) * 1000)
    return row


def percentile(values: list[float], pct: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = min(len(ordered) - 1, int(round((len(ordered) - 1) * pct)))
    return ordered[index]


def ratio(hits: list[Optional[bool]]) -> str:
    """แสดงเป็น 'เปอร์เซ็นต์ (ผ่าน/ทั้งหมด)' โดยข้ามรูปที่ไม่มีเฉลย"""
    scored = [hit for hit in hits if hit is not None]
    if not scored:
        return "-"
    passed = sum(1 for hit in scored if hit)
    return f"{passed / len(scored) * 100:.0f}% ({passed}/{len(scored)})"


def summarize(rows: list[dict[str, Any]], stage: str) -> dict[str, str]:
    latencies = [row["latency_ms"] for row in rows]
    chars = [row.get("ocr_char_count", 0) for row in rows if row["ok"]]
    summary = {
        "images": str(len(rows)),
        "ocr_ok": ratio([row["ok"] for row in rows]),
        "total_hit": ratio([row.get("total_hit") for row in rows]),
        "chars_median": f"{int(statistics.median(chars)) if chars else 0}",
        "chunks_avg": f"{statistics.fmean([row.get('chunk_count', 1) for row in rows]):.1f}",
        "retry_used": str(sum(1 for row in rows if row.get("attempts_max", 1) > 1)),
        "p50_ms": f"{percentile(latencies, 0.5):.0f}",
        "p95_ms": f"{percentile(latencies, 0.95):.0f}",
    }
    if stage == "full":
        summary["total_exact"] = ratio([row.get("total_exact") for row in rows])
        summary["saved_match"] = ratio([row.get("saved_match") for row in rows])
        summary["items_match"] = ratio([row.get("items_match") for row in rows])
    return summary


def print_table(summaries: dict[str, dict[str, str]]) -> None:
    if not summaries:
        return
    columns = list(next(iter(summaries.values())).keys())
    header = ["variant"] + columns
    widths = [
        max(len(header[i]), *(len(str(row.get(col, ""))) for row in summaries.values()))
        if i > 0
        else max(len(header[0]), *(len(name) for name in summaries))
        for i, col in enumerate([""] + columns)
    ]

    def line(cells: list[str]) -> str:
        return " | ".join(cell.ljust(widths[i]) for i, cell in enumerate(cells))

    print()
    print(line(header))
    print("-+-".join("-" * width for width in widths))
    for name, row in summaries.items():
        print(line([name] + [str(row.get(col, "")) for col in columns]))
    print()


def main() -> int:
    parser = argparse.ArgumentParser(description="วัดคุณภาพ OCR pipeline ของ JodNid")
    parser.add_argument("--images", required=True, help="โฟลเดอร์ที่เก็บรูปใบเสร็จ")
    parser.add_argument("--labels", help="ไฟล์ JSON เฉลย (ดู --init-labels)")
    parser.add_argument("--init-labels", help="สร้างไฟล์เฉลยเปล่าไว้ที่ path นี้แล้วจบ")
    parser.add_argument(
        "--variants",
        default="legacy,vlm",
        help=f"รายชื่อ variant คั่นด้วย comma เลือกได้: {','.join(VARIANTS)}",
    )
    parser.add_argument(
        "--stage",
        choices=["ocr", "full"],
        default="ocr",
        help="ocr = วัดเฉพาะชั้นอ่านข้อความ, full = สกัดรายการด้วย LLM ด้วย",
    )
    parser.add_argument("--user-id", help="line_user_id ที่มีอยู่จริง (จำเป็นเมื่อ --stage full)")
    parser.add_argument("--limit", type=int, help="จำกัดจำนวนรูป")
    parser.add_argument("--out", help="เขียนผลดิบเป็น JSON ไว้ที่ path นี้")
    args = parser.parse_args()

    root = Path(args.images)
    if not root.is_dir():
        print(f"ไม่พบโฟลเดอร์รูป: {root}")
        return 1

    images = find_images(root, args.limit)
    if not images:
        print(f"ไม่พบไฟล์รูปใน {root}")
        return 1

    if args.init_labels:
        init_labels(images, root, Path(args.init_labels))
        return 0

    if args.stage == "full" and not args.user_id:
        print("--stage full ต้องระบุ --user-id ด้วย (ใช้ดึงรายการหมวดหมู่ของผู้ใช้)")
        return 1

    selected = [name.strip() for name in args.variants.split(",") if name.strip()]
    unknown = [name for name in selected if name not in VARIANTS]
    if unknown:
        print(f"ไม่รู้จัก variant: {', '.join(unknown)} (เลือกได้: {', '.join(VARIANTS)})")
        return 1

    labels = load_labels(Path(args.labels) if args.labels else None)
    labeled = sum(1 for item in labels.values() if item.get("grand_total") is not None)
    print(f"รูปทั้งหมด {len(images)} ใบ / มีเฉลย {labeled} ใบ / variant: {', '.join(selected)}")
    if args.stage == "full":
        print("โหมด full: จะเรียก LLM สกัดรายการเพิ่มอีก 2 ครั้งต่อรูป")

    db_session = None
    if args.stage == "full":
        from sqlmodel import Session

        from model.models import engine

        db_session = Session(engine)

    all_rows: dict[str, list[dict[str, Any]]] = {}
    try:
        for variant_name in selected:
            variant = VARIANTS[variant_name]
            rows = []
            print(f"\n=== {variant_name} ===")
            for index, image_path in enumerate(images, start=1):
                key = str(image_path.relative_to(root)).replace("\\", "/")
                label = labels.get(key, {})
                image_bytes = image_path.read_bytes()

                try:
                    row = run_one(
                        image_bytes=image_bytes,
                        filename=image_path.name,
                        variant=variant,
                        stage=args.stage,
                        user_id=args.user_id,
                        db_session=db_session,
                    )
                except Exception as e:  # รูปเดียวพังต้องไม่ทำให้ทั้ง benchmark ตาย
                    row = {"ok": False, "error": f"bench error: {e}", "latency_ms": 0, "text": ""}

                expected_total = label.get("grand_total")
                row["file"] = key
                row["expected_total"] = expected_total
                row["total_hit"] = total_in_text(expected_total, row.get("text", ""))
                row["keyword_hit"] = keywords_in_text(label.get("keywords") or [], row.get("text", ""))

                if args.stage == "full" and row["ok"]:
                    expected_items = label.get("item_count")
                    if expected_total is not None:
                        row["total_exact"] = row.get("grand_total") == expected_total
                        row["saved_match"] = abs((row.get("amount_saved") or 0) - expected_total) <= 1.0
                    if expected_items is not None:
                        row["items_match"] = row.get("item_count") == expected_items

                status = "ok " if row["ok"] else "FAIL"
                hit = {True: "hit ", False: "miss", None: "-   "}[row["total_hit"]]
                print(
                    f"  [{index:>3}/{len(images)}] {status} total:{hit} "
                    f"chunks:{row.get('chunk_count', 1)} chars:{row.get('ocr_char_count', 0):>5} "
                    f"{row['latency_ms']:>6}ms  {key}"
                    + (f"  <- {row['error']}" if row.get("error") else "")
                )
                rows.append(row)

            all_rows[variant_name] = rows
    finally:
        if db_session:
            db_session.close()

    summaries = {name: summarize(rows, args.stage) for name, rows in all_rows.items()}
    print_table(summaries)

    if args.out:
        # ตัดข้อความดิบให้สั้นลงก่อนเขียนไฟล์ กันไฟล์บวมเป็นสิบเมกะไบต์
        dump = {
            name: [{**row, "text": row.get("text", "")[:2000]} for row in rows]
            for name, rows in all_rows.items()
        }
        Path(args.out).write_text(
            json.dumps({"summary": summaries, "rows": dump}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        print(f"เขียนผลดิบไว้ที่ {args.out}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
