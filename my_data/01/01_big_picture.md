# Slide Deck: Big Picture — Local RAG for Programming
> Session 01 | Module 1: Foundation | 10 slides

---

## Slide 1 — Title
**Local RAG for Programming**
สร้าง Coding Assistant ที่รู้จัก codebase ของคุณ รันฟรีบนเครื่องตัวเอง

Session 01 — Roadmap & Setup

---

## Slide 2 — เป้าหมายปลายทาง
**Key Message**: หลักสูตรนี้สร้าง AI assistant ที่ตอบคำถาม codebase จริงได้ โดยไม่ต้องส่งข้อมูลออกไปข้างนอก

**สิ่งที่คุณจะสร้างได้เมื่อจบหลักสูตร:**

```
คุณ: "function ไหนจัดการ user authentication?"
AI:  "พบใน auth/login.py บรรทัด 42 — authenticate_user()
      รับ username/password ตรวจกับ DB และคืน JWT token"

คุณ: "แก้ db.py กระทบไฟล์ไหนบ้าง?"
AI:  "db.py ถูก import โดย 6 ไฟล์: auth/, users/, orders/..."
```

✅ รันบนเครื่อง — ฟรี 100% — ข้อมูลไม่ออกจากเครื่อง

---

## Slide 3 — ปัญหา: LLM ไม่รู้จัก Codebase ของเรา
**Key Message**: LLM ฉลาดแต่ "ตาบอด" — ไม่รู้จัก code ที่คุณเขียนเอง

**LLM รู้จัก:**
- Python standard library ✅
- Popular frameworks (Django, FastAPI) ✅
- Design patterns ✅

**LLM ไม่รู้จัก:**
- `myproject/internal_api.py` ❌
- Business logic เฉพาะของบริษัท ❌
- Code ที่เขียนหลัง training cutoff ❌

**[FIGURE: diagram showing LLM knowledge boundary vs private codebase]**

---

## Slide 4 — RAG คืออะไร?
**Key Message**: RAG = ให้ LLM "อ่านโค้ด" ก่อนตอบ ไม่ใช่ "จำ" ทุกอย่าง

**Retrieval-Augmented Generation:**
```
คำถาม
  ↓
ค้นหาโค้ดที่เกี่ยวข้อง (Retrieve)
  ↓
ใส่โค้ดนั้นใน prompt (Augment)
  ↓
LLM ตอบโดยมีโค้ดเป็น context (Generate)
```

**เปรียบเทียบ:**
- ❌ LLM ล้วน: ตอบจากความจำ (hallucinate ได้)
- ✅ RAG: ตอบจากโค้ดจริงที่ retrieve มา

---

## Slide 5 — Pipeline ทั้งหมด
**Key Message**: RAG for Code ต้องการ 2 ประเภทของ storage — Vector สำหรับ "ความหมาย" และ Graph สำหรับ "โครงสร้าง"

```
[ Codebase ของคุณ ]
       │
       ├──► AST Parser ──► [ Graph DB (Kuzu) ]
       │                        "ใครเรียกใคร"
       └──► Embeddings ──► [ Vector DB (FAISS) ]
                               "ความหมายคล้ายกัน"
                   คำถาม ──► [ Router ]
                                  │
                    ┌─────────────┴─────────────┐
                    ▼                           ▼
              Graph Query               Vector Search
                    └─────────────┬─────────────┘
                                  ▼
                           [ qwen2.5-coder ]
                                  │
                               คำตอบ
```

---

## Slide 6 — Stack ที่ใช้ (ทั้งหมดฟรี)
**Key Message**: ทุกเครื่องมือเป็น open-source รันได้บน Windows โดยไม่ต้องมี GPU แพง

| เครื่องมือ | บทบาท | ต้องการ |
|-----------|-------|---------|
| **Ollama** | รัน LLM local | RAM ≥ 8GB |
| **qwen2.5-coder:7b** | LLM สำหรับ code | ~4.5GB disk |
| **nomic-embed-text** | Embedding | ~270MB |
| **FAISS** | Vector search | Python |
| **Kuzu** | Graph DB | Python |
| **LangChain** | Orchestration | Python |
| **Streamlit** | Web UI | Python |

**ค่าใช้จ่าย: ฟรี 100%**

---

## Slide 7 — แผนการเรียน 14 Sessions
**Key Message**: ทุก session ต่อยอดจากสิ่งที่เรียนก่อนหน้า จนได้ product จริงใน session สุดท้าย

```
Module 1 (01-03) ─── Foundation & LLM
Module 2 (04-05) ─── Prompt Engineering
Module 3 (06-07) ─── Embeddings & Vector DB
Module 4 (08-09) ─── RAG Pipeline
Module 5 (10-11) ─── Graph DB
Module 6 (12-14) ─── ประกอบ + UI + Demo Day
```

**Deliverable แต่ละ session สะสมกัน:**
01 → setup | 02 → llm_basics.py | 05 → prompt_library.py
07 → vector_db/ | 08 → rag_pipeline.py | 11 → graph_db/
12 → hybrid_rag.py | 13 → app.py | 14 → **LIVE DEMO** 🎉

---

## Slide 8 — Setup Overview (Windows)
**Key Message**: ติดตั้งครั้งเดียว ใช้ได้ตลอดหลักสูตร

```powershell
# Step 1: ติดตั้ง Ollama
winget install Ollama.Ollama

# Step 2: ติดตั้ง uv (package manager)
winget install astral-sh.uv

# Step 3: Pull models
ollama pull qwen2.5-coder:7b
ollama pull nomic-embed-text

# Step 4: สร้าง project
uv init coding-assistant --python 3.11
cd coding-assistant
uv add langchain-ollama langchain-community faiss-cpu kuzu streamlit

# Step 5: ทดสอบ
uv run python test_setup.py
```

---

## Slide 9 — ทำไมต้อง uv แทน pip?
**Key Message**: uv เร็วกว่า pip 10-100x และจัดการ environment ให้อัตโนมัติ

| | pip + venv | **uv** |
|--|-----------|--------|
| ความเร็ว | baseline | **10-100x เร็วกว่า** |
| จัดการ Python version | ❌ | ✅ |
| Lock file อัตโนมัติ | ❌ ต้อง freeze เอง | ✅ uv.lock |
| Activate venv | ต้องทำเอง | ❌ ไม่ต้อง |
| คำสั่งรัน script | `python script.py` | `uv run python script.py` |

```powershell
# ❌ วิธีเก่า
python -m venv .venv
.venv\Scripts\activate
pip install langchain-ollama

# ✅ วิธีใหม่
uv add langchain-ollama
uv run python my_script.py
```

---

## Slide 10 — Summary + Session ถัดไป
**Key Message**: Setup เสร็จแล้ว — พร้อมเรียนรู้ว่า LLM ทำงานอย่างไร

**สิ่งที่ทำได้หลัง Session นี้:**
- ✅ Ollama + qwen2.5-coder + nomic-embed-text ติดตั้งแล้ว
- ✅ Python environment พร้อมใช้
- ✅ เข้าใจ big picture ของ RAG pipeline
- ✅ รู้ว่าแต่ละ session สร้างอะไร

**Session 02 — LLM Basics:**
- Token คืออะไร? Context window ทำงานอย่างไร?
- Temperature ส่งผลต่อคำตอบอย่างไร?
- เขียน Python เรียก LLM และดูผลลัพธ์จริง
