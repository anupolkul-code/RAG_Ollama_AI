# Slide Deck: 02 — Prompt Patterns for Code

> Session 04 | Module 2: Prompt Engineering | 8 slides

---

## Slide 1 - Title

# Prompt Patterns สำหรับ Coding
## Techniques ที่ใช้จริงใน Production

**Session 04 — Deck 2**

> Patterns ที่เรียนวันนี้ = สิ่งที่ใช้ทุกวันใน RAG pipeline

**Key Message:** ไม่ต้องจำทุก pattern — รู้จักพอที่จะเลือกใช้ถูกสถานการณ์

---

## Slide 2 - Role Prompting

### กำหนด "ตัวตน" ของ LLM

**Basic Role:**
```python
"You are a Python expert."
"You are a security auditor."
"You are a junior developer learning."
```

**Detailed Role (ดีกว่า):**
```python
system_prompt = """
You are a senior Python developer with 10 years experience.
You specialize in:
- Clean code and SOLID principles
- Performance optimization
- Security best practices

When reviewing code, you:
1. First mention what's done well
2. Then identify issues by severity
3. Always suggest specific fixes
"""
```

### Role ส่งผลต่อ Output อย่างไร

```python
# Same code, different roles:
code = "def process(data): return [x for x in data if x > 0]"

# Role A: Junior explainer
"You are explaining to a beginner."
# -> อธิบายยาว ใช้ภาษาง่าย

# Role B: Security auditor
"You are a security auditor."
# -> มองหา input validation, injection risks

# Role C: Performance engineer
"You are optimizing for performance."
# -> พิจารณา memory, time complexity
```

**Key Message:** Role prompting เปลี่ยน "lens" ที่ LLM ใช้มอง code — เลือก role ให้ตรงกับ task

---

## Slide 3 - Step-by-Step Instruction

### ทำไมต้อง Explicit Steps?

```python
# Vague (ผลลัพธ์ unpredictable):
"Review this code"

# Step-by-step (ผลลัพธ์ predictable):
"""
Review this code following these steps:
1. Check for syntax errors
2. Check for logic errors
3. Check for security vulnerabilities
4. Check for performance issues
5. Suggest improvements

For each step, list findings or write "None found."
"""
```

### Pattern: Ordered Analysis

```python
code_review_template = """
Analyze this code in order:

STEP 1 — SYNTAX & STYLE
Check: naming conventions, PEP 8, type hints

STEP 2 — LOGIC CORRECTNESS
Check: edge cases, off-by-one errors, null handling

STEP 3 — SECURITY
Check: injection vulnerabilities, input validation

STEP 4 — PERFORMANCE
Check: time/space complexity, unnecessary operations

STEP 5 — SUMMARY
Rate overall quality: 1-5 stars, with justification

Code:
{code}
"""
```

**Key Message:** Numbered steps = deterministic output structure — LLM follows ordered instructions better than vague ones

---

## Slide 4 - Delimiter Usage — ``` ### <tag>

### ทำไม Delimiters สำคัญ?

Delimiters ช่วย LLM แยกแยะระหว่าง:
- Code ที่ต้อง analyze
- Instruction ที่ต้องทำตาม
- Context ที่เป็นข้อมูลอ้างอิง

### 3 วิธีที่ใช้บ่อย

**วิธี 1: Triple backticks สำหรับ code**
```python
prompt = """
Review this Python code:

```python
{code}
```

Focus on: security, performance, readability.
"""
```

**วิธี 2: ### สำหรับ sections**
```python
prompt = """
### CODE TO ANALYZE
{code}

### YOUR TASK
Find bugs and suggest fixes.

### OUTPUT FORMAT
List each bug as: Line N: [description] -> [fix]
"""
```

**วิธี 3: XML-style tags**
```python
prompt = """
<code>
{code}
</code>

<task>
Explain what the above code does.
</task>

<format>
Respond in Thai. Maximum 3 sentences.
</format>
"""
```

### เมื่อไหรใช้อะไร

| Delimiter | ใช้สำหรับ | ตัวอย่าง |
|-----------|----------|---------|
| ` ```python ` | Code blocks | `{user_code}` |
| `###` | Section headers | `### TASK ###` |
| `<tag>` | Structured data | `<context>{doc}</context>` |
| `---` | Separators | ระหว่าง examples |

**Key Message:** Delimiters ลด ambiguity ของ prompt — LLM รู้ว่าส่วนไหนคือ "what to do" และ "what to process"

---

## Slide 5 - Negative Instructions — ห้ามทำอะไร

### บอก LLM ว่า "อย่าทำ" อะไร

```python
# ปัญหาที่เกิดบ่อย:
# LLM อธิบายยาวมาก ทั้งที่อยากได้แค่ code

# แก้ด้วย negative instruction:
prompt = """
Write a Python function that reverses a string.

Rules:
- Code ONLY (no explanation)
- No comments
- No docstrings
- No import statements
- Function name must be: reverse_string
"""
```

### Negative Instructions ที่มีประโยชน์

```python
# สำหรับ code generation:
"Do not use deprecated APIs"
"Do not use global variables"
"Do not write code that requires external libraries"

# สำหรับ analysis:
"Do not repeat the code back to me"
"Do not give general advice about Python"

# สำหรับ format:
"Do not use bullet points"
"Do not include a preamble"
"Do not say 'Certainly!' or 'Sure!'"
```

