# Session 03 — LLM Limitations: เข้าใจข้อจำกัดและแรงจูงใจสู่ RAG

> **Module 1: Foundation & LLM** | ครั้งที่ 3 จาก 14 | 3 ชั่วโมง

---

## เป้าหมายการเรียนรู้ (Learning Objectives)

เมื่อจบ Session นี้ นักศึกษาจะสามารถ:

1. **ระบุข้อจำกัดของ LLM ได้อย่างน้อย 5 ประเภท** พร้อมตัวอย่างจริงที่ทดสอบได้
2. **ทดสอบ hallucination และ outdated knowledge ได้จริง** ผ่าน code experiment
3. **อธิบายได้ว่าทำไม RAG จึงแก้ปัญหาเหล่านี้ได้** และ RAG มีข้อจำกัดอะไรบ้าง

---

## ตารางเวลา (Schedule Overview)

| ช่วง | เวลา (นาที) | หัวข้อ | รูปแบบ |
|------|------------|--------|--------|
| 1 | 50 | Theory: LLM Limitations ทั้ง 5 ประเภท | บรรยาย + สาธิต |
| 2 | 60 | Workshop: ทดสอบ LLM กับ coding tasks จริง | Hands-on Lab |
| 3 | 50 | Workshop: ทดสอบข้อจำกัด Private Knowledge | Hands-on Lab |
| 4 | 20 | สรุป RAG Motivation + Preview Session 04 | อภิปราย |

**รวม:** 180 นาที (3 ชั่วโมง)

---

## ช่วงที่ 1 — Theory: 5 ประเภทข้อจำกัดของ LLM (50 นาที)

### 1.1 LLM รู้อะไร และไม่รู้อะไร?

LLM (Large Language Model) เรียนรู้จาก **text corpus** ที่เก็บรวบรวมจากอินเทอร์เน็ต, GitHub, Wikipedia, และแหล่งอื่นๆ จนถึงวันที่หนึ่ง (training cutoff date)

```
┌─────────────────────────────────────────────────────────────┐
│                    สิ่งที่ LLM รู้จัก                        │
│  - Public APIs (Python stdlib, popular libraries)           │
│  - Algorithms & data structures                             │
│  - General programming patterns                             │
│  - Documentation ที่มีออนไลน์ก่อน training cutoff          │
│  - Stack Overflow answers, GitHub public repos              │
├─────────────────────────────────────────────────────────────┤
│                    สิ่งที่ LLM ไม่รู้จัก                     │
│  - Codebase ภายในองค์กรของคุณ                              │
│  - APIs ที่ release หลัง training cutoff                    │
│  - Internal conventions และ architecture decisions          │
│  - Documents, tickets, และ comments ที่ private             │
│  - Runtime context (ค่า variable ปัจจุบัน)                 │
│  - ข้อมูลที่ไม่เคยถูก publish ออนไลน์                       │
└─────────────────────────────────────────────────────────────┘
```

สิ่งสำคัญที่ต้องเข้าใจ: **LLM ไม่ใช่ search engine** และไม่ได้ "lookup" ข้อมูลจริง — มันเพียงแค่ predict token ถัดไปโดยอิงจากสิ่งที่เคย train มา

---

### 1.2 ข้อจำกัดประเภทที่ 1: Hallucination

**นิยาม:** LLM สร้างข้อมูลที่ดูน่าเชื่อถือแต่ไม่เป็นความจริง โดยเฉพาะอย่างยิ่งใน code context

**ตัวอย่างจริงที่เกิดขึ้นบ่อย:**

```python
# ถาม LLM: "How to use pandas read_parquet with engine='fastparquet2'?"
# LLM อาจตอบ:

import pandas as pd
df = pd.read_parquet('data.parquet', engine='fastparquet2')

# ปัญหา: 'fastparquet2' ไม่มีอยู่จริง!
# LLM แต่งชื่อขึ้นมาจากที่รู้จัก 'fastparquet'
```

```python
# อีกตัวอย่าง: ถาม LLM เรื่อง numpy function
# Q: "How to use np.string_to_array() function?"
# LLM อาจตอบ:

import numpy as np
arr = np.string_to_array("hello world", dtype=np.float32)
# Function นี้ไม่มีใน numpy!
```

