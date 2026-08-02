# Slide Deck 01: Embedding Concepts

> Session 06 | Module 3: Vector DB & Embeddings | 10 slides

---

## Slide 1 - Title

# Embeddings and Semantic Search
## Session 06 — Local RAG for Programming

**Embedding Model:** `nomic-embed-text` via Ollama  
**Stack:** numpy, matplotlib, langchain-ollama  

> "Embeddings are the bridge between human language and machine understanding."

---

## Slide 2 - ปัญหา — คอมพิวเตอร์ไม่เข้าใจ "ความหมาย"

# คอมพิวเตอร์ทำงานกับ "ตัวอักษร" ไม่ใช่ "ความหมาย"

### Keyword Search — มีข้อจำกัด

```python
documents = [
    "Python is a programming language",     # doc 1
    "I enjoy coding in Python",              # doc 2  
    "Software development requires logic",   # doc 3
]

query = "software engineering"

# Keyword search: ค้นหา exact match
# → doc 3 match "software"
# → doc 1, 2 ไม่ match ทั้งที่ content เกี่ยวข้อง!
```

### ปัญหาหลัก

| ปัญหา | ตัวอย่าง |
|-------|---------|
| Synonyms | "car" vs "automobile" ≠ match |
| Paraphrase | "fix bug" vs "resolve issue" ≠ match |
| Context | "bank" (river?) vs "bank" (financial?) |
| Language | Thai query + English doc = no match |

### เราต้องการ: Semantic Search

**"ค้นหาสิ่งที่ หมายถึง สิ่งเดียวกัน"**

**Key Message:** Keyword search ค้นหา "คำ" แต่เราต้องการค้นหา "ความหมาย"

---

## Slide 3 - Vector Space — ทุกอย่างเป็นตัวเลข

# Vector Space: ภาษา → ตัวเลข

### แนวคิด: แทน text ด้วย vector

```
"king"    → [0.2,  0.8,  0.1,  0.5, ...]  ← 768 ตัวเลข
"queen"   → [0.2,  0.9,  0.3,  0.4, ...]  ← ใกล้เคียง "king"!
"apple"   → [0.7,  0.1,  0.9,  0.2, ...]  ← ห่างมาก
"orange"  → [0.6,  0.2,  0.8,  0.3, ...]  ← ใกล้ "apple"
```

[FIGURE: 2D vector space scatter plot — words grouped by meaning: cooking/food/apple/orange cluster, king/queen cluster, Python/JavaScript/code cluster]

```
        cooking ●
                    ● food
    orange ●  ● apple
    
                            ● king
                                    ● queen
    
    ● Python     ● JavaScript
         ● code
```

### Vector Arithmetic — ความมหัศจรรย์

```
king - man + woman ≈ queen
Paris - France + Italy ≈ Rome
```

Text ที่มีความสัมพันธ์คล้ายกัน → vector arithmetic ให้ผลที่มีความหมาย

**Key Message:** Vector space = map ของ "ความหมาย" ในพื้นที่ตัวเลข

---

## Slide 4 - Cosine Similarity — วัดมุม ไม่วัดระยะทาง

# Cosine Similarity

[FIGURE: cosine similarity diagram — two vectors A and B in 2D space, angle θ between them, formula: cos(θ) = A·B / (|A||B|), range from 0 (perpendicular, no similarity) to 1 (parallel, identical direction)]

```
         vec_A
        /
       /  θ (มุมเล็ก = similar)
      /────────── vec_B
     O

cos(θ) ≈ 1.0  → สองทิศทางเดียวกัน = VERY SIMILAR
cos(θ) = 0.0  → ฉากกัน = NOT RELATED
cos(θ) ≈ -1.0 → ตรงข้าม = OPPOSITE
```

### สูตร

$$\text{cosine\_sim}(A, B) = \frac{A \cdot B}{\|A\| \cdot \|B\|}$$

### Implementation

```python
import numpy as np

def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))
```

### ทำไมใช้ Cosine ไม่ใช่ Euclidean?

