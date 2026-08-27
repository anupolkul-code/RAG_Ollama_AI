# Session 07 — FAISS + Code Chunking

> **Module 3: Vector DB & Embeddings** | ครั้งที่ 7 จาก 14 | 3 ชั่วโมง

**Course:** Local RAG for Programming  
**Duration:** 180 minutes  
**Prerequisites:** Sessions 01–06 (Python basics, Ollama setup, LangChain intro)

---

## เป้าหมายของ Session นี้

เมื่อจบ session นี้ นักเรียนจะสามารถ:

1. อธิบาย chunking strategies ได้: semantic (ตาม function/class) vs fixed-size
2. Parse Python ไฟล์ด้วย `ast` module แล้วแยก functions เป็น chunks ได้
3. สร้าง FAISS index จาก embeddings และ save/load ได้
4. ค้นหา code ที่เกี่ยวข้องด้วย natural language query ได้
5. Filter ผลลัพธ์ด้วย metadata (filename, function_name) ได้

---

## ตารางเวลา

| ช่วง | เวลา | หัวข้อ |
|------|------|--------|
| 1 | 30 นาที | Theory: Chunking strategies — ตัดตาม function, class, หรือขนาด |
| 2 | 70 นาที | Workshop: Parse Python files → chunk → embed → เก็บใน FAISS |
| 3 | 60 นาที | Workshop: ค้นหา: semantic search, filter by file/function, metadata |
| 4 | 20 นาที | Workshop: วัด retrieval quality |

---

## ช่วงที่ 1 — Theory: Chunking Strategies (30 นาที)

### ทำไม Chunking ถึงสำคัญ?

ก่อนที่จะ embed โค้ดหรือข้อความลง vector database เราต้องแบ่งมันออกเป็น "chunks" ก่อน เหตุผลหลักคือ:

1. **Embedding models มีขนาด input จำกัด** — `nomic-embed-text` รับได้ประมาณ 8192 tokens
2. **Retrieval precision** — chunk ที่เล็กกว่าจะ match กับ query ได้แม่นยำกว่า
3. **Context relevance** — เราต้องการส่ง context ที่ตรงกับคำถาม ไม่ใช่ทั้งไฟล์

### Chunking Strategies เปรียบเทียบ

#### 1. Fixed-Size Chunking (ตัดตามขนาด)
```python
# ─── Fixed-size chunking ────────────────────────────────────────────────────
# วัตถุประสงค์: แบ่ง text เป็นชิ้นๆ ตามจำนวนตัวอักษรหรือ tokens
# ง่ายที่สุดแต่ไม่สนใจโครงสร้างของโค้ด — อาจตัดกลางฟังก์ชัน

def fixed_size_chunks(text: str, chunk_size: int = 500, overlap: int = 50) -> list[str]:
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start += chunk_size - overlap  # overlap ช่วยให้ context ต่อเนื่อง
    return chunks
```

**ข้อดี:** ง่าย, เร็ว, ทำนาย size ได้  
**ข้อเสีย:** ตัดกลางฟังก์ชัน, ไม่เข้าใจโครงสร้าง

#### 2. Semantic Chunking (ตามโครงสร้าง)
```python
# ─── Semantic chunking by function ──────────────────────────────────────────
# วัตถุประสงค์: ใช้ Python AST parser เพื่อแยก chunk ตาม function/class boundary
# แต่ละ chunk คือ 1 function ทำให้ retrieval แม่นยำมากขึ้น

import ast

def extract_functions(filepath: str) -> list[dict]:
    with open(filepath, "r", encoding="utf-8") as f:
        source = f.read()
    
    tree = ast.parse(source)
    source_lines = source.splitlines()
    chunks = []
    
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            # ดึง source code ของแต่ละ function
            start_line = node.lineno - 1
            end_line = node.end_lineno
            func_source = "\n".join(source_lines[start_line:end_line])
            
            chunks.append({
                "name": node.name,
                "code": func_source,
                "file": filepath,
                "line_start": node.lineno,
                "line_end": node.end_lineno,
                "docstring": ast.get_docstring(node) or "",
            })
    
    return chunks
```

