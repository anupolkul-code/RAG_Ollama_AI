# Session 01 — Roadmap & Setup

> **Module 1: Foundation & LLM** | ครั้งที่ 1 จาก 14 | 3 ชั่วโมง

---

## เป้าหมายของ Session นี้

เมื่อจบ session นี้ นักเรียนจะสามารถ:
- อธิบายได้ว่าหลักสูตรนี้จะสร้างอะไร และแต่ละ session ต่อกันอย่างไร
- อธิบาย big picture ของ RAG pipeline ได้ในระดับ conceptual
- ติดตั้ง tools ทั้งหมดและรัน qwen2.5-coder:7b บนเครื่องตัวเองได้

---

## ตารางเวลา

| ช่วง | เวลา | กิจกรรม |
|------|------|---------|
| 1 | 45 นาที | Demo ปลายทาง + Roadmap ทั้งหลักสูตร |
| 2 | 30 นาที | Big Picture: แต่ละ component ทำงานอย่างไร |
| 3 | 75 นาที | Workshop: ติดตั้ง tools ทีละขั้น |
| 4 | 30 นาที | ทดสอบให้ผ่านทุกเครื่อง + Q&A |

---

## ช่วงที่ 1 — Demo ปลายทาง (45 นาที)

**สิ่งที่เราจะสร้างได้ตอนจบหลักสูตร:**

```
นักเรียน: "function ไหนจัดการเรื่อง user authentication?"
Assistant: "พบใน auth/login.py บรรทัด 42 — function `authenticate_user()`
            รับ username และ password ตรวจสอบกับ database ผ่าน
            `UserRepository.find_by_email()` และคืนค่า JWT token"

นักเรียน: "ถ้าแก้ db.py จะกระทบไฟล์ไหนบ้าง?"
Assistant: "db.py ถูก import โดย 6 ไฟล์:
            - auth/login.py
            - users/repository.py
            - orders/service.py
            ..."
```

> ทั้งหมดนี้รันบนเครื่องตัวเอง ไม่มีค่าใช้จ่าย ข้อมูลไม่ออกจากเครื่อง

---

## ช่วงที่ 2 — Big Picture (30 นาที)

### RAG คืออะไร และทำไมต้องใช้

**RAG** (Retrieval-Augmented Generation — การดึงข้อมูลมาเสริมก่อน Generate) คือแนวทางแก้ปัญหา LLM (Large Language Model — โมเดลภาษาขนาดใหญ่) ที่ฉลาดแต่ไม่รู้จัก codebase ของเรา

```
ปัญหา: LLM ฉลาดแต่ไม่รู้จัก codebase ของเรา
แนวทางแก้: ก่อนตอบ ให้ LLM "อ่าน" โค้ดที่เกี่ยวข้องก่อน → RAG
```

### Pipeline ทั้งหมดที่จะเรียน

[FIGURE: RAG pipeline flow diagram — Codebase splits into AST Parser (→ Graph DB) and Embeddings (→ Vector DB); user question goes to Router which picks Graph Query or Vector Search; results merge and go to LLM → Answer]

```
[ Codebase ]
     │
     ├──► AST Parser ──────► [ Graph DB ]  ← โครงสร้าง: ใครเรียกใคร
     │                           │
     └──► Embeddings ─────► [ Vector DB ] ← ความหมาย: โค้ดคล้ายกัน
          (Embedding — แปลงโค้ดเป็น Vector ตัวเลขที่แทนความหมาย)
                                 │
                    คำถาม ──► [ Router ]
                                 │
                    ┌────────────┴────────────┐
                    ▼                         ▼
              Graph Query              Vector Search
                    └────────────┬────────────┘
                                 ▼
                      [ qwen2.5-coder:7b LLM ]
                                 │
                              คำตอบ
```

### สิ่งที่จะเรียนรู้แต่ละ Session

```
Session 01-03  →  LLM คืออะไร ใช้ยังไง มีขีดจำกัดอะไร
Session 04-05  →  Prompt Engineering เขียน prompt ให้ได้ผลดี
Session 06-07  →  Embedding + Vector DB ค้นหาด้วยความหมาย
Session 08-09  →  RAG Pipeline ประกอบทุกอย่างเข้าด้วยกัน
Session 10-11  →  Graph DB วิเคราะห์โครงสร้าง code
Session 12-14  →  Hybrid RAG + UI + Demo Day
```

---

