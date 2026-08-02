# Slide Deck 01: Coding-Specific Prompt Engineering

> Session 05 | Module 2: Prompt Engineering | 10 slides

---

## Slide 1 - Title

# Prompt Engineering for Code
## Session 05 — Local RAG for Programming

**LLM:** `qwen2.5-coder:7b` via Ollama  

> "The right prompt is the difference between a junior assistant and a senior developer."

**Key Message:** Prompt ที่ดีทำให้ LLM เป็น "senior developer" — ไม่ใช่แค่ autocomplete

---

## Slide 2 - Coding Tasks ที่ใช้บ่อย

# 5 Coding Tasks ที่ต้องมี Prompt ที่ดี

| Task | สิ่งที่ต้องการจาก LLM |
|------|----------------------|
| **Explain** | อธิบาย code อย่างชัดเจนตาม audience |
| **Debug** | หา bugs พร้อมระบุ line และวิธีแก้ |
| **Refactor** | ปรับปรุง code ตาม goal ที่กำหนด |
| **Test** | สร้าง unit tests ที่รันได้จริง |
| **Review** | ประเมิน code quality พร้อม score |

### Key Insight
Prompt ทั่วไป: "อธิบาย code นี้"  
Prompt ที่ดี: "อธิบาย code นี้สำหรับ beginner โดยใช้ analogy ที่เข้าใจง่าย"

**Key Message:** แต่ละ task ต้องการ prompt structure ที่แตกต่างกัน

---

## Slide 3 - Prompt for Code Explanation

# Code Explanation Prompt Structure

### Structure ที่ดี

```
[System]: You are a senior developer.
          [detail_level instruction]
          
[Human]:  Explain this code:
          ```python
          {code}
          ```
```

### 3 Detail Levels

```python
detail_instructions = {
    "brief":    "Explain in 2-3 sentences only.",
    "detailed": "Explain step by step. Cover: purpose, logic flow, edge cases.",
    "beginner": "Use simple analogies. Avoid jargon."
}
```

### ผลที่ได้ต่างกันอย่างไร?

- **brief** → สรุปสั้นๆ สำหรับ code review
- **detailed** → เข้าใจ code ลึก ก่อน modify
- **beginner** → สอนนักเรียนหรือ junior developer

**Key Message:** Detail level ในชื่อตัวแปรเดียว → ผลลัพธ์ต่างกันมาก

---

## Slide 4 - Prompt for Debugging

# Debugging Prompt — บอก LLM ให้หา Bug อย่างไร

### ปัญหาของ Prompt แบบทั่วไป

```
❌ "หา bug ใน code นี้"
→ LLM อธิบายยาว ไม่ระบุ line ไม่บอกวิธีแก้
```

### Prompt ที่บังคับ JSON Output

```python
system_prompt = """You are an expert code reviewer.
CRITICAL: Respond with ONLY valid JSON.

Output format:
{
  "bugs": [
    {
      "line": <integer>,
      "issue": "<description>",
      "fix": "<how to fix>"
    }
  ],
  "severity": "<critical|high|medium|low|none>",
  "summary": "<one sentence>"
}"""
```

### สิ่งสำคัญ

1. ระบุ `temperature=0.0` → deterministic output
2. บอก "ONLY valid JSON" ชัดเจน
3. ให้ตัวอย่าง format ใน prompt

**Key Message:** JSON output spec ใน system prompt = parseable results ทุกครั้ง

---

## Slide 5 - Prompt for Refactoring

# Refactoring Prompt — บอก Goal ชัดเจน

### 3 Goals ที่ต่างกัน

```python
goal_criteria = {
    "readability":  "Clear names, docstrings, shorter functions",
    "performance":  "Reduce complexity, avoid repeated computation",
    "pythonic":     "List comprehensions, context managers, idiomatic"
}
```

### ตัวอย่าง: Refactor for Pythonic

**Before:**
```python
result = []
for i in range(len(data)):
    if data[i] > 0:
        result.append(data[i] * 2)
```

**After (Pythonic):**
```python
result = [x * 2 for x in data if x > 0]
```

### Output ที่ต้องการ

```json
{
  "refactored_code": "...",
  "changes": ["Used list comprehension", "Removed index-based loop"],
  "reasoning": "More idiomatic Python, more readable"
}
```

**Key Message:** Goal-based refactoring prompt → ผลลัพธ์ที่ตรงกับความต้องการ

---

## Slide 6 - Prompt for Test Generation

# Test Generation Prompt — ระบุ Framework

### ทำไมต้องระบุ Framework?

pytest และ unittest มี style ต่างกันมาก:

```python
# pytest style
def test_add_positive():
    assert add(2, 3) == 5

# unittest style  
class TestAdd(unittest.TestCase):
    def test_add_positive(self):
        self.assertEqual(add(2, 3), 5)
```

### Prompt Template

```python
framework_guide = {
    "pytest": """Use pytest framework.
- Use def test_<name>(): functions
- Use assert statements  
- Include @pytest.mark.parametrize for multiple cases
- Test: happy path, edge cases, error cases""",
    
    "unittest": """Use unittest.TestCase.
- Inherit from unittest.TestCase
- Use self.assertEqual, self.assertRaises
- Test: happy path, edge cases, error cases"""
}
```