**ข้อดี:** เข้าใจโครงสร้าง, แต่ละ chunk สมบูรณ์ในตัวเอง  
**ข้อเสีย:** ซับซ้อนกว่า, ขนาด chunk ไม่สม่ำเสมอ

#### 3. Class-Level Chunking
```python
# ─── Extract classes as chunks ───────────────────────────────────────────────
# วัตถุประสงค์: แยก chunk ตาม class สำหรับโค้ดเชิง OOP
# ดีสำหรับ codebase ที่มีการจัดกลุ่มโค้ดด้วย class

def extract_classes(filepath: str) -> list[dict]:
    with open(filepath, "r", encoding="utf-8") as f:
        source = f.read()
    
    tree = ast.parse(source)
    source_lines = source.splitlines()
    chunks = []
    
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            start_line = node.lineno - 1
            end_line = node.end_lineno
            class_source = "\n".join(source_lines[start_line:end_line])
            
            # ดึง methods ภายใน class
            methods = [n.name for n in ast.walk(node) if isinstance(n, ast.FunctionDef)]
            
            chunks.append({
                "name": node.name,
                "type": "class",
                "code": class_source,
                "file": filepath,
                "methods": methods,
                "line_start": node.lineno,
            })
    
    return chunks
```

### เปรียบเทียบ Chunking Methods

| Method | Chunk Size | Semantic Awareness | Best For |
|--------|-----------|-------------------|----------|
| Fixed-size | คงที่ | ต่ำ | Documents ทั่วไป |
| By Function | แปรผัน | สูง | Python codebase |
| By Class | ใหญ่ | สูงมาก | OOP projects |
| Hybrid | แปรผัน | กลาง | Mixed codebases |

### Hybrid Strategy: Function + Size Fallback
```python
# ─── Hybrid chunking strategy ────────────────────────────────────────────────
# วัตถุประสงค์: ใช้ function chunking ก่อน แต่ถ้า function ใหญ่เกินไป
# ให้แบ่งย่อยอีกรอบด้วย fixed-size เพื่อให้ embed ได้ดี

MAX_CHUNK_SIZE = 2000  # characters

def hybrid_chunks(filepath: str) -> list[dict]:
    func_chunks = extract_functions(filepath)
    final_chunks = []
    
    for chunk in func_chunks:
        if len(chunk["code"]) <= MAX_CHUNK_SIZE:
            final_chunks.append(chunk)
        else:
            # ฟังก์ชันใหญ่เกินไป — แบ่งย่อยอีก
            sub_chunks = fixed_size_chunks(chunk["code"], chunk_size=MAX_CHUNK_SIZE, overlap=100)
            for i, sub in enumerate(sub_chunks):
                final_chunks.append({
                    **chunk,
                    "name": f"{chunk['name']}_part{i+1}",
                    "code": sub,
                })
    
    return final_chunks
```

---

## ช่วงที่ 2 — Workshop: Parse → Chunk → Embed → FAISS (70 นาที)

### Setup Dependencies

```powershell
# ─── Install required packages ───────────────────────────────────────────────
# วัตถุประสงค์: เพิ่ม packages ที่จำเป็นสำหรับ session นี้
# faiss-cpu = vector similarity search library
# langchain-community = FAISS wrapper + document loaders

uv add langchain-ollama langchain-community faiss-cpu langchain-core
```

### Step 1: Parse Python Files

```python
# ─── File discovery and parsing ──────────────────────────────────────────────
# วัตถุประสงค์: หา Python files ทั้งหมดใน directory แล้ว parse แต่ละไฟล์
# ใช้ pathlib สำหรับ cross-platform path handling

from pathlib import Path
import ast

def discover_python_files(directory: str) -> list[Path]:
    """ค้นหา .py files ทั้งหมดใน directory (recursive)"""
    root = Path(directory)
    return list(root.rglob("*.py"))

def parse_all_files(directory: str) -> list[dict]:
    """Parse ทุกไฟล์และรวม chunks"""
    all_chunks = []
    files = discover_python_files(directory)
    
    print(f"Found {len(files)} Python files")
    
    for filepath in files:
        try:
            chunks = extract_functions(str(filepath))
            all_chunks.extend(chunks)
            print(f"  {filepath.name}: {len(chunks)} functions")
        except SyntaxError as e:
            print(f"  WARNING: Skipping {filepath.name} — syntax error: {e}")
    
    return all_chunks
```

