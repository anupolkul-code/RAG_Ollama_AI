# Slide Deck: 01 — Prompt Engineering Fundamentals

> Session 04 | Module 2: Prompt Engineering | 10 slides

---

## Slide 1 - Title

# Prompt Engineering
## ศิลปะแห่งการสื่อสารกับ LLM

**Session 04 — Local RAG for Programming**

- Model: `qwen2.5-coder:7b` via Ollama
- Stack: LangChain · Python · uv

> "LLM เหมือนนักพัฒนาที่เก่งมาก แต่ต้องได้รับคำสั่งที่ชัดเจน"

**Key Message:** Prompt Engineering ไม่ใช่ "magic words" — เป็นการออกแบบ input อย่างเป็นระบบ

---

## Slide 2 - Prompt Anatomy — 4 ส่วนสำคัญ

### โครงสร้าง Prompt ที่มีประสิทธิภาพ

```
┌──────────────────────────────────────────────┐
│  INSTRUCTION                                  │
│  "Analyze the code below and find bugs."      │
├──────────────────────────────────────────────┤
│  CONTEXT                                      │
│  "This is used in a payment system."          │
│  "Security is critical."                      │
├──────────────────────────────────────────────┤
│  EXAMPLES (Few-shot)                          │
│  Input: def add(a,b): return a+b             │
│  Output: {"bugs": [], "severity": "none"}     │
├──────────────────────────────────────────────┤
│  FORMAT SPECIFICATION                         │
│  "Respond ONLY with valid JSON."              │
│  {"bugs": [...], "severity": "low/med/high"}  │
└──────────────────────────────────────────────┘
         |
         v
    Better LLM Response
```

### ผลต่าง: Prompt แย่ vs ดี

| | Prompt แย่ | Prompt ดี |
|--|-----------|---------|
| Input | "explain this" | Full anatomy (4 ส่วน) |
| Output | ยาว/สั้น/ภาษาอะไรก็ได้ | ตรง format ที่ต้องการ |
| Reproducible | ไม่ | ใช่ (temperature=0) |

**Key Message:** Prompt ที่ดีกำหนด output ได้ — ไม่ใช่แค่ถามอะไร แต่ถามอย่างไร

---

## Slide 3 - Zero-shot Prompting — เมื่อไหรได้ผล เมื่อไหรไม่ได้ผล

### Zero-shot: ไม่มีตัวอย่าง

```python
# Zero-shot — ตรงไปตรงมา
prompt = "What is a binary search tree?"
# LLM ตอบจากความรู้ที่มีอยู่ใน training data
```

### เมื่อไหรได้ผล

```
ได้ผลดี:                        ไม่ได้ผล:
─────────────────               ─────────────────
Common knowledge                Specific format required
General explanation             Domain-specific pattern
Open-ended tasks                Consistent style needed
LLM knows the topic well        Novel/private concepts
```

### ตัวอย่างเปรียบเทียบ

```python
# Zero-shot: ได้ผลดี
"What does the Python `with` statement do?"
# LLM รู้จักดี -> ตอบถูก

# Zero-shot: ไม่ได้ผล
"Analyze my company's DataPipeline.process() function"
# LLM ไม่รู้จัก -> hallucinate หรือปฏิเสธ
```

**Key Message:** Zero-shot เหมาะกับ "สิ่งที่ LLM รู้ดีอยู่แล้ว" — ถ้า task ต้องการ context ให้ต้องใส่เอง

---

## Slide 4 - Few-shot Prompting — ตัวอย่าง Input-Output Pattern

### Few-shot: สอน LLM ด้วยตัวอย่าง

```python
prompt = """
Classify Python code complexity.

Example 1:
Code: x = 1 + 1
Complexity: simple

Example 2:
Code: result = {k: v for k, v in items if v > 0}
Complexity: moderate

Example 3:
Code: [User's code here]
Complexity:"""
```

### ทำไม Few-shot ทำงานได้?

```
Training data เต็มไปด้วย pattern:
  Q: ... A: ...
  Input: ... Output: ...
  Example: ... Answer: ...

LLM เรียนรู้ "in-context" pattern จาก examples
  -> เลียนแบบ format และ style ที่ให้มา
  -> ไม่ต้อง retrain model
```

### Rules of Thumb สำหรับ Few-shot