### Test Cases ที่ LLM ควร Generate

1. Happy path (normal input)
2. Edge cases (empty, zero, negative)
3. Error cases (wrong type, out of range)

**Key Message:** Framework specification → test code ที่ copy-paste แล้วรันได้เลย

---

## Slide 7 - Prompt for Code Review

# Code Review Prompt — Checklist-based

### Code Review Criteria

```python
default_criteria = "correctness, style, performance, security, maintainability"
```

### Prompt Template ด้วย PromptTemplate

```python
CODE_REVIEW_TEMPLATE = ChatPromptTemplate.from_messages([
    SystemMessagePromptTemplate.from_template(
        """You are a senior {language} developer.
Review criteria: {criteria}
Output: JSON with keys:
- overall_score (1-10)
- issues (list of strings)
- suggestions (list of strings)  
- approved (boolean)"""
    ),
    HumanMessagePromptTemplate.from_template(
        "Review this {language} code:\n\n```{language}\n{code}\n```"
    )
])
```

### ข้อดีของ Checklist-based Review

- Score ที่ compare กันได้ระหว่าง code versions
- Issues และ suggestions แยกชัดเจน
- `approved` flag สำหรับ CI/CD integration

**Key Message:** Structured review → feedback ที่ actionable และ consistent

---

## Slide 8 - Structured Output — ทำไม JSON Output สำคัญ

# ทำไม Structured Output ถึงสำคัญ?

### LLM ใน Pipeline

```
Code → LLM → Parse Result → Next Step
              ↑
         ถ้าตรงนี้พัง → ทั้ง pipeline พัง
```

### เปรียบเทียบ: Free-form vs JSON

**Free-form output:**
```
The code has a potential bug on line 5 where division by zero 
could occur if the list is empty. You should add a check...
```
→ ต้อง parse text เอง = เสี่ยงพัง

**JSON output:**
```json
{"bugs": [{"line": 5, "issue": "Division by zero", "fix": "Check len > 0"}]}
```
→ `json.loads()` ทันที = reliable

### 3 เทคนิคบังคับ JSON

1. **System prompt**: "Respond with ONLY valid JSON"
2. **Few-shot examples**: ให้ตัวอย่าง input → JSON output
3. **Temperature = 0**: ลด creativity = follow format มากขึ้น

**Key Message:** JSON output = machine-readable = pipeline-ready

---

## Slide 9 - Pydantic + LLM Output Validation

# Pydantic — Validate JSON จาก LLM

### ปัญหา: LLM อาจส่ง JSON ที่ structure ผิด

```python
# LLM ส่งมา (ผิด)
{"bugs": "none found"}  # ควรเป็น list ไม่ใช่ string
{"severity": "medium-high"}  # ค่าไม่ valid
```

### Pydantic Model

```python
from pydantic import BaseModel, field_validator  # Pydantic v2
from typing import List

class BugReport(BaseModel):
    line: int
    issue: str
    fix: str

class CodeAnalysisResult(BaseModel):
    bugs: List[BugReport]
    severity: str
    summary: str
    
    @field_validator('severity')
    @classmethod
    def severity_must_be_valid(cls, v):
        valid = {'critical', 'high', 'medium', 'low', 'none'}
        if v not in valid:
            raise ValueError(f'Must be one of {valid}')
        return v

# ใช้งาน
result = CodeAnalysisResult(**json_from_llm)
# ถ้า structure ผิด → ValidationError ชัดเจน
```

### Retry on Validation Error

```python
for attempt in range(3):
    try:
        data = json.loads(llm_response)
        validated = CodeAnalysisResult(**data)
        return validated
    except (json.JSONDecodeError, ValidationError):
        # retry with stronger prompt
        pass
```

**Key Message:** Pydantic = type safety สำหรับ LLM output

---

## Slide 10 - Prompt Library Pattern

# Prompt Library Pattern — Reusable Functions

### Anti-pattern: Prompt กระจัดกระจาย

```python
# ❌ แย่: prompt อยู่ใน code ทุกที่
def analyze():
    prompt = "analyze this code..."  # hardcoded
    
def debug():
    prompt = "find bugs in..."  # hardcoded อีกที่
```

### Pattern ที่ดี: Centralized Library

```
prompts/
  coding_prompts.py   ← รวม prompts ทั้งหมด
  
lab/
  lab_05.py           ← import จาก library
  
assignment/
  demo.py             ← import จาก library
```

### CodingAssistant Class

```python
class CodingAssistant:
    def explain(self, code, detail_level="detailed") -> str: ...
    def debug(self, code, language="python") -> dict: ...
    def refactor(self, code, goal="readability") -> dict: ...
    def generate_tests(self, code, framework="pytest") -> str: ...
    def review(self, code, language="Python") -> dict: ...
    def analyze_all(self, code) -> dict: ...

# ใช้งาน
assistant = CodingAssistant()
result = assistant.analyze_all(my_code)
```

### ประโยชน์

- Test prompt ได้เป็นระบบ
- เปลี่ยน LLM model ที่จุดเดียว
- Share กับทีมได้ง่าย

**Key Message:** Prompt Library = ลงทุนครั้งเดียว ใช้ได้ตลอดหลักสูตร

---

*Slide Deck 01 | Session 05 | Local RAG for Programming*