**ทำไม Hallucination เกิดขึ้น:**
- LLM predict token ถัดไปโดยใช้ probability — ไม่มีกลไก "lookup จริง"
- เมื่อไม่มีข้อมูล LLM จะ "interpolate" จากสิ่งที่คล้ายกัน
- ยิ่ง prompt มีความเฉพาะเจาะจงสูง โอกาส hallucinate ยิ่งมาก
- LLM ถูก train ให้ตอบ — ไม่ถูก train ให้บอกว่า "ไม่รู้"

**ผลกระทบต่อ coding:**
- แต่ API ที่ไม่มีอยู่จริง
- ใส่ parameter ผิดใน function
- เขียน import ที่ library version ไม่รองรับ
- อ้างอิง function ที่ถูก deprecate ไปแล้ว
- สร้าง code ที่ดูถูกแต่ run ไม่ได้

---

### 1.3 ข้อจำกัดประเภทที่ 2: Knowledge Cutoff

**นิยาม:** LLM มี training data จนถึงวันที่หนึ่ง — ข้อมูลหลังจากนั้นไม่มีใน model เลย

```
Training Cutoff
     |
     v
─────+──────────────────────────────────────────────────> เวลา
     |
  รู้จัก                                              ไม่รู้จัก
(In training)                                      (After cutoff)
     |                    ช่องว่าง                        |
     +── Python 3.11 ──────────────────────────────────── Python 3.13
     +── LangChain 0.1 ───────────────────────────────── LangChain 0.3
     +── qwen2.5 release ─────────────────────────────── version ใหม่
     +── Security patches ──────────────────────────────── ล่าสุด
```

**ตัวอย่างใน coding:**

```powershell
# เปิด PowerShell แล้วทดสอบ:
# ถาม LLM: "What are the new features in Python 3.13?"
# สังเกตว่า LLM ตอบถูกหรือผิดโดยเทียบกับ:
# https://docs.python.org/3.13/whatsnew/3.13.html
```

**ผลกระทบ:**
- API ที่แนะนำอาจถูก deprecate แล้ว
- Best practices อาจเปลี่ยนไปแล้ว
- Security patches ที่ LLM ไม่รู้จัก
- Library syntax อาจเปลี่ยนแล้ว (breaking changes)
- Framework versions ที่ LLM แนะนำอาจ outdated

---

### 1.4 ข้อจำกัดประเภทที่ 3: Context Window Limit

**นิยาม:** LLM รับ input ได้จำนวน token จำกัด — ไม่สามารถ "อ่าน" codebase ทั้งหมดพร้อมกัน

**การเปรียบเทียบขนาด:**

```
Token count comparison:
  4,096 tokens  ≈  200-300 บรรทัด code
  8,192 tokens  ≈  400-600 บรรทัด code
  32,000 tokens ≈  1,500-2,500 บรรทัด code
  128,000 tokens ≈ 6,000-10,000 บรรทัด code

โครงการ Real-world:
  Small project  ≈    5,000-20,000 บรรทัด
  Medium project ≈   50,000-200,000 บรรทัด
  Large project  ≈ 1,000,000+ บรรทัด (เช่น Linux kernel)
```

**ปัญหาใน practice:**

```python
# ถ้าคุณ paste codebase ทั้งหมดใน prompt:
# 1. อาจเกิน context limit -> error หรือ truncation
# 2. LLM "ลืม" ส่วนต้นเมื่อประมวลผลส่วนท้าย (attention dilution)
# 3. ค่าใช้จ่าย/เวลา ประมวลผลเพิ่มขึ้น quadratically
# 4. "Lost in the middle" problem: LLM มองข้ามข้อมูลกลาง context
```

**ทดสอบ token estimation:**

```powershell
# Windows PowerShell
uv run python -c "
def estimate_tokens(text):
    # Rough estimate: ~4 characters per token
    return len(text) // 4

# ทดสอบขนาดต่างๆ
for n_lines in [50, 100, 200, 500, 1000]:
    code = 'def function(x):\n    return x * 2\n\n' * n_lines
    tokens = estimate_tokens(code)
    print(f'{n_lines:5d} lines ~= {tokens:7,d} tokens')
"
```

