# Session 06 — Embeddings and Semantic Search

> **Module 3: Vector DB & Embeddings** | ครั้งที่ 6 จาก 14 | 3 ชั่วโมง

---

## เป้าหมายของ Session นี้

เมื่อจบ session นี้ นักเรียนจะสามารถ:

1. **อธิบาย vector space และ cosine similarity ได้** — แนวคิด embedding, มิติ, การวัดความคล้ายคลึง
2. **สร้าง embedding จาก text และ code ด้วย nomic-embed-text ได้** — ใช้ langchain-ollama
3. **วัด semantic similarity และ visualize ได้** — similarity matrix, heatmap, t-SNE

---

## ตารางเวลา (Session Schedule) — รวม 180 นาที

| ช่วง | เวลา | หัวข้อ | รูปแบบ |
|------|------|--------|--------|
| 1 | 40 นาที | Theory — Vector space, cosine similarity, embedding concept | Lecture + Discussion |
| 2 | 60 นาที | Workshop — สร้าง embedding, วัด similarity, visualize | Hands-on |
| 3 | 60 นาที | Workshop — Embed code, เปรียบเทียบ text vs code embedding | Hands-on |
| 4 | 20 นาที | สรุป + ข้อจำกัดของ embedding | Discussion |

---

## Prerequisites

- ผ่าน Session 05 แล้ว
- ติดตั้ง `nomic-embed-text` ใน Ollama

```powershell
# ดาวน์โหลด nomic-embed-text
ollama pull nomic-embed-text

# ตรวจสอบ
ollama list

# ติดตั้ง dependencies
uv add langchain-ollama langchain-core numpy matplotlib
```

---

## ช่วงที่ 1 (40 นาที) — Theory: Vector Space & Embeddings

### 1.1 ปัญหาหลัก: คอมพิวเตอร์ไม่เข้าใจ "ความหมาย"

```
คอมพิวเตอร์ทำได้:
  "cat" == "cat"  → True
  "cat" == "dog"  → False

คอมพิวเตอร์ทำไม่ได้:
  similar("cat", "dog")  → ???  (ทั้งคู่เป็นสัตว์เลี้ยง แต่ string ต่างกัน)
```

Keyword search ค้นหาตาม **ตัวอักษร** ไม่ใช่ **ความหมาย**:

```python
# Keyword search
documents = ["Python is a programming language", "I love coding in Python"]
query = "software development"
# ไม่ match! ทั้งที่ความหมายเกี่ยวข้อง
```

### 1.2 Vector Space: แปลงทุกอย่างเป็นตัวเลข

Embedding แปลง text → vector (array ของตัวเลข):

```python
# แนวคิด (simplified)
embed("king")   → [0.2, 0.8, 0.1, ...]  # vector 768 มิติ
embed("queen")  → [0.2, 0.9, 0.3, ...]  # ใกล้เคียงกัน!
embed("apple")  → [0.7, 0.1, 0.9, ...]  # ห่างกันมาก
```

Vectors ที่มีความหมายคล้ายกัน → **อยู่ใกล้กันใน vector space**

### 1.3 Cosine Similarity — วัดมุม ไม่วัดระยะทาง

```python
import numpy as np

def cosine_similarity(vec1: np.ndarray, vec2: np.ndarray) -> float:
    """
    คำนวณ cosine similarity ระหว่าง 2 vectors
    
    สูตร: cos(θ) = dot(a, b) / (||a|| * ||b||)
    
    ค่าที่ได้:
    - 1.0  = เหมือนกันทั้งหมด (มุม 0°)
    - 0.0  = ไม่เกี่ยวข้องกันเลย (มุม 90°)
    - -1.0 = ตรงข้ามกัน (มุม 180°)
    """
    # ─── คำนวณ dot product ───
    # วัตถุประสงค์: วัดความสอดคล้องกันของ direction
    dot_product = np.dot(vec1, vec2)
    
    # ─── คำนวณ magnitude ───
    # วัตถุประสงค์: normalize เพื่อให้ scale ไม่มีผล
    magnitude1 = np.linalg.norm(vec1)
    magnitude2 = np.linalg.norm(vec2)
    
    if magnitude1 == 0 or magnitude2 == 0:
        return 0.0
    
    return dot_product / (magnitude1 * magnitude2)
```

