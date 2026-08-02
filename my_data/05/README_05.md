# Session 05 — Prompt Engineering for Code

> **Module 2: Prompt Engineering** | ครั้งที่ 5 จาก 14 | 3 ชั่วโมง

---

## เป้าหมายการเรียนรู้ (Learning Objectives)

เมื่อจบ session นี้ นักเรียนจะสามารถ:

1. **สร้าง prompt เฉพาะทางสำหรับ coding tasks แต่ละประเภทได้** — explain, debug, refactor, test generation, code review
2. **บังคับ LLM ให้ output เป็น structured JSON ได้อย่างน่าเชื่อถือ** — JSON format specification, validation, retry logic
3. **รวม prompts เป็น reusable library ได้** — Prompt Library Pattern ที่ใช้ซ้ำได้ตลอดหลักสูตร

---

## ตารางเวลา (Session Schedule) — รวม 180 นาที

| ช่วง | เวลา | หัวข้อ | รูปแบบ |
|------|------|--------|--------|
| 1 | 60 นาที | Workshop — Prompts สำหรับ explain/debug/refactor/test/review | Hands-on |
| 2 | 60 นาที | Workshop — Structured output: JSON, validation, error handling | Hands-on |
| 3 | 50 นาที | Workshop — สร้าง Prompt Library รวมทั้งหมด | Project |
| 4 | 10 นาที | สรุป + Demo ทั้ง Library | Demo |

---

## Prerequisites

- ผ่าน Session 04 (Prompt Engineering พื้นฐาน) แล้ว
- Ollama รัน `qwen2.5-coder:7b` อยู่
- มี Python environment พร้อม uv

```powershell
# ตรวจสอบ Ollama
ollama list

# ติดตั้ง dependencies
uv add langchain-ollama langchain-core langchain-community
```

---

## ช่วงที่ 1 (60 นาที) — Coding-Specific Prompts

### แนวคิดหลัก: Prompts สำหรับ Code Tasks ต้องการ Context พิเศษ

LLM ทั่วไปตอบคำถาม code ได้ แต่ถ้าเราออกแบบ prompt ที่ดี จะได้ output ที่:
- มี **structure** ที่คาดเดาได้
- มี **context** ที่เหมาะสม (ภาษา, framework, style guide)
- **actionable** — บอกได้ทันทีว่าต้องทำอะไร

### 1.1 Code Explanation Prompt

```python
# ─── Code Explanation Prompt ───
# วัตถุประสงค์: บังคับ LLM ให้อธิบาย code ตาม detail level ที่กำหนด

from langchain_ollama import ChatOllama
from langchain_core.messages import SystemMessage, HumanMessage

def explain_code(code: str, detail_level: str = "detailed") -> str:
    """
    อธิบาย code ตาม detail level
    
    Args:
        code: Python code ที่ต้องการอธิบาย
        detail_level: "brief" | "detailed" | "beginner"
    
    Returns:
        คำอธิบายจาก LLM
    """
    # ─── กำหนด system prompt ตาม detail level ───
    # วัตถุประสงค์: ปรับ persona และ output format ของ LLM
    detail_instructions = {
        "brief": "Explain in 2-3 sentences only. Focus on the main purpose.",
        "detailed": "Explain step by step. Cover: purpose, inputs/outputs, logic flow, edge cases.",
        "beginner": "Explain as if teaching a beginner. Use simple analogies. Avoid jargon."
    }
    
    system_prompt = f"""You are a senior Python developer and teacher.
{detail_instructions.get(detail_level, detail_instructions['detailed'])}
Always structure your explanation clearly."""

    llm = ChatOllama(model="qwen2.5-coder:7b", temperature=0.1)
    
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=f"Explain this code:\n\n```python\n{code}\n```")
    ]
    
    response = llm.invoke(messages)
    return response.content


# ─── ทดสอบ Code Explanation ───
# วัตถุประสงค์: ดูความแตกต่างระหว่าง detail levels
if __name__ == "__main__":
    sample_code = """
def fibonacci(n: int) -> list[int]:
    if n <= 0:
        return []
    elif n == 1:
        return [0]
    
    fib = [0, 1]
    while len(fib) < n:
        fib.append(fib[-1] + fib[-2])
    return fib
"""
    
    for level in ["brief", "detailed", "beginner"]:
        print(f"\n{'='*50}")
        print(f"Detail Level: {level.upper()}")
        print('='*50)
        result = explain_code(sample_code, level)
        print(result)
```

