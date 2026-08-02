# Slide Deck 02: Similarity Search

> Session 06 | Module 3: Vector DB & Embeddings | 8 slides

---

## Slide 1 - Title

# Similarity Search in Practice
## Cosine, Distance Metrics & Efficient Search

**Session 06 — Part 2 | Local RAG for Programming**

> "Finding the most relevant code is a geometry problem."

---

## Slide 2 - Cosine Similarity — Formula และ Implementation

# Cosine Similarity ในทางปฏิบัติ

### Formula

$$\text{cosine}(A, B) = \frac{\sum_{i=1}^{n} A_i B_i}{\sqrt{\sum_{i=1}^{n} A_i^2} \cdot \sqrt{\sum_{i=1}^{n} B_i^2}}$$

หรือเขียนแบบ compact:

$$\text{cosine}(A, B) = \frac{A \cdot B}{\|A\| \cdot \|B\|}$$

### Python Implementation (NumPy Only)

```python
import numpy as np

def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """
    Cosine similarity ระหว่าง 2 vectors
    ใช้ numpy เท่านั้น ไม่ใช้ sklearn
    
    Returns:
        float: ค่า -1 ถึง 1 (1 = identical direction)
    """
    # ─── dot product ───
    dot = np.dot(a, b)          # scalar
    
    # ─── magnitudes (L2 norm) ───
    norm_a = np.linalg.norm(a)  # ||a||
    norm_b = np.linalg.norm(b)  # ||b||
    
    # ─── handle zero vectors ───
    if norm_a == 0 or norm_b == 0:
        return 0.0
    
    return float(dot / (norm_a * norm_b))


# Vectorized version (เร็วกว่า สำหรับ many comparisons)
def cosine_similarity_matrix(vectors: np.ndarray) -> np.ndarray:
    """Compute N×N similarity matrix สำหรับ N vectors"""
    # normalize each vector
    norms = np.linalg.norm(vectors, axis=1, keepdims=True)
    normalized = vectors / (norms + 1e-10)
    # matrix multiplication = all pairwise dot products
    return normalized @ normalized.T
```

### ค่าตัวอย่าง

```
identical vectors:  cos = 1.00  ← 0°
related concepts:   cos = 0.75  ← ~41°
loosely related:    cos = 0.40  ← ~66°
unrelated:          cos = 0.10  ← ~84°
```

**Key Message:** Cosine = 1 หมายถึง "ชี้ทิศเดียวกัน" ไม่ใช่ "เหมือนกันทุกอย่าง"

---

## Slide 3 - Dot Product vs Euclidean vs Cosine

# เปรียบเทียบ 3 Distance/Similarity Metrics

### 1. Dot Product

```python
dot = np.dot(a, b)
# ดี: เร็วมาก
# เสีย: ไวต่อ magnitude — doc ยาวได้คะแนนสูงกว่าเสมอ
# ใช้เมื่อ: vectors normalize แล้ว (magnitude = 1)
```

### 2. Euclidean Distance

```python
dist = np.linalg.norm(a - b)
# ดี: เข้าใจง่าย
# เสีย: ไวต่อ magnitude, ยิ่งมิติมาก ยิ่ง dense ("curse of dimensionality")
# ใช้เมื่อ: spatial data (coordinates, pixel locations)
```

### 3. Cosine Similarity

```python
cos = np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))
# ดี: magnitude-invariant, scale-free
# เสีย: ไม่รู้ absolute distance
# ใช้เมื่อ: NLP/code semantic search
```

### สรุป: ใช้อะไรเมื่อไหร่?

| Metric | ใช้เมื่อ |
|--------|---------|
| Dot product | Vectors normalized แล้ว (faster) |
| Euclidean | Spatial data, same scale |
| **Cosine** | **Text/code similarity** ← เราใช้นี้ |

**Key Message:** สำหรับ semantic search ใช้ Cosine เสมอ

---

## Slide 4 - Nearest Neighbor Search (Brute Force → Efficient)

# Nearest Neighbor Search

### Brute Force — O(N × D)