### Step 2: สร้าง LangChain Documents

```python
# ─── Convert chunks to LangChain Documents ──────────────────────────────────
# วัตถุประสงค์: แปลง dict chunks เป็น Document objects ที่ LangChain เข้าใจ
# metadata จะถูก save ไว้ใน FAISS เพื่อใช้ filter ภายหลัง

from langchain_core.documents import Document

def chunks_to_documents(chunks: list[dict]) -> list[Document]:
    """แปลง chunk dicts เป็น Document objects"""
    documents = []
    
    for chunk in chunks:
        # page_content คือสิ่งที่จะถูก embed
        # metadata คือข้อมูลเพิ่มเติมที่ไม่ถูก embed แต่ใช้ filter ได้
        doc = Document(
            page_content=chunk["code"],
            metadata={
                "source": chunk["file"],
                "function_name": chunk["name"],
                "line_start": chunk["line_start"],
                "line_end": chunk.get("line_end", -1),
                "docstring": chunk.get("docstring", ""),
                "file_name": Path(chunk["file"]).name,
            }
        )
        documents.append(doc)
    
    return documents

# ตัวอย่างการใช้งาน
chunks = parse_all_files("./my_project")
docs = chunks_to_documents(chunks)
print(f"Total documents: {len(docs)}")
print(f"Sample document:\n{docs[0].page_content[:200]}")
print(f"Metadata: {docs[0].metadata}")
```

### Step 3: สร้าง FAISS Index

```python
# ─── Build FAISS vector index ────────────────────────────────────────────────
# วัตถุประสงค์: สร้าง embeddings สำหรับทุก document แล้วเก็บลงใน FAISS index
# nomic-embed-text สร้าง 768-dimensional vectors สำหรับแต่ละ document

from langchain_community.vectorstores import FAISS
from langchain_ollama import OllamaEmbeddings

def build_faiss_index(documents: list[Document], save_path: str = "vector_db") -> FAISS:
    """สร้าง FAISS index จาก documents และ save ลงดิสก์"""
    print("Loading embedding model...")
    embeddings = OllamaEmbeddings(model="nomic-embed-text")
    
    print(f"Embedding {len(documents)} documents...")
    print("(This may take a few minutes depending on your hardware)")
    
    # from_documents จะ embed ทุก document และสร้าง index
    vectorstore = FAISS.from_documents(documents, embeddings)
    
    # Save index ลงดิสก์เพื่อใช้ซ้ำได้
    vectorstore.save_local(save_path)
    print(f"Saved FAISS index to '{save_path}/'")
    
    return vectorstore

# สร้าง index
vectorstore = build_faiss_index(docs, save_path="vector_db")
```

### Step 4: Load และ Search

```python
# ─── Load FAISS index and search ────────────────────────────────────────────
# วัตถุประสงค์: โหลด index ที่บันทึกไว้กลับมาใช้งาน
# allow_dangerous_deserialization=True จำเป็นสำหรับ LangChain FAISS
# (เป็น security warning — ใช้ได้ถ้า index สร้างเองและ trust ไฟล์นั้น)

def load_faiss_index(save_path: str = "vector_db") -> FAISS:
    """โหลด FAISS index จากดิสก์"""
    embeddings = OllamaEmbeddings(model="nomic-embed-text")
    vectorstore = FAISS.load_local(
        save_path, 
        embeddings, 
        allow_dangerous_deserialization=True
    )
    print(f"Loaded FAISS index from '{save_path}/'")
    return vectorstore

# ─── Semantic search ─────────────────────────────────────────────────────────
# วัตถุประสงค์: ค้นหา code ที่เกี่ยวข้องกับ query ด้วย natural language
# FAISS จะคำนวณ cosine similarity ระหว่าง query vector และ document vectors

def search_code(vectorstore: FAISS, query: str, k: int = 5) -> list[Document]:
    """ค้นหา k documents ที่ใกล้เคียงกับ query มากที่สุด"""
    results = vectorstore.similarity_search(query, k=k)
    return results

# ตัวอย่าง
vs = load_faiss_index()
results = search_code(vs, "function that reads CSV files", k=3)

for i, doc in enumerate(results, 1):
    print(f"\n--- Result {i} ---")
    print(f"Function: {doc.metadata['function_name']}")
    print(f"File: {doc.metadata['file_name']}")
    print(f"Code preview:\n{doc.page_content[:200]}...")
```