### 1.4 ทำไม Cosine ดีกว่า Euclidean Distance?

```
Euclidean distance: วัดระยะห่างในพื้นที่
- "I love Python" (doc สั้น) → vector เล็ก
- "I really love Python programming" (doc ยาว) → vector ใหญ่
→ ดูห่างกัน ทั้งที่ความหมายเกือบเหมือนกัน

Cosine similarity: วัดมุมระหว่าง vectors
- ไม่สนใจขนาดของ vector
- สนใจแค่ "ทิศทาง" = ความหมาย
→ ผลลัพธ์ที่ดีกว่าสำหรับ semantic search
```

### 1.5 nomic-embed-text — 768 Dimensions

```python
# ─── สร้าง embedding ด้วย nomic-embed-text ───
# วัตถุประสงค์: แปลง text เป็น vector 768 มิติ

from langchain_ollama import OllamaEmbeddings

embeddings = OllamaEmbeddings(model="nomic-embed-text")

# embed single text
vector = embeddings.embed_query("Hello, world!")
print(f"Dimensions: {len(vector)}")  # 768

# embed multiple texts
vectors = embeddings.embed_documents([
    "Python is a programming language",
    "JavaScript runs in the browser",
    "I enjoy hiking in mountains"
])
print(f"Number of vectors: {len(vectors)}")  # 3
print(f"Each vector has: {len(vectors[0])} dimensions")  # 768
```

---

## ช่วงที่ 2 (60 นาที) — Workshop: Embeddings & Similarity

### 2.1 สร้าง Embedding และ Visualize

```python
# ─── Embedding Visualization ───
# วัตถุประสงค์: เห็นว่า texts ที่คล้ายกันอยู่ใกล้กัน

import numpy as np
import matplotlib.pyplot as plt
from langchain_ollama import OllamaEmbeddings

def compute_similarity_matrix(texts: list[str]) -> np.ndarray:
    """
    สร้าง similarity matrix สำหรับ list ของ texts
    
    Args:
        texts: list ของ text strings
    
    Returns:
        np.ndarray: NxN matrix ที่ [i][j] = cosine_similarity(texts[i], texts[j])
    """
    # ─── สร้าง embeddings ───
    # วัตถุประสงค์: embed ทุก text พร้อมกัน
    embedder = OllamaEmbeddings(model="nomic-embed-text")
    vectors = np.array(embedder.embed_documents(texts))
    
    n = len(texts)
    matrix = np.zeros((n, n))
    
    # ─── คำนวณ similarity ทุกคู่ ───
    # วัตถุประสงค์: สร้าง symmetric matrix
    for i in range(n):
        for j in range(n):
            dot = np.dot(vectors[i], vectors[j])
            norm_i = np.linalg.norm(vectors[i])
            norm_j = np.linalg.norm(vectors[j])
            matrix[i][j] = dot / (norm_i * norm_j) if norm_i * norm_j > 0 else 0
    
    return matrix


def plot_similarity_heatmap(matrix: np.ndarray, labels: list[str], title: str = "Similarity Matrix"):
    """
    วาด heatmap ของ similarity matrix
    
    Args:
        matrix: NxN similarity matrix
        labels: list ของ label สำหรับแกน x และ y
        title: ชื่อกราฟ
    """
    # ─── สร้าง heatmap ───
    # วัตถุประสงค์: visualize ว่า texts ไหน similar กัน
    fig, ax = plt.subplots(figsize=(10, 8))
    
    im = ax.imshow(matrix, cmap='RdYlGn', vmin=0, vmax=1)
    plt.colorbar(im, ax=ax)
    
    ax.set_xticks(range(len(labels)))
    ax.set_yticks(range(len(labels)))
    ax.set_xticklabels(labels, rotation=45, ha='right')
    ax.set_yticklabels(labels)
    
    # ─── เพิ่ม ค่าใน cell ───
    # วัตถุประสงค์: แสดงค่าตัวเลขในแต่ละ cell
    for i in range(len(labels)):
        for j in range(len(labels)):
            ax.text(j, i, f'{matrix[i][j]:.2f}',
                   ha='center', va='center', fontsize=8)
    
    ax.set_title(title)
    plt.tight_layout()
    plt.savefig('similarity_heatmap.png', dpi=150, bbox_inches='tight')
    plt.show()
    print("Saved: similarity_heatmap.png")
```

