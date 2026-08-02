# Session 04 — Prompt Engineering: ศิลปะแห่งการสื่อสารกับ LLM

> **Module 2: Prompt Engineering** | ครั้งที่ 4 จาก 14 | 3 ชั่วโมง

---

## เป้าหมายการเรียนรู้ (Learning Objectives)

เมื่อจบ Session นี้ นักศึกษาจะสามารถ:

1. **เขียน prompt ในรูปแบบ Zero-shot, Few-shot, Chain-of-Thought ได้** และรู้ว่าเมื่อไหรควรใช้แบบไหน
2. **วัดและเปรียบเทียบคุณภาพ prompt ต่างๆ ได้** ด้วย structured A/B testing
3. **สร้าง PromptTemplate function รับตัวแปรได้** เพื่อ reuse ใน RAG pipeline

---

## ตารางเวลา (Schedule Overview)

| ช่วง | เวลา (นาที) | หัวข้อ | รูปแบบ |
|------|------------|--------|--------|
| 1 | 30 | Theory: Prompt Anatomy — 4 ส่วนสำคัญ | บรรยาย |
| 2 | 60 | Workshop: Zero-shot vs Few-shot vs CoT A/B test | Hands-on |
| 3 | 60 | Workshop: System prompt, Output formatting (JSON) | Hands-on |
| 4 | 30 | Workshop: สร้าง reusable PromptTemplate | Hands-on |

**รวม:** 180 นาที (3 ชั่วโมง)

---

## ช่วง 1 — Theory: Prompt Anatomy (30 นาที)

### 1.1 ทำไม Prompt Engineering สำคัญ?

```
Input (Prompt)          Processing          Output
──────────────    ─────────────────    ──────────────
Garbage in   ──>  LLM (same model) ──> Garbage out
Good prompt  ──>  LLM (same model) ──> Useful answer
```

**ตัวอย่าง: prompt แย่ vs ดี**

```python
# PROMPT แย่:
"explain this code"
# LLM ตอบอย่างไรก็ได้ — ยาวสั้นก็ได้ ภาษาไหนก็ได้

# PROMPT ดี:
"""
You are a Python expert who explains code clearly.

Analyze the following Python function and provide:
1. Purpose (1 sentence)
2. Parameters with types
3. Return value with type
4. One usage example

Format your response as JSON.

Function to analyze:
def fibonacci(n: int) -> list:
    if n <= 0: return []
    if n == 1: return [0]
    fib = [0, 1]
    while len(fib) < n:
        fib.append(fib[-1] + fib[-2])
    return fib
"""
# LLM ตอบ JSON ที่ structured และ useful
```

---

### 1.2 Prompt Anatomy: 4 ส่วนสำคัญ

**ส่วนที่ 1: Instruction (บอกว่าต้องการอะไร)**

```
Analyze the Python function below.
Identify any potential bugs.
```

**ส่วนที่ 2: Context (ให้ข้อมูลที่จำเป็น)**

```
This function is used in a production payment system.
It processes credit card transactions.
```

**ส่วนที่ 3: Examples (Few-shot — แสดงตัวอย่าง input/output)**

```
Example input:  def add(a, b): return a + b
Example output: {"purpose": "adds two numbers", "bugs": [], "severity": "none"}
```

**ส่วนที่ 4: Format Specification (บอก format ที่ต้องการ)**

```
Respond ONLY with valid JSON. No prose. No markdown.
Format: {"purpose": "...", "bugs": [...], "severity": "low/medium/high"}
```

**รวมกัน — Prompt ที่สมบูรณ์:**

```python
full_prompt = """
[INSTRUCTION]
Analyze the Python function below and identify potential bugs.

[CONTEXT]
This function is used in a production payment system that processes 
credit card transactions. Security and correctness are critical.

[EXAMPLE]
Input function:
def divide(a, b):
    return a / b

Output:
{"purpose": "divides two numbers", "bugs": ["division by zero when b=0"], "severity": "high"}

[FORMAT]
Respond ONLY with valid JSON. No explanation outside JSON.
Format: {"purpose": "...", "bugs": [...], "severity": "low/medium/high/critical"}

[TASK]
Analyze this function:
def process_payment(amount, card_number):
    if amount > 0:
        charge_card(card_number, amount)
        return True
"""
```