### Search with Similarity Scores

```python
# ─── Search with similarity scores ──────────────────────────────────────────
# วัตถุประสงค์: ดู score ของแต่ละผลลัพธ์เพื่อประเมินคุณภาพ
# score ต่ำกว่า = ใกล้เคียงกว่า (distance metric ไม่ใช่ similarity)

def search_with_scores(vectorstore: FAISS, query: str, k: int = 5):
    """ค้นหาพร้อม similarity scores"""
    results = vectorstore.similarity_search_with_score(query, k=k)
    
    print(f"Query: '{query}'")
    print(f"Top {k} results:\n")
    
    for doc, score in results:
        print(f"Score: {score:.4f} | {doc.metadata['function_name']} in {doc.metadata['file_name']}")
        print(f"  {doc.page_content[:100].strip()}...")
        print()
    
    return results
```

---

## ช่วงที่ 3 — Workshop: Search + Metadata Filtering (60 นาที)

### Metadata Filtering

FAISS ใน LangChain รองรับ metadata filtering ผ่าน `filter` parameter:

```python
# ─── Metadata filtering ──────────────────────────────────────────────────────
# วัตถุประสงค์: กรองผลลัพธ์ตาม metadata fields
# ช่วยให้ค้นหาเฉพาะไฟล์หรือ module ที่ต้องการ

def search_in_file(vectorstore: FAISS, query: str, filename: str, k: int = 5):
    """ค้นหาเฉพาะในไฟล์ที่กำหนด"""
    results = vectorstore.similarity_search(
        query, 
        k=k,
        filter={"file_name": filename}
    )
    return results

def search_by_function_prefix(vectorstore: FAISS, query: str, prefix: str, k: int = 5):
    """ค้นหา functions ที่ชื่อขึ้นต้นด้วย prefix ที่กำหนด"""
    # FAISS filter รองรับ exact match เท่านั้น
    # สำหรับ prefix match ต้องทำเอง
    all_results = vectorstore.similarity_search(query, k=k * 3)
    filtered = [
        doc for doc in all_results 
        if doc.metadata["function_name"].startswith(prefix)
    ]
    return filtered[:k]
```

### Advanced Search Patterns

```python
# ─── Multi-query search ──────────────────────────────────────────────────────
# วัตถุประสงค์: ค้นหาด้วยหลาย queries แล้วรวมผลลัพธ์ (deduplication)
# ช่วยให้ได้ผลลัพธ์ที่ครอบคลุมมากขึ้นสำหรับ query ที่ซับซ้อน

def multi_query_search(vectorstore: FAISS, queries: list[str], k: int = 3) -> list[Document]:
    """ค้นหาด้วยหลาย queries และ deduplicate ผลลัพธ์"""
    seen_contents = set()
    unique_results = []
    
    for query in queries:
        results = vectorstore.similarity_search(query, k=k)
        for doc in results:
            # ใช้ function name + file เป็น unique key
            key = f"{doc.metadata['function_name']}::{doc.metadata['source']}"
            if key not in seen_contents:
                seen_contents.add(key)
                unique_results.append(doc)
    
    return unique_results

# ตัวอย่าง: ค้นหา authentication code
queries = [
    "user authentication login",
    "password verification check",
    "JWT token generation",
]
results = multi_query_search(vectorstore, queries)
print(f"Found {len(results)} unique functions")
```