### 2.2 ตัวอย่าง: Text Similarity Groups

```python
# ─── Demo: Similarity ระหว่าง text groups ต่างๆ ───
# วัตถุประสงค์: เห็น clustering ของ texts ที่มีความหมายคล้ายกัน

texts = [
    # Programming group
    "Python is a programming language",
    "def fibonacci(n): return n",
    "JavaScript runs in browsers",
    
    # Nature group
    "The cat sat on the mat",
    "Dogs are loyal animals",
    "Birds can fly in the sky",
    
    # Math group
    "2 + 2 = 4",
    "The square root of 16 is 4",
    "Linear algebra uses matrices",
]

labels = [
    "Python", "Python code", "JavaScript",
    "Cat", "Dog", "Birds",
    "Arithmetic", "Square root", "Linear algebra"
]

matrix = compute_similarity_matrix(texts)
plot_similarity_heatmap(matrix, labels, "Text Semantic Similarity")
```

---

## ช่วงที่ 3 (60 นาที) — Workshop: Code Embeddings

### 3.1 Code ที่ทำสิ่งเดียวกัน → Vector ใกล้กัน

สมมติฐาน: code snippets ที่ implement logic เดียวกัน (แม้ต่าง style) ควรมี embedding ใกล้กัน

```python
# ─── Code Embedding Experiment ───
# วัตถุประสงค์: ทดสอบว่า code ที่ทำสิ่งเดียวกัน cluster เข้าหากันไหม

# 3 คู่ที่ทำสิ่งเดียวกัน (แต่ต่าง style/language)

# คู่ 1: Sum of list
sum_loop = """
def sum_list(lst):
    total = 0
    for x in lst:
        total += x
    return total
"""

sum_builtin = """
def sum_list(numbers):
    return sum(numbers)
"""

# คู่ 2: Check even number
is_even_if = """
def is_even(n):
    if n % 2 == 0:
        return True
    else:
        return False
"""

is_even_oneliner = """
def is_even(n):
    return n % 2 == 0
"""

# คู่ 3: Filter positive numbers
filter_loop = """
def get_positives(numbers):
    result = []
    for n in numbers:
        if n > 0:
            result.append(n)
    return result
"""

filter_comprehension = """
def get_positives(numbers):
    return [n for n in numbers if n > 0]
"""

# Unrelated code
read_file = """
def read_config(path):
    with open(path) as f:
        return f.read()
"""

code_snippets = [
    sum_loop, sum_builtin,
    is_even_if, is_even_oneliner,
    filter_loop, filter_comprehension,
    read_file
]

code_labels = [
    "sum-loop", "sum-builtin",
    "is_even-if", "is_even-oneliner",
    "filter-loop", "filter-comprehension",
    "read-file (unrelated)"
]
```

### 3.2 Visualize Code Clusters