---

### 1.3 Zero-shot Prompting

**นิยาม:** ถาม LLM โดยไม่ให้ตัวอย่าง — ต้องอาศัยความรู้ที่ LLM มีใน training data

**เมื่อไหรได้ผล:**
- งานที่ LLM มีความรู้มากพอ (common patterns)
- ต้องการคำตอบแบบ open-ended
- งานง่ายๆ ที่ไม่ต้องการ specific format

**เมื่อไหรไม่ได้ผล:**
- ต้องการ output format ที่เฉพาะเจาะจงมาก
- LLM ต้องเข้าใจ convention ที่ผิดปกติ
- งานที่ต้องการความสม่ำเสมอสูง

```python
# Zero-shot
prompt = "What is a binary search tree? Explain briefly."
response = llm.invoke(prompt)
```

---

### 1.4 Few-shot Prompting

**นิยาม:** ให้ตัวอย่าง input-output pattern 2-5 ตัวอย่างก่อนถามจริง

**เมื่อไหรได้ผล:**
- ต้องการ output format ที่เฉพาะเจาะจง
- LLM ต้องเรียนรู้ pattern จาก domain เฉพาะ
- ต้องการความสม่ำเสมอใน response style

```python
# Few-shot
prompt = """
Classify Python code complexity. Answer: simple/moderate/complex

Code: x = 1 + 1
Classification: simple

Code: result = [x**2 for x in range(100) if x % 2 == 0]
Classification: moderate

Code: {user_code}
Classification:"""
```

**ข้อดี:** LLM เข้าใจ pattern จากตัวอย่าง — ไม่ต้องอธิบายยาว

---

### 1.5 Chain-of-Thought (CoT) Prompting

**นิยาม:** กระตุ้นให้ LLM "คิดก่อนตอบ" โดยแสดง reasoning step-by-step

**วิธีใช้:**

```python
# แบบที่ 1: Zero-shot CoT
prompt = "Debug this code. Think step by step.\n\n{code}"

# แบบที่ 2: Few-shot CoT (ให้ตัวอย่าง reasoning ด้วย)
prompt = """
Debug this code. Show your reasoning.

Example:
Code: def sum_list(lst): return sum(lst)
Analysis: 
  Step 1: Function takes a list argument
  Step 2: Uses built-in sum() - no custom logic needed
  Step 3: Works correctly for numbers, fails for strings
Result: Minor issue - no type checking

Now analyze: {user_code}
Analysis:"""
```

**ทำไม CoT ช่วย:**
- บังคับให้ LLM ประมวลผลหลายขั้นตอน
- ลด hallucination ในงานที่ต้องใช้ logic
- ทำให้ trace reasoning ได้ง่ายกว่า
- มีประสิทธิภาพสูงกับงาน debugging และ analysis

---

### 1.6 วัดผล Prompt อย่างไร?

**Metrics สำหรับ Coding Tasks:**

```python
# 1. Correctness: Code รันได้และผลถูกต้องหรือไม่?
def evaluate_correctness(code_response: str) -> bool:
    # ลอง execute code
    ...

# 2. Format compliance: ตอบตาม format ที่ระบุหรือไม่?
import json
def evaluate_json_format(response: str) -> bool:
    try:
        json.loads(response)
        return True
    except json.JSONDecodeError:
        return False

# 3. Completeness: ครอบคลุม requirements ทั้งหมดหรือไม่?
def evaluate_completeness(response: str, requirements: list) -> float:
    covered = sum(1 for req in requirements if req.lower() in response.lower())
    return covered / len(requirements)
```

---

## ช่วง 2 — Workshop: Zero-shot vs Few-shot vs CoT (60 นาที)

### Setup

```powershell
# Windows PowerShell
uv init session_04_workshop
cd session_04_workshop
uv add langchain-ollama langchain-core langchain-community
```

---

### Step 2.1: A/B Testing Framework

สร้างไฟล์ `ab_test_setup.py`:

