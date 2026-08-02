# Slide Deck 2: FAISS Vector Search

> Session 07 | Module 3: Vector DB & Embeddings | 10 slides

---

## Slide 1 - What is FAISS?

**Key Message:** FAISS คือ library สำหรับ similarity search ที่เร็วและมีประสิทธิภาพ พัฒนาโดย Meta AI

- **FAISS** = Facebook AI Similarity Search
- ค้นหา vectors ที่ "ใกล้เคียงที่สุด" จาก millions ของ vectors ได้อย่างรวดเร็ว
- ใช้ **cosine similarity** หรือ **L2 distance** ในการเปรียบเทียบ
- รองรับ CPU และ GPU
- ใน LangChain: `langchain_community.vectorstores.FAISS`

[FIGURE: Scatter plot of dots (document vectors) in 2D space. A star (query vector) is shown. Arrows point from star to the 3 nearest dots, labeled "Top-3 results". Title: "Vector Space Search". Note: Real embeddings are 768+ dimensions but visualized in 2D.]

---

## Slide 2 - How Embeddings Work

**Key Message:** Embedding แปลง text เป็น vector ที่แสดง "ความหมาย" — ข้อความคล้ายกัน = vector ใกล้กัน

- `nomic-embed-text` สร้าง **768-dimensional vector** สำหรับแต่ละ text
- "read CSV file" และ "load_csv function" → vectors ใกล้กัน
- "authentication" และ "read CSV" → vectors ไกลกัน
- ความใกล้ = cosine similarity หรือ inverse of L2 distance

[FIGURE: 3D visualization (simplified from 768D). Show vectors for "read CSV", "load_csv()", "parse data" clustered together. "login()", "authenticate()" clustered separately. Arrow showing distance between clusters.]

---

## Slide 3 - FAISS in LangChain — The API

**Key Message:** LangChain ห่อ FAISS ด้วย API ที่ใช้ง่าย ไม่ต้องจัดการ vectors โดยตรง

[EXAMPLE:
```python
from langchain_community.vectorstores import FAISS
from langchain_ollama import OllamaEmbeddings
from langchain_core.documents import Document

# 1. สร้าง embedding model
embeddings = OllamaEmbeddings(model="nomic-embed-text")

# 2. สร้าง FAISS จาก documents (embed + index ในขั้นตอนเดียว)
vectorstore = FAISS.from_documents(documents, embeddings)

# 3. Search
results = vectorstore.similarity_search("query text", k=5)

# 4. Save
vectorstore.save_local("vector_db/")

# 5. Load
vs = FAISS.load_local("vector_db/", embeddings, allow_dangerous_deserialization=True)
```
]

---

## Slide 4 - Building the Index Step by Step

**Key Message:** `FAISS.from_documents()` ทำ embed + index ให้อัตโนมัติ — แต่ใช้เวลาตาม size

[FIGURE: Timeline/flowchart. Step 1: Documents list (47 docs). Step 2: OllamaEmbeddings calls nomic-embed-text API (local). Step 3: 47 x 768-dim vectors created. Step 4: FAISS index built. Step 5: Save to disk (2 files: .faiss + .pkl). Estimated time annotations: ~2-5 min for 47 docs on laptop.]

- **ขั้นตอนการทำงาน:**
  1. LangChain ส่ง `page_content` ของแต่ละ document ไปให้ Ollama embed
  2. ได้ vectors กลับมา (768 dimensions ต่อ document)
  3. FAISS สร้าง index จาก vectors
  4. บันทึก index (`.faiss`) และ metadata (`.pkl`) ลงดิสก์

- **Files ที่ได้:** `vector_db/index.faiss` + `vector_db/index.pkl`

---

## Slide 5 - Similarity Search Types

**Key Message:** FAISS ใน LangChain มีหลาย search methods — เลือกตาม use case

| Method | Return Type | เมื่อใช้ |
|--------|-------------|---------|
| `similarity_search(q, k)` | `list[Document]` | ต้องการแค่ documents |
| `similarity_search_with_score(q, k)` | `list[tuple[Document, float]]` | ต้องการ score ด้วย |
| `similarity_search_with_relevance_scores(q, k)` | `list[tuple[Document, float]]` | score normalized 0–1 |
| `max_marginal_relevance_search(q, k)` | `list[Document]` | ต้องการ diversity |

[EXAMPLE:
```python
# พร้อม L2 distance (ต่ำกว่า = ใกล้กว่า)
results = vs.similarity_search_with_score("read CSV", k=3)
for doc, score in results:
    print(f"{score:.3f} | {doc.metadata['function_name']}")
# Output:
# 0.312 | load_csv
# 0.487 | read_data
# 0.651 | parse_file
```
]

---

## Slide 6 - Metadata Filtering

**Key Message:** Filter ด้วย metadata ช่วยให้ค้นหาเฉพาะ subset ที่ต้องการได้โดยไม่ต้องสร้าง index ใหม่

