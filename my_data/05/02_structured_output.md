# Slide Deck 02: Structured Output from LLMs

> Session 05 | Module 2: Prompt Engineering | 8 slides

---

## Slide 1 - Title

# Structured Output from LLMs
## JSON, Validation & Error Handling

**Session 05 — Part 2 | Local RAG for Programming**

> "An LLM that can't be parsed is useless in production."

---

## Slide 2 - JSON Output Format Specification

# วิธีบอก LLM ให้ตอบเป็น JSON

### เทคนิค 1: System Prompt ที่ชัดเจน

```python
system = """You are a code analysis API.
CRITICAL RULES:
1. Respond with ONLY valid JSON
2. No markdown code blocks (no ```)
3. No explanation outside JSON
4. No trailing commas

Required schema:
{
  "result": "<string>",
  "confidence": <float 0-1>,
  "issues": ["<string>", ...]
}"""
```

### เทคนิค 2: Negative Instructions

```
❌ ห้ามพิมพ์  Don't say "Here is the JSON:"
❌ ห้ามพิมพ์  ```json ... ```
❌ ห้ามพิมพ์  Any text before or after the JSON
✅ ให้พิมพ์   {   (เริ่ม JSON ทันที)
```

### เทคนิค 3: Temperature = 0

```python
llm = ChatOllama(model="qwen2.5-coder:7b", temperature=0.0)
# temperature=0 → follow format มากขึ้น, ลด creativity
```

**Key Message:** 3 เทคนิครวมกัน = JSON ที่ parse ได้ ~95% ของเวลา

---

## Slide 3 - Few-Shot Examples สำหรับ JSON

# Few-Shot Examples — สอน LLM ด้วยตัวอย่าง

### ทำไม Few-Shot ช่วยได้?

LLM เรียนรู้ pattern จากตัวอย่าง → เลียนแบบ format ที่เห็น

### System Prompt พร้อม Few-Shot

```python
SYSTEM_FEW_SHOT = """Analyze Python code and respond in JSON.

EXAMPLE 1:
Input: "def add(a, b): return a + b"
Output: {
  "purpose": "adds two numbers",
  "complexity": "O(1)",
  "issues": [],
  "quality_score": 8
}

EXAMPLE 2:
Input: "for i in range(1000000): lst.append(i)"
Output: {
  "purpose": "creates list of 1M integers",
  "complexity": "O(n)",
  "issues": ["inefficient append in loop"],
  "quality_score": 4
}