---

### 1.5 ข้อจำกัดประเภทที่ 4: Private Knowledge Problem

**นิยาม:** LLM ไม่รู้จักโค้ดที่เขียนเอง, ไฟล์ config, internal API, หรือ documentation ภายในองค์กร เพราะสิ่งเหล่านี้ไม่เคยอยู่ใน training data

**ตัวอย่าง:**

```python
# สมมติคุณมี internal library ในองค์กร:
# mycompany/data_pipeline.py

class DataPipeline:
    def process_with_custom_validator(self, schema_id: str) -> bool:
        """
        ใช้ internal schema registry ที่ URL: internal.company.com/schemas
        ไม่มีอยู่ใน training data ของ LLM
        """
        ...

# ถาม LLM: "How do I use DataPipeline.process_with_custom_validator?"
# LLM ไม่รู้จัก -> hallucinate หรือบอกว่าไม่รู้
```

**กรณีที่เจอบ่อย:**
- Internal SDK ขององค์กร
- Custom framework ที่ทีมสร้างเอง
- Configuration files (`.yaml`, `.env`, `config.toml`) ที่ LLM ไม่เคยเห็น
- Business logic ที่เฉพาะเจาะจงกับ domain
- Database schemas และ API endpoints ขององค์กร
- README และ Wiki ภายในที่ไม่ public

---

### 1.6 ข้อจำกัดประเภทที่ 5: The "Confident but Wrong" Problem

**นิยาม:** LLM ตอบด้วย confidence สูงแม้จะผิด — ไม่มีกลไก "ไม่รู้" ที่ชัดเจน

```python
# ถาม: "Does Python's list.sort() use TimSort or QuickSort?"
# LLM ตอบ: "Python's list.sort() uses QuickSort, which provides..."
# ความจริง: ใช้ TimSort ซึ่ง guarantee O(n log n) worst case
# LLM ตอบผิด แต่ตอบด้วยความมั่นใจสูงมาก

# อีกตัวอย่าง:
# ถาม: "What's the default timeout in requests library?"
# LLM ตอบ: "The default timeout is 30 seconds."
# ความจริง: requests ไม่มี default timeout (None = ไม่มี timeout!)
# นี่เป็น security issue ที่ LLM บอกผิด
```

**วิธีสังเกต Overconfidence ใน LLM Response:**
- ตอบโดยไม่มี caveat ("I'm not sure but...")
- ไม่ขอ clarification เพิ่มเติม
- ให้ตัวเลขที่เฉพาะเจาะจงมากโดยไม่มีแหล่งอ้างอิง
- อ้างอิง "documentation" โดยไม่ระบุ URL ที่ตรวจสอบได้
- บอกว่า "always" หรือ "never" โดยไม่มีเงื่อนไข

---

## ช่วงที่ 2 — Workshop: ทดสอบ LLM กับ Coding Tasks จริง (60 นาที)

### Setup ก่อนเริ่ม

```powershell
# Windows PowerShell
# ตรวจสอบ Ollama ทำงานอยู่
ollama list
# ควรเห็น: qwen2.5-coder:7b

# ถ้ายังไม่มี ให้ pull:
ollama pull qwen2.5-coder:7b

# สร้าง working directory
mkdir session_03_workshop
cd session_03_workshop
uv init .
uv add langchain-ollama langchain-core langchain-community
```

---

### Step 2.1: Basic Coding Task (LLM ทำได้ดี)

เรามาทดสอบก่อนว่า LLM เก่งอะไรจริงๆ