## ช่วงที่ 3 — Workshop: ติดตั้ง Tools (75 นาที)

> **หลักสูตรนี้ใช้ Python เป็นภาษาหลัก และใช้ `uv` ในการจัดการ environment แทน venv + pip**

### ทำไมถึงใช้ uv?

| | pip + venv | uv |
|--|-----------|-----|
| ความเร็ว | ปกติ | เร็วกว่า 10–100x |
| จัดการ Python version | ไม่ได้ | ได้ |
| lock file | ต้อง freeze เอง | อัตโนมัติ |
| คำสั่ง | หลายคำสั่ง | คำสั่งเดียว |

---

### Step 1: ติดตั้ง uv (5 นาที)

**Windows (winget):**
```powershell
winget install astral-sh.uv
```

**macOS / Linux:**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

ทดสอบ:
```bash
uv --version
```

---

### Step 2: VS Code + Extensions (10 นาที)

ดาวน์โหลด [VS Code](https://code.visualstudio.com/)

Extensions ที่แนะนำ:
- Python (Microsoft)
- Pylance
- GitLens

---

### Step 3: ติดตั้ง Ollama (15 นาที)

**Windows (winget):**
```powershell
winget install Ollama.Ollama --version 0.24.0
```

**macOS / Linux:**
```bash
curl -fsSL https://ollama.com/install.sh | sh
```

ทดสอบหลังติดตั้ง:
```bash
ollama --version
# ควรได้ ollama version 0.24.0
```

---

### Step 4: Pull Models (20 นาที)

```bash
# LLM หลักสำหรับงาน code
ollama pull qwen2.5-coder:7b

# Embedding model (แปลงข้อความเป็น vector)
ollama pull nomic-embed-text

# ตรวจสอบว่า pull สำเร็จ
ollama list
```

**หมายเหตุ:** qwen2.5-coder:7b มีขนาด ~4.7GB

> **ต้องการ model ที่แม่นยำกว่า (GPU ≥ 16GB VRAM):**
> ```bash
> ollama pull qwen2.5-coder:14b
> ```

---

### Step 5: สร้าง Project ด้วย uv (10 นาที)

```bash
# สร้าง project พร้อม Python 3.11 และ virtual environment อัตโนมัติ
uv init coding-assistant --python 3.11
cd coding-assistant
```

uv จะสร้างโครงสร้างให้ทันที:
```
coding-assistant/
├── .venv/           ← virtual environment (สร้างอัตโนมัติ)
├── pyproject.toml   ← แทน requirements.txt
├── .python-version  ← กำหนด Python version ของ project
└── hello.py
```

> **ไม่ต้อง activate venv เอง** — `uv run` จัดการให้อัตโนมัติ

---

### Step 6: ติดตั้ง Python Packages (15 นาที)

```bash
uv add \
  langchain-ollama \
  langchain-community \
  langchain-core \
  faiss-cpu \
  kuzu \
  streamlit \
  pypdf \
  python-dotenv \
  networkx \
  matplotlib \
  rank-bm25
```

uv จะอัปเดต `pyproject.toml` และสร้าง `uv.lock` ให้อัตโนมัติ

ตรวจสอบ packages ที่ติดตั้ง:
```bash
uv pip list
```

---

### การรัน Script ด้วย uv

```bash
# แทนที่จะ activate venv แล้วรัน python
uv run python test_setup.py

# รัน streamlit
uv run streamlit run app.py

# รัน script ใดก็ได้
uv run python <script.py>
```

---

## ช่วงที่ 4 — ทดสอบให้ผ่าน (30 นาที)

สร้างไฟล์ `test_setup.py` และรัน:

```python
# test_setup.py — ทดสอบว่า tools ทุกตัวพร้อมใช้งาน
errors = []

try:
    from langchain_ollama import OllamaLLM
    llm = OllamaLLM(model="qwen2.5-coder:7b")
    r = llm.invoke("ตอบว่า OK เท่านั้น")
    print(f"✓ qwen2.5-coder:7b: {r.strip()}")
except Exception as e:
    errors.append(f"✗ LLM: {e}")

try:
    from langchain_ollama import OllamaEmbeddings
    vec = OllamaEmbeddings(model="nomic-embed-text").embed_query("test")
    print(f"✓ Embedding (nomic-embed-text): {len(vec)} dimensions")
except Exception as e:
    errors.append(f"✗ Embedding: {e}")

try:
    import faiss, kuzu, streamlit
    print(f"✓ FAISS {faiss.__version__}  Kuzu OK  Streamlit {streamlit.__version__}")
except Exception as e:
    errors.append(f"✗ Packages: {e}")

print("\n✓ ทุกอย่างพร้อมใช้งาน!" if not errors else "\n".join(errors))
```

```bash
uv run python test_setup.py
```

**ผลลัพธ์ที่ต้องการ:**
```
✓ qwen2.5-coder:7b: OK
✓ Embedding (nomic-embed-text): 768 dimensions
✓ FAISS 1.x.x  Kuzu OK  Streamlit 1.x.x

✓ ทุกอย่างพร้อมใช้งาน!
```

---

## โครงสร้างโปรเจกต์ที่จะสร้างตลอดหลักสูตร

```
coding-assistant/
├── setup.py                  # index codebase (รัน 1 ครั้ง)
├── app.py                    # Streamlit UI (Session 13)
├── hybrid_rag.py             # Hybrid RAG engine (Session 12)
├── rag_pipeline.py           # Vector RAG (Session 8)
├── ast_parser.py             # Code → Graph (Session 11)
├── embed_codebase.py         # Code → Vector (Session 7)
├── prompts/
│   └── coding_prompts.py     # Prompt templates (Session 5)
├── vector_db/                # FAISS index (generated)
├── graph_db/                 # Kuzu data (generated)
├── .venv/                    # virtual environment (managed by uv)
├── pyproject.toml            # dependencies (managed by uv)
├── uv.lock                   # lock file (managed by uv)
├── .python-version           # Python version ของ project
└── .env                      # config (ถ้าต้องการ)
```

---

## แนวคิดสำคัญที่พบในครั้งนี้

| แนวคิด | คำอธิบายสั้น |
|--------|------------|
| **LLM** (Large Language Model) | โมเดลภาษาขนาดใหญ่ — ตอบคำถามได้แต่ไม่รู้จัก codebase ของเรา |
| **Ollama** | เครื่องมือรัน LLM บนเครื่องตัวเอง ฟรี ไม่ต้องใช้ internet |
| **qwen2.5-coder:7b** | LLM ที่เชี่ยวชาญด้าน code โดยเฉพาะ |
| **RAG** (Retrieval-Augmented Generation) | การดึงข้อมูลมาเสริมก่อน Generate — ให้ LLM อ่านข้อมูลก่อนตอบ |
| **Embedding** | การแปลงข้อความ/โค้ดเป็น Vector (ชุดตัวเลขที่แทนความหมาย) |
| **Vector DB** | ฐานข้อมูลค้นหาด้วย "ความหมาย" (Semantic Search) ไม่ใช่แค่ keyword |
| **Graph DB** | ฐานข้อมูลกราฟ — เก็บความสัมพันธ์ระหว่าง node เช่น "A เรียก B" |

---

## ปัญหาที่พบบ่อยและวิธีแก้

| ปัญหา | วิธีแก้ |
|-------|---------|
| `ollama: command not found` | restart terminal หลังติดตั้ง Ollama |
| `Error: model not found` | รัน `ollama pull qwen2.5-coder:7b` และ `ollama pull nomic-embed-text` ก่อน |
| RAM ไม่พอ | ใช้ `qwen2.5-coder:7b` (7B ใช้ RAM ~6GB เท่านั้น) |
| `uv: command not found` | restart terminal หลังติดตั้ง uv |
| package หาย | รัน `uv sync` เพื่อ restore จาก `uv.lock` |
| Kuzu import error | `uv add kuzu --upgrade` |

---

## Session ถัดไป

**Session 02 — LLM คืออะไร + ใช้งานผ่าน Code**

จะเรียนรู้:
- Token คืออะไร context window คืออะไร
- Temperature ส่งผลต่อคำตอบอย่างไร
- เขียน Python เรียก LLM (qwen2.5-coder:7b) และดูผลลัพธ์จริง

---

## Checklist ก่อนออกจาก Session นี้

```
□ รัน ollama list แล้วเห็น qwen2.5-coder:7b และ nomic-embed-text
□ รัน uv run python test_setup.py แล้วผ่านทุก test
□ เข้าใจ big picture ว่าแต่ละ session จะสร้างอะไร
□ มี folder coding-assistant/ พร้อม pyproject.toml และ uv.lock
□ เข้าใจความแตกต่างระหว่าง uv กับ pip + venv
```