```python
# ─── A/B Test Framework ───
# วัตถุประสงค์: เปรียบเทียบ prompt variants อย่างเป็นระบบ

from langchain_ollama import OllamaLLM
from langchain_core.prompts import PromptTemplate

llm = OllamaLLM(model="qwen2.5-coder:7b", temperature=0)

# Task: analyze Python function และ output structured info
test_function = """
def calculate_discount(price: float, user_tier: str) -> float:
    tiers = {'gold': 0.2, 'silver': 0.1, 'bronze': 0.05}
    discount = tiers.get(user_tier, 0)
    return price * (1 - discount)
"""

# Variant A: Zero-shot
prompt_a = PromptTemplate.from_template(
    "Analyze this Python function:\n{code}\n"
    "Provide: purpose, parameters, return value."
)

# Variant B: Few-shot  
prompt_b = PromptTemplate.from_template("""
Analyze Python functions in this format:

Function: def add(a, b): return a + b
Analysis: Purpose: adds two numbers | Params: a(number), b(number) | Returns: number

Function: def greet(name): return f"Hello, {{name}}!"
Analysis: Purpose: creates greeting string | Params: name(str) | Returns: str

Function: {code}
Analysis:""")

# Variant C: Chain-of-Thought
prompt_c = PromptTemplate.from_template("""
Analyze this Python function step by step:

Function: {code}

Step 1 - What does this function do? (purpose)
Step 2 - What are the input parameters and their types?
Step 3 - What does it return?
Step 4 - Are there any potential issues?

Final Answer:""")

# รัน A/B test
for name, prompt in [("Zero-shot", prompt_a), ("Few-shot", prompt_b), ("CoT", prompt_c)]:
    result = (prompt | llm).invoke({"code": test_function})
    print(f"\n{'='*50}")
    print(f"Variant: {name}")
    print(f"{'='*50}")
    print(result)
```

```powershell
uv run python ab_test_setup.py
```

---

### Step 2.2: ทดสอบ Debugging Task

```python
# ─── debug_prompt_test.py ───
# วัตถุประสงค์: เปรียบเทียบ prompt สำหรับ debugging task

from langchain_ollama import OllamaLLM
from langchain_core.prompts import PromptTemplate

llm = OllamaLLM(model="qwen2.5-coder:7b", temperature=0)

buggy_code = """
def find_average(numbers):
    total = 0
    for num in numbers:
        total = total + num
    average = total / len(numbers)
    return average

# Bug: crashes when numbers = []
"""

# ─── Prompt A: Direct (Zero-shot) ───
prompt_a = f"Find the bug in this code:\n{buggy_code}"
result_a = llm.invoke(prompt_a)
print("=== Zero-shot Debug ===")
print(result_a)

# ─── Prompt B: CoT debugging ───
prompt_b = f"""
Debug this Python function. Think step by step.

Code:
{buggy_code}

Analysis:
Step 1: What does the function try to do?
Step 2: What edge cases exist?
Step 3: What happens when input is empty list?
Step 4: What is the fix?

Fixed code:"""
result_b = llm.invoke(prompt_b)
print("\n=== CoT Debug ===")
print(result_b)
```

```powershell
uv run python debug_prompt_test.py
```

**สังเกต:** CoT มักให้ผลที่ดีกว่าสำหรับ debugging เพราะ LLM ต้องแสดง reasoning ก่อน

---

### Step 2.3: วัดผล Format Compliance