### 1.2 Bug Finding Prompt

```python
# ─── Bug Finding Prompt ───
# วัตถุประสงค์: บังคับ LLM ให้ output bugs เป็น JSON format ที่ parse ได้

import json
from langchain_ollama import ChatOllama
from langchain_core.messages import SystemMessage, HumanMessage

def find_bugs(code: str, language: str = "python") -> dict:
    """
    ค้นหา bugs ใน code
    
    Args:
        code: source code ที่ต้องการตรวจสอบ
        language: ภาษา programming
    
    Returns:
        dict: {"bugs": [{"line": int, "issue": str, "fix": str}], "severity": str}
    """
    # ─── System prompt สำหรับ bug finding ───
    # วัตถุประสงค์: กำหนด output format อย่างเข้มงวด
    system_prompt = """You are an expert code reviewer specializing in finding bugs.

IMPORTANT: You MUST respond with ONLY valid JSON. No markdown, no explanation outside JSON.

Output format:
{
  "bugs": [
    {
      "line": <line number as integer>,
      "issue": "<description of the bug>",
      "fix": "<how to fix it>"
    }
  ],
  "severity": "<critical|high|medium|low|none>",
  "summary": "<one sentence overall assessment>"
}

If no bugs found, return: {"bugs": [], "severity": "none", "summary": "No bugs found."}"""

    llm = ChatOllama(model="qwen2.5-coder:7b", temperature=0.0)
    
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=f"Find bugs in this {language} code:\n\n```{language}\n{code}\n```")
    ]
    
    response = llm.invoke(messages)
    
    # ─── Parse JSON output ───
    # วัตถุประสงค์: แปลง string response เป็น Python dict
    try:
        result = json.loads(response.content)
    except json.JSONDecodeError:
        # fallback: พยายาม extract JSON จาก response
        import re
        json_match = re.search(r'\{.*\}', response.content, re.DOTALL)
        if json_match:
            result = json.loads(json_match.group())
        else:
            result = {"bugs": [], "severity": "unknown", "summary": "Failed to parse response"}
    
    return result


# ─── ทดสอบ Bug Finding ───
buggy_code = """
def calculate_average(numbers):
    total = 0
    for n in numbers:
        total = total + n
    return total / len(numbers)  # Bug: division by zero if empty list

def get_user_data(user_id):
    users = {"1": "Alice", "2": "Bob"}
    return users[user_id]  # Bug: KeyError if user_id not found
"""

bugs = find_bugs(buggy_code)
print(json.dumps(bugs, indent=2, ensure_ascii=False))
```

### 1.3 Test Generation Prompt

```python
# ─── Test Generation Prompt ───
# วัตถุประสงค์: ให้ LLM สร้าง unit tests ที่รันได้จริง

def generate_tests(code: str, framework: str = "pytest") -> str:
    """
    สร้าง unit tests สำหรับ code ที่รับมา
    
    Args:
        code: Python function ที่ต้องการสร้าง tests
        framework: "pytest" | "unittest"
    
    Returns:
        str: test code ที่รันได้
    """
    # ─── กำหนด framework-specific instructions ───
    # วัตถุประสงค์: ปรับ style ของ test ตาม framework ที่ใช้
    framework_guide = {
        "pytest": """Use pytest framework.
- Use def test_<name>(): functions
- Use assert statements
- Include parametrize decorator for multiple test cases
- Test: happy path, edge cases, error cases""",
        
        "unittest": """Use unittest framework.
- Inherit from unittest.TestCase
- Use self.assertEqual, self.assertRaises, etc.
- Include setUp if needed
- Test: happy path, edge cases, error cases"""
    }
    
    system_prompt = f"""You are an expert Python test writer.
{framework_guide.get(framework, framework_guide['pytest'])}

Return ONLY the test code. No explanation. Include all imports."""

    llm = ChatOllama(model="qwen2.5-coder:7b", temperature=0.1)
    
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=f"Write tests for this code:\n\n```python\n{code}\n```")
    ]
    
    response = llm.invoke(messages)
    return response.content
```

