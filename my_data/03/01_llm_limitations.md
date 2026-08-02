# Slide Deck: 01 — LLM Limitations

> Session 03 | Module 1: Foundation & LLM | 10 slides

---

## Slide 1 - Title

# LLM Limitations
## เข้าใจข้อจำกัดก่อนสร้าง RAG

**Session 03 — Local RAG for Programming**

- Model: `qwen2.5-coder:7b` via Ollama
- Stack: LangChain · Python · uv

> "รู้เขา รู้เรา รบร้อยครั้ง ชนะร้อยครั้ง"
> — ต้องเข้าใจข้อจำกัด LLM ก่อนจะใช้มันได้ดี

**Key Message:** LLM เป็นเครื่องมือที่ทรงพลัง แต่มีข้อจำกัดที่ชัดเจน — เข้าใจแล้วจะใช้ได้ถูกวิธี

---

## Slide 2 - LLM รู้อะไร ไม่รู้อะไร (Knowledge Boundary)

### Knowledge Boundary Diagram

```
          ┌─────────────────────────────────────┐
          │      Training Data (รู้จัก)           │
          │                                     │
          │  • Python stdlib, NumPy, Pandas      │
          │  • Public GitHub repos              │
          │  • Stack Overflow Q&A               │
          │  • Wikipedia, documentation         │
          │                                     │
          └───────────────┬─────────────────────┘
                          │ Training Cutoff
          ┌───────────────▼─────────────────────┐
          │       ไม่รู้จัก (Unknown)              │
          │                                     │
          │  • Codebase ภายในองค์กร              │
          │  • Private repositories             │
          │  • APIs ที่ release หลัง cutoff      │
          │  • Internal documentation           │
          └─────────────────────────────────────┘
```

**LLM ไม่ใช่ search engine** — มันเพียง predict token ถัดไป  
ไม่มีกลไก "ค้นหาข้อมูลจริง" ในขณะตอบคำถาม

**Key Message:** LLM รู้แค่สิ่งที่อยู่ใน training data — ทุกอย่างนอกจากนั้นคือ "terra incognita"

---

## Slide 3 - Limitation #1 — Hallucination

### นิยาม
LLM สร้างข้อมูลที่ **ดูน่าเชื่อถือแต่ไม่เป็นความจริง**

### ตัวอย่างจริงใน Code

**Prompt:** "How to use `pandas.DataFrame.smart_fillna()`?"

**LLM ตอบ (ผิด แต่ฟังดูสมจริง):**
```python
import pandas as pd
df = pd.DataFrame({'A': [1, None, 3]})
# ใช้ smart_fillna กับ intelligence_level parameter
df_filled = df.smart_fillna(method='forward', intelligence_level=2)
```

**ความจริง:** `smart_fillna()` ไม่มีอยู่ใน pandas เลย!

### ทำไมเกิดขึ้น?
1. LLM เห็น `fillna`, `ffill`, `bfill` ใน training
2. Pattern matching → สร้าง "smart" version ที่ดูสมเหตุสมผล
3. ไม่มีกลไกตรวจสอบว่า function นั้นมีอยู่จริง

**Key Message:** LLM พูดด้วยความมั่นใจแม้จะแต่งเรื่องขึ้นมา — ต้องตรวจสอบทุกครั้ง

---

## Slide 4 - Limitation #2 — Knowledge Cutoff

### Training มีวันหมดอายุ

```
──────────────────────────┬──────────────────────────────>
                          │                           เวลา
                   Training Cutoff

    รู้จักดี              │          ไม่รู้จัก / อาจผิด
──────────────────────────┼──────────────────────────────
  Python 3.11 syntax      │  Python 3.13 new features
  LangChain 0.1 API       │  LangChain 0.3 LCEL changes
  Older security patches  │  CVE-2024-xxxxx and beyond
  pandas 2.0 behavior     │  Breaking changes after cutoff
```

### ตัวอย่างที่เจอบ่อย