### Building a Search Interface

```python
# ─── Interactive search CLI ──────────────────────────────────────────────────
# วัตถุประสงค์: สร้าง command-line interface สำหรับค้นหา code
# รับ query จาก user และแสดงผลลัพธ์แบบ formatted

import argparse

def main():
    parser = argparse.ArgumentParser(description="Search code with natural language")
    parser.add_argument("--query", "-q", required=True, help="Search query")
    parser.add_argument("--top-k", "-k", type=int, default=5, help="Number of results")
    parser.add_argument("--file", "-f", help="Filter by filename")
    parser.add_argument("--db", default="vector_db", help="Path to FAISS index")
    args = parser.parse_args()
    
    # โหลด index
    vectorstore = load_faiss_index(args.db)
    
    # ค้นหา
    if args.file:
        results = search_in_file(vectorstore, args.query, args.file, k=args.top_k)
    else:
        results = search_code(vectorstore, args.query, k=args.top_k)
    
    # แสดงผล
    print(f"\nResults for: '{args.query}'")
    print("=" * 60)
    
    for i, doc in enumerate(results, 1):
        meta = doc.metadata
        print(f"\n[{i}] {meta['function_name']} — {meta['file_name']}")
        print(f"    Line {meta['line_start']}–{meta['line_end']}")
        if meta.get("docstring"):
            print(f"    Docstring: {meta['docstring'][:80]}...")
        print(f"\n{doc.page_content}\n")
        print("-" * 40)

if __name__ == "__main__":
    main()
```

---

## ช่วงที่ 4 — Workshop: วัด Retrieval Quality (20 นาที)

### Retrieval Evaluation Metrics

```python
# ─── Retrieval quality metrics ───────────────────────────────────────────────
# วัตถุประสงค์: วัดว่า retrieval ของเรา "ดี" แค่ไหน
# Precision@K: ใน K ผลลัพธ์แรก มีกี่อันที่ relevant
# Recall@K: ในบรรดาสิ่งที่ relevant ทั้งหมด เราหาเจอกี่อัน

def precision_at_k(retrieved: list[str], relevant: list[str], k: int) -> float:
    """
    คำนวณ Precision@K
    retrieved: list ของ function names ที่ retrieve มาได้
    relevant: list ของ function names ที่ควรจะ retrieve
    """
    top_k = retrieved[:k]
    relevant_set = set(relevant)
    hits = sum(1 for item in top_k if item in relevant_set)
    return hits / k

def recall_at_k(retrieved: list[str], relevant: list[str], k: int) -> float:
    """
    คำนวณ Recall@K
    วัดว่าเราหา relevant items เจอได้กี่ % ใน K ผลลัพธ์แรก
    """
    top_k = retrieved[:k]
    relevant_set = set(relevant)
    hits = sum(1 for item in top_k if item in relevant_set)
    return hits / len(relevant_set) if relevant_set else 0.0

# ─── Evaluate retrieval on test cases ───────────────────────────────────────
# วัตถุประสงค์: ทดสอบ retrieval ด้วย test cases ที่เรารู้คำตอบล่วงหน้า
# เรียกว่า "golden set" evaluation

def evaluate_retrieval(vectorstore: FAISS, test_cases: list[dict]) -> dict:
    """
    test_cases format:
    [{"query": "...", "relevant_functions": ["func1", "func2"]}, ...]
    """
    all_precision = []
    all_recall = []
    
    for case in test_cases:
        results = vectorstore.similarity_search(case["query"], k=5)
        retrieved_names = [doc.metadata["function_name"] for doc in results]
        
        p = precision_at_k(retrieved_names, case["relevant_functions"], k=5)
        r = recall_at_k(retrieved_names, case["relevant_functions"], k=5)
        
        all_precision.append(p)
        all_recall.append(r)
        
        print(f"Query: {case['query'][:50]}")
        print(f"  Precision@5: {p:.2f}, Recall@5: {r:.2f}")
    
    return {
        "mean_precision": sum(all_precision) / len(all_precision),
        "mean_recall": sum(all_recall) / len(all_recall),
    }

# ตัวอย่าง test cases
test_cases = [
    {
        "query": "read data from CSV file",
        "relevant_functions": ["load_csv", "read_data", "parse_csv"]
    },
    {
        "query": "calculate statistics mean standard deviation",
        "relevant_functions": ["calc_stats", "compute_mean", "describe_data"]
    },
]

metrics = evaluate_retrieval(vectorstore, test_cases)
print(f"\nOverall — Precision@5: {metrics['mean_precision']:.2f}, Recall@5: {metrics['mean_recall']:.2f}")
```