```python
# ─── measure_format.py ───
# วัตถุประสงค์: วัดว่า prompt ใด output ตาม format ได้ดีกว่า

from langchain_ollama import OllamaLLM
import json

llm = OllamaLLM(model="qwen2.5-coder:7b", temperature=0)

code_sample = "def multiply(a, b): return a * b"

# ─── Prompt ที่ระบุ format อย่างชัดเจน ───
strict_prompt = f"""
Analyze this Python function and respond ONLY with valid JSON.
No explanation, no markdown, just JSON.

Required format:
{{"function_name": "...", "purpose": "...", "params": ["..."], "returns": "..."}}

Function: {code_sample}

JSON:"""

result = llm.invoke(strict_prompt)
print("Response:")
print(result)
print()

# วัด compliance
try:
    # ลอง parse JSON
    cleaned = result.strip()
    # หา JSON object ใน response (บางครั้งมี text นำหน้า)
    start = cleaned.find('{')
    end = cleaned.rfind('}') + 1
    if start >= 0:
        json_str = cleaned[start:end]
        parsed = json.loads(json_str)
        print("JSON Parse: SUCCESS")
        print(f"Keys found: {list(parsed.keys())}")
    else:
        print("JSON Parse: FAILED (no JSON object found)")
except json.JSONDecodeError as e:
    print(f"JSON Parse: FAILED — {e}")
```

```powershell
uv run python measure_format.py
```

---

## ช่วง 3 — Workshop: System Prompt และ Output Formatting (60 นาที)

### Step 3.1: System Prompt ด้วย ChatPromptTemplate

```python
# ─── system_prompt_demo.py ───
# วัตถุประสงค์: ใช้ System Prompt เพื่อกำหนด role และ behavior

from langchain_ollama import OllamaLLM, ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import SystemMessage, HumanMessage

# วิธีที่ 1: ใช้ ChatOllama กับ ChatPromptTemplate
chat_llm = ChatOllama(model="qwen2.5-coder:7b", temperature=0)

template = ChatPromptTemplate.from_messages([
    ("system", 
     "You are a Python code reviewer. "
     "Always respond in Thai. "
     "Focus on: 1) bugs 2) performance 3) readability. "
     "Be concise - maximum 5 bullet points total."),
    ("human", "Review this code:\n\n```python\n{code}\n```")
])

chain = template | chat_llm
result = chain.invoke({"code": "def sum_squares(n): return sum([i**2 for i in range(n)])"})
print("=== System Prompt (Thai reviewer) ===")
print(result.content)
```

```powershell
uv run python system_prompt_demo.py
```

---

### Step 3.2: JSON Output Enforcement

```python
# ─── json_output_demo.py ───
# วัตถุประสงค์: บังคับให้ LLM output JSON เท่านั้น

from langchain_ollama import OllamaLLM
from langchain_core.prompts import PromptTemplate
import json

llm = OllamaLLM(model="qwen2.5-coder:7b", temperature=0)

# ─── Template ที่ enforce JSON ───
json_template = PromptTemplate.from_template("""
You are a code analyzer. You MUST respond with valid JSON only.
Do not include any text before or after the JSON object.

Analyze this Python function and output:
{{
  "function_name": "name of the function",
  "purpose": "one sentence description",
  "parameters": [
    {{"name": "param_name", "type": "type", "description": "what it is"}}
  ],
  "returns": {{"type": "return_type", "description": "what it returns"}},
  "complexity": "O(?)",
  "potential_issues": ["issue1", "issue2"]
}}

Function to analyze:
```python
{code}
```

JSON output:""")

# ─── Test กับหลาย functions ───
test_functions = [
    "def factorial(n): return 1 if n <= 1 else n * factorial(n-1)",
    "def binary_search(arr, target):\n    lo, hi = 0, len(arr)-1\n    while lo <= hi:\n        mid = (lo + hi) // 2\n        if arr[mid] == target: return mid\n        elif arr[mid] < target: lo = mid + 1\n        else: hi = mid - 1\n    return -1",
]

for code in test_functions:
    result = (json_template | llm).invoke({"code": code})
    print(f"Code: {code[:50]}...")
    
    # ลอง parse JSON
    try:
        start = result.find('{')
        end = result.rfind('}') + 1
        if start >= 0:
            parsed = json.loads(result[start:end])
            print(f"Function: {parsed.get('function_name', 'unknown')}")
            print(f"Purpose:  {parsed.get('purpose', 'unknown')}")
            print(f"Complexity: {parsed.get('complexity', 'unknown')}")
            print("JSON: VALID")
        else:
            print("JSON: NOT FOUND in response")
    except json.JSONDecodeError as e:
        print(f"JSON: INVALID — {e}")
    print()
```

```powershell
uv run python json_output_demo.py
```