### 1.4 Code Refactoring Prompt

```python
# ─── Code Refactoring Prompt ───
# วัตถุประสงค์: ขอ refactoring พร้อม explanation ว่าเปลี่ยนอะไร

def refactor_code(code: str, goal: str = "readability") -> dict:
    """
    Refactor code ตาม goal ที่กำหนด
    
    Args:
        code: Python code ที่ต้องการ refactor
        goal: "readability" | "performance" | "pythonic"
    
    Returns:
        dict: {"refactored_code": str, "changes": [str], "reasoning": str}
    """
    # ─── กำหนด goal-specific criteria ───
    goal_criteria = {
        "readability": "Focus on: clear variable names, docstrings, comments, shorter functions",
        "performance": "Focus on: algorithmic complexity, avoid repeated computation, use built-ins",
        "pythonic": "Focus on: list comprehensions, context managers, unpacking, idiomatic Python"
    }
    
    system_prompt = f"""You are a Python refactoring expert.
Goal: {goal_criteria.get(goal, goal_criteria['readability'])}

Respond with ONLY valid JSON:
{{
  "refactored_code": "<complete refactored code as string>",
  "changes": ["<change 1>", "<change 2>", ...],
  "reasoning": "<overall explanation>"
}}"""

    llm = ChatOllama(model="qwen2.5-coder:7b", temperature=0.1)
    
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=f"Refactor this code for {goal}:\n\n```python\n{code}\n```")
    ]
    
    response = llm.invoke(messages)
    
    try:
        return json.loads(response.content)
    except json.JSONDecodeError:
        import re
        json_match = re.search(r'\{.*\}', response.content, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())
        return {"refactored_code": code, "changes": [], "reasoning": "Parse error"}
```

---

## ช่วงที่ 2 (60 นาที) — Structured Output: JSON, Validation, Error Handling

### แนวคิดหลัก: ทำไม Structured Output ถึงสำคัญ

เมื่อ LLM เป็นส่วนหนึ่งของ pipeline:
- code ต้องการ **predictable output** ที่ parse ได้
- ถ้า LLM ตอบ free-form text → pipeline พัง
- Solution: บังคับ JSON format + validation + retry

### 2.1 JSON Format Specification

```python
# ─── JSON Format Specification Technique ───
# วัตถุประสงค์: เทคนิคต่างๆ ในการบังคับ JSON output

# Technique 1: ระบุ format ใน system prompt อย่างชัดเจน
SYSTEM_STRICT_JSON = """You are a code analysis API.
CRITICAL: Your response must be ONLY valid JSON. 
Do not include markdown code blocks.
Do not include any text outside the JSON object.

Required format:
{
  "result": "<string>",
  "confidence": <float between 0 and 1>,
  "metadata": {}
}"""

# Technique 2: ใช้ few-shot examples
SYSTEM_FEW_SHOT = """You analyze code and respond in JSON.

Example input: "def add(a, b): return a + b"
Example output: {"purpose": "adds two numbers", "complexity": "O(1)", "issues": []}

Example input: "for i in range(1000000): lst.append(i)"
Example output: {"purpose": "creates list of integers", "complexity": "O(n)", "issues": ["inefficient, use list comprehension"]}

Now analyze the given code in the same JSON format."""
```

### 2.2 Validation ด้วย Pydantic

```python
# ─── Pydantic Validation ───
# วัตถุประสงค์: ตรวจสอบ structure ของ JSON output จาก LLM

from pydantic import BaseModel, field_validator  # Pydantic v2
from typing import List, Optional

class BugReport(BaseModel):
    """Pydantic model สำหรับ validate bug report จาก LLM"""
    line: int
    issue: str
    fix: str
    
    @field_validator('line')
    @classmethod
    def line_must_be_positive(cls, v):
        if v < 0:
            raise ValueError('Line number must be non-negative')
        return v

class CodeAnalysisResult(BaseModel):
    """Pydantic model สำหรับ validate ผลลัพธ์การวิเคราะห์ code"""
    bugs: List[BugReport]
    severity: str
    summary: str
    
    @field_validator('severity')
    @classmethod
    def severity_must_be_valid(cls, v):
        valid = {'critical', 'high', 'medium', 'low', 'none'}
        if v not in valid:
            raise ValueError(f'severity must be one of {valid}')
        return v


def find_bugs_validated(code: str) -> CodeAnalysisResult:
    """find_bugs พร้อม Pydantic validation"""
    raw_result = find_bugs(code)
    
    # ─── Validate ด้วย Pydantic ───
    # วัตถุประสงค์: ถ้า structure ไม่ถูกต้อง จะ raise ValidationError ทันที
    return CodeAnalysisResult(**raw_result)
```