```
Euclidean: ไวต่อขนาดของ vector (doc สั้น vs ยาว)
Cosine:    วัดแค่ "ทิศทาง" → ไม่สนใจขนาด
→ document ความยาวต่างกัน แต่ content เหมือน = similarity สูง
```

**Key Message:** Cosine วัด "ทิศทาง" ของความหมาย ไม่ใช่ "ขนาด" ของ document

---

## Slide 5 - Word → Sentence → Code Embeddings

# วิวัฒนาการของ Embeddings

### Word Embeddings (Word2Vec, 2013)

```
"cat" → vector
ปัญหา: คำเดียวกัน context ต่าง → vector เดียวกัน
"bank" (river) = "bank" (finance) ← เหมือนกัน!
```

### Sentence Embeddings (BERT, 2018)

```
"I went to the bank to deposit money" → vector A
"The river bank was muddy" → vector B
A ≠ B  ← context-aware!
```

### Code Embeddings

```python
# Code สองแบบนี้ → embedding ใกล้กัน
def sum_loop(lst):          # explicit loop
    total = 0
    for x in lst: total += x
    return total

def sum_builtin(lst):       # built-in
    return sum(lst)

# แม้ syntax ต่างกัน แต่ "logic" เหมือนกัน
cosine_similarity(embed(sum_loop), embed(sum_builtin)) ≈ 0.85
```

### Timeline

```
2013: Word2Vec → word-level
2018: BERT → sentence-level
2021: CodeBERT → code-aware
2023: nomic-embed-text → general-purpose (text + code)
```

**Key Message:** Modern embeddings เข้าใจ context และ code semantics

---

## Slide 6 - nomic-embed-text — 768 Dimensions

# nomic-embed-text: Embedding Model ที่เราใช้

### ลักษณะสำคัญ

| Property | ค่า |
|----------|-----|
| Dimensions | 768 |
| Context window | 8192 tokens |
| Languages | Multilingual (รวม Thai) |
| Speciality | Code + Text |
| License | Apache 2.0 |

### วิธีใช้

```python
from langchain_ollama import OllamaEmbeddings

# สร้าง embedder
embedder = OllamaEmbeddings(model="nomic-embed-text")

# embed single text (สำหรับ query)
query_vector = embedder.embed_query("how to sort a list")
print(len(query_vector))  # 768

# embed multiple texts (สำหรับ documents)
doc_vectors = embedder.embed_documents([
    "bubble sort algorithm",
    "merge sort implementation",
    "recipe for chocolate cake"
])
print(len(doc_vectors))    # 3
print(len(doc_vectors[0])) # 768
```

### คุณสมบัติ 768 มิติ

- ข้อมูลมาก → capture ความหมาย nuanced ได้
- เร็วพอสำหรับ real-time search
- ขนาดพอดีสำหรับ local deployment

**Key Message:** 768 มิติ = enough expressiveness สำหรับ code + text semantic search

---

## Slide 7 - Semantic Search vs Keyword Search

# เปรียบเทียบ: 2 วิธีค้นหา

### ตัวอย่าง Documents

```python
docs = [
    "def bubble_sort(arr): ...",              # doc 1
    "Quick sort uses divide and conquer",     # doc 2
    "Python recipe: pasta carbonara",         # doc 3
    "Sorting algorithms comparison table",   # doc 4
]
```

### Query: `"how to sort data efficiently"`

**Keyword Search:**
```
"sort" matches: doc 1 ✓, doc 2 (no "sort") ✗, doc 3 ✗, doc 4 ✓
Result: [doc 1, doc 4]
← พลาด doc 2 ที่พูดถึงการ sort!
```

**Semantic Search:**
```
embed(query) = [...]
similarity scores:
  doc 1: 0.82 ✓
  doc 2: 0.79 ✓  ← คำต่างกัน แต่ความหมายเดียวกัน!
  doc 3: 0.21 ✗  ← unrelated ถูกต้อง
  doc 4: 0.75 ✓
Result: [doc 1, doc 2, doc 4]
```

### เมื่อไหรควรใช้อะไร?

| สถานการณ์ | ใช้ |
|-----------|-----|
| ค้นหา function name แน่นอน | Keyword |
| ค้นหาตาม concept | Semantic |
| Mixed content | Hybrid (Session 09) |