```python
# ─── t-SNE Visualization สำหรับ Code Embeddings ───
# วัตถุประสงค์: plot code ใน 2D space เพื่อดู clustering

from sklearn.manifold import TSNE
import matplotlib.pyplot as plt
import numpy as np

def plot_code_clusters(code_snippets: list[str], labels: list[str]):
    """
    Visualize code snippets ใน 2D space ด้วย t-SNE
    
    Args:
        code_snippets: list ของ code strings
        labels: list ของ label สำหรับแต่ละ snippet
    """
    # ─── สร้าง embeddings ───
    embedder = OllamaEmbeddings(model="nomic-embed-text")
    vectors = np.array(embedder.embed_documents(code_snippets))
    
    # ─── ลด dimension เป็น 2D ด้วย t-SNE ───
    # วัตถุประสงค์: visualize 768D vectors ใน 2D
    tsne = TSNE(n_components=2, perplexity=min(5, len(code_snippets) - 1), random_state=42)
    vectors_2d = tsne.fit_transform(vectors)
    
    # ─── Plot ───
    fig, ax = plt.subplots(figsize=(10, 8))
    
    colors = plt.cm.tab10(np.linspace(0, 1, len(labels)))
    
    for i, (label, color) in enumerate(zip(labels, colors)):
        ax.scatter(vectors_2d[i, 0], vectors_2d[i, 1],
                  color=color, s=200, zorder=5)
        ax.annotate(label,
                   (vectors_2d[i, 0], vectors_2d[i, 1]),
                   textcoords="offset points",
                   xytext=(10, 5),
                   fontsize=9)
    
    ax.set_title("Code Embeddings in 2D (t-SNE)")
    ax.set_xlabel("Component 1")
    ax.set_ylabel("Component 2")
    plt.tight_layout()
    plt.savefig('code_clusters.png', dpi=150, bbox_inches='tight')
    plt.show()
    print("Saved: code_clusters.png")
```

### 3.3 Semantic Search

```python
# ─── Simple Semantic Search ───
# วัตถุประสงค์: ค้นหา documents ที่ใกล้เคียงกับ query มากที่สุด

def semantic_search(
    query: str,
    documents: list[str],
    top_k: int = 3
) -> list[dict]:
    """
    ค้นหา documents ที่ semantic ใกล้เคียงกับ query มากที่สุด
    
    Args:
        query: คำถามหรือ query text
        documents: list ของ documents ที่ค้นหาจาก
        top_k: จำนวน results ที่ return
    
    Returns:
        list ของ {"index": int, "document": str, "score": float}
        เรียงจาก score สูงสุดไปต่ำสุด
    
    Example:
        >>> results = semantic_search(
        ...     "how to sort a list",
        ...     ["bubble sort implementation", "recipe for pasta", "quick sort"]
        ... )
        >>> print(results[0]["document"])
        quick sort
    """
    # ─── สร้าง embeddings ───
    # วัตถุประสงค์: embed query และ documents ทั้งหมด
    embedder = OllamaEmbeddings(model="nomic-embed-text")
    
    query_vector = np.array(embedder.embed_query(query))
    doc_vectors = np.array(embedder.embed_documents(documents))
    
    # ─── คำนวณ similarity ─── 
    # วัตถุประสงค์: หา documents ที่ใกล้เคียง query มากที่สุด
    scores = []
    for i, doc_vec in enumerate(doc_vectors):
        dot = np.dot(query_vector, doc_vec)
        norm_q = np.linalg.norm(query_vector)
        norm_d = np.linalg.norm(doc_vec)
        score = dot / (norm_q * norm_d) if norm_q * norm_d > 0 else 0.0
        scores.append({"index": i, "document": documents[i], "score": score})
    
    # ─── Sort และ return top_k ───
    # วัตถุประสงค์: return results เรียงตาม score
    scores.sort(key=lambda x: x["score"], reverse=True)
    return scores[:top_k]


# ─── Demo ───
documents = [
    "Bubble sort: compare adjacent elements and swap if needed",
    "Recipe: boil pasta for 10 minutes with salt",
    "Quick sort: pick pivot, partition, recurse on sub-arrays",
    "Merge sort: divide array in half, sort, then merge",
    "Database indexing improves query performance",
    "Python list comprehensions are more Pythonic than loops"
]

query = "how to sort an array efficiently"
results = semantic_search(query, documents, top_k=3)

print(f"Query: '{query}'\n")
for i, r in enumerate(results, 1):
    print(f"#{i} (score: {r['score']:.3f}): {r['document']}")
```