---

## Full Example: Complete Pipeline

```python
# ─── Complete pipeline demo ───────────────────────────────────────────────────
# วัตถุประสงค์: ตัวอย่าง end-to-end pipeline ตั้งแต่ parse files จนถึง search
# ใช้เป็น reference สำหรับทำ lab และ assignment

import ast
from pathlib import Path
from langchain_core.documents import Document
from langchain_community.vectorstores import FAISS
from langchain_ollama import OllamaEmbeddings


def extract_functions(filepath: str) -> list[dict]:
    """Parse Python file and extract function chunks."""
    with open(filepath, "r", encoding="utf-8") as f:
        source = f.read()
    
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return []
    
    source_lines = source.splitlines()
    chunks = []
    
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            start_line = node.lineno - 1
            end_line = node.end_lineno
            func_source = "\n".join(source_lines[start_line:end_line])
            
            chunks.append({
                "name": node.name,
                "code": func_source,
                "file": filepath,
                "line_start": node.lineno,
                "line_end": node.end_lineno,
                "docstring": ast.get_docstring(node) or "",
            })
    
    return chunks


def build_index(directory: str, save_path: str = "vector_db") -> FAISS:
    """Build complete FAISS index from directory of Python files."""
    # Step 1: Parse files
    all_chunks = []
    for filepath in Path(directory).rglob("*.py"):
        chunks = extract_functions(str(filepath))
        all_chunks.extend(chunks)
    
    print(f"Total chunks: {len(all_chunks)}")
    
    # Step 2: Create documents
    docs = [
        Document(
            page_content=chunk["code"],
            metadata={
                "source": chunk["file"],
                "function_name": chunk["name"],
                "file_name": Path(chunk["file"]).name,
                "line_start": chunk["line_start"],
            }
        )
        for chunk in all_chunks
    ]
    
    # Step 3: Build and save FAISS
    embeddings = OllamaEmbeddings(model="nomic-embed-text")
    vectorstore = FAISS.from_documents(docs, embeddings)
    vectorstore.save_local(save_path)
    
    return vectorstore


def search(save_path: str, query: str, k: int = 5):
    """Load index and search."""
    embeddings = OllamaEmbeddings(model="nomic-embed-text")
    vs = FAISS.load_local(save_path, embeddings, allow_dangerous_deserialization=True)
    
    results = vs.similarity_search_with_score(query, k=k)
    
    for doc, score in results:
        print(f"[{score:.3f}] {doc.metadata['function_name']} — {doc.metadata['file_name']}")


if __name__ == "__main__":
    # Build index from current directory
    vs = build_index(".", save_path="vector_db")
    
    # Search
    search("vector_db", "function that handles file I/O")
    search("vector_db", "error handling and exceptions")
```

---

## ปัญหาที่พบบ่อยและวิธีแก้

| ปัญหา | วิธีแก้ |
|-------|---------|
| `ollama.ResponseError: model 'nomic-embed-text' not found` | รัน `ollama pull nomic-embed-text` ก่อนใช้งาน |
| `ModuleNotFoundError: No module named 'faiss'` | รัน `uv add faiss-cpu` เพื่อติดตั้ง package |
| `PermissionError` เมื่อ save FAISS index | สร้าง directory ก่อนด้วย `os.makedirs("vector_db", exist_ok=True)` |
| FAISS index ว่าง หรือผลลัพธ์ไม่ตรง | ตรวจสอบด้วย `vectorstore.index.ntotal` ว่า index มีข้อมูล |
| `allow_dangerous_deserialization` error เมื่อ load FAISS | ต้องส่ง parameter `allow_dangerous_deserialization=True` ตอน load |