### 2.3 Retry Logic

```python
# ─── Retry Logic สำหรับ JSON Parsing ───
# วัตถุประสงค์: ลอง parse ซ้ำถ้า LLM ไม่ตาม format

import time
import json
from typing import Callable, TypeVar, Any

T = TypeVar('T')

def with_json_retry(
    llm_call: Callable[[], str],
    max_retries: int = 3,
    retry_prompt_suffix: str = "\n\nIMPORTANT: Respond with ONLY valid JSON. No other text."
) -> dict:
    """
    Wrapper ที่ retry การเรียก LLM ถ้า JSON parse ล้มเหลว
    
    Args:
        llm_call: function ที่เรียก LLM และ return string
        max_retries: จำนวนครั้งสูงสุดที่ retry
        retry_prompt_suffix: ข้อความเพิ่มเติมเมื่อ retry
    
    Returns:
        dict: parsed JSON result
    
    Raises:
        ValueError: ถ้า retry หมดแล้วยังไม่ได้ JSON ที่ถูกต้อง
    """
    last_error = None
    
    for attempt in range(max_retries):
        try:
            # ─── เรียก LLM ───
            response = llm_call()
            
            # ─── พยายาม parse JSON ───
            # วัตถุประสงค์: ทำ clean ก่อน parse เพื่อรับมือกับ markdown code blocks
            cleaned = response.strip()
            if cleaned.startswith("```json"):
                cleaned = cleaned[7:]
            if cleaned.startswith("```"):
                cleaned = cleaned[3:]
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3]
            cleaned = cleaned.strip()
            
            return json.loads(cleaned)
            
        except json.JSONDecodeError as e:
            last_error = e
            print(f"Attempt {attempt + 1} failed: {e}")
            if attempt < max_retries - 1:
                time.sleep(0.5)  # รอเล็กน้อยก่อน retry
    
    raise ValueError(f"Failed to get valid JSON after {max_retries} attempts. Last error: {last_error}")
```

---

## ช่วงที่ 3 (50 นาที) — สร้าง Prompt Library

### แนวคิดหลัก: Prompt Library Pattern

Prompt Library คือ collection ของ reusable prompt functions ที่:
- มี **type hints** ชัดเจน
- มี **docstrings** ครบถ้วน
- ใช้ **PromptTemplate** สำหรับ parameterization
- ง่ายต่อการ **test** และ **maintain**

### 3.1 PromptTemplate Pattern

```python
# ─── PromptTemplate Pattern ───
# วัตถุประสงค์: สร้าง reusable prompt templates ที่ fill ตัวแปรได้

from langchain_core.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate

# กำหนด template ด้วย {placeholders}
CODE_REVIEW_TEMPLATE = ChatPromptTemplate.from_messages([
    SystemMessagePromptTemplate.from_template(
        """You are a senior {language} developer conducting a code review.
Review criteria: {criteria}
Output format: JSON with keys: overall_score (1-10), issues (list), suggestions (list), approved (bool)"""
    ),
    HumanMessagePromptTemplate.from_template(
        "Review this {language} code:\n\n```{language}\n{code}\n```"
    )
])

def review_code(code: str, language: str = "Python", criteria: str = "correctness, style, performance") -> dict:
    """
    Code review พร้อม score และ suggestions
    
    Args:
        code: source code ที่ต้องการ review
        language: ภาษา programming
        criteria: หัวข้อที่ต้องการ review
    
    Returns:
        dict: {"overall_score": int, "issues": list, "suggestions": list, "approved": bool}
    """
    llm = ChatOllama(model="qwen2.5-coder:7b", temperature=0.0)
    chain = CODE_REVIEW_TEMPLATE | llm
    
    response = chain.invoke({
        "language": language,
        "criteria": criteria,
        "code": code
    })
    
    try:
        return json.loads(response.content)
    except json.JSONDecodeError:
        import re
        match = re.search(r'\{.*\}', response.content, re.DOTALL)
        return json.loads(match.group()) if match else {}