---

## ช่วงที่ 4 (20 นาที) — สรุป + ข้อจำกัด

### สิ่งที่เรียนรู้ใน Session นี้

1. **Vector Space**: text/code → vector ที่ captures semantic meaning
2. **Cosine Similarity**: วัดมุมระหว่าง vectors = semantic similarity
3. **nomic-embed-text**: 768-dimensional embeddings ที่ดีสำหรับ code
4. **Semantic Search**: หา documents ที่ "หมายถึง" สิ่งเดียวกัน แม้ใช้คำต่างกัน

## ปัญหาที่พบบ่อยและวิธีแก้

| ปัญหา | วิธีแก้ |
|-------|---------|
| Semantic Drift — คำเดียวกันมีหลายความหมาย (เช่น "bank") ทำให้ embedding blend หลาย context | เพิ่ม context ใน query เช่น "river bank" หรือ "financial bank" เพื่อให้ชัดเจน |
| Language Bias — nomic-embed-text trained ส่วนใหญ่บน English ทำให้ Thai text embedding แม่นน้อยกว่า | ใช้ English สำหรับ code comments หรือเลือก model ที่รองรับ multilingual |
| Out-of-Vocabulary Code — library ใหม่หรือ API เฉพาะที่ model ไม่เคยเห็น ทำให้ embedding ไม่แม่น | เพิ่ม description หรือ docstring อธิบาย library นั้นเพื่อช่วย embedding |
| Context Window จำกัด — nomic-embed-text รับได้สูงสุด ~2048 tokens ทำให้ code ยาวต้อง chunk ก่อน | ใช้ chunking strategy จาก Session 07 เพื่อแบ่ง code ก่อน embed |
| Static Embeddings — embedding ไม่เปลี่ยนตาม context ทำให้ความหมายคลุมเครือ | ใส่ context เพิ่มเติมใน text ที่จะ embed เพื่อช่วย disambiguate |

### ข้อจำกัดของ Embeddings (รายละเอียด)

#### 1. Semantic Drift

```python
# คำเดียวกัน ความหมายต่างกัน (Polysemy)
embed("bank")  
# = river bank หรือ financial bank?
# Embedding จะ blend ทั้งสองความหมาย
# อาจ match ผิด context
```

#### 2. Language Bias

```python
# nomic-embed-text trained ส่วนใหญ่บน English
texts_en = ["Hello world", "Good morning"]
texts_th = ["สวัสดีโลก", "อรุณสวัสดิ์"]

# English embeddings มักจะ accurate กว่า Thai embeddings
# ถ้าใช้ Thai code comments → accuracy อาจลดลง
```

#### 3. Out-of-Vocabulary Code

```python
# Library ใหม่หรือ API เฉพาะ อาจ embed ไม่ดี
embed("import my_custom_library_v2")
# model ไม่เคยเห็น library นี้ → embedding ไม่แม่น
```

#### 4. Context Window ของ Embedding

```python
# nomic-embed-text รับ input ได้สูงสุด ~2048 tokens
# ถ้า code ยาวกว่านี้ → ต้อง chunk ก่อน embed
# (จะเรียนใน Session 07: ChromaDB & Chunking)
```

#### 5. Static Embeddings

```python
# Embedding ไม่เปลี่ยนตาม context ใน document
# "I deposited money at the bank" vs "I sat by the river bank"
# อาจได้ embedding ที่ใกล้กันถ้า model ไม่ดีพอ
```

---

## Deliverables ของ Session นี้