### A/B Test: With vs Without Negative Instructions

```python
# Without negative:
"Explain list comprehension in Python"
# LLM: "Certainly! List comprehension is a powerful..."
# -> Verbose, filler words

# With negative:
"Explain list comprehension in Python.
Do not start with filler phrases.
Do not repeat back my question."
# -> Direct, concise explanation
```

**Key Message:** Negative instructions ตัด "noise" ออกจาก response — ใช้เมื่อ LLM ทำอะไรที่ไม่ต้องการซ้ำๆ

---

## Slide 6 - Output Format Specification

### 3 ระดับของ Format Specification

**Level 1: Type specification (ง่าย)**
```python
"Respond as a Python list of strings."
"Answer with a single integer."
"Output as markdown table."
```

**Level 2: Template (ปานกลาง)**
```python
"Use this format:
FUNCTION: [name]
PURPOSE: [one sentence]
BUGS: [list or 'none']"
```

**Level 3: Schema + Example (ละเอียด)**
```python
"""
Output ONLY valid JSON matching this schema:
{
  "function_name": "string",
  "bugs": [{"line": int, "description": "string", "severity": "low|medium|high"}],
  "suggestion": "string"
}

Example output:
{"function_name": "add", "bugs": [], "suggestion": "Add type hints"}

Now analyze: {code}

JSON:"""
```

### ความสำเร็จในการ Parse JSON

```
Format vague   -> JSON parse success ~50%
Level 1 spec   -> JSON parse success ~65%
Level 2 template -> JSON parse success ~80%
Level 3 schema+example -> JSON parse success ~90%+
```

**Key Message:** ยิ่ง format specification ละเอียด ยิ่ง parse success rate สูง — invest time ใน Level 3 สำหรับ production

---

## Slide 7 - Chaining Prompts

### ทำไมต้อง Chain หลาย Prompts?

บางครั้ง task เดียว = หลาย sub-tasks

```
Task: "Review code security"
= Step 1: Extract all user inputs
= Step 2: Check each input for injection risks
= Step 3: Suggest sanitization for each risk
= Step 4: Generate summary report
```

### Prompt Chaining Pattern

```python
from langchain_ollama import OllamaLLM
from langchain_core.prompts import PromptTemplate

llm = OllamaLLM(model="qwen2.5-coder:7b")

# Step 1: Extract inputs
extract_template = PromptTemplate.from_template(
    "List all user inputs in this code. Code only, no explanation:\n{code}"
)

# Step 2: Analyze each input
analyze_template = PromptTemplate.from_template(
    "For each input below, check for injection risks:\n{inputs}\n"
    "Format: input_name: [risk description or 'safe']"
)

# Step 3: Generate fix
fix_template = PromptTemplate.from_template(
    "Given these security risks:\n{risks}\n"
    "Write secure validation code for each input."
)

# Chain
code = "def login(username, password): db.query(f'SELECT * FROM users WHERE name={username}')"

inputs_result = (extract_template | llm).invoke({"code": code})
analysis_result = (analyze_template | llm).invoke({"inputs": inputs_result})
fix_result = (fix_template | llm).invoke({"risks": analysis_result})

print("Final recommendation:")
print(fix_result)
```

**Key Message:** Chain prompts เมื่อ task ซับซ้อน — แต่ละ step มี focused prompt ที่ดีกว่า 1 mega-prompt

---

## Slide 8 - Prompt Versioning

### ทำไมต้อง Version Prompts?

```python
# ปัญหา: prompt เปลี่ยนไปแต่ไม่รู้ว่าดีขึ้นหรือแย่ลง

# Solution: Version ชัดเจน + Track changes
PROMPTS = {
    "code_analyzer_v1": """Analyze this code: {code}""",

    "code_analyzer_v2": """
    You are a Python expert. Analyze this code for bugs.
    {code}
    List issues found:""",

    "code_analyzer_v3": """
    You are a Python expert. Analyze this code for:
    1) Bugs 2) Security 3) Performance

    Code: ```python\n{code}\n```

    Output as JSON: {{"bugs": [], "security": [], "performance": []}}
    JSON:"""
}
```

### Version Control สำหรับ Prompts

```
prompts/
├── code_analyzer_v1.txt    <- baseline
├── code_analyzer_v2.txt    <- added structure
├── code_analyzer_v3.txt    <- added JSON format
└── CHANGELOG.md
    v1 -> v2: Added role + output spec
    v2 -> v3: Added JSON format, more categories
    v3: JSON parse rate improved from 60% to 90%
```

### Evaluation Before Upgrade

```python
def compare_prompt_versions(v_old: str, v_new: str, test_cases: list) -> None:
    scores_old = [evaluate(v_old.format(code=tc)) for tc in test_cases]
    scores_new = [evaluate(v_new.format(code=tc)) for tc in test_cases]
    improvement = (sum(scores_new) - sum(scores_old)) / len(test_cases)
    print(f"Improvement: {improvement:+.2f}")
    print(f"Upgrade: {'YES' if improvement > 0.05 else 'NO'}")
```

**Key Message:** Treat prompts like code — version control, test before upgrade, track regression

---

*Deck 2 of 2 — Session 04: Prompt Engineering*