| ข้อมูล | แนะนำ |
|--------|-------|
| จำนวน examples | 2-5 ตัวอย่าง |
| ความหลากหลาย | ครอบคลุม cases ที่เป็นไปได้ |
| Format | สม่ำเสมอทุก example |
| ความยาว | ไม่ยาวเกิน (context limit) |

**Key Message:** Few-shot เปลี่ยน LLM ให้เรียนรู้ pattern จาก example — powerful สำหรับ structured output

---

## Slide 5 - Chain-of-Thought — ให้ LLM "คิดก่อนตอบ"

### CoT: Show Your Work

```python
# Without CoT:
prompt = "Is this code correct?\n{code}"
# LLM ตอบทันที อาจผิด

# With Zero-shot CoT:
prompt = "Is this code correct? Think step by step.\n{code}"
# LLM แสดง reasoning -> ตอบถูกกว่า

# With Few-shot CoT:
prompt = """
Example analysis:
Code: def divide(a, b): return a / b
Thinking:
  Step 1: What does this do? -> divides a by b
  Step 2: Edge cases? -> b could be 0
  Step 3: What happens? -> ZeroDivisionError
  Step 4: Fix? -> add if b == 0: return None
Result: Has division by zero bug

Now analyze: {user_code}
Thinking:"""
```

### ทำไม CoT ช่วย?

```
Without CoT:              With CoT:
─────────────            ─────────────
Question → Answer        Question → Reasoning → Answer
(one-step)               (multi-step)

Like asking a student:   Like asking a student:
"What's the answer?"     "Show your work."
(might guess)            (thinks it through)
```

[FIGURE: Bar chart comparing CoT vs No-CoT accuracy on complex debugging tasks — CoT typically 20-40% higher accuracy]

**Key Message:** "Think step by step" เป็นหนึ่งใน most powerful prompting techniques — ใช้กับ complex reasoning

---

## Slide 6 - System Prompt — กำหนด Role และ Behavior

### System Prompt คืออะไร?

ใน Chat models มี 3 role:
- **system**: กำหนด behavior, persona, constraints
- **human**: คำถามจาก user
- **ai**: คำตอบของ LLM

```python
from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama import ChatOllama

llm = ChatOllama(model="qwen2.5-coder:7b")

# System prompt กำหนด "character" ของ LLM
template = ChatPromptTemplate.from_messages([
    ("system", """You are a senior Python developer at a fintech company.
Rules:
- Always write production-quality code
- Include error handling
- Add type hints
- Response in Thai
- Max response: 200 words"""),
    ("human", "{user_question}")
])
```

### System Prompt ที่ดีประกอบด้วย

```
1. Role/Persona:    "You are a Python security expert"
2. Constraints:     "Always include error handling"
3. Style guide:     "Response in Thai, max 3 bullet points"
4. What NOT to do:  "Do not suggest deprecated APIs"
```

**Key Message:** System prompt เป็น "job description" ของ LLM — กำหนดก่อน ทุก conversation จะ consistent

---

## Slide 7 - Output Formatting — JSON, Markdown, Structured Data

### ทำไม Output Formatting สำคัญมาก?

```python
# Unstructured output (ยากใช้ใน code):
result = "The function takes two parameters: name which is a string,
          and age which is an integer. It returns a greeting string."

# Structured JSON output (ง่ายใช้ใน code):
result = '{"params": [{"name": "name", "type": "str"}, {"name": "age", "type": "int"}], "returns": "str"}'
data = json.loads(result)  # ใช้งานได้ทันที
```

### วิธี Enforce JSON Output

**เทคนิค 1: Explicit instruction**
```python
"Respond ONLY with valid JSON. No prose."
```

**เทคนิค 2: JSON template ใน prompt**
```python
'Output format: {"key": "value", "list": [...]}'
```

**เทคนิค 3: Example + instruction**
```python
"""
Example output:
{"function_name": "add", "purpose": "adds numbers"}

Now analyze: {code}

JSON:"""
```

[FIGURE: Pie chart showing JSON parse success rate — explicit instruction ~70%, template ~85%, example+instruction ~90%]

**Key Message:** JSON output ทำให้ LLM กลายเป็น "structured API" — parse ด้วย `json.loads()` แล้วใช้ใน RAG pipeline ได้

---

## Slide 8 - A/B Testing Prompts — วัดผลอย่างไร