```python
def brute_force_search(
    query_vec: np.ndarray,
    doc_vecs: np.ndarray,
    top_k: int = 5
) -> list[tuple[int, float]]:
    """
    ค้นหา top_k nearest neighbors แบบ brute force
    
    Time: O(N × D)  where N = docs, D = dimensions
    Space: O(N × D)
    
    OK สำหรับ: N < 10,000
    ช้าสำหรับ: N > 100,000
    """
    # ─── คำนวณ similarity กับทุก document ───
    similarities = []
    for i, doc_vec in enumerate(doc_vecs):
        sim = cosine_similarity(query_vec, doc_vec)
        similarities.append((i, sim))
    
    # ─── sort และ return top_k ───
    similarities.sort(key=lambda x: x[1], reverse=True)
    return similarities[:top_k]


# Vectorized version (เร็วกว่ามาก)
def vectorized_search(
    query_vec: np.ndarray,
    doc_vecs: np.ndarray,
    top_k: int = 5
) -> list[tuple[int, float]]:
    """Vectorized search using matrix multiplication"""
    query_norm = query_vec / np.linalg.norm(query_vec)
    doc_norms = doc_vecs / np.linalg.norm(doc_vecs, axis=1, keepdims=True)
    
    scores = doc_norms @ query_norm  # shape: (N,)
    top_indices = np.argsort(scores)[::-1][:top_k]
    
    return [(int(i), float(scores[i])) for i in top_indices]
```

### เมื่อ N ใหญ่: ใช้ FAISS

```python
# faiss: Fast Approximate Nearest Neighbors
import faiss

index = faiss.IndexFlatIP(768)   # Inner Product (for normalized vectors)
index.add(doc_vecs.astype('float32'))

distances, indices = index.search(
    query_vec.reshape(1, -1).astype('float32'), k=5
)
```

**Key Message:** Brute force ดีพอสำหรับ < 10K docs; ใช้ FAISS สำหรับ production

---

## Slide 5 - Batch Embedding

# Batch Embedding — ประหยัดเวลา

### ทำไมต้อง Batch?

```python
# แบบ naive: embed ทีละตัว → N round trips ไปยัง Ollama
for doc in documents:
    vector = embedder.embed_query(doc)  # 1 API call each

# แบบ batch: embed ทั้งหมดพร้อมกัน → 1 round trip
vectors = embedder.embed_documents(documents)  # 1 API call total
```

### Batch Embedding Implementation

```python
from langchain_ollama import OllamaEmbeddings
import numpy as np
import time

def embed_in_batches(
    texts: list[str],
    batch_size: int = 32,
    verbose: bool = True
) -> np.ndarray:
    """
    Embed texts เป็น batches เพื่อประหยัดเวลาและ memory
    
    Args:
        texts: list ของ text strings
        batch_size: จำนวน texts ต่อ batch
        verbose: แสดง progress หรือไม่
    
    Returns:
        np.ndarray: shape (N, 768)
    """
    embedder = OllamaEmbeddings(model="nomic-embed-text")
    all_vectors = []
    
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]
        
        if verbose:
            print(f"Embedding batch {i//batch_size + 1}/"
                  f"{(len(texts)-1)//batch_size + 1} ({len(batch)} texts)")
        
        # ─── embed batch ───
        # วัตถุประสงค์: 1 API call สำหรับ batch ทั้งหมด
        batch_vectors = embedder.embed_documents(batch)
        all_vectors.extend(batch_vectors)
    
    return np.array(all_vectors)
```

### ความเร็ว Comparison

```
100 texts, embed_query() x 100:  ~45 seconds
100 texts, embed_documents() x1: ~12 seconds
```

**Key Message:** Batch embedding เร็วกว่า individual calls 3-4x

---

## Slide 6 - Caching Embeddings

# Caching — ไม่ต้อง Embed ซ้ำ

### ทำไมต้อง Cache?

```
Embedding 1000 code functions ใช้เวลา ~10 นาที
ถ้าไม่ cache → ต้อง embed ใหม่ทุกครั้งที่ restart!
```

### Simple File Cache

```python
import numpy as np
import json
import hashlib
from pathlib import Path

class EmbeddingCache:
    """Cache embeddings ลง disk เพื่อ reuse"""
    
    def __init__(self, cache_dir: str = ".embedding_cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
    
    def _get_cache_key(self, text: str) -> str:
        """Hash text เป็น cache key"""
        return hashlib.md5(text.encode()).hexdigest()
    
    def get(self, text: str) -> np.ndarray | None:
        """ดึง embedding จาก cache"""
        key = self._get_cache_key(text)
        cache_file = self.cache_dir / f"{key}.npy"
        
        if cache_file.exists():
            return np.load(str(cache_file))
        return None
    
    def set(self, text: str, vector: np.ndarray):
        """บันทึก embedding ลง cache"""
        key = self._get_cache_key(text)
        cache_file = self.cache_dir / f"{key}.npy"
        np.save(str(cache_file), vector)
    
    def embed_with_cache(self, text: str, embedder) -> np.ndarray:
        """Embed พร้อม cache — ถ้ามี cache ใช้ cache"""
        cached = self.get(text)
        if cached is not None:
            return cached
        
        vector = np.array(embedder.embed_query(text))
        self.set(text, vector)
        return vector
```