```python
# LLM แนะนำ (อาจ outdated):
from langchain.llms import Ollama  # ← deprecated!

# ที่ถูกต้องตาม version ใหม่:
from langchain_ollama import OllamaLLM  # ← correct
```

### ผลกระทบ
- Code ที่ LLM เขียนอาจใช้ deprecated API
- Security advice อาจ outdated
- ต้องตรวจสอบกับ official docs เสมอ

**Key Message:** LLM training cutoff หมายความว่าทุก "latest" ที่ LLM พูดถึงอาจเก่าแล้ว

---

## Slide 5 - Limitation #3 — Context Window Limit

### ทำไม 4,096 Tokens ไม่พอสำหรับ Codebase

| ขนาด | Token (ประมาณ) | เทียบเท่า |
|------|--------------|---------|
| 4,096 | ~4K tokens | 200-300 บรรทัด code |
| 32,000 | ~32K tokens | 1,500-2,500 บรรทัด |
| 128,000 | ~128K tokens | 6,000-10,000 บรรทัด |
| **Real project** | **500K-50M+** | **50K-5M+ บรรทัด** |

### "Lost in the Middle" Problem

```
Context: [AAAAAA ... BBBBBBB ... CCCCCC]
              ^                      ^
         จำได้ดี              จำได้ดี
                     ^
                จำได้แย่ที่สุด!
```

**งานวิจัยพบว่า:** LLM มักมองข้ามข้อมูลที่อยู่กลาง context  
(Liu et al., 2023 — "Lost in the Middle")

**Key Message:** แม้ context window จะใหญ่ขึ้น ก็ยังไม่ใช่ทางออกที่ดีสำหรับ codebase ขนาดใหญ่

---

## Slide 6 - Limitation #4 — Private Knowledge Problem

### LLM ไม่รู้จัก Codebase ของเรา

```
Public Internet                    Your Company
────────────────                   ─────────────────────
GitHub public repos    ──────>     Internal Git repos  (X)
PyPI packages          ──────>     company_internal_sdk (X)
Stack Overflow         ──────>     Internal Wiki        (X)
Documentation sites    ──────>     Confluence/Notion    (X)
                                   config.yaml          (X)
                                   .env files           (X)
```

**ผลลัพธ์:** ถาม LLM เรื่อง internal function → hallucinate หรือปฏิเสธ

```python
# ถาม: "How to use our DataPipeline.transform_invoice_batch()?"
# LLM: (แต่ implementation ขึ้นมาเองโดยไม่มีพื้นฐาน)
def transform_invoice_batch(invoices):
    # LLM แต่ง parameter ขึ้นมาเอง
    return process_invoices_standard(invoices)
# ^ WRONG — ไม่ตรงกับ implementation จริงเลย
```

**Key Message:** ทุก codebase ในองค์กรคือ "terra incognita" สำหรับ LLM — RAG คือสะพานเชื่อม

---

## Slide 7 - The "Confident but Wrong" Problem

### LLM ไม่รู้ว่าตัวเองไม่รู้

**Test cases ที่น่าสนใจ:**

| คำถาม | LLM มักตอบ | คำตอบที่ถูกต้อง |
|-------|-----------|--------------|
| Python list.sort() algorithm? | "QuickSort" | **Timsort** |
| requests default timeout? | "30 seconds" | **None (ไม่มี timeout!)** |
| dict lookup complexity? | "O(1)" | O(1) average ✓ |
| `is` vs `==` in Python? | ผสมกัน | ต่างกันมาก (identity vs equality) |

### ทำไมถึงอันตราย?

```python
# LLM บอกว่า requests มี default timeout
# คุณเชื่อ → ไม่ใส่ timeout
import requests
response = requests.get("http://slow-server.com/api")
# ^ อาจ hang ตลอดไป! เป็น production bug!

# ที่ถูกต้อง:
response = requests.get("http://server.com/api", timeout=30)
```

**Key Message:** LLM ไม่มี "ไม่รู้" mode — confidence ในการตอบไม่ correlate กับความถูกต้อง

