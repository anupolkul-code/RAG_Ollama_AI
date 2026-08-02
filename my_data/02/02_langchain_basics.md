# Slide Deck: LangChain + Python — invoke, stream, history
> Session 02 | Module 1: Foundation & LLM | 12 slides

---

## Slide 1 — Title

**Local RAG for Programming — Session 02 (Workshop)**

# LangChain Basics: เรียก LLM ผ่าน Python

**Key Message**: LangChain คือ layer ที่ทำให้เราสลับ LLM ได้ง่าย — วันนี้ใช้ Ollama, อนาคตใช้ OpenAI หรืออื่นๆ โดยแทบไม่ต้องเปลี่ยน code
- Steps: 1 (invoke) → 2 (temperature) → 3 (chat+system) → 4 (template) → 5 (stream) → 6 (history)

---

## Slide 2 — LangChain Architecture

**Key Message**: LangChain แยก "interface" ออกจาก "implementation" — ทำให้ swap LLM ได้ทันที

```
Your Code
    │
    ▼
LangChain Interface
(OllamaLLM / ChatOllama)
    │
    ▼
Ollama Server (localhost:11434)
    │
    ▼
qwen2.5-coder:7b (local model)
```

**2 คลาสหลักที่ใช้วันนี้:**
| คลาส | ใช้เมื่อ | Input | Output |
|------|---------|-------|--------|
| `OllamaLLM` | text-in text-out | string | string |
| `ChatOllama` | มี roles (system/user/AI) | list[Message] | AIMessage |

---

## Slide 3 — Step 1: Basic Invoke

**Key Message**: `.invoke()` คือ simplest API — ส่ง string รับ string

```python
# ─── install ──────────────────────────────────────────
# PowerShell: uv add langchain-ollama
# ─────────────────────────────────────────────────────

from langchain_ollama import OllamaLLM

# ─── สร้าง LLM instance ───────────────────────────────
# วัตถุประสงค์: สร้าง connection ไปยัง Ollama service ที่รันอยู่
llm = OllamaLLM(model="qwen2.5-coder:7b")

# ─── invoke: ส่ง prompt รับ response ─────────────────
# วัตถุประสงค์: .invoke() block จนกว่าจะได้ response ครบ
response = llm.invoke("Write a Python function that returns the factorial of n")
print(response)
```

**รันด้วย:**
```powershell
uv run python step1_basic.py
```

[EXAMPLE: ผล output แสดง Python function พร้อม comment]

---

## Slide 4 — Step 2: Temperature Experiment

**Key Message**: ทดลองด้วยตนเองคือวิธีเดียวที่จะเชื่อว่า temperature=0 ให้ผลสม่ำเสมอจริง

```python
prompt = "Suggest a creative variable name for storing user's email address"

for temp in [0.0, 0.5, 1.0]:
    # ─── สร้าง LLM ด้วย temperature ต่างกัน ──────────
    # วัตถุประสงค์: เห็นความแตกต่างของ output ตาม temperature
    llm = OllamaLLM(model="qwen2.5-coder:7b", temperature=temp)
    response = llm.invoke(prompt)
    print(f"\n--- Temperature {temp} ---")
    print(response.strip())
```

**ผลที่คาดหวัง:**
```
--- Temperature 0.0 ---
user_email          ← เหมือนกันทุกครั้ง

--- Temperature 1.0 ---
email_address / recipient_email / contact_email  ← แตกต่างกันทุกครั้ง
```

---

## Slide 5 — Step 3: ChatOllama + System Prompt

**Key Message**: System prompt คือ "บุคลิก" ที่กำหนดให้ AI ก่อนเริ่ม conversation

```python
from langchain_ollama import ChatOllama
from langchain_core.messages import SystemMessage, HumanMessage

chat = ChatOllama(model="qwen2.5-coder:7b", temperature=0)

# ─── กำหนด role ด้วย system message ──────────────────
# วัตถุประสงค์: system message กำหนดว่า AI ควรตอบแบบไหน
messages = [
    SystemMessage(content="You are a senior Python developer. Be concise and practical."),
    HumanMessage(content="What's wrong with: for i in range(len(mylist)): print(mylist[i])")
]

response = chat.invoke(messages)
print(response.content)
```

**ผลที่คาดหวัง:**
```
Use direct iteration instead:
for item in mylist:
    print(item)
```

---

## Slide 6 — 3 Message Types

**Key Message**: LLM รองรับ 3 roles ที่มีบทบาทชัดเจน — ต้องใช้ให้ถูก

| Message Type | วัตถุประสงค์ | ตัวอย่าง |
|-------------|------------|---------|
| `SystemMessage` | กำหนด persona/constraints ของ AI | "You are a Python expert." |
| `HumanMessage` | สิ่งที่ user พิมพ์ | "How do I read a CSV file?" |
| `AIMessage` | response ของ AI (บันทึกไว้ใน history) | "Use pd.read_csv('file.csv')" |

```python
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

# ─── pattern ทั่วไป ────────────────────────────────
conversation = [
    SystemMessage(content="..."),   # ใส่แค่ครั้งแรก
    HumanMessage(content="..."),    # turn 1
    AIMessage(content="..."),       # ตอบ turn 1
    HumanMessage(content="..."),    # turn 2
]
```

---

## Slide 7 — Step 4: PromptTemplate

**Key Message**: PromptTemplate = template สำหรับ reuse prompt pattern — ลด code ซ้ำ