```python
# ─── test_basic_task.py ───
# วัตถุประสงค์: ทดสอบว่า LLM เขียน code พื้นฐานได้ดีแค่ไหน

from langchain_ollama import OllamaLLM
from langchain_core.prompts import PromptTemplate

# สร้าง LLM instance
llm = OllamaLLM(model="qwen2.5-coder:7b")

# Task 1: เขียน function ง่ายๆ
prompt1 = PromptTemplate.from_template(
    "Write a Python function that takes a list of integers "
    "and returns the top-3 most frequent elements. "
    "Show only the function code, no explanation."
)
result1 = (prompt1 | llm).invoke({})
print("=== Task 1: Top-3 Frequent ===")
print(result1)
print()

# Task 2: เขียน class
prompt2 = PromptTemplate.from_template(
    "Write a Python class Stack with push, pop, peek, and is_empty methods. "
    "Include type hints and docstrings. Code only."
)
result2 = (prompt2 | llm).invoke({})
print("=== Task 2: Stack Class ===")
print(result2)
```

```powershell
uv run python test_basic_task.py
```

**สังเกต:** LLM ทำงานได้ดีมากในงานเหล่านี้ เพราะเป็น pattern ที่พบบ่อยใน training data

---

### Step 2.2: ทดสอบ Hallucination

```python
# ─── test_hallucination.py ───
# วัตถุประสงค์: ดูว่า LLM สร้าง API ปลอมหรือไม่

from langchain_ollama import OllamaLLM

llm = OllamaLLM(model="qwen2.5-coder:7b")

# ทดสอบ 1: ถาม library ที่ไม่มีจริง
print("=== Test 1: Fake Library ===")
test1 = llm.invoke(
    "Show me how to use the mycompany_internal_sdk version 5.2 "
    "function process_data_with_ai_enhancement(). "
    "Give me a complete code example with all parameters."
)
print(test1)
print()

# ทดสอบ 2: ถาม method ที่ไม่มีใน pandas
print("=== Test 2: Fake pandas method ===")
test2 = llm.invoke(
    "How do I use pandas.DataFrame.smart_fillna() method? "
    "Show a complete example with the intelligence_level parameter."
)
print(test2)
print()

# ทดสอบ 3: ถาม Python built-in ที่ไม่มี
print("=== Test 3: Fake Python built-in ===")
test3 = llm.invoke(
    "Show me how to use Python's built-in optimize_list() function "
    "to automatically sort and deduplicate a list."
)
print(test3)
```

```powershell
uv run python test_hallucination.py
```

**คำถามที่ต้องตอบหลังทดสอบ:**
- LLM บอกว่าไม่รู้จัก หรือ hallucinate code ที่ดูสมจริง?
- มี confidence ในการตอบสูงหรือต่ำ?
- ถ้า hallucinate — code นั้น run ได้จริงหรือไม่?
- LLM ใช้ caveat ("I'm not sure", "I couldn't verify") หรือไม่?

---

### Step 2.3: ทดสอบ Knowledge Cutoff

```python
# ─── test_knowledge_cutoff.py ───
# วัตถุประสงค์: ทดสอบว่า LLM รู้จัก feature ล่าสุดแค่ไหน

from langchain_ollama import OllamaLLM

llm = OllamaLLM(model="qwen2.5-coder:7b")

queries = [
    ("Python 3.13 features",
     "What are the new features in Python 3.13? List all major ones."),
    ("LangChain 0.3 syntax",
     "Show me how to use LangChain 0.3 new LCEL streaming syntax."),
    ("Qwen2.5-coder info",
     "What are the capabilities of qwen2.5-coder:7b model?"),
]

for name, query in queries:
    print(f"=== {name} ===")
    print(f"Q: {query}")
    response = llm.invoke(query)
    print(f"A: {response}")
    print()
    print("Verify at:")
    if "Python" in name:
        print("  https://docs.python.org/3.13/whatsnew/3.13.html")
    print()
```

```powershell
uv run python test_knowledge_cutoff.py
```

**วิธีตรวจสอบความถูกต้อง:**

```powershell
# เปิด browser ไปที่แหล่งอ้างอิงจริง:
# Python 3.13: https://docs.python.org/3.13/whatsnew/3.13.html
# LangChain: https://python.langchain.com/docs/
# เปรียบเทียบกับสิ่งที่ LLM ตอบ
```

---

### Step 2.4: ทดสอบ Coding Advice Accuracy