---

### Step 3.3: Markdown Structured Output

```python
# ─── markdown_output_demo.py ───
# วัตถุประสงค์: บังคับ LLM output เป็น structured Markdown

from langchain_ollama import OllamaLLM
from langchain_core.prompts import PromptTemplate

llm = OllamaLLM(model="qwen2.5-coder:7b", temperature=0)

md_template = PromptTemplate.from_template("""
Generate documentation for this Python function in Markdown format.
Follow this EXACT template:

## `{{function_name}}`

**Purpose:** [one sentence]

**Parameters:**
| Name | Type | Description |
|------|------|-------------|
| ... | ... | ... |

**Returns:** `type` — description

**Example:**
```python
# Example usage
result = function_name(...)
```

**Notes:**
- [important notes]

---

Function to document:
```python
{code}
```""")

code = """
def chunk_list(lst: list, chunk_size: int) -> list:
    return [lst[i:i+chunk_size] for i in range(0, len(lst), chunk_size)]
"""

result = (md_template | llm).invoke({"code": code})
print(result)
```

```powershell
uv run python markdown_output_demo.py
```

---

## ช่วง 4 — Workshop: สร้าง Reusable PromptTemplate (30 นาที)

### Step 4.1: PromptTemplate Function Pattern

```python
# ─── prompt_library_demo.py ───
# วัตถุประสงค์: สร้าง reusable prompt functions ที่ใช้ใน RAG pipeline

from langchain_ollama import OllamaLLM
from langchain_core.prompts import PromptTemplate, ChatPromptTemplate

llm = OllamaLLM(model="qwen2.5-coder:7b", temperature=0)


# ─── Pattern 1: Simple PromptTemplate function ───
def create_code_explainer(language: str = "Python") -> PromptTemplate:
    """
    สร้าง PromptTemplate สำหรับอธิบาย code

    Args:
        language: programming language (default: Python)
    Returns:
        PromptTemplate ที่รับ {code} variable
    """
    return PromptTemplate.from_template(
        f"You are a {language} expert. "
        f"Explain the following {language} code in simple terms. "
        f"Target audience: beginners.\n\n"
        f"Code:\n{{code}}\n\n"
        f"Explanation:"
    )


# ─── Pattern 2: PromptTemplate กับหลาย variables ───
def create_bug_finder(
    language: str = "Python",
    severity_focus: str = "all"
) -> PromptTemplate:
    """
    สร้าง PromptTemplate สำหรับหา bugs

    Args:
        language: programming language
        severity_focus: 'all', 'critical', 'security'
    Returns:
        PromptTemplate ที่รับ {code} variable
    """
    severity_instruction = {
        "all": "List ALL bugs including minor ones.",
        "critical": "Focus ONLY on bugs that cause crashes or data loss.",
        "security": "Focus ONLY on security vulnerabilities."
    }.get(severity_focus, "List all bugs.")

    return PromptTemplate.from_template(
        f"You are a {language} code security expert.\n"
        f"{severity_instruction}\n\n"
        f"For each bug, provide:\n"
        f"- Line number (approximate)\n"
        f"- Bug description\n"
        f"- Severity: low/medium/high/critical\n"
        f"- Fix suggestion\n\n"
        f"Code to analyze:\n{{code}}\n\n"
        f"Bugs found:"
    )


# ─── ทดสอบ ───
test_code = """
def get_user(user_id):
    query = f"SELECT * FROM users WHERE id = {user_id}"
    return db.execute(query)
"""

print("=== Code Explanation ===")
explainer = create_code_explainer("Python")
chain = explainer | llm
print(chain.invoke({"code": test_code}))

print("\n=== Security Bug Finding ===")
bug_finder = create_bug_finder("Python", "security")
chain = bug_finder | llm
print(chain.invoke({"code": test_code}))
```

```powershell
uv run python prompt_library_demo.py
```

---

### Step 4.2: RAG-ready PromptTemplate