```

### 3.2 CodingAssistant Class

```python
# ─── CodingAssistant Class ───
# วัตถุประสงค์: รวม methods ทั้งหมดเป็น class เดียว สะดวกต่อการใช้งาน

class CodingAssistant:
    """
    Production-ready coding assistant ที่รวม prompt methods ทั้งหมด
    
    Usage:
        assistant = CodingAssistant()
        explanation = assistant.explain(my_code)
        bugs = assistant.debug(my_code)
        tests = assistant.generate_tests(my_code)
    """
    
    def __init__(self, model: str = "qwen2.5-coder:7b", temperature: float = 0.1):
        self.llm = ChatOllama(model=model, temperature=temperature)
        self.llm_strict = ChatOllama(model=model, temperature=0.0)
    
    def explain(self, code: str, detail_level: str = "detailed") -> str:
        return explain_code(code, detail_level)
    
    def debug(self, code: str, language: str = "python") -> dict:
        return find_bugs(code, language)
    
    def refactor(self, code: str, goal: str = "readability") -> dict:
        return refactor_code(code, goal)
    
    def generate_tests(self, code: str, framework: str = "pytest") -> str:
        return generate_tests(code, framework)
    
    def review(self, code: str, language: str = "Python") -> dict:
        return review_code(code, language)
    
    def analyze_all(self, code: str) -> dict:
        """รัน analysis ทุกอย่างในครั้งเดียว"""
        return {
            "explanation": self.explain(code, "brief"),
            "bugs": self.debug(code),
            "review": self.review(code)
        }
```

---

## ช่วงที่ 4 (10 นาที) — สรุป + Demo

### สิ่งที่เรียนรู้ใน Session นี้

1. **Prompt ที่ดีสำหรับ Code** ต้องมี:
   - System prompt ที่กำหนด persona ของ LLM ชัดเจน
   - Output format specification อย่างเข้มงวด
   - Context เพิ่มเติม (ภาษา, framework, style)

2. **Structured Output** ต้องมี:
   - JSON format specification ใน system prompt
   - Parsing + error handling
   - Validation (Pydantic)
   - Retry logic

3. **Prompt Library Pattern** ช่วย:
   - Reuse prompts ที่ดีซ้ำได้
   - Test prompt อย่างเป็นระบบ
   - Maintain ง่าย

### Demo: ใช้ CodingAssistant

```python
# ─── Demo: CodingAssistant ───
# วัตถุประสงค์: แสดงการใช้งาน library ที่สร้างขึ้นมา

from prompts.coding_prompts import CodingAssistant
import json

assistant = CodingAssistant()

demo_code = """
def process_data(data):
    result = []
    for i in range(len(data)):
        if data[i] > 0:
            result.append(data[i] * 2)
    return result
"""

print("=== EXPLANATION ===")
print(assistant.explain(demo_code, "brief"))

print("\n=== BUGS ===")
bugs = assistant.debug(demo_code)
print(json.dumps(bugs, indent=2))

print("\n=== REFACTORED (Pythonic) ===")
refactored = assistant.refactor(demo_code, "pythonic")
print(refactored.get("refactored_code", ""))
print("\nChanges:")
for change in refactored.get("changes", []):
    print(f"  - {change}")
```

---

## Deliverables ของ Session นี้

| ไฟล์ | คำอธิบาย |
|------|----------|
| `lab/lab_05_code_prompts.py` | Starter สำหรับ hands-on lab |
| `lab/lab_05_code_prompts_solution.py` | Solution ครบทุก TODO |
| `prompts/coding_prompts.py` | Production-ready prompt library |
| `assignment/hw_05_prompt_library.md` | โจทย์การบ้าน |
| `assignment/hw_05_rubric.md` | Rubric การให้คะแนน |

---

## การรันโปรแกรม (Windows)

```powershell
# ติดตั้ง dependencies
uv add langchain-ollama langchain-core pydantic