```python
# ─── test_coding_advice.py ───
# วัตถุประสงค์: ทดสอบว่า LLM ให้คำแนะนำที่ถูกต้องหรือไม่

from langchain_ollama import OllamaLLM

llm = OllamaLLM(model="qwen2.5-coder:7b")

# คำถามที่มีคำตอบถูกต้องที่ตรวจสอบได้
questions = [
    "What sorting algorithm does Python's list.sort() use?",
    "What is the default timeout value in the Python requests library?",
    "Is Python's GIL removed in Python 3.13?",
    "What is the time complexity of dict lookup in Python?",
]

for q in questions:
    print(f"Q: {q}")
    print(f"A: {llm.invoke(q)}")
    print()
```

```powershell
uv run python test_coding_advice.py
```

**เฉลย (ตรวจสอบ LLM):**
- Python uses **Timsort** (hybrid merge sort + insertion sort)
- requests default timeout = **None** (no timeout! — security risk)
- GIL: Python 3.13 มี experimental "free-threaded" mode (ต้องเปิดเอง)
- dict lookup: **O(1)** average case

---

## ช่วงที่ 3 — Workshop: ทดสอบ Private Knowledge และ Context (50 นาที)

### Step 3.1: สร้าง Fake Private Codebase

```python
# ─── create_fake_codebase.py ───
# วัตถุประสงค์: สร้าง "codebase" สมมติที่ LLM ไม่รู้จัก

# fake_company_sdk.py
fake_code = '''
"""
MyCompany Internal Data SDK v3.1
ไม่มีอยู่บน PyPI หรือ GitHub
"""

class InvoiceProcessor:
    """Process invoices using company schema validator."""
    
    def __init__(self, schema_version: str = "v3.1"):
        self.schema_version = schema_version
        self._validator = None
    
    def transform_invoice_batch(
        self, 
        invoices: list, 
        output_format: str = "compressed_json"
    ) -> dict:
        """
        Transform a batch of invoices to company standard format.
        
        Args:
            invoices: list of raw invoice dicts
            output_format: one of 'compressed_json', 'flat_csv', 'nested_xml'
        
        Returns:
            dict with keys: 'success_count', 'failed_ids', 'output_data'
        """
        ...
    
    def validate_schema(self, data: dict, strict: bool = False) -> bool:
        """
        Validate against internal schema registry at internal.company.com/schemas.
        strict=True raises InternalSchemaError on any warning.
        """
        ...

def connect_to_datalake(
    environment: str = "staging",
    region: str = "ap-southeast-1"
) -> "DataLakeConnection":
    """
    Connect to company data lake.
    environment: 'dev', 'staging', 'prod'
    Reads credentials from COMPANY_DL_TOKEN env var.
    """
    ...
'''

with open("fake_company_sdk.py", "w", encoding="utf-8") as f:
    f.write(fake_code)

print("Created: fake_company_sdk.py")
print(f"Lines: {len(fake_code.splitlines())}")
```

```powershell
uv run python create_fake_codebase.py
```

---

### Step 3.2: ทดสอบ Private Knowledge

```python
# ─── test_private_knowledge.py ───
# วัตถุประสงค์: เปรียบเทียบ LLM response กับ/ไม่มี context

from langchain_ollama import OllamaLLM

llm = OllamaLLM(model="qwen2.5-coder:7b")

# อ่าน fake codebase
with open("fake_company_sdk.py", encoding="utf-8") as f:
    source_code = f.read()

question = (
    "How do I use InvoiceProcessor.transform_invoice_batch() to process "
    "a list of 3 invoices and get the result as flat CSV? "
    "Show me a complete example."
)

# ─── Test A: ไม่มี source code ───
print("=" * 60)
print("TEST A: Without source code (LLM ไม่รู้จัก)")
print("=" * 60)
response_a = llm.invoke(question)
print(response_a)
print()

# ─── Test B: มี source code ใน prompt ───
print("=" * 60)
print("TEST B: With source code in prompt (context injection)")
print("=" * 60)
augmented_prompt = f"""Here is the source code of our internal SDK:

```python
{source_code}
```

Based on this code, {question}"""

response_b = llm.invoke(augmented_prompt)
print(response_b)
```

```powershell
uv run python test_private_knowledge.py
```