**Key Message:** Cache = ลงทุนครั้งเดียว, ใช้ได้นานโดยไม่ต้อง re-embed

---

## Slide 7 - Embedding Dimensionality Tradeoffs

# Tradeoffs ของ Embedding Dimensions

### เปรียบเทียบ Models

| Model | Dimensions | Speed | Quality | Notes |
|-------|------------|-------|---------|-------|
| all-minilm | 384 | Fast | Good | General text |
| **nomic-embed-text** | **768** | **Medium** | **Great** | **Our choice** |
| text-embedding-3-large | 3072 | Slow | Excellent | OpenAI (cloud) |

### ผลของ Dimensions

**มิติมากขึ้น:**
- Capture ความหมาย nuanced มากขึ้น
- ใช้ memory มากขึ้น (768 float32 = 3KB ต่อ vector)
- Search ช้าลง (เมื่อ N ใหญ่)

**มิติน้อยลง:**
- เร็วกว่า, ใช้ memory น้อยกว่า
- อาจ lose information

### Memory Calculation

```python
n_documents = 10_000
dimensions = 768
bytes_per_float = 4  # float32

total_mb = (n_documents * dimensions * bytes_per_float) / (1024**2)
print(f"Memory for {n_documents:,} docs: {total_mb:.1f} MB")
# Memory for 10,000 docs: 29.3 MB

# จริงๆ แล้วไม่มาก! สำหรับ local RAG
```

**Key Message:** 768 dimensions เป็น sweet spot สำหรับ local RAG project

---

## Slide 8 - Practical Examples กับ Code Snippets

# ตัวอย่างที่ใช้งานได้จริง

### Example 1: Code Search Engine

```python
from langchain_ollama import OllamaEmbeddings
import numpy as np

class CodeSearchEngine:
    """Simple semantic code search"""
    
    def __init__(self):
        self.embedder = OllamaEmbeddings(model="nomic-embed-text")
        self.snippets: list[str] = []
        self.vectors: np.ndarray | None = None
    
    def index(self, code_snippets: list[str]):
        """Index code snippets"""
        self.snippets = code_snippets
        vectors = self.embedder.embed_documents(code_snippets)
        self.vectors = np.array(vectors)
        # normalize สำหรับ dot product search
        norms = np.linalg.norm(self.vectors, axis=1, keepdims=True)
        self.vectors = self.vectors / (norms + 1e-10)
        print(f"Indexed {len(snippets)} code snippets")
    
    def search(self, query: str, top_k: int = 3) -> list[dict]:
        """ค้นหา code snippets ที่ match query"""
        query_vec = np.array(self.embedder.embed_query(query))
        query_vec = query_vec / (np.linalg.norm(query_vec) + 1e-10)
        
        scores = self.vectors @ query_vec
        top_indices = np.argsort(scores)[::-1][:top_k]
        
        return [
            {"rank": i+1, "score": float(scores[idx]), "code": self.snippets[idx]}
            for i, idx in enumerate(top_indices)
        ]

# Usage
engine = CodeSearchEngine()
engine.index(my_code_snippets)

results = engine.search("function to calculate average")
for r in results:
    print(f"#{r['rank']} (score: {r['score']:.3f})")
    print(r['code'][:100])
```

### Example 2: Similarity Threshold Filter

```python
def filter_by_similarity(
    query: str,
    documents: list[str],
    threshold: float = 0.5
) -> list[str]:
    """Return เฉพาะ documents ที่ similarity > threshold"""
    results = semantic_search(query, documents, top_k=len(documents))
    return [r["document"] for r in results if r["score"] >= threshold]
```

**Key Message:** Building blocks เหล่านี้รวมกัน = Local RAG Engine (Session 08)

---

*Slide Deck 02 | Session 06 | Local RAG for Programming*