```python
from langchain_core.prompts import PromptTemplate
from langchain_ollama import OllamaLLM

# ─── สร้าง template ด้วย variables ────────────────────
# วัตถุประสงค์: {language} และ {task} ถูก inject ตอน invoke
template = PromptTemplate.from_template(
    "You are a {language} expert. {task}\n"
    "Provide a clean, well-commented solution."
)

llm = OllamaLLM(model="qwen2.5-coder:7b", temperature=0)

# ─── LCEL chain: template → llm ───────────────────────
# วัตถุประสงค์: | operator เชื่อม components เหมือน Unix pipe
chain = template | llm

# ─── invoke chain ─────────────────────────────────────
result = chain.invoke({
    "language": "Python",
    "task": "Write a function to merge two sorted lists"
})
```

---

## Slide 8 — LCEL: LangChain Expression Language

**Key Message**: LCEL ทำให้เชื่อม components ด้วย `|` — เหมือน Unix pipe สำหรับ AI

```
input_dict
    │
    ▼
PromptTemplate  →  format string
    │
    ▼  (|)
OllamaLLM       →  generate response
    │
    ▼  (|)
StrOutputParser →  extract string (optional)
    │
    ▼
output
```

```python
# ─── สร้าง chain หลายขั้นตอน ──────────────────────────
from langchain_core.output_parsers import StrOutputParser

chain = template | llm | StrOutputParser()
result = chain.invoke({"language": "Go", "task": "Write a hello world function"})
```

**ข้อดี:** Composable, Lazy evaluation, Streamable

---

## Slide 9 — Step 5: Streaming Output

**Key Message**: `.stream()` ทำให้ user เห็น response ทันที ไม่ต้องรอจนครบ

```python
import sys
from langchain_ollama import OllamaLLM

llm = OllamaLLM(model="qwen2.5-coder:7b", temperature=0)

print("Response:")
print("-" * 40)

# ─── iterate generator ทีละ chunk ─────────────────────
# วัตถุประสงค์: แต่ละ chunk = tokens ใหม่ที่ generate มา
#              flush=True บังคับให้แสดงผลทันที ไม่รอ buffer
for chunk in llm.stream("Explain Python decorators in 3 bullet points"):
    print(chunk, end="", flush=True)

print("\n" + "-" * 40)
```

**สำคัญ:** ถ้าไม่มี `flush=True` → ผลจะแสดงทีเดียวตอนจบ (ไม่ stream)

---

## Slide 10 — Step 6: Conversation History

**Key Message**: เพราะ LLM stateless — ต้องส่ง history ทั้งหมดทุก request ด้วยตัวเอง

```python
from langchain_ollama import ChatOllama
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

chat = ChatOllama(model="qwen2.5-coder:7b", temperature=0)

# ─── เริ่มต้นด้วย system message ─────────────────────
conversation_history = [
    SystemMessage(content="You are a Python tutor. Be brief and educational.")
]

while True:
    user_input = input("\nคุณ: ").strip()
    if user_input.lower() in ['quit', 'q']:
        break
    
    # ─── append → invoke → append ─────────────────────
    # วัตถุประสงค์: pattern นี้คือหัวใจของ stateful conversation
    conversation_history.append(HumanMessage(content=user_input))
    response = chat.invoke(conversation_history)
    conversation_history.append(AIMessage(content=response.content))
    
    print(f"AI: {response.content}")
```

---

## Slide 11 — Pattern สำคัญ: append → invoke → append

**Key Message**: 3 บรรทัดนี้คือ pattern ที่ใช้ใน RAG, Chatbot, และ Agent ทุกตัว

```
ก่อน invoke turn N:

conversation_history = [
    SystemMessage("..."),         ← กำหนดครั้งเดียว
    HumanMessage("turn 1"),       ← จาก user
    AIMessage("response 1"),      ← บันทึก AI response
    HumanMessage("turn 2"),       ← จาก user
    AIMessage("response 2"),      ← บันทึก AI response
    HumanMessage("turn N"),       ← ← ← ส่งมาใหม่
]
                                         ↓
                               response = chat.invoke(history)
                                         ↓
                      history.append(AIMessage(response.content))
```

**Memory grows linearly** — ต้องมี strategy จัดการ (truncate/summarize) เมื่อ history ใหญ่

---

## Slide 12 — สรุปและ Checklist

**Key Message**: ถ้าทำ 6 steps ครบ คุณพร้อมสำหรับ Session 03 แล้ว

**สิ่งที่เรียนรู้วันนี้:**

| Step | สิ่งที่ทำ | Pattern |
|------|---------|---------|
| 1 | Basic invoke | `llm.invoke(string) → string` |
| 2 | Temperature | `OllamaLLM(temperature=N)` |
| 3 | System prompt | `ChatOllama + SystemMessage` |
| 4 | PromptTemplate | `template | llm` (LCEL) |
| 5 | Streaming | `for chunk in llm.stream(...): print(chunk, flush=True)` |
| 6 | History | `append → invoke → append` loop |

**Checklist ก่อนออก:**
```
□ llm.invoke() ได้ response จาก qwen2.5-coder:7b
□ เห็นความแตกต่างของ temperature=0.0 vs 1.0
□ .stream() แสดงผล real-time ได้
□ conversation history "จำ" ข้อมูลข้าม turn ได้
□ สร้าง PromptTemplate พร้อม variables ได้
```

**Session 03:** ทดสอบขีดจำกัด LLM — เมื่อไหรมัน hallucinate และทำไม RAG จึงจำเป็น