**สังเกตความแตกต่างระหว่าง:**
- Response A: LLM ไม่รู้จัก → hallucinate หรือปฏิเสธ
- Response B: มี source code ใน prompt → ตอบได้ถูกต้องและตรงตาม spec

**นี่คือหัวใจของ RAG:** แทนที่จะ paste source code ทั้งหมด → ดึงเฉพาะ chunk ที่เกี่ยวข้อง

---

### Step 3.3: ทดสอบ Context Window Limit

```python
# ─── test_context_window.py ───
# วัตถุประสงค์: ทดสอบ LLM เมื่อ context ใหญ่มาก

from langchain_ollama import OllamaLLM

llm = OllamaLLM(model="qwen2.5-coder:7b")

# สร้าง fake large codebase
large_code_lines = []
for i in range(500):
    large_code_lines.extend([
        f"def process_item_{i:04d}(data: dict, config: dict) -> dict:",
        f'    """Process item type {i} with custom business logic."""',
        f"    result = {{key: val * {i} for key, val in data.items()}}",
        f"    return result",
        "",
    ])
large_code = "\n".join(large_code_lines)
with open("large_codebase.py", "w", encoding="utf-8") as f:
    f.write(large_code)

# นับขนาด
n_lines = len(large_code.splitlines())
n_chars = len(large_code)
n_tokens_est = n_chars // 4
print(f"Created large_codebase.py: {n_lines} lines, ~{n_tokens_est:,} tokens")
print()

lines = large_code.splitlines()

# ทดสอบ 1: Context เล็ก (100 บรรทัดแรก)
small_context = "\n".join(lines[:100])
print("=== Small Context (100 lines) ===")
r1 = llm.invoke(
    f"In this Python code:\n{small_context}\n\n"
    "What does process_item_0001 do? What parameters does it take?"
)
print(r1)
print()

# ทดสอบ 2: ถามเรื่อง function ที่อยู่ใน context
medium_context = "\n".join(lines[:200])
print("=== Medium Context (200 lines), asking about item near end ===")
r2 = llm.invoke(
    f"In this Python code:\n{medium_context}\n\n"
    "What does process_item_0035 do?"
)
print(r2)
print()

# ทดสอบ 3: Context ใหญ่ ถาม function ที่ไม่อยู่ใน context
large_context = "\n".join(lines[:500])
print("=== Ask about function NOT in provided context ===")
r3 = llm.invoke(
    f"In this Python code:\n{large_context[:4000]}\n\n"
    "What does process_item_0499 do?"
)
print(r3)
```

```powershell
uv run python test_context_window.py
```

**สังเกต "Lost in the Middle":**
- LLM มักตอบได้ดีสำหรับ function ที่อยู่ตอนต้นหรือตอนท้าย context
- Function ที่อยู่กลาง context อาจถูก "มองข้าม"
- RAG แก้ปัญหานี้โดยดึงเฉพาะ chunk ที่เกี่ยวข้อง ไม่ใช่ paste ทั้งหมด

---

## ช่วงที่ 4 — สรุป: ทำไม RAG แก้ปัญหาเหล่านี้ได้? (20 นาที)

### 4.1 ตารางสรุปปัญหาและวิธีแก้

| ข้อจำกัด | ปัญหา | RAG แก้อย่างไร |
|---------|-------|--------------|
| Hallucination | LLM แต่ง API ปลอม | ดึง doc จริงมาให้ก่อนตอบ |
| Knowledge Cutoff | API เก่า/ผิด | Index documents ใหม่ได้ตลอด |
| Private Knowledge | ไม่รู้จัก codebase เรา | Index codebase ของเราเองได้ |
| Context Window | Paste ทั้งไฟล์ไม่ได้ | ดึงเฉพาะ chunk ที่เกี่ยวข้อง |
| Overconfidence | ตอบผิดด้วยความมั่นใจ | มีหลักฐานอ้างอิงใน context |

### 4.2 RAG Architecture ขั้นพื้นฐาน

