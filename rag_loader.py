"""
RAG Universal Loader
====================
โหลดข้อมูลได้ทุกรูปแบบ → Embed → บันทึก FAISS → ค้นหา + ถาม Ollama

รองรับ:
  .pdf  .txt  .md  .py  .docx  .csv  .json  .xlsx
  URL (เว็บไซต์)  และ plain text string

วิธีรัน:
  uv run python rag_loader.py
"""

# ─── encoding fix (Windows terminal) ─────────────────────────────────────────
import sys, io
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
elif hasattr(sys.stdout, "buffer"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

import os
from pathlib import Path
from langchain_core.documents import Document
from langchain_community.vectorstores import FAISS
from langchain_ollama import OllamaEmbeddings, ChatOllama
from langchain_text_splitters import RecursiveCharacterTextSplitter


# =============================================================================
# SECTION 1: Universal Loader — รองรับทุกรูปแบบ
# =============================================================================

def load_pdf(path: str) -> list[Document]:
    """โหลด PDF — ต้องติดตั้ง: uv add pypdf"""
    from langchain_community.document_loaders import PyPDFLoader
    return PyPDFLoader(path).load()


def load_txt(path: str) -> list[Document]:
    """โหลด .txt / .md / .py / ไฟล์ text ทั่วไป"""
    from langchain_community.document_loaders import TextLoader
    return TextLoader(path, encoding="utf-8").load()


def load_docx(path: str) -> list[Document]:
    """โหลด Word .docx — ต้องติดตั้ง: uv add docx2txt"""
    from langchain_community.document_loaders import Docx2txtLoader
    return Docx2txtLoader(path).load()


def load_csv(path: str) -> list[Document]:
    """โหลด CSV — แต่ละแถวเป็น 1 document"""
    from langchain_community.document_loaders import CSVLoader
    return CSVLoader(path, encoding="utf-8").load()


def load_excel(path: str) -> list[Document]:
    """โหลด Excel .xlsx — ต้องติดตั้ง: uv add openpyxl pandas"""
    import pandas as pd
    df = pd.read_excel(path)
    docs = []
    for i, row in df.iterrows():
        content = "\n".join(
            f"{col}: {val}" for col, val in row.items() if str(val).strip()
        )
        docs.append(Document(
            page_content=content,
            metadata={"source": path, "row": i, "file_name": Path(path).name},
        ))
    return docs


def load_json(path: str) -> list[Document]:
    """โหลด JSON — รองรับ list หรือ dict"""
    import json
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    items = data if isinstance(data, list) else [data]
    docs = []
    for i, item in enumerate(items):
        content = json.dumps(item, ensure_ascii=False, indent=2)
        docs.append(Document(
            page_content=content,
            metadata={"source": path, "index": i, "file_name": Path(path).name},
        ))
    return docs


def load_url(url: str) -> list[Document]:
    """โหลดเว็บไซต์ — ต้องติดตั้ง: uv add beautifulsoup4"""
    from langchain_community.document_loaders import WebBaseLoader
    return WebBaseLoader(url).load()


def load_directory(folder: str, extensions: list[str] | None = None) -> list[Document]:
    """โหลดทุกไฟล์ใน folder (recursive)"""
    folder_path = Path(folder)
    all_docs: list[Document] = []
    default_exts = extensions or [".pdf", ".txt", ".md", ".py", ".docx", ".csv", ".json", ".xlsx"]

    for ext in default_exts:
        for file_path in folder_path.rglob(f"*{ext}"):
            try:
                docs = load_file(str(file_path))
                all_docs.extend(docs)
                print(f"  ✅ {file_path.name} → {len(docs)} document(s)")
            except Exception as e:
                print(f"  ⚠️  {file_path.name} → ข้ามไป ({e})")

    return all_docs


def load_text_string(text: str, source_name: str = "manual_input") -> list[Document]:
    """โหลดจาก plain text string โดยตรง"""
    return [Document(page_content=text, metadata={"source": source_name})]


def load_file(path: str) -> list[Document]:
    """
    Auto-detect และโหลดไฟล์ตามนามสกุล
    รองรับ: .pdf .txt .md .py .docx .csv .json .xlsx
    """
    ext = Path(path).suffix.lower()
    loaders = {
        ".pdf":  load_pdf,
        ".txt":  load_txt,
        ".md":   load_txt,
        ".py":   load_txt,
        ".docx": load_docx,
        ".csv":  load_csv,
        ".json": load_json,
        ".xlsx": load_excel,
        ".xls":  load_excel,
    }
    loader_fn = loaders.get(ext)
    if loader_fn is None:
        print(f"  ℹ️  ไม่รู้จักนามสกุล '{ext}' — ลองอ่านเป็น text")
        return load_txt(path)
    return loader_fn(path)


# =============================================================================
# SECTION 2: Chunking — ตัดข้อมูลให้พอดีกับการ embed
# =============================================================================

def chunk_documents(
    docs: list[Document],
    chunk_size: int = 500,
    chunk_overlap: int = 50,
) -> list[Document]:
    """
    ตัด documents เป็น chunks ขนาดเล็ก

    Args:
        docs        : list ของ Document จาก loader
        chunk_size  : ขนาด chunk สูงสุด (ตัวอักษร)
        chunk_overlap: overlap ระหว่าง chunk (ป้องกันการตัดกลางประโยค)

    Returns:
        list ของ Document chunks พร้อม metadata เดิม
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", ".", ".", " ", ""],
    )
    chunks = splitter.split_documents(docs)
    print(f"  ✂️  ตัดจาก {len(docs)} → {len(chunks)} chunks (size={chunk_size}, overlap={chunk_overlap})")
    return chunks


# =============================================================================
# SECTION 3: Vector Store — บันทึก/โหลด FAISS index
# =============================================================================

EMBED_MODEL = "nomic-embed-text"   # รันบน Ollama (offline)
CHAT_MODEL  = "qwen2.5-coder:7b"  # เปลี่ยนตาม model ที่มี


def get_embeddings() -> OllamaEmbeddings:
    return OllamaEmbeddings(model=EMBED_MODEL)


def build_and_save(
    chunks: list[Document],
    save_path: str = "knowledge_base",
) -> FAISS:
    """
    Embed chunks และบันทึก FAISS index ลงดิสก์

    Args:
        chunks    : list ของ Document chunks
        save_path : folder สำหรับบันทึก index

    Returns:
        FAISS vectorstore instance
    """
    print(f"\n🔄 กำลัง embed {len(chunks)} chunks ด้วย {EMBED_MODEL}...")
    print("   (อาจใช้เวลา 1-5 นาที ขึ้นอยู่กับจำนวนข้อมูล)")

    embeddings = get_embeddings()
    vectorstore = FAISS.from_documents(chunks, embeddings)

    os.makedirs(save_path, exist_ok=True)
    vectorstore.save_local(save_path)

    print(f"✅ บันทึก {vectorstore.index.ntotal} vectors → '{save_path}/'")
    return vectorstore


def load_vectorstore(save_path: str = "knowledge_base") -> FAISS:
    """โหลด FAISS index ที่บันทึกไว้แล้วกลับมาใช้งาน"""
    embeddings = get_embeddings()
    vs = FAISS.load_local(save_path, embeddings, allow_dangerous_deserialization=True)
    print(f"📂 โหลด vector store จาก '{save_path}/' ({vs.index.ntotal} vectors)")
    return vs


def add_to_existing(
    new_chunks: list[Document],
    save_path: str = "knowledge_base",
) -> FAISS:
    """
    เพิ่มข้อมูลใหม่เข้า vector store ที่มีอยู่แล้ว
    (ไม่ต้อง embed ข้อมูลเก่าทั้งหมดใหม่)
    """
    embeddings = get_embeddings()
    existing_vs = FAISS.load_local(save_path, embeddings, allow_dangerous_deserialization=True)

    print(f"📥 เพิ่ม {len(new_chunks)} chunks เข้า existing store ({existing_vs.index.ntotal} vectors)...")
    new_vs = FAISS.from_documents(new_chunks, embeddings)
    existing_vs.merge_from(new_vs)
    existing_vs.save_local(save_path)

    print(f"✅ รวมแล้ว: {existing_vs.index.ntotal} vectors → '{save_path}/'")
    return existing_vs


# =============================================================================
# SECTION 4: RAG Query — ค้นหาและถาม Ollama (offline)
# =============================================================================

def _find_matching_source(vectorstore: FAISS, question: str) -> str | None:
    """
    ตรวจว่าคำถามกล่าวถึงชื่อไฟล์ใดใน vectorstore หรือไม่
    คืน path ของ source ที่ตรงกัน หรือ None ถ้าไม่มี
    """
    all_sources: set[str] = set()
    for doc_id in vectorstore.docstore._dict:
        doc = vectorstore.docstore._dict[doc_id]
        src = doc.metadata.get("source", "")
        if src:
            all_sources.add(src)

    q_lower = question.lower()
    for src in all_sources:
        stem = Path(src).stem.lower()
        name = Path(src).name.lower()
        if stem in q_lower or name in q_lower:
            return src
    return None


def _keyword_search(
    vectorstore: FAISS,
    question: str,
    k: int = 10,
) -> list[tuple]:
    """
    ค้นหาด้วย Keyword matching (BM25-style) โดยไม่ต้องพึ่ง embedding model
    ใช้เป็น fallback หรือ hybrid เมื่อ semantic search ไม่แม่นพอ

    Returns list of (Document, keyword_score) เรียงจากมากไปน้อย
    """
    import re

    # แยกคำจากคำถาม (กรองคำสั้น ๆ ที่ไม่มีความหมาย)
    tokens = re.sub(r"[^\wก-๙]", " ", question.lower()).split()
    keywords = [t for t in tokens if len(t) > 1]

    if not keywords:
        return []

    scored: list[tuple] = []
    all_docs = list(vectorstore.docstore._dict.values())

    for doc in all_docs:
        content = doc.page_content.lower()
        # นับจำนวนครั้งที่แต่ละ keyword ปรากฏ (term frequency)
        tf_score = sum(content.count(kw) for kw in keywords)
        # bonus: ถ้า keyword ปรากฏในประโยคเดียวกัน (proximity bonus)
        prox_bonus = sum(1 for kw in keywords if kw in content) / max(len(keywords), 1)
        final_score = tf_score + prox_bonus * 5
        if final_score > 0:
            scored.append((doc, final_score))

    scored.sort(key=lambda x: x[1], reverse=True)
    return scored[:k]


def search_context(
    vectorstore: FAISS,
    question: str,
    k: int = 5,
) -> list[tuple]:
    """
    ค้นหาข้อมูลที่เกี่ยวข้องจาก vectorstore
    """
    matched_source = _find_matching_source(vectorstore, question)

    if matched_source:
        print(f"\n📁 ตรวจพบชื่อไฟล์ → ดึงจาก: {Path(matched_source).name}")
        all_docs = [
            doc for doc in vectorstore.docstore._dict.values()
            if doc.metadata.get("source", "") == matched_source
        ]
        results = [(doc, 0.0) for doc in all_docs[:k]]

    else:
        # Hybrid Search: Keyword + Semantic
        fetch_k = k * 4

        # Semantic search
        sem_results = vectorstore.similarity_search_with_score(question, k=fetch_k)

        # Keyword search
        kw_results = _keyword_search(vectorstore, question, k=fetch_k)

        # Reciprocal Rank Fusion (RRF)
        RRF_K = 60
        doc_scores: dict[str, float] = {}
        doc_map:    dict[str, object] = {}

        def _doc_id(doc) -> str:
            return doc.page_content[:120]

        for rank, (doc, _) in enumerate(sem_results):
            did = _doc_id(doc)
            doc_scores[did] = doc_scores.get(did, 0) + 1 / (rank + RRF_K)
            doc_map[did] = doc

        for rank, (doc, _) in enumerate(kw_results):
            did = _doc_id(doc)
            doc_scores[did] = doc_scores.get(did, 0) + 1 / (rank + RRF_K)
            doc_map[did] = doc

        top_ids = sorted(doc_scores, key=lambda d: doc_scores[d], reverse=True)[:k]
        results = [(doc_map[did], doc_scores[did]) for did in top_ids]

        mode = "🔀 Hybrid (Keyword + Semantic)"
        print(f"\n   [{mode}]")

    return results

def generate_answer(question: str, context: str, model: str = CHAT_MODEL) -> str:
    """ส่งคำถามและ context ไปให้ LLM สร้างคำตอบ"""
    if not context.strip():
        return "ไม่พบข้อมูลที่เกี่ยวข้องใน knowledge base"

    llm = ChatOllama(model=model)
    prompt = f"""คุณคือ assistant ที่ตอบคำถามจากข้อมูลที่ให้มาเท่านั้น
ถ้าข้อมูลไม่เพียงพอ ให้บอกตามตรง อย่าเดาหรือแต่งเติม

ข้อมูลอ้างอิง:
{context}

คำถาม: {question}

คำตอบ:"""
    response = llm.invoke(prompt)
    return response.content

def ask(
    vectorstore: FAISS,
    question: str,
    k: int = 5,
    model: str = CHAT_MODEL,
) -> str:
    """
    ค้นหาข้อมูลที่เกี่ยวข้องแล้วถาม Ollama (ทำงานออฟไลน์)
    """
    results = search_context(vectorstore, question, k)
    if not results:
        return "ไม่พบข้อมูลที่เกี่ยวข้องใน knowledge base"

    context_parts = []
    print(f"\n🔍 พบ {len(results)} chunks ที่เกี่ยวข้อง:")
    for doc, score in results:
        source = doc.metadata.get("source", "unknown")
        print(f"   Score {score:.4f} | {Path(source).name}")
        context_parts.append(f"[จาก: {Path(source).name}]\n{doc.page_content}")

    context = "\n\n---\n\n".join(context_parts)
    return generate_answer(question, context, model)


# =============================================================================
# SECTION 5: Pipeline Helper — ฟังก์ชันสำเร็จรูป
# =============================================================================

def ingest(
    sources: list[str],
    save_path: str = "knowledge_base",
    chunk_size: int = 500,
    chunk_overlap: int = 50,
    add_to_existing_store: bool = False,
) -> FAISS:
    """
    Pipeline สำเร็จรูป: โหลด → ตัด → embed → บันทึก

    Args:
        sources              : list ของ path ไฟล์, URL, หรือ folder
        save_path            : folder สำหรับบันทึก vector store
        chunk_size           : ขนาด chunk (ตัวอักษร)
        chunk_overlap        : overlap ระหว่าง chunk
        add_to_existing_store: True = เพิ่มข้อมูลเข้าที่มีอยู่แล้ว

    Returns:
        FAISS vectorstore instance
    """
    all_docs: list[Document] = []

    print("📥 กำลังโหลดข้อมูล...")
    for source in sources:
        print(f"\n  → {source}")
        try:
            if source.startswith("http://") or source.startswith("https://"):
                docs = load_url(source)
            elif Path(source).is_dir():
                docs = load_directory(source)
            else:
                docs = load_file(source)
            all_docs.extend(docs)
            print(f"     โหลดได้ {len(docs)} document(s)")
        except Exception as e:
            print(f"     ❌ Error: {e}")

    print(f"\n📊 รวม: {len(all_docs)} documents")

    chunks = chunk_documents(all_docs, chunk_size, chunk_overlap)

    if add_to_existing_store and Path(save_path).exists():
        return add_to_existing(chunks, save_path)
    else:
        return build_and_save(chunks, save_path)