### Framework สำหรับ A/B Testing Prompts

```python
def run_ab_test(
    prompt_a: str,
    prompt_b: str,
    test_inputs: list,
    metric_fn: callable
) -> dict:
    """รัน A/B test และวัดผล"""
    results_a = [llm.invoke(prompt_a.format(code=inp)) for inp in test_inputs]
    results_b = [llm.invoke(prompt_b.format(code=inp)) for inp in test_inputs]

    scores_a = [metric_fn(r) for r in results_a]
    scores_b = [metric_fn(r) for r in results_b]

    return {
        "variant_a": {"avg_score": sum(scores_a) / len(scores_a)},
        "variant_b": {"avg_score": sum(scores_b) / len(scores_b)},
        "winner": "A" if sum(scores_a) > sum(scores_b) else "B"
    }
```

### Metrics สำหรับ Coding Tasks

| Metric | วิธีวัด | ดีเมื่อ |
|--------|---------|-------|
| JSON validity | `json.loads()` ไม่ error | ต้องการ structured output |
| Completeness | % requirements ที่ครอบคลุม | ต้องการ comprehensive analysis |
| Code correctness | `exec()` + assertions | ต้องการ working code |
| Response length | character count | ต้องการ concise/detailed |
| Consistency | variance across 3 runs | ต้องการ reproducible |

**Key Message:** อย่าเลือก prompt "ตามความรู้สึก" — วัดผลด้วย metric ที่ objective

---

## Slide 9 - Common Mistakes — Prompt ที่ไม่ได้ผล

### 5 ความผิดพลาดที่พบบ่อย

**Mistake 1: Vague Instruction**
```python
# BAD:
"make the code better"

# GOOD:
"Refactor this code to: 1) remove duplication, 2) add type hints, 3) handle edge cases"
```

**Mistake 2: No Format Spec**
```python
# BAD:
"list the bugs"
# LLM ตอบยาวสั้นก็ได้

# GOOD:
"List bugs as JSON array: [{'line': N, 'bug': '...', 'fix': '...'}]"
```

**Mistake 3: Contradictory Instructions**
```python
# BAD:
"Be very detailed but also very brief."
# LLM ไม่รู้จะเลือกอะไร

# GOOD:
"Provide 3 bullet points, each under 20 words."
```

**Mistake 4: Too Long Context**
```python
# BAD:
"Paste 2000 lines of code" + question
# Lost in the middle effect

# GOOD:
"Paste only relevant 50 lines" + question
```

**Mistake 5: No Example for Complex Format**
```python
# BAD:
"Output as our custom format"
# LLM ไม่รู้ format ของคุณ

# GOOD:
"Output as: [example of your format]"
```

**Key Message:** Prompt ที่ดีคือ "specification ที่ชัดเจน" — LLM ทำงานได้ดีขึ้นเมื่อ ambiguity น้อยลง

---

## Slide 10 - Prompt Template Pattern

### PromptTemplate ใน LangChain

```python
from langchain_core.prompts import PromptTemplate, ChatPromptTemplate

# Pattern 1: Simple template
template = PromptTemplate.from_template(
    "You are a {language} expert. Explain: {code}"
)
# ใช้:
chain = template | llm
result = chain.invoke({"language": "Python", "code": "..."})

# Pattern 2: Chat template
chat_template = ChatPromptTemplate.from_messages([
    ("system", "You are a {role}."),
    ("human", "Review: {code}")
])
```

### ทำไมต้องใช้ PromptTemplate?

```
ไม่ใช้ Template:          ใช้ Template:
────────────────          ─────────────────
f-string ทุกที่           Define once, reuse everywhere
ยากเปลี่ยน               แก้ที่เดียว
ไม่ type-safe             Input validation
ไม่ composable            Chain กับ components อื่น
```

### Preview: RAG ใช้ PromptTemplate

```python
# Session 08: RAG Template
rag_template = PromptTemplate.from_template("""
Context from codebase:
{retrieved_chunks}

Question: {user_question}

Answer based only on the context:""")

# RAG chain:
rag_chain = retriever | format_docs | rag_template | llm
```

**Key Message:** PromptTemplate เป็น building block ของ RAG — master ตอนนี้ ใช้ใน Sessions 08+

---

*Deck 1 of 2 — Session 04: Prompt Engineering Fundamentals*