```python
# ─── rag_ready_template.py ───
# วัตถุประสงค์: สร้าง PromptTemplate ที่พร้อมสำหรับใช้ใน RAG pipeline

from langchain_core.prompts import PromptTemplate
from langchain_ollama import OllamaLLM

llm = OllamaLLM(model="qwen2.5-coder:7b", temperature=0)


def create_rag_code_qa_prompt() -> PromptTemplate:
    """
    สร้าง PromptTemplate สำหรับ RAG coding Q&A

    Template variables:
        {context}: relevant code chunks จาก vector DB
        {question}: user's question

    Returns:
        PromptTemplate พร้อมใช้ใน RAG chain
    """
    return PromptTemplate.from_template("""
You are a helpful coding assistant with access to the project codebase.

CONTEXT FROM CODEBASE:
{context}

---

QUESTION: {question}

INSTRUCTIONS:
- Answer based ONLY on the provided context
- If the context doesn't contain enough info, say "I need more context"
- Show relevant code snippets when applicable
- Be specific and concise

ANSWER:""")


# ─── ทดสอบ RAG-style prompt ───
rag_prompt = create_rag_code_qa_prompt()

# สมมติว่า RAG ดึง context มาให้
fake_context = """
# From: invoice_processor.py

class InvoiceProcessor:
    def transform_invoice_batch(self, invoices: list, output_format: str = "compressed_json") -> dict:
        \"\"\"
        Transform invoices. output_format: 'compressed_json', 'flat_csv', 'nested_xml'
        Returns: {'success_count': int, 'failed_ids': list, 'output_data': any}
        \"\"\"
        ...
"""

question = "How do I use InvoiceProcessor to process invoices as CSV?"

chain = rag_prompt | llm
result = chain.invoke({"context": fake_context, "question": question})
print("=== RAG-style Answer ===")
print(result)
print()
print("Note: This is how RAG will work in Session 08!")
print("RAG = auto-retrieve context + this prompt pattern")
```

```powershell
uv run python rag_ready_template.py
```

---

## สรุป: Prompt Engineering Cheat Sheet

### เลือก Prompt Type อย่างไร

```
คำถามง่าย + LLM รู้ดีอยู่แล้ว
     └──> Zero-shot (เร็ว ง่าย)

ต้องการ format เฉพาะ / pattern เฉพาะ
     └──> Few-shot (ให้ตัวอย่าง 2-5 ตัว)

งาน complex / debugging / reasoning
     └──> Chain-of-Thought ("think step by step")

ต้องการ structured JSON / Markdown output
     └──> Format specification + Few-shot

ต้องการ consistent behavior / role
     └──> System prompt (ใช้ ChatPromptTemplate)
```

### PromptTemplate ใน LangChain

```python
from langchain_core.prompts import PromptTemplate, ChatPromptTemplate

# Simple template (1 variable)
pt = PromptTemplate.from_template("Explain {topic} briefly.")

# Multi-variable template
pt2 = PromptTemplate(
    template="As a {role}, analyze {code} and output {format}.",
    input_variables=["role", "code", "format"]
)

# Chat template (with system/human/ai roles)
ct = ChatPromptTemplate.from_messages([
    ("system", "You are a {role}."),
    ("human", "{question}")
])

# ใช้ใน chain
chain = pt | llm
result = chain.invoke({"topic": "recursion"})
```

---

## Files ใน Session นี้

```
session_04_prompt_engineering/
├── README.md                                   <- ไฟล์นี้ (450+ บรรทัด)
├── slides/
│   ├── 01_prompt_fundamentals.md              <- Slides: Prompt Engineering ขั้นพื้นฐาน
│   └── 02_prompt_patterns.md                  <- Slides: Patterns ขั้นสูง
├── lab/
│   ├── lab_04_prompt_engineering.py           <- Lab starter (มี TODO, 150+ บรรทัด)
│   └── lab_04_prompt_engineering_solution.py  <- Solution สมบูรณ์ (200+ บรรทัด)
└── assignment/
    ├── hw_04_prompt_lab.md                    <- โจทย์การบ้าน (10 คะแนน)
    └── hw_04_rubric.md                        <- เกณฑ์การให้คะแนน 4 ระดับ
```

---

## Prerequisites

