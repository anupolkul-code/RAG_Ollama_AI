# Slide Deck: 02 — LLM for Code: Strengths & Weaknesses

> Session 03 | Module 1: Foundation & LLM | 8 slides

---

## Slide 1 - Title

# LLM สำหรับ Coding
## เก่งอะไร ไม่เก่งอะไร และ RAG ช่วยได้อย่างไร

**Session 03 — Deck 2**

> ก่อนใช้เครื่องมือ ต้องรู้ว่ามันทำอะไรได้และไม่ได้

**Key Message:** LLM เป็น coding assistant ที่ดีเยี่ยม — แต่ต้องรู้ขอบเขตก่อนเชื่อ

---

## Slide 2 - LLM เก่งอะไรใน Coding

### Strength Zone: สิ่งที่ LLM ทำได้ดีมาก

**1. เขียน Boilerplate Code**
```python
# ขอแค่บอก spec — LLM เขียนได้ถูกต้องเกือบทุกครั้ง
# "Write a Python dataclass for User with name, email, age"
from dataclasses import dataclass
from typing import Optional

@dataclass
class User:
    name: str
    email: str
    age: int
    bio: Optional[str] = None
```

**2. อธิบาย Code ที่ไม่คุ้นเคย**
- อธิบาย algorithm ที่ซับซ้อน
- Translate ระหว่าง programming languages
- อธิบาย regex patterns
- Document existing code

**3. Suggest Solutions สำหรับ Common Problems**
- Sorting, searching, data transformation
- File I/O operations
- String manipulation
- Standard library usage

**Key Message:** LLM เป็น "senior developer" สำหรับ common patterns — แต่ "intern" สำหรับ project-specific logic

---

## Slide 3 - LLM ไม่เก่งอะไรใน Coding

### Weakness Zone: สิ่งที่ LLM มักทำพลาด

**1. Project-specific Logic**
```python
# "How does our OrderProcessor.calculate_discount() work?"
# LLM ไม่รู้ business rules ของเรา → ตอบผิดหรือ hallucinate
```

**2. Recent APIs (หลัง Training Cutoff)**
```python
# LangChain เปลี่ยน API บ่อยมาก
# LLM อาจแนะนำ deprecated syntax:
from langchain.llms import Ollama  # OLD (deprecated)
# ที่ถูก:
from langchain_ollama import OllamaLLM  # NEW
```

**3. Internal Conventions และ Architecture Decisions**
- "เราใช้ snake_case หรือ camelCase สำหรับ database fields?"
- "Config file format ของ project เราคืออะไร?"
- "ทีมเราตกลง error handling pattern ไว้อย่างไร?"

**4. Runtime Context**
```python
# "Why is self.cache_size returning None?"
# LLM ไม่รู้ค่า runtime ปัจจุบัน
# ต้องให้ context เพิ่ม (stacktrace, variable values)
```

**Key Message:** ยิ่งคำถาม project-specific มากเท่าไหร่ LLM ยิ่งต้องการ context จากเรามากขึ้น

---

## Slide 4 - Demo — LLM แต่ง API ที่ไม่มีอยู่จริง

### ทดสอบ Live: Internal Library

```python
from langchain_ollama import OllamaLLM

llm = OllamaLLM(model="qwen2.5-coder:7b")

# ถาม LLM เรื่อง library สมมติ
response = llm.invoke("""
We use 'dataflow_engine' library internally.
Show me how to use dataflow_engine.Pipeline.add_transform_step()
with a custom validator. Give complete working code.
""")
print(response)
```

### ผลที่มักเกิดขึ้น

**Scenario A — Hallucinate (พบบ่อย):**
```python
# LLM อาจตอบ:
from dataflow_engine import Pipeline, TransformStep

pipeline = Pipeline(name="my_pipeline")
pipeline.add_transform_step(
    step=TransformStep(name="clean", func=lambda x: x.strip()),
    validator=CustomValidator(schema="v2")
)
# ^ Code ดูสมจริง แต่ไม่ตรงกับ implementation จริง!
```

**Scenario B — Honest Refusal (ดีกว่า):**
```
I'm not familiar with 'dataflow_engine' library. 
Could you provide the documentation or source code?
```

**Key Message:** Scenario B คือพฤติกรรมที่ดี แต่ LLM ไม่รับประกันว่าจะเลือก Scenario B

---

## Slide 5 - Hallucination ใน Code — Pattern ที่พบบ่อย

### 5 รูปแบบ Hallucination ใน Coding

**1. Invented Parameters**
```python
# Real pandas:
df.fillna(value=0, method='ffill')

# LLM hallucinated:
df.fillna(value=0, method='ffill', smart_interpolate=True)
#                                  ^ ไม่มี parameter นี้
```