[EXAMPLE:
```python
# ค้นหาทั้ง index
results = vs.similarity_search("authentication", k=5)

# ค้นหาเฉพาะใน auth.py
results = vs.similarity_search(
    "authentication",
    k=5,
    filter={"file_name": "auth.py"}
)

# ค้นหาเฉพาะ function ชื่อ validate*
# (FAISS filter เป็น exact match — ใช้ post-filter สำหรับ prefix)
all_results = vs.similarity_search("validate input", k=20)
filtered = [d for d in all_results 
            if d.metadata["function_name"].startswith("validate")]
```
]

- **FAISS filter** รองรับ exact match บน metadata fields
- สำหรับ fuzzy/prefix match → ดึงมาก่อนแล้ว filter เอง (post-filtering)

---

## Slide 7 - Saving and Loading the Index

**Key Message:** Save/Load FAISS index เพื่อไม่ต้อง embed ซ้ำทุกครั้ง — ประหยัดเวลามาก

[FIGURE: Workflow diagram. Left side: "First time" — Parse → Embed (slow, 2-5 min) → Save to disk. Right side: "Every time after" — Load from disk (fast, < 1 sec) → Search immediately. Arrow between them showing disk icon as persistent storage.]

[EXAMPLE:
```python
# ─── Save index ──────────────────────────────────────────────────────────────
# สร้าง directory ถ้ายังไม่มี แล้ว save
import os
os.makedirs("vector_db", exist_ok=True)
vectorstore.save_local("vector_db")
# สร้างไฟล์: vector_db/index.faiss, vector_db/index.pkl

# ─── Load index ──────────────────────────────────────────────────────────────
# ต้องใช้ embedding model เดิมเสมอ
embeddings = OllamaEmbeddings(model="nomic-embed-text")
vs = FAISS.load_local(
    "vector_db",
    embeddings,
    allow_dangerous_deserialization=True,  # required!
)
print(f"Loaded {vs.index.ntotal} vectors")
```
]

---

## Slide 8 - Retrieval Quality Metrics

**Key Message:** วัด Precision@K และ Recall@K เพื่อรู้ว่า retrieval ของเรา "ดี" แค่ไหน

- **Precision@K**: ใน K ผลลัพธ์แรก มีกี่ % ที่ relevant?
  - `P@5 = 3/5 = 0.60` → 3 ใน 5 ผลลัพธ์ตรง
- **Recall@K**: ในทั้งหมดที่ควรได้ เราหาเจอกี่ %?
  - `R@5 = 3/4 = 0.75` → เจอ 3 จาก 4 ที่ควรเจอ

[FIGURE: Grid showing query "load CSV file". Relevant functions marked with checkmark: load_csv ✓, read_data ✓, parse_csv ✓, load_json ✗ (not relevant). Retrieved top-5: load_csv ✓, parse_csv ✓, read_data ✓, open_file ✗, fetch_url ✗. P@5 = 3/5 = 0.60. R@5 = 3/4 = 0.75.]

---

## Slide 9 - Full End-to-End Demo

**Key Message:** pipeline ทั้งหมดจาก directory ของ Python files ถึง semantic search ทำได้ใน ~50 บรรทัด

[EXAMPLE:
```powershell
# Terminal: build index
uv run python build_index.py --dir ./my_project --save vector_db

# Output:
# Found 8 Python files
# Total chunks: 47 functions
# Embedding 47 documents...
# Saved FAISS index to 'vector_db/'
```

```powershell
# Terminal: search
uv run python search.py --query "read CSV file" --top-k 3

# Output:
# Results for: 'read CSV file'
# ────────────────────────────────────────
# [1] load_csv — utils.py (line 12–14)
#     def load_csv(path): return pd.read_csv(path)
# [2] read_data — data_loader.py (line 8–20)
#     def read_data(filepath, format="csv"): ...
# [3] parse_input — cli.py (line 45–58)
#     def parse_input(args): ...
```
]

---

## Slide 10 - Common Mistakes and Fixes

**Key Message:** ปัญหาที่พบบ่อยในการใช้ FAISS มักแก้ได้ง่ายถ้ารู้ root cause

| ปัญหา | สาเหตุ | วิธีแก้ |
|--------|--------|---------|
| Index ว่าง (0 vectors) | `from_documents()` ได้ list ว่าง | Print len(documents) ก่อน |
| Results ไม่ตรง | Metadata filter ผิด field | Print `doc.metadata` ดู keys จริง |
| Load fails | ใช้ embedding model ต่างกัน | ใช้ model เดิมทั้ง build และ load |
| Slow embedding | Ollama ไม่ได้รัน | Check `ollama list` |
| `allow_dangerous_deserialization` error | ลืมใส่ parameter | เพิ่ม `allow_dangerous_deserialization=True` |

[EXAMPLE:
```python
# Debug: ตรวจสอบ index
print(f"Index size: {vs.index.ntotal}")
print(f"Dimension: {vs.index.d}")

# Debug: ดู metadata ของ document แรก
sample = vs.similarity_search("test", k=1)
if sample:
    print(f"Metadata keys: {list(sample[0].metadata.keys())}")
```
]
