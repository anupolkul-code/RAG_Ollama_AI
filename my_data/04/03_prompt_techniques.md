# Slide Deck: Zero-shot, Few-shot, CoT — เทคนิค Prompt Engineering
> Session 04 | Module 1: Foundation & LLM | 11 slides

---

## Slide 1 — Title

**Local RAG for Programming — Session 04 (Part 2)**

# Prompt Techniques: Zero-shot → Few-shot → Chain-of-Thought

**Key Message**: การเลือกเทคนิค prompt ที่ถูกต้องคือความแตกต่างระหว่าง LLM ที่ "ใช้ไม่ได้" กับ "ใช้ได้จริง"

---

## Slide 2 — 3 Prompt Strategies Overview

**Key Message**: แต่ละ strategy มี trade-off ที่ชัดเจน — ไม่มีอะไรดีที่สุดสำหรับทุก task

```
Task Complexity →
    ↑
    │  Zero-shot   Few-shot    Chain-of-Thought
    │  ─────────   ─────────   ────────────────
    │  Fast        Balanced    Slow
    │  No examples Need ex.    Need examples+steps
    │  Works for   Works for   Works for
    │  simple tasks medium     complex reasoning
    ↓
Simplicity
```

| Strategy | ตัวอย่างใน prompt | เหมาะกับ |
|----------|-----------------|---------|
| Zero-shot | ไม่มี | Simple, well-defined tasks |
| Few-shot | 2-5 ตัวอย่าง input→output | Pattern-following tasks |
| CoT | ขั้นตอนการคิด | Reasoning, debugging, math |

---

## Slide 3 — Zero-shot Prompting

**Key Message**: Zero-shot เหมาะเมื่อ task ชัดเจนและ LLM มีความรู้นั้นอยู่แล้ว

**ไม่มีตัวอย่าง — แค่ instruction:**
```python
zero_shot_prompt = """
You are a Python expert.
Add type hints to the following function:

def calculate_area(width, height):
    return width * height
"""
```

**เมื่อใช้ Zero-shot:**
✓ Task ง่าย และมีคำนิยามชัดเจน ("add type hints", "fix syntax error")
✓ ไม่มีเวลาสร้าง examples
✗ Task ต้องการรูปแบบ output เฉพาะ
✗ Task ที่ต้องการ multi-step reasoning

---

## Slide 4 — Few-shot Prompting

**Key Message**: ตัวอย่าง Input→Output คือวิธีที่มีประสิทธิภาพที่สุดในการ "สอน" รูปแบบ

**มีตัวอย่าง input→output:**
```python
few_shot_prompt = """
Convert Python function to use f-strings:

Input: "Hello, " + name + "!"
Output: f"Hello, {name}!"

Input: str(x) + " items at " + str(price) + " each"
Output: f"{x} items at {price} each"

Input: "Error: " + error_msg + " at line " + str(line)
Output: """
# LLM จะตอบ: f"Error: {error_msg} at line {line}"
```

**Rules of thumb:**
- 2-5 examples: เพียงพอสำหรับ pattern learning
- Examples ควร diverse (ครอบคลุม edge cases)
- Input/Output format ต้องสม่ำเสมอ

---

## Slide 5 — Chain-of-Thought (CoT)

**Key Message**: CoT บังคับให้ LLM "แสดงงาน" — ลด hallucination ใน complex tasks

**Step-by-step reasoning:**
```python
cot_prompt = """
Debug this Python function step by step:

def find_max(numbers):
    max_val = 0
    for n in numbers:
        if n > max_val:
            max_val = n
    return max_val

Think through:
1. What is the function supposed to do?
2. What is the bug?
3. What happens with [-5, -3, -1]?
4. What is the correct fix?
"""
# LLM จะวิเคราะห์ทีละขั้น และพบว่า max_val = 0 ทำให้ fail กับ negative numbers
```

**เมื่อใช้ CoT:**
✓ Debugging — trace execution step by step
✓ Code review — analyze each section
✓ Algorithm design — explain approach before code
✗ Simple, direct tasks (เสียเวลา tokens โดยไม่จำเป็น)

---

## Slide 6 — Prompt Anatomy Workshop

**Key Message**: Prompt ที่ดีมี 4 ส่วน — ขาดส่วนไหนก็ได้ผลลัพธ์แย่ลง

```
┌────────────────────────────────────────────────┐
│  1. ROLE / PERSONA                             │
│     "You are a senior Python developer..."     │
├────────────────────────────────────────────────┤
│  2. TASK / INSTRUCTION                         │
│     "Review the following code and..."         │
├────────────────────────────────────────────────┤
│  3. CONTEXT / EXAMPLES                         │
│     "Here is the code: [code block]"           │
│     "Example output: [example]"                │
├────────────────────────────────────────────────┤
│  4. OUTPUT FORMAT / CONSTRAINTS                │
│     "Respond in JSON format."                  │
│     "Keep answer under 200 words."             │
└────────────────────────────────────────────────┘
```