**2. Wrong Return Types**
```python
# LLM บอก: "os.path.exists() returns the path string if exists"
# ความจริง: returns bool (True/False)
result = os.path.exists("/tmp/file.txt")
if result == "/tmp/file.txt":  # WRONG! result เป็น True/False
    ...
```

**3. Non-existent Functions**
```python
# LLM hallucinated:
import sys
sys.memory_usage()  # ไม่มีอยู่จริง
# ที่ถูก:
import psutil
psutil.Process().memory_info()
```

**4. Wrong Import Paths**
```python
# LLM (อาจ outdated):
from langchain.chat_models import ChatOllama  # ผิด
# ที่ถูก:
from langchain_ollama import ChatOllama  # ถูก
```

**5. Incorrect Method Names**
```python
# LLM: "Use list.delete(item) to remove"
# ความจริง:
lst.remove(item)   # correct
del lst[index]     # also correct
# list.delete() ไม่มีอยู่จริง
```

**Key Message:** ทดสอบทุก code ที่ LLM ให้มาเสมอ — อย่า copy-paste โดยไม่ verify

---

## Slide 6 - Best Practices — ใช้ LLM เป็น Assistant ไม่ใช่ Oracle

### หลักการใช้ LLM อย่างฉลาด

```
TREAT LLM AS:              NOT AS:
─────────────────          ─────────────────
Junior developer           Senior authority
Draft generator            Final answer
Pattern suggester          Documentation
Boilerplate helper         Source of truth
```

### Workflow ที่ดี

```
1. คุณเขียน spec/requirement ที่ชัดเจน
       |
       v
2. LLM สร้าง draft code
       |
       v
3. คุณ review + verify ทุก API ที่ใช้
       |
       v
4. คุณ test กับ codebase จริง
       |
       v
5. คุณ commit (ไม่ใช่ LLM)
```

### Red Flags ที่ต้องระวัง
- LLM ตอบเร็วมากสำหรับคำถาม project-specific
- Code ดูสมบูรณ์แบบเกินไป
- LLM ไม่ขอ clarification ในงานที่ complex
- Import paths ไม่ตรงกับ project setup ของคุณ

**Key Message:** LLM เป็น "code completion on steroids" — ต้องมี human review เสมอ

---

## Slide 7 - RAG ทำให้ LLM รู้จัก Codebase จริงๆ

### Before RAG vs After RAG

**Before RAG:**
```
Your Question ──> LLM (ไม่รู้อะไรเกี่ยวกับ code คุณ)
                       |
                       v
              Hallucinated Answer
```

**After RAG:**
```
Your Question ──> Retriever ──> FAISS (your code indexed)
                                    |
                              Relevant chunks:
                              - class definition
                              - function docstring
                              - usage examples
                                    |
                                    v
              Your Question + Context ──> LLM
                                           |
                                           v
                                  Accurate Answer
                                 (grounded in your code)
```

### สิ่งที่ RAG ทำได้

| Task | Without RAG | With RAG |
|------|------------|---------|
| "How to use our AuthService?" | Hallucinate | ตอบจาก code จริง |
| "What does this function return?" | ดูจาก context | ดูจาก indexed code |
| "Find all usages of deprecated API" | ไม่รู้ | ค้นหาได้ |
| "Explain our database schema" | ไม่รู้ | ตอบจาก schema file |

**Key Message:** RAG = LLM + ความรู้เกี่ยวกับ codebase ของคุณ — เหมือน "onboarding" developer ใหม่ด้วย codebase ของจริง

---

## Slide 8 - Summary + Path Forward

### สรุป: LLM สำหรับ Coding

```
ทำได้ดี                          ต้องการ RAG
─────────────────                ─────────────────
- Boilerplate code               - Internal APIs
- Common algorithms              - Project conventions
- Standard library usage         - Recent APIs
- Code explanation               - Private docs
- Debugging hints (public)       - Business logic
- Unit test templates            - Schema queries
```

### ก้าวต่อไป (Sessions ที่เหลือ)

```
Session 03 (ตอนนี้)   : เข้าใจข้อจำกัด
Session 04            : Prompt Engineering (ใช้ LLM ได้ดีขึ้น)
Session 05            : Prompts สำหรับ Code โดยเฉพาะ
Session 06            : Embeddings (ดัชนีสำหรับ RAG)
Session 07            : FAISS + Chunking (เก็บ vectors)
Session 08            : Full RAG Pipeline (รวมทุกอย่าง)
...
Session 14            : Demo Day
```

### Call to Action

```powershell
# เริ่ม Lab ทดสอบด้วยตัวเอง:
uv run python lab\lab_03_llm_testing.py
```

**Key Message:** เส้นทางจาก "LLM ที่ไม่รู้อะไรเกี่ยวกับ code เรา" ไปสู่ "coding assistant ที่รู้จัก codebase ทุก byte" คือ Sessions 03-08

---

*Deck 2 of 2 — Session 03: LLM Limitations*