### Error: `ollama.ResponseError: model 'nomic-embed-text' not found`
```powershell
# วิธีแก้: pull model ก่อน
ollama pull nomic-embed-text
```

### Error: `ModuleNotFoundError: No module named 'faiss'`
```powershell
# วิธีแก้: install package
uv add faiss-cpu
```

### Error: `PermissionError` เมื่อ save FAISS
```python
# วิธีแก้: ตรวจสอบว่า directory มีสิทธิ์เขียนได้
import os
os.makedirs("vector_db", exist_ok=True)
```

### Error: FAISS index ว่าง / ผลลัพธ์ไม่ตรง
```python
# ตรวจสอบจำนวน documents ใน index
print(f"Index size: {vectorstore.index.ntotal} vectors")
```

### Error: `allow_dangerous_deserialization`
```python
# ต้องใส่ parameter นี้เมื่อโหลด FAISS ที่ save ด้วย LangChain
FAISS.load_local(path, embeddings, allow_dangerous_deserialization=True)
```

---

## Summary

Session 07 สอนให้เราทำ **Code Indexing Pipeline** ครบ:

```
Python Files
     │
     ▼
   AST Parse (extract_functions)
     │
     ▼
   Documents (LangChain)
     │
     ▼
   Embed (nomic-embed-text via Ollama)
     │
     ▼
   FAISS Index (save to disk)
     │
     ▼
   Semantic Search (natural language → relevant code)
```

Session 08 จะต่อด้วยการนำ FAISS มาใช้ใน **RAG pipeline** เต็มรูปแบบ: Query → Retrieve → Generate answer ด้วย `qwen2.5-coder:7b`

---

## แนวคิดสำคัญที่พบในครั้งนี้

| แนวคิด | คำอธิบายสั้น |
|--------|------------|
| Chunking | การแบ่ง code/text เป็นชิ้นย่อยก่อน embed เพื่อให้ retrieval แม่นยำขึ้น |
| Semantic Chunking | การตัด chunk ตามโครงสร้างโค้ด เช่น function/class แทนการตัดตามขนาด |
| Python AST | Abstract Syntax Tree ที่ใช้ parse Python code เพื่อหา function boundaries |
| FAISS | library สำหรับ similarity search ที่เร็วและ scalable รองรับ millions of vectors |
| embed_codebase | กระบวนการ parse Python files → chunk → embed → store ใน FAISS index |
| Metadata Filtering | การกรองผลการค้นหาตาม metadata เช่น filename หรือ function name |

---

## Session ถัดไป

**Session 08 — RAG Pipeline**
จะเรียนรู้:
- สร้าง RAG pipeline ครบ: Query → Retrieve → Augment → Generate
- ใช้ FAISS จาก Session 07 ร่วมกับ qwen2.5-coder:7b
- จัดการ edge cases เช่น query ไม่มีใน DB, query กว้างเกินไป
- วัดคุณภาพ RAG ด้วย relevance และ faithfulness metrics

---

## Checklist ก่อนออกจาก Session นี้

```
□ Parse Python file ด้วย ast module และ extract functions ได้สำเร็จ
□ สร้าง FAISS index จาก code chunks และ save ลงดิสก์ได้
□ Load FAISS index กลับมาและ search ด้วย natural language ได้
□ อธิบายความแตกต่างระหว่าง fixed-size และ semantic chunking ได้
□ ทดสอบ metadata filtering เพื่อค้นหาเฉพาะไฟล์ที่ต้องการได้
```

---

## References

- [FAISS Documentation](https://faiss.ai/)
- [LangChain FAISS Integration](https://python.langchain.com/docs/integrations/vectorstores/faiss/)
- [Python AST Module](https://docs.python.org/3/library/ast.html)
- [nomic-embed-text on Ollama](https://ollama.com/library/nomic-embed-text)
- [LangChain OllamaEmbeddings](https://python.langchain.com/docs/integrations/text_embedding/ollama/)