# รัน lab
uv run python lab\lab_05_code_prompts.py

# รัน solution
uv run python lab\lab_05_code_prompts_solution.py

# ทดสอบ prompt library
uv run python prompts\coding_prompts.py
```

---

## ทรัพยากรเพิ่มเติม

- [LangChain Prompt Templates](https://python.langchain.com/docs/concepts/prompt_templates/)
- [Pydantic Validation](https://docs.pydantic.dev/latest/)
- [Ollama Models](https://ollama.ai/library)
- [qwen2.5-coder Documentation](https://ollama.ai/library/qwen2.5-coder)

---

## หมายเหตุสำหรับผู้สอน

- **ช่วง 1**: ให้นักเรียน run code snippets ทีละ section แล้วสังเกต output
- **ช่วง 2**: เน้นให้เห็นว่า LLM บางครั้งไม่ตาม format → ต้องมี error handling
- **ช่วง 3**: ให้นักเรียนรวม functions ที่ทำได้เป็น class ของตัวเอง
- **ช่วง 4**: Demo ผลงานของนักเรียนคนละ 1-2 นาที

---

---

## แนวคิดสำคัญที่พบในครั้งนี้

| แนวคิด | คำอธิบายสั้น |
|--------|-------------|
| Coding-Specific Prompt | Prompt ที่ระบุ persona, output format และ context (ภาษา, framework) อย่างชัดเจนให้ผลดีกว่า |
| JSON Format Enforcement | บังคับ LLM ให้ output JSON โดยระบุ schema ใน system prompt และใช้ few-shot examples |
| Pydantic Validation | ใช้ Pydantic BaseModel ตรวจสอบ structure ของ JSON output จาก LLM ก่อนใช้งาน |
| Retry Logic | Wrapper ที่ retry การเรียก LLM ถ้า JSON parse ล้มเหลว ทำ pipeline แข็งแกร่งขึ้น |
| Prompt Library Pattern | รวม prompt functions ที่ผ่านการทดสอบแล้วเป็น class/module เดียว ใช้ซ้ำได้ทั่ว codebase |
| CodingAssistant Class | รวม explain, debug, refactor, generate_tests, review เป็น interface เดียวที่ใช้งานง่าย |

---

## ปัญหาที่พบบ่อยและวิธีแก้

| ปัญหา | วิธีแก้ |
|-------|---------|
| LLM ตอบ JSON ที่มี markdown code block ห่ออยู่ | ทำ clean ก่อน parse: ลบ ` ```json ` และ ` ``` ` ออกด้วย string stripping |
| Pydantic ValidationError เมื่อ field ขาดหายหรือผิด type | เพิ่ม `Optional` field หรือใช้ `validator` แปลงค่า แล้วใส่ fallback ใน except block |
| `json.loads` ล้มเหลวเมื่อ LLM ตอบ mixed text+JSON | ใช้ `re.search(r'\{.*\}', response, re.DOTALL)` เพื่อ extract เฉพาะส่วน JSON |
| ChatOllama import error | ตรวจสอบว่า install `langchain-ollama` เวอร์ชันล่าสุด: `uv add langchain-ollama` |

---

## Session ถัดไป

**Session 06 — Embeddings & Semantic Search**
จะเรียนรู้:
- Embedding คืออะไร และ semantic search ทำงานอย่างไร
- สร้าง embeddings ด้วย `nomic-embed-text` ผ่าน Ollama
- Vector similarity: cosine similarity, dot product
- เตรียม pipeline สำหรับ Vector DB ใน Session 07

---

## Checklist ก่อนออกจาก Session นี้

```
□ สร้าง prompt สำหรับ explain, debug, refactor, และ generate tests ได้ และ run code สำเร็จ
□ บังคับ LLM ให้ output JSON พร้อม parsing และ error handling ได้
□ เพิ่ม Pydantic validation ให้กับ JSON output จาก LLM ได้
□ รวม functions ทั้งหมดเป็น CodingAssistant class และ demo ได้
□ มี prompts/coding_prompts.py ที่พร้อมใช้เป็น Prompt Library ตลอดหลักสูตร
```

*Session 05 of 14 — Local RAG for Programming*