**Key Message:** Semantic search ค้นหาด้วย "ความหมาย" — ดีกว่า keyword สำหรับ code discovery

---

## Slide 8 - Code Embeddings — ทำไม Code ที่ทำสิ่งเดียวกัน Vector ใกล้กัน

# Code Semantics ใน Vector Space

### ทดลอง: 3 implementations ของ factorial

```python
# Version 1: Recursive
def factorial_recursive(n):
    if n == 0: return 1
    return n * factorial_recursive(n - 1)

# Version 2: Iterative
def factorial_iterative(n):
    result = 1
    for i in range(1, n + 1):
        result *= i
    return result

# Version 3: math.factorial
import math
def factorial_builtin(n):
    return math.factorial(n)
```

### Similarity Results (ตัวอย่าง)

```
factorial_recursive ↔ factorial_iterative: 0.87
factorial_recursive ↔ factorial_builtin:   0.82
factorial_iterative ↔ factorial_builtin:   0.85

factorial_recursive ↔ "boil pasta":        0.12
```

### ทำไม Embedding รู้ว่า Logic เหมือนกัน?

- Model เรียนรู้จาก code ที่มีคนเขียน comments ว่า "same as"
- ชื่อ function/variable บอก intent
- Pattern ของ recursion/loop/built-in เป็น recurring pattern

**Key Message:** Code embedding capture "what it does" ไม่ใช่ "how it looks"

---

## Slide 9 - Embedding ใน RAG Pipeline

# ตำแหน่งของ Embedding ใน RAG

### RAG = Retrieval-Augmented Generation

```
┌─────────────────────────────────────────┐
│              RAG PIPELINE               │
│                                         │
│  1. INDEXING (ทำครั้งเดียว)             │
│     code files                          │
│         ↓                               │
│     chunk code into functions           │
│         ↓                               │
│     embed each chunk          ← Session 06 │
│         ↓                               │
│     store in vector DB        ← Session 07 │
│                                         │
│  2. RETRIEVAL (ทุก query)               │
│     user query                          │
│         ↓                               │
│     embed query               ← Session 06 │
│         ↓                               │
│     find similar chunks       ← Session 08 │
│         ↓                               │
│     return top-k results                │
│                                         │
│  3. GENERATION                          │
│     context + query → LLM → answer     │
└─────────────────────────────────────────┘
```

### Session Roadmap

```
Session 06: Embeddings (เรียนอยู่)
Session 07: ChromaDB + Chunking
Session 08: Full RAG Pipeline
```

**Key Message:** Embedding คือ foundation ที่ทุก session ถัดไปต้องใช้

---

## Slide 10 - Limitations — ข้อจำกัดของ Embeddings

# ข้อจำกัดที่ต้องรู้

### 1. Semantic Drift (Polysemy)

```python
# "bank" มีหลายความหมาย
"I went to the bank"     # financial institution
"The river bank was wet" # river bank

# Embedding blend ทั้งสองความหมาย
# → อาจ match ผิด context
```

### 2. Language Bias

```python
# nomic-embed-text trained ส่วนใหญ่บน English
# Thai, Japanese, etc. อาจไม่แม่นเท่า English
# Code comments ภาษาไทย → accuracy อาจลดลง
```

### 3. Context Window จำกัด

```python
# nomic-embed-text: max ~2048-8192 tokens
# ถ้า code file ยาว → ต้อง chunk ก่อน
# Solution: Session 07 (Chunking)
```

### 4. Static (ไม่ update real-time)

```python
# ถ้าแก้ code → ต้อง re-embed
# ถ้า library ใหม่ → model ไม่รู้จัก
# Solution: periodic re-indexing
```

### 5. ไม่ capture Syntax Correctness

```python
embed("def broken function")    # syntax error
embed("def correct_function()") # valid
# Similarity อาจสูง ทั้งที่ syntax ต่างกัน
```

**Key Message:** Embedding ดีสำหรับ semantic search แต่ต้องรู้ข้อจำกัด เพื่อ design system ที่ดี

---

*Slide Deck 01 | Session 06 | Local RAG for Programming*