```powershell
# ตรวจสอบ Ollama
ollama list   # ควรเห็น qwen2.5-coder:7b

# ติดตั้ง dependencies
uv add langchain-ollama langchain-core langchain-community
```

---

## Quick Reference: LangChain Imports

```python
# ─── core imports ───
from langchain_ollama import OllamaLLM         # LLM สำหรับ completion
from langchain_ollama import ChatOllama         # Chat-style LLM
from langchain_core.prompts import PromptTemplate           # Basic template
from langchain_core.prompts import ChatPromptTemplate       # Chat template
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

# ─── chain syntax ───
chain = prompt | llm             # LCEL pipe syntax
result = chain.invoke({"var": "value"})
```

---

## ทรัพยากรเพิ่มเติม

- [LangChain PromptTemplate Docs](https://python.langchain.com/docs/concepts/prompt_templates/)
- [Prompt Engineering Guide](https://www.promptingguide.ai/)
- [Chain-of-Thought Prompting (Wei et al., 2022)](https://arxiv.org/abs/2201.11903)
- [Few-Shot Learners (Brown et al., 2020)](https://arxiv.org/abs/2005.14165)

---

---

## แนวคิดสำคัญที่พบในครั้งนี้

| แนวคิด | คำอธิบายสั้น |
|--------|-------------|
| Zero-shot Prompting | ถาม LLM โดยไม่มีตัวอย่าง เหมาะกับงานที่ LLM มีความรู้มากพอ |
| Few-shot Prompting | ให้ตัวอย่าง input-output 2-5 ตัวก่อนถามจริง ช่วยกำหนด pattern และ format |
| Chain-of-Thought (CoT) | กระตุ้นให้ LLM "คิดก่อนตอบ" step-by-step ลด hallucination ในงาน reasoning |
| Prompt Anatomy | Prompt ที่ดีมี 4 ส่วน: Instruction, Context, Examples, Format Specification |
| System Prompt | กำหนด role และ behavior ของ LLM ผ่าน ChatPromptTemplate |
| PromptTemplate | สร้าง reusable prompt ที่รับตัวแปร ใช้ซ้ำได้ทั่ว RAG pipeline |

---

## ปัญหาที่พบบ่อยและวิธีแก้

| ปัญหา | วิธีแก้ |
|-------|---------|
| LLM ไม่ตาม format JSON ที่ระบุ | ระบุ format อย่างชัดเจนใน system prompt และเพิ่ม few-shot example ของ JSON ที่ถูกต้อง |
| PromptTemplate แสดง KeyError เมื่อ invoke | ตรวจสอบว่า input_variables ตรงกับ `{placeholders}` ใน template ทุกตัว |
| LangChain LCEL chain ไม่ทำงาน | ตรวจสอบว่า import ถูกต้อง และใช้ syntax `chain = prompt | llm` แล้ว `chain.invoke({...})` |
| LLM ตอบยาวเกินต้องการ | เพิ่ม instruction เช่น "Be concise. Maximum 5 bullet points." ใน system prompt |

---

## Session ถัดไป

**Session 05 — Prompt Engineering for Code**
จะเรียนรู้:
- Prompts เฉพาะทางสำหรับ coding tasks: explain, debug, refactor, test generation, code review
- Structured output ด้วย JSON validation และ Pydantic
- สร้าง Prompt Library ที่ reuse ได้ตลอดหลักสูตร

---

## Checklist ก่อนออกจาก Session นี้

```
□ เขียน prompt แบบ Zero-shot, Few-shot, และ Chain-of-Thought ได้และรู้ว่าแต่ละแบบเหมาะกับงานอะไร
□ สร้าง PromptTemplate ที่รับตัวแปรได้และใช้ใน LCEL chain ได้
□ บังคับ LLM ให้ output JSON และ parse ผลลัพธ์ได้สำเร็จ
□ ทดสอบ A/B comparison ระหว่าง prompt variants และอธิบายความแตกต่างได้
□ สร้าง RAG-ready PromptTemplate ที่รับ {context} และ {question} พร้อมใช้ใน Session 08
```

*Session 04 of 14 — Local RAG for Programming*