```
User Question: "How does transform_invoice_batch work?"
      |
      v
[Step 1: Embed question]
  question -> vector [0.23, -0.45, 0.78, ...]
      |
      v
[Step 2: Retrieve from Vector DB]
  FAISS -> top-3 most similar code chunks
  - InvoiceProcessor class definition
  - transform_invoice_batch docstring
  - Example usage from README
      |
      v relevant_chunks
[Step 3: Augment Prompt]
  prompt = """
  Context from codebase:
  {relevant_chunks}
  
  Question: {user_question}
  """
      |
      v
[Step 4: Generate Answer]
  LLM ตอบโดยอิงจาก context จริง -> คำตอบที่ถูกต้อง
```

### 4.3 ข้อจำกัดของ RAG (RAG ไม่ใช่ Silver Bullet)

RAG แก้ปัญหาได้มาก แต่ยังมีข้อจำกัด:

1. **Retrieval quality** — ถ้าดึง chunk ผิด LLM ก็ตอบผิด (GIGO: Garbage In, Garbage Out)
2. **Chunk boundaries** — context ที่ตัดออกมาอาจไม่ complete (ตัดกลาง function)
3. **Semantic search ไม่สมบูรณ์แบบ** — บางครั้ง embedding ไม่จับความหมายได้ถูกต้อง
4. **Latency เพิ่มขึ้น** — ต้อง embed query + search + augment ก่อนตอบ
5. **Index freshness** — ต้อง re-index เมื่อ code เปลี่ยน
6. **Chunking strategy สำคัญมาก** — ขนาด chunk ส่งผลต่อคุณภาพการดึง

### 4.4 Preview Session 04: Prompt Engineering

Session ถัดไปเราจะเรียน **ทักษะที่ทำให้ RAG ทำงานได้ดีขึ้น:**

- **Zero-shot vs Few-shot vs Chain-of-Thought** — เมื่อไหรใช้อะไร
- **Output formatting** — บังคับให้ LLM ตอบเป็น JSON
- **System prompts** — กำหนด role และ behavior ของ LLM
- **PromptTemplate** — สร้าง reusable prompt components

```python
# ตัวอย่าง: Prompt Engineering ที่ดีกว่า
from langchain_core.prompts import ChatPromptTemplate

# แทนที่จะถามแบบนี้:
# "explain this code"

# ถามแบบนี้แทน (structured + few-shot):
template = ChatPromptTemplate.from_messages([
    ("system", "You are a Python expert. Always explain in Thai. Output JSON only."),
    ("human", """Analyze this Python function:

```python
{code}
```

Output format: {{"purpose": "...", "params": [...], "returns": "...", "complexity": "O(...)"}}""")
])
# นี่คือ Prompt Engineering!
```

---

## Files ใน Session นี้

```
session_03_llm_limitations/
├── README.md                           <- ไฟล์นี้ (400+ บรรทัด)
├── slides/
│   ├── 01_llm_limitations.md          <- Slides: 5 ข้อจำกัด LLM (10+ slides)
│   └── 02_llm_for_code.md             <- Slides: LLM กับ Coding (8+ slides)
├── lab/
│   ├── lab_03_llm_testing.py          <- Lab starter (มี TODO, 120+ บรรทัด)
│   └── lab_03_llm_testing_solution.py <- Solution สมบูรณ์ (180+ บรรทัด)
└── assignment/
    ├── hw_03_limitations_analysis.md  <- โจทย์การบ้าน (10 คะแนน)
    └── hw_03_rubric.md                <- เกณฑ์การให้คะแนน 4 ระดับ
```

---

## Prerequisites

ก่อนเริ่ม session นี้ นักศึกษาควร:

- ผ่าน Session 01 (Setup) และ Session 02 (LLM Basics) แล้ว
- มี Ollama ติดตั้งและ pull model แล้ว:
  ```powershell
  ollama pull qwen2.5-coder:7b
  ollama pull nomic-embed-text
  ```
- มี Python project พร้อม dependencies:
  ```powershell
  uv init my_project
  cd my_project
  uv add langchain-ollama langchain-core langchain-community
  ```

---

## Quick Reference: คำสั่ง Windows

```powershell
# Run lab starter
uv run python lab\lab_03_llm_testing.py

# Run solution
uv run python lab\lab_03_llm_testing_solution.py

# Check Ollama status
ollama ps

# List available models
ollama list

# Add dependency
uv add langchain-ollama

# Check installed packages
uv pip list

# Start Ollama server (ถ้ายังไม่ได้ start)
ollama serve
```