| ไฟล์ | คำอธิบาย |
|------|----------|
| `lab/lab_06_embeddings.py` | Starter สำหรับ hands-on lab |
| `lab/lab_06_embeddings_solution.py` | Solution ครบ พร้อม visualization |
| `assignment/hw_06_embeddings.md` | โจทย์การบ้าน |
| `assignment/hw_06_rubric.md` | Rubric การให้คะแนน |

---

## การรันโปรแกรม (Windows)

```powershell
# ติดตั้ง dependencies
uv add langchain-ollama numpy matplotlib scikit-learn

# pull embedding model
ollama pull nomic-embed-text

# รัน lab
uv run python lab\lab_06_embeddings.py

# รัน solution
uv run python lab\lab_06_embeddings_solution.py
```

---

## Connection กับ Sessions อื่น

```
Session 06 (Embeddings)
        ↓
Session 07 (ChromaDB & Chunking) — เก็บ embeddings ใน vector DB
        ↓
Session 08 (RAG Pipeline) — ใช้ embeddings ค้นหา context
        ↓
Session 09 (Hybrid Search) — ผสม embedding + keyword search
```

Embedding คือหัวใจของ RAG pipeline ทั้งหมด

---

## แนวคิดสำคัญที่พบในครั้งนี้

| แนวคิด | คำอธิบายสั้น |
|--------|------------|
| Embedding | การแปลง text/code เป็น vector ตัวเลขหลายมิติที่ captures ความหมาย |
| Vector Space | พื้นที่ n-มิติที่ texts ที่มีความหมายคล้ายกันอยู่ใกล้กัน |
| Cosine Similarity | การวัดมุมระหว่าง 2 vectors เพื่อประเมินความคล้ายคลึงทางความหมาย |
| nomic-embed-text | embedding model 768 มิติที่รันผ่าน Ollama เหมาะสำหรับ code |
| Semantic Search | การค้นหาโดยเปรียบเทียบ "ความหมาย" แทนการ match ตัวอักษร |
| t-SNE | เทคนิค dimensionality reduction ใช้ visualize vectors หลายมิติใน 2D |

---

## Session ถัดไป

**Session 07 — FAISS + Code Chunking**
จะเรียนรู้:
- Chunking strategies: ตัดตาม function/class ด้วย Python AST
- สร้าง FAISS index จาก embeddings และ save/load ได้
- ค้นหา code ด้วย natural language query
- Filter ผลลัพธ์ด้วย metadata (filename, function_name)

---

## Checklist ก่อนออกจาก Session นี้

```
□ รัน nomic-embed-text ด้วย Ollama และ embed text ได้สำเร็จ
□ คำนวณ cosine similarity ระหว่าง 2 vectors ได้ถูกต้อง
□ สร้าง similarity heatmap จาก texts หลาย groups ได้
□ ทดสอบ semantic search และอธิบายได้ว่า score หมายถึงอะไร
□ อธิบายข้อจำกัดของ embedding ได้อย่างน้อย 3 ข้อ
```

---

## ทรัพยากรเพิ่มเติม

- [nomic-embed-text on Ollama](https://ollama.ai/library/nomic-embed-text)
- [Word2Vec Original Paper](https://arxiv.org/abs/1301.3781)
- [Sentence Transformers](https://sbert.net/)
- [Understanding Cosine Similarity](https://en.wikipedia.org/wiki/Cosine_similarity)

---

## หมายเหตุสำหรับผู้สอน

- **ช่วง 1**: ใช้ whiteboard วาด 2D vector space ให้เห็นภาพ → แล้วค่อยเปิด code
- **ช่วง 2**: ให้นักเรียนเลือก texts เองและสร้าง heatmap → เปรียบเทียบกัน
- **ช่วง 3**: เน้น "code ที่ทำสิ่งเดียวกัน cluster เข้าหากัน" → นี่คือพื้นฐาน code search
- **ช่วง 4**: เปิด discussion เรื่อง limitation → นักเรียนจะเจอปัญหาจริงใน assignments

---

*Session 06 | Local RAG for Programming | Embedding: nomic-embed-text*