Now analyze the given code in the EXACT same JSON format."""
```

### กฎ Few-Shot ที่ดี

1. ตัวอย่างอย่างน้อย 2 ตัวอย่าง
2. ครอบคลุม cases ที่ต่างกัน (simple / complex)
3. Format ต้องเหมือนกันทุก example

**Key Message:** Few-shot = pattern matching ที่ LLM เก่งมาก

---

## Slide 4 - Error Handling เมื่อ LLM ไม่ตาม Format

# Error Handling Strategies

### 3 ประเภทของ Error

```
1. JSONDecodeError  → LLM ส่ง text ที่ไม่ใช่ JSON
2. KeyError         → JSON ขาด key ที่ต้องการ
3. TypeError        → ค่ามี type ผิด (string แทน int)
```

### Defensive Parsing

```python
def safe_parse_json(response: str) -> dict | None:
    """Parse JSON อย่างปลอดภัย — handle edge cases"""
    
    cleaned = response.strip()
    
    # ─── ลบ markdown code blocks ───
    # วัตถุประสงค์: LLM บางครั้งห่อ JSON ด้วย ```json ... ```
    if cleaned.startswith("```json"):
        cleaned = cleaned[7:]
    elif cleaned.startswith("```"):
        cleaned = cleaned[3:]
    if cleaned.endswith("```"):
        cleaned = cleaned[:-3]
    cleaned = cleaned.strip()
    
    # ─── ลอง parse ตรงๆ ───
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass
    
    # ─── ลอง extract JSON จาก text ───
    import re
    match = re.search(r'\{.*\}', cleaned, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass
    
    return None  # parse ล้มเหลว
```

**Key Message:** Defensive parsing ลด failure rate ได้อีก 3-5%

---

## Slide 5 - Retry Logic

# Retry Logic — ลองใหม่เมื่อ Fail

### เมื่อไหรต้อง Retry?

```
Attempt 1: json.JSONDecodeError → retry
Attempt 2: ValidationError → retry with stronger prompt
Attempt 3: Success ✓
```

### Retry with Escalating Prompt

```python
def call_with_retry(messages: list, max_retries: int = 3) -> dict:
    """Retry LLM call พร้อม escalating prompt pressure"""
    
    llm = ChatOllama(model="qwen2.5-coder:7b", temperature=0.0)
    
    for attempt in range(max_retries):
        response = llm.invoke(messages)
        result = safe_parse_json(response.content)
        
        if result is not None:
            return result
        
        # ─── เพิ่ม pressure เมื่อ retry ───
        # วัตถุประสงค์: บอก LLM ชัดขึ้นเมื่อ format ผิด
        retry_msg = HumanMessage(
            content=f"ERROR: Your response was not valid JSON. "
                    f"Attempt {attempt + 1}/{max_retries}. "
                    f"Return ONLY the JSON object, nothing else."
        )
        messages = messages + [response, retry_msg]
    
    raise ValueError(f"Failed after {max_retries} attempts")
```

### Success Rate จริง

| Model | ครั้งแรก | หลัง 1 retry | หลัง 2 retry |
|-------|----------|--------------|--------------|
| qwen2.5-coder:7b | ~85% | ~96% | ~99% |

**Key Message:** Retry ง่ายๆ แต่เพิ่ม reliability ได้มาก

---

## Slide 6 - Pydantic Models สำหรับ Validation

# Pydantic — Type-Safe LLM Output

### ทำไมต้อง Validate หลัง JSON Parse?

```python
# JSON parse สำเร็จ แต่ค่าผิด!
data = {"severity": "super-critical", "bugs": "none"}
# severity ไม่ใช่ค่าที่ valid
# bugs ควรเป็น list ไม่ใช่ string
```

### Pydantic Model ครบ

```python
from pydantic import BaseModel, Field, validator
from typing import List, Literal

class BugItem(BaseModel):
    line: int = Field(ge=0, description="Line number")
    issue: str = Field(min_length=1)
    fix: str = Field(min_length=1)

class BugAnalysis(BaseModel):
    bugs: List[BugItem]
    severity: Literal["critical", "high", "medium", "low", "none"]
    summary: str
    
# ─── ใช้งาน ───
try:
    result = BugAnalysis(**json_data)
    print(f"Found {len(result.bugs)} bugs, severity: {result.severity}")
except ValidationError as e:
    print(f"LLM gave invalid data: {e}")
    # retry หรือ return default
```

### ประโยชน์

- Type hints ใน IDE (autocomplete)
- Catch ข้อผิดพลาดเร็วกว่า
- Self-documenting schema

**Key Message:** Pydantic = contract ระหว่าง LLM และ code ของเรา

---

## Slide 7 - LangChain Output Parsers

# LangChain Output Parsers

### Built-in Parsers

```python
from langchain_core.output_parsers import JsonOutputParser, StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

# ─── JsonOutputParser ───
# วัตถุประสงค์: parse JSON output อัตโนมัติ + format instructions
parser = JsonOutputParser()

prompt = ChatPromptTemplate.from_messages([
    ("system", "Analyze the code.\n{format_instructions}"),
    ("human", "{code}")
]).partial(format_instructions=parser.get_format_instructions())

chain = prompt | llm | parser
result = chain.invoke({"code": my_code})
# result เป็น dict แล้ว ไม่ต้อง json.loads() เอง
```

### PydanticOutputParser

```python
from langchain_core.output_parsers import PydanticOutputParser

parser = PydanticOutputParser(pydantic_object=BugAnalysis)

prompt = ChatPromptTemplate.from_messages([
    ("system", "Analyze bugs.\n{format_instructions}"),
    ("human", "{code}")
]).partial(format_instructions=parser.get_format_instructions())

chain = prompt | llm | parser
result: BugAnalysis = chain.invoke({"code": my_code})
# result เป็น BugAnalysis object ที่ validated แล้ว!
```

**Key Message:** LangChain parsers ลด boilerplate และจัดการ format instructions ให้

---

## Slide 8 - Production Considerations

# Production Considerations

### Checklist สำหรับ Production JSON Output

```
✅ Temperature = 0.0 สำหรับ structured output
✅ Defensive JSON parsing (handle markdown blocks)
✅ Retry logic (อย่างน้อย 3 ครั้ง)
✅ Pydantic validation หลัง parse
✅ Logging ทุก attempt (ไม่ใช่แค่ success)
✅ Timeout handling
✅ Fallback response เมื่อทุก retry ล้มเหลว
```

### Measuring Success Rate

```python
import logging

def tracked_llm_call(code: str) -> dict:
    """LLM call พร้อม tracking"""
    attempts = 0
    start_time = time.time()
    
    for attempt in range(3):
        attempts += 1
        try:
            result = find_bugs(code)
            logging.info(f"Success on attempt {attempts}, "
                        f"time={time.time()-start_time:.2f}s")
            return result
        except Exception as e:
            logging.warning(f"Attempt {attempts} failed: {e}")
    
    logging.error(f"All {attempts} attempts failed")
    return {"bugs": [], "severity": "unknown", "summary": "Analysis failed"}
```

### เมื่อควร Raise Error vs Return Default?

| สถานการณ์ | Action |
|-----------|--------|
| Interactive tool | Raise error + show to user |
| Background pipeline | Return default + log |
| Critical operation | Raise error + alert |

**Key Message:** Production = reliability + observability

---

*Slide Deck 02 | Session 05 | Local RAG for Programming*