[EXAMPLE: Workshop Step 1 — เปรียบเทียบ prompt ที่ขาด/มีครบ 4 ส่วน]

---

## Slide 7 — Output Format Control

**Key Message**: บอก LLM ว่าต้องการ output รูปแบบไหน — ไม่งั้นมันเลือกเอง

**Unstructured vs Structured:**

```python
# ❌ Unstructured — ได้ paragraph ที่ parse ยาก
prompt = "List the bugs in this code"
# Output: "There are several issues with this code. First, the variable..."

# ✓ Structured JSON — parse ง่าย
prompt = """
Analyze the bugs in this code.
Respond ONLY with a JSON array in this exact format:
[{"line": N, "type": "bug_type", "description": "...", "fix": "..."}]
"""
# Output: [{"line": 5, "type": "logic_error", "description": "...", "fix": "..."}]
```

**Formats ที่มีประโยชน์:**
- JSON: API responses, automated processing
- Markdown: Documentation, human-readable reports
- Code only: CI/CD pipeline integration
- Numbered list: Step-by-step instructions

---

## Slide 8 — PromptTemplate: Reusable Patterns

**Key Message**: PromptTemplate เปลี่ยน one-time prompt เป็น reusable component

```python
from langchain_core.prompts import PromptTemplate, ChatPromptTemplate

# ─── PromptTemplate สำหรับ code review ────────────────
# วัตถุประสงค์: reuse ได้กับทุก language และ focus
code_review_template = ChatPromptTemplate.from_messages([
    ("system", "You are a {language} expert focused on {focus}."),
    ("human", "Review this code:\n\n```{language}\n{code}\n```\n\n"
               "Provide feedback in JSON format with fields: "
               "issues (list), suggestions (list), rating (1-10)")
])

# ─── สร้าง chain ───────────────────────────────────────
from langchain_ollama import ChatOllama
chain = code_review_template | ChatOllama(model="qwen2.5-coder:7b", temperature=0)

# ─── reuse กับ inputs ต่างกัน ──────────────────────────
result1 = chain.invoke({"language": "Python", "focus": "PEP 8", "code": "..."})
result2 = chain.invoke({"language": "JavaScript", "focus": "security", "code": "..."})
```

---

## Slide 9 — A/B Testing Prompts

**Key Message**: อย่า "เดา" ว่า prompt ไหนดีกว่า — วัดด้วยข้อมูลจริง

**Systematic A/B Testing:**

```python
import time

prompts = {
    "zero_shot": "Fix the bug in this Python function: {code}",
    "few_shot": "Fix bugs like these examples:\nInput: ...\nFixed: ...\n\nFix: {code}",
    "cot": "Debug step by step: 1) What should it do? 2) What's wrong? 3) Fix: {code}"
}

results = {}
for name, prompt_template in prompts.items():
    start = time.time()
    response = llm.invoke(prompt_template.format(code=test_code))
    elapsed = time.time() - start
    results[name] = {"response": response, "time": elapsed}
    
# วัด: speed, accuracy, format compliance
```

---

## Slide 10 — Common Prompt Mistakes

**Key Message**: Prompt engineering มี anti-patterns ที่พบบ่อย — หลีกเลี่ยงได้เลยถ้ารู้ล่วงหน้า

| Anti-Pattern | ตัวอย่าง | Fix |
|-------------|---------|-----|
| Too vague | "fix this" | "Fix the IndexError in line 5 of this Python code" |
| No format spec | "list issues" | "List issues as JSON array with fields: line, type, fix" |
| Too long | 500 words instruction | ย่อเหลือ key points |
| Conflicting instructions | "be brief" + "explain everything" | เลือกอย่างใดอย่างหนึ่ง |
| No examples | complex output format | เพิ่ม 1 example ของ format ที่ต้องการ |

---

## Slide 11 — สรุปและ Big Picture

**Key Message**: Prompt engineering เป็น skill ที่ต้องฝึก — session นี้คือ foundation

**สิ่งที่เรียนรู้วันนี้:**

| เทคนิค | เมื่อใช้ | ตัวอย่าง use case |
|--------|---------|----------------|
| Zero-shot | Task ชัดเจน, simple | Add type hints, rename variable |
| Few-shot | ต้องการ format เฉพาะ | Convert to f-string, format docstring |
| CoT | Complex reasoning | Debug, algorithm design |
| Structured output | Automated processing | JSON API, CI/CD integration |
| PromptTemplate | Reusable patterns | Code reviewer, docstring generator |

**Big Picture:**
```
Session 04 (Prompt) ──► Session 07 (RAG) ──► Session 12 (Hybrid)
                              ↑
                    Prompt เป็น interface ที่ต่อกับ
                    retrieved context ใน RAG pipeline
```

**Session 05:** ใช้ prompt techniques กับ coding tasks โดยตรง — docstring gen, bug fix, refactor