---

## Slide 8 - ทดสอบจริง — ถาม LLM เรื่อง Internal API

### Demo: ทดสอบ Live

```python
from langchain_ollama import OllamaLLM

llm = OllamaLLM(model="qwen2.5-coder:7b")

# ถาม 1: Library ที่ไม่มีอยู่จริง
response1 = llm.invoke(
    "Show me how to use mycompany_internal_sdk v5.2 "
    "function process_data_with_ai_enhancement(). "
    "Give a complete example."
)

# ถาม 2: เดียวกัน แต่ให้ source code
source = """
class DataEnhancer:
    def process_data_with_ai_enhancement(
        self, data: list, model_id: str = "default"
    ) -> dict:
        # Use internal ML pipeline
        ...
"""
response2 = llm.invoke(
    f"Source code:\n{source}\n\n"
    "Now explain process_data_with_ai_enhancement and show example."
)
```

### ผลที่คาดหวัง
- **Test 1:** LLM hallucinate หรือปฏิเสธ (ไม่มี context)
- **Test 2:** LLM ตอบถูกต้องตาม source code (มี context)

**Key Message:** Context injection = "สอน" LLM เกี่ยวกับ private code ก่อนตอบ — นี่คือ core idea ของ RAG

---

## Slide 9 - RAG แก้ปัญหาเหล่านี้ได้อย่างไร

### RAG = Retrieval-Augmented Generation

```
Before RAG:
  Question ──> LLM ──> Answer (อาจผิด)

After RAG:
  Question ──> [Retrieve] ──> Relevant chunks from your codebase
                   |
                   v
              [Augment] ──> Question + Context
                   |
                   v
              LLM ──> Answer (grounded in real code)
```

### ตารางเปรียบเทียบ

| ปัญหา | ไม่มี RAG | มี RAG |
|-------|----------|-------|
| Hallucination | LLM แต่ API ปลอม | ดึง doc จริงมาให้ก่อน |
| Knowledge Cutoff | ข้อมูลเก่า | Index ใหม่ได้ตลอด |
| Private Knowledge | ไม่รู้จักเลย | Index codebase เราได้ |
| Context Window | ต้อง paste ทั้งไฟล์ | ดึงเฉพาะ relevant chunks |
| Overconfidence | ไม่มีหลักฐาน | มี source อ้างอิงได้ |

**Key Message:** RAG เพิ่ม "memory" ให้ LLM โดยไม่ต้อง retrain — เร็ว ถูก และ flexible

---

## Slide 10 - Summary + Motivation สำหรับ RAG

### สรุป 5 ข้อจำกัดที่ต้องรู้

```
1. Hallucination      — LLM แต่ข้อมูลที่ไม่มีอยู่จริง
2. Knowledge Cutoff   — ข้อมูลมีวันหมดอายุ
3. Context Window     — ไม่สามารถอ่านทั้ง codebase
4. Private Knowledge  — ไม่รู้จัก internal code
5. Overconfidence     — ไม่รู้ว่าตัวเองไม่รู้
```

### RAG: The Solution

```
Your Codebase                                 LLM
──────────────    RAG Pipeline    ─────────────────────
  .py files   ──>  Index  ──>    Relevant    ──>  Accurate
  .md files   ──> (Vector   ──>  Context     ──>  Answer
  .yaml files ──>   DB)    ──>  Injection    ──>  with Source
```

### Next Session: Prompt Engineering

ก่อนสร้าง RAG pipeline เต็มๆ ต้องเรียน **Prompt Engineering** ก่อน:
- เขียน prompt ให้ได้ผลดีขึ้น
- บังคับ output format (JSON)
- Chain-of-Thought สำหรับ code reasoning

**Key Message:** เข้าใจข้อจำกัด LLM แล้ว → RAG คือทางออกที่ elegant — Sessions ต่อไปเราสร้างมันจริงๆ

---

*Deck 1 of 2 — Session 03: LLM Limitations*