---

## ทรัพยากรเพิ่มเติม

- [Ollama Documentation](https://ollama.ai/docs)
- [LangChain OllamaLLM Docs](https://python.langchain.com/docs/integrations/llms/ollama)
- [RAG Survey Paper (2023)](https://arxiv.org/abs/2312.10997)
- [Hallucination in LLMs Survey](https://arxiv.org/abs/2311.05232)
- [Python 3.13 What's New](https://docs.python.org/3.13/whatsnew/3.13.html)
- [Lost in the Middle Paper](https://arxiv.org/abs/2307.03172)

---

---

## แนวคิดสำคัญที่พบในครั้งนี้

| แนวคิด | คำอธิบายสั้น |
|--------|-------------|
| Hallucination | LLM สร้างข้อมูลที่ดูน่าเชื่อถือแต่ไม่เป็นความจริง เช่น แต่ง API ที่ไม่มีจริง |
| Knowledge Cutoff | LLM มี training data ถึงวันที่หนึ่ง — ข้อมูลหลังจากนั้นไม่มีใน model |
| Context Window Limit | LLM รับ input ได้จำนวน token จำกัด ไม่สามารถอ่าน codebase ทั้งหมดพร้อมกัน |
| Private Knowledge Problem | LLM ไม่รู้จัก codebase, internal API, หรือ docs ภายในองค์กรที่ไม่เคยอยู่ใน training data |
| Overconfidence | LLM ตอบด้วย confidence สูงแม้จะผิด ไม่มีกลไก "ไม่รู้" ที่ชัดเจน |
| RAG Motivation | RAG แก้ปัญหาด้านบนโดยดึง context จริงมาให้ LLM ก่อนตอบ แทนที่จะพึ่ง training data อย่างเดียว |

---

## ปัญหาที่พบบ่อยและวิธีแก้

| ปัญหา | วิธีแก้ |
|-------|---------|
| LLM ตอบ API ที่ไม่มีจริงด้วยความมั่นใจ | ทดสอบ code ที่ได้รับเสมอ อย่า copy-paste โดยไม่ run |
| Ollama ไม่ตอบสนองหรือช้ามาก | ตรวจสอบด้วย `ollama ps` และ `ollama serve` ว่า server ทำงานอยู่ |
| uv run ไม่เจอ package | ตรวจสอบว่า `uv add langchain-ollama` ทำในโฟลเดอร์ project ที่ถูกต้อง |
| Context ใหญ่เกินและ LLM ตอบผิด | ลดขนาด context หรือดึงเฉพาะ chunk ที่เกี่ยวข้อง (แนวทาง RAG) |
| JSON parse ล้มเหลวเมื่อพยายาม structured output | ใช้ `re.search(r'\{.*\}', response, re.DOTALL)` เพื่อ extract JSON จาก response |

---

## Session ถัดไป

**Session 04 — Prompt Engineering: ศิลปะแห่งการสื่อสารกับ LLM**
จะเรียนรู้:
- Zero-shot, Few-shot, Chain-of-Thought prompting
- Output formatting — บังคับ LLM ให้ตอบเป็น JSON
- System prompts — กำหนด role และ behavior ของ LLM
- PromptTemplate — สร้าง reusable prompt components สำหรับ RAG pipeline

---

## Checklist ก่อนออกจาก Session นี้

```
□ สามารถระบุข้อจำกัดของ LLM ได้อย่างน้อย 5 ประเภทพร้อมตัวอย่าง
□ ทดสอบ hallucination ผ่าน test_hallucination.py และสังเกตผลได้
□ เปรียบเทียบ LLM response แบบมี/ไม่มี context ใน test_private_knowledge.py
□ อธิบายได้ว่า RAG แก้ปัญหา hallucination, knowledge cutoff และ private knowledge อย่างไร
□ บันทึก session_03_workshop ไว้สำหรับใช้ใน sessions ถัดไป
```

*Session 03 of 14 — Local RAG for Programming*
