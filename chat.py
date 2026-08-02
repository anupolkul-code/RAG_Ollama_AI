"""
RAG Chat — ถามผ่าน terminal แบบ interactive
============================================
วิธีรัน:
  uv run python chat.py

- ตรวจสอบไฟล์ใหม่ใน my_data/ อัตโนมัติ → embed ถ้ามีของใหม่
- เพิ่ม URL ใน MY_URLS → ดึงและ embed อัตโนมัติ (ต้องมีอินเทอร์เน็ตครั้งแรก)
- พิมพ์คำถาม แล้วกด Enter → ได้คำตอบ
- พิมพ์ 'exit' หรือ 'quit' หรือกด Ctrl+C เพื่อออก
"""

# ─── encoding fix (Windows terminal) ─────────────────────────────────────────
import sys, io
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
elif hasattr(sys.stdout, "buffer"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

import json
from pathlib import Path
from rag_loader import ask, load_vectorstore, ingest

# ─── config ───────────────────────────────────────────────────────────────────
KNOWLEDGE_BASE_PATH = "my_knowledge_base"
DATA_FOLDER         = "my_data"
TRACKER_FILE        = "my_knowledge_base/.indexed_files.json"  # ติดตามไฟล์/URL ที่ embed แล้ว

# ✏️  เพิ่ม URL ที่ต้องการดึงข้อมูลที่นี่ (ต้องการอินเทอร์เน็ตแค่ครั้งแรก)
MY_URLS = [
    # ── ภาษาอังกฤษ ───────────────────────────────────────────────────
    "https://en.wikipedia.org/wiki/Python_(programming_language)",
    "https://en.wikipedia.org/wiki/Mathematics",
    "https://en.wikipedia.org/wiki/Physics",
    "https://en.wikipedia.org/wiki/Chemistry",
    "https://en.wikipedia.org/wiki/Biology",
    "https://en.wikipedia.org/wiki/Computer_science",
    "https://en.wikipedia.org/wiki/Electrical_engineering",
    "https://en.wikipedia.org/wiki/Mechanical_engineering",
    "https://en.wikipedia.org/wiki/Civil_engineering",
    "https://en.wikipedia.org/wiki/Chemical_engineering",
    "https://en.wikipedia.org/wiki/Aerospace_engineering",
    "https://en.wikipedia.org/wiki/Biomedical_engineering",
    "https://en.wikipedia.org/wiki/Environmental_engineering",
    "https://en.wikipedia.org/wiki/Information_technology",
    "https://en.wikipedia.org/wiki/History",
    "https://en.wikipedia.org/wiki/Social_science",
    "https://en.wikipedia.org/wiki/Humanities",
    "https://en.wikipedia.org/wiki/Linguistics",
    "https://en.wikipedia.org/wiki/Program",

    # ── ภาษาไทย (Thai Wikipedia) ──────────────────────────────────────
    "https://th.wikipedia.org/wiki/คณิตศาสตร์",
    "https://th.wikipedia.org/wiki/ฟิสิกส์",
    "https://th.wikipedia.org/wiki/เคมี",
    "https://th.wikipedia.org/wiki/ชีววิทยา",
    "https://th.wikipedia.org/wiki/วิทยาการคอมพิวเตอร์",
    "https://th.wikipedia.org/wiki/ประวัติศาสตร์",
    "https://th.wikipedia.org/wiki/ภาษาไทย",
    "https://th.wikipedia.org/wiki/สังคมศาสตร์",
    "https://th.wikipedia.org/wiki/มนุษยศาสตร์",
    "https://th.wikipedia.org/wiki/ภาษาศาสตร์",
    "https://th.wikipedia.org/wiki/การเขียนโปรแกรมคอมพิวเตอร์",
]
# ──────────────────────────────────────────────────────────────────────────────


def load_tracker() -> dict:
    """โหลดรายการไฟล์ที่ embed ไปแล้ว"""
    p = Path(TRACKER_FILE)
    if p.exists():
        return json.loads(p.read_text(encoding="utf-8"))
    return {}


def save_tracker(data: dict):
    """บันทึกรายการไฟล์ที่ embed แล้ว"""
    Path(TRACKER_FILE).write_text(
        json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def get_file_signature(path: Path) -> str:
    """ใช้ขนาด + วันแก้ไขเป็น signature ตรวจสอบการเปลี่ยนแปลง"""
    stat = path.stat()
    return f"{stat.st_size}_{stat.st_mtime}"


def check_and_embed_new_files() -> bool:
    """
    ตรวจว่ามีไฟล์ใหม่ใน my_data/ หรือ URL ใหม่ใน MY_URLS หรือเปล่า
    ถ้ามี → embed อัตโนมัติ → return True
    """
    data_path = Path(DATA_FOLDER)
    data_path.mkdir(exist_ok=True)

    tracker = load_tracker()
    new_sources = []

    # ── ตรวจไฟล์ใน my_data/ (รวมโฟลเดอร์ย่อย) ───────────────────────
    for f in data_path.rglob("*"):
        if f.is_file():
            sig = get_file_signature(f)
            if tracker.get(str(f)) != sig:
                new_sources.append(("file", f))

    # ── ตรวจ URL ใน MY_URLS ───────────────────────────────────────────
    for url in MY_URLS:
        if url not in tracker:
            new_sources.append(("url", url))

    if not new_sources:
        return False

    # แสดงรายการที่จะ embed
    print(f"\n🆕 พบข้อมูลใหม่ {len(new_sources)} รายการ:")
    for kind, src in new_sources:
        label = src.name if kind == "file" else src
        icon  = "📄" if kind == "file" else "🌐"
        print(f"   {icon} {label}")

    print("\n🔄 กำลัง embed ข้อมูลใหม่...")
    kb_exists = Path(KNOWLEDGE_BASE_PATH).exists()
    ingest(
        [str(src) if kind == "file" else src for kind, src in new_sources],
        save_path=KNOWLEDGE_BASE_PATH,
        add_to_existing_store=kb_exists,
    )

    # อัปเดต tracker
    for kind, src in new_sources:
        if kind == "file":
            tracker[str(src)] = get_file_signature(src)
        else:
            tracker[src] = "url"  # URL ไม่มี signature ใช้ "url" แทน
    save_tracker(tracker)


    return True


def main():
    print("=" * 60)
    print("💬 RAG Chat — ถามจาก knowledge base ของคุณ")
    print("=" * 60)

    # ตรวจและ embed ไฟล์ใหม่อัตโนมัติ
    had_new_files = check_and_embed_new_files()

    # โหลด knowledge base
    kb_path = Path(KNOWLEDGE_BASE_PATH)
    if not kb_path.exists():
        print(f"\n❌ ยังไม่มี knowledge base")
        print(f"   → วางไฟล์ใน '{DATA_FOLDER}/' แล้วรัน chat.py ใหม่")
        return

    if not had_new_files:
        print("✅ ไม่มีไฟล์ใหม่ — ใช้ knowledge base เดิม")

    print(f"\n📂 โหลด knowledge base...")
    vs = load_vectorstore(KNOWLEDGE_BASE_PATH)
    print("✅ พร้อมแล้ว! พิมพ์คำถามได้เลย (พิมพ์ 'exit' เพื่อออก)\n")

    while True:
        try:
            question = input("❓ คำถาม: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\n\n👋 ออกจากโปรแกรม")
            break

        if not question:
            continue

        if question.lower() in ("exit", "quit", "ออก", "/bye"):
            print("👋 ออกจากโปรแกรม")
            break

        print("\n🤔 กำลังค้นหาและตอบ...\n")
        answer = ask(vs, question)
        print(f"💡 คำตอบ:\n{answer}")
        print("\n" + "-" * 60 + "\n")


if __name__ == "__main__":
    main()
