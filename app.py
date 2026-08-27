"""
RAG Web App — Flask Backend
============================
รันด้วย:
  uv run python app.py

แล้วเปิดเบราว์เซอร์ที่ http://localhost:5000
"""

# ─── encoding fix (Windows terminal) ──────────────────────────────────────────
import sys, io
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
elif hasattr(sys.stdout, "buffer"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

import json
import os
import shutil
from pathlib import Path
from flask import Flask, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename
from rag_loader import ask, load_vectorstore, ingest, search_context, generate_answer

app = Flask(__name__, static_folder="web", static_url_path="")

# ─── config ───────────────────────────────────────────────────────────────────
KNOWLEDGE_BASE_PATH = "my_knowledge_base"
DATA_FOLDER         = "my_data"
TRACKER_FILE        = "my_knowledge_base/.indexed_files.json"
ALLOWED_EXTENSIONS  = {".pdf", ".txt", ".md", ".docx", ".csv", ".json", ".xlsx"}

MY_URLS = [
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
    "https://www.athometh.com/math/solving-equations/",
]

# ─── global vectorstore (โหลดครั้งเดียว) ────────────────────────────────────
_vectorstore = None


def get_vectorstore():
    global _vectorstore
    if _vectorstore is None:
        kb_path = Path(KNOWLEDGE_BASE_PATH)
        if kb_path.exists():
            _vectorstore = load_vectorstore(KNOWLEDGE_BASE_PATH)
    return _vectorstore


def reload_vectorstore():
    global _vectorstore
    _vectorstore = None
    return get_vectorstore()


# ─── tracker helpers ─────────────────────────────────────────────────────────
def load_tracker() -> dict:
    p = Path(TRACKER_FILE)
    if p.exists():
        return json.loads(p.read_text(encoding="utf-8"))
    return {}


def save_tracker(data: dict):
    Path(TRACKER_FILE).write_text(
        json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def get_file_signature(path: Path) -> str:
    stat = path.stat()
    return f"{stat.st_size}_{stat.st_mtime}"


# ─── routes ──────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return send_from_directory("web", "index.html")


@app.route("/api/status")
def api_status():
    """ตรวจสถานะ knowledge base"""
    kb_path = Path(KNOWLEDGE_BASE_PATH)
    tracker = load_tracker()

    # นับไฟล์ใน my_data
    data_path = Path(DATA_FOLDER)
    data_path.mkdir(exist_ok=True)
    files = [f for f in data_path.rglob("*") if f.is_file()]

    # นับ vectors
    vs = get_vectorstore()
    vector_count = vs.index.ntotal if vs else 0

    # ตรวจไฟล์ที่ยังไม่ได้ embed
    pending_files = []
    for f in files:
        sig = get_file_signature(f)
        if tracker.get(str(f)) != sig:
            pending_files.append(f.name)

    pending_urls = [u for u in MY_URLS if u not in tracker]

    return jsonify({
        "kb_ready": kb_path.exists() and vs is not None,
        "vector_count": vector_count,
        "file_count": len(files),
        "indexed_count": len(tracker),
        "pending_files": pending_files,
        "pending_url_count": len(pending_urls),
        "files": [f.name for f in files],
    })


@app.route("/api/search", methods=["POST"])
def api_search():
    """ค้นหาข้อมูลที่เกี่ยวข้องจาก knowledge base (ส่งคืนแหล่งที่มา)"""
    data = request.get_json()
    question = (data or {}).get("question", "").strip()
    if not question:
        return jsonify({"error": "กรุณาพิมพ์คำถาม"}), 400

    vs = get_vectorstore()
    if vs is None:
        return jsonify({"error": "ยังไม่มี knowledge base กรุณา embed ข้อมูลก่อน"}), 503

    try:
        results = search_context(vs, question)
        if not results:
            return jsonify({"sources": [], "context": ""})

        sources = list(set([Path(doc.metadata.get("source", "unknown")).name for doc, score in results]))
        
        context_parts = []
        for doc, score in results:
            source = doc.metadata.get("source", "unknown")
            context_parts.append(f"[จาก: {Path(source).name}]\n{doc.page_content}")
            
        context = "\n\n---\n\n".join(context_parts)
        
        return jsonify({"sources": sources, "context": context})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/generate", methods=["POST"])
def api_generate():
    """สร้างคำตอบจาก context ที่ให้มา"""
    data = request.get_json()
    question = (data or {}).get("question", "").strip()
    context = (data or {}).get("context", "").strip()
    
    if not question:
        return jsonify({"error": "กรุณาพิมพ์คำถาม"}), 400

    try:
        answer = generate_answer(question, context)
        return jsonify({"answer": answer})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/chat", methods=["POST"])
def api_chat():
    """ตอบคำถามจาก knowledge base (แบบเดิม รวม search+generate)"""
    data = request.get_json()
    question = (data or {}).get("question", "").strip()
    if not question:
        return jsonify({"error": "กรุณาพิมพ์คำถาม"}), 400

    vs = get_vectorstore()
    if vs is None:
        return jsonify({"error": "ยังไม่มี knowledge base กรุณา embed ข้อมูลก่อน"}), 503

    try:
        answer = ask(vs, question)
        return jsonify({"answer": answer})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/upload", methods=["POST"])
def api_upload():
    """อัปโหลดไฟล์ลง my_data/"""
    if "files" not in request.files:
        return jsonify({"error": "ไม่พบไฟล์"}), 400

    uploaded = []
    skipped  = []
    data_path = Path(DATA_FOLDER)
    data_path.mkdir(exist_ok=True)

    for f in request.files.getlist("files"):
        ext = Path(f.filename).suffix.lower()
        if ext not in ALLOWED_EXTENSIONS:
            skipped.append(f.filename)
            continue
        fname = secure_filename(f.filename)
        f.save(data_path / fname)
        uploaded.append(fname)

    return jsonify({"uploaded": uploaded, "skipped": skipped})


@app.route("/api/embed", methods=["POST"])
def api_embed():
    """embed ไฟล์ใหม่ทั้งหมดใน my_data/ + URL ใน MY_URLS"""
    data_path = Path(DATA_FOLDER)
    data_path.mkdir(exist_ok=True)

    tracker = load_tracker()
    new_sources = []

    # ตรวจไฟล์ใหม่
    for f in data_path.rglob("*"):
        if f.is_file():
            sig = get_file_signature(f)
            if tracker.get(str(f)) != sig:
                new_sources.append(("file", f))

    # ตรวจ URL ใหม่
    data = request.get_json() or {}
    embed_urls = data.get("embed_urls", False)
    if embed_urls:
        for url in MY_URLS:
            if url not in tracker:
                new_sources.append(("url", url))

    if not new_sources:
        return jsonify({"message": "ไม่มีข้อมูลใหม่ที่ต้อง embed", "count": 0})

    kb_exists = Path(KNOWLEDGE_BASE_PATH).exists()
    try:
        ingest(
            [str(src) if kind == "file" else src for kind, src in new_sources],
            save_path=KNOWLEDGE_BASE_PATH,
            add_to_existing_store=kb_exists,
        )
        for kind, src in new_sources:
            if kind == "file":
                tracker[str(src)] = get_file_signature(src)
            else:
                tracker[src] = "url"
        save_tracker(tracker)

        # reload vectorstore
        reload_vectorstore()

        return jsonify({
            "message": f"embed เสร็จสิ้น {len(new_sources)} รายการ",
            "count": len(new_sources),
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/files", methods=["GET"])
def api_files():
    """รายการไฟล์ใน my_data/"""
    data_path = Path(DATA_FOLDER)
    data_path.mkdir(exist_ok=True)
    tracker = load_tracker()
    files = []
    for f in sorted(data_path.rglob("*")):
        if f.is_file():
            sig = get_file_signature(f)
            files.append({
                "name": f.name,
                "size": f.stat().st_size,
                "indexed": tracker.get(str(f)) == sig,
            })
    return jsonify({"files": files})


@app.route("/api/files/<filename>", methods=["DELETE"])
def api_delete_file(filename):
    """ลบไฟล์ออกจาก my_data/"""
    data_path = Path(DATA_FOLDER)
    target = data_path / secure_filename(filename)
    if not target.exists():
        return jsonify({"error": "ไม่พบไฟล์"}), 404
    tracker = load_tracker()
    tracker.pop(str(target), None)
    save_tracker(tracker)
    target.unlink()
    return jsonify({"message": f"ลบ {filename} เรียบร้อย"})


if __name__ == "__main__":
    print("=" * 60)
    print("🌐 RAG Web App")
    print("=" * 60)
    print(f"📂 Data folder : {DATA_FOLDER}/")
    print(f"🗄  Knowledge   : {KNOWLEDGE_BASE_PATH}/")
    print("─" * 60)
    print("🚀 เปิดเบราว์เซอร์ที่: http://localhost:5000")
    print("=" * 60)
    app.run(debug=True, port=5000, use_reloader=False)
