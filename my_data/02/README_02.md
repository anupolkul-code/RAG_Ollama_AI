# Session 02 — LLM คืออะไร + ใช้งานผ่าน Code
> **Module 1: Foundation & LLM** | ครั้งที่ 2 จาก 14 | 3 ชั่วโมง

---

## เป้าหมายของ Session นี้

เมื่อจบ session นี้ นักเรียนจะสามารถ:
- อธิบายได้ว่า Token, Context Window, และ Temperature คืออะไรและส่งผลต่อ output อย่างไร
- เรียกใช้ `qwen2.5-coder:7b` ผ่าน Python (invoke, stream, batch) ได้
- สร้าง conversation history และ PromptTemplate สำหรับงาน coding ได้

---

## ตารางเวลา

| ช่วง | เวลา | กิจกรรม |
|------|------|---------|
| 1 | 50 นาที | Theory — Token, Context Window, Temperature, Sampling |
| 2 | 60 นาที | Workshop — เรียก LLM จาก Python, ทดลองเปลี่ยน parameters |
| 3 | 50 นาที | Workshop — Streaming output, Conversation history |
| 4 | 20 นาที | สรุป + ข้อจำกัด LLM (preview Session 03) |

---

## ช่วงที่ 1 — Theory: LLM ทำงานอย่างไร (50 นาที)

### 1.1 Token คืออะไร?

LLM ไม่ได้ประมวลผล "ตัวอักษร" — มันประมวลผล **token** ซึ่งเป็นกลุ่มของตัวอักษร

```python
# ตัวอย่าง tokenization (approximate)
"Hello, world!"  →  ["Hello", ",", " world", "!"]  # 4 tokens
"def fibonacci"  →  ["def", " fib", "on", "acci"]  # 4 tokens
"สวัสดี"         →  ["ส", "ว", "ัส", "ด", "ี"]    # 5 tokens (Thai ใช้ token มากกว่า)
```

**กฎทั่วไป:**
- ภาษาอังกฤษ: ~1 token ≈ 0.75 คำ หรือ 4 ตัวอักษร
- ภาษาไทย: ~1 token ≈ 1-2 ตัวอักษร (ใช้ token มากกว่า English ~3x)
- Code: keyword สั้นๆ = 1 token, identifier ยาว = หลาย tokens

### 1.2 Context Window

Context window = จำนวน token สูงสุดที่ LLM รับได้ในครั้งเดียว (input + output รวมกัน)

```
qwen2.5-coder:7b context window = 32,768 tokens
≈ 24,000 คำภาษาอังกฤษ
≈ ไฟล์ Python ~1,000 บรรทัด
≈ ไฟล์ Python ~300 บรรทัด (ถ้าเป็นภาษาไทย)
```

**ปัญหาของ context window limit:**
- ไม่สามารถส่ง codebase ทั้งหมดไปได้ในครั้งเดียว
- นี่คือเหตุผลหลักที่เราต้องการ RAG

### 1.3 Temperature

Temperature ควบคุม "ความสร้างสรรค์" หรือ "randomness" ของ output:

| Temperature | พฤติกรรม | เหมาะกับ |
|------------|----------|---------|
| 0.0 | Deterministic — ตอบเหมือนกันทุกครั้ง | Code generation, factual Q&A |
| 0.3 | Mostly stable + slight variation | Code review, debugging |
| 0.7 | Balanced creativity | General writing |
| 1.0 | High creativity, may be incoherent | Brainstorming |
| >1.0 | Very random, often gibberish | ไม่แนะนำ |

**สำหรับ coding tasks: ใช้ temperature=0.0 หรือ 0.1 เสมอ**

---

## ช่วงที่ 2 — Workshop: เรียก LLM จาก Python (60 นาที)

### Step 1: Basic LLM Call

```python
# ─── setup ─────────────────────────────────────────────────────────────────
# วัตถุประสงค์: นำเข้า OllamaLLM เพื่อเชื่อมต่อกับ Ollama service
from langchain_ollama import OllamaLLM

# ─── สร้าง LLM instance ────────────────────────────────────────────────────
# วัตถุประสงค์: สร้าง connection ไปยัง qwen2.5-coder:7b บน localhost
llm = OllamaLLM(model="qwen2.5-coder:7b")

# ─── invoke: รับ response เดียว ────────────────────────────────────────────
# วัตถุประสงค์: .invoke() ส่ง prompt และรอจน response ครบก่อน return
response = llm.invoke("Write a Python function that returns the factorial of n")
print(response)
```

**รันใน Windows PowerShell:**
```powershell
uv run python step1_basic.py
```

### Step 2: ทดลองเปลี่ยน Temperature

```python
# ─── temperature experiment ────────────────────────────────────────────────
# วัตถุประสงค์: เห็นว่า temperature ส่งผลต่อ output อย่างไรในทางปฏิบัติ
prompt = "Suggest a creative variable name for storing user's email address"

for temp in [0.0, 0.5, 1.0]:
    # ─── สร้าง LLM ด้วย temperature ต่างกัน ────────────────────────────
    # วัตถุประสงค์: แต่ละ instance มี randomness ต่างกัน
    llm = OllamaLLM(model="qwen2.5-coder:7b", temperature=temp)
    response = llm.invoke(prompt)
    print(f"\n--- Temperature {temp} ---")
    print(response.strip())
```

**สังเกต:** temperature=0.0 ตอบเหมือนกันทุกครั้ง, temperature=1.0 แตกต่างกัน

### Step 3: ChatOllama กับ System Prompt

```python
# ─── import chat model ─────────────────────────────────────────────────────
# วัตถุประสงค์: ChatOllama รองรับ system/user/assistant roles
from langchain_ollama import ChatOllama
from langchain_core.messages import SystemMessage, HumanMessage

# ─── สร้าง chat model ──────────────────────────────────────────────────────
# วัตถุประสงค์: กำหนด model และ parameters
chat = ChatOllama(model="qwen2.5-coder:7b", temperature=0)

# ─── ส่ง messages พร้อม system prompt ─────────────────────────────────────
# วัตถุประสงค์: system message กำหนด role และ behavior ของ AI
messages = [
    SystemMessage(content="You are a senior Python developer. Be concise and practical."),
    HumanMessage(content="What's wrong with this code: for i in range(len(mylist)): print(mylist[i])")
]

response = chat.invoke(messages)
print(response.content)
```

### Step 4: PromptTemplate

```python
# ─── import PromptTemplate ─────────────────────────────────────────────────
# วัตถุประสงค์: PromptTemplate ทำให้ reuse prompt pattern ได้
from langchain_core.prompts import PromptTemplate

# ─── สร้าง template ────────────────────────────────────────────────────────
# วัตถุประสงค์: {language} และ {task} เป็น variables ที่เปลี่ยนได้
template = PromptTemplate.from_template(
    "You are a {language} expert. {task}\n"
    "Provide a clean, well-commented solution."
)

# ─── สร้าง chain: template → llm ────────────────────────────────────────────
# วัตถุประสงค์: LCEL chain ประกอบ component เข้าด้วยกัน (| operator)
llm = OllamaLLM(model="qwen2.5-coder:7b", temperature=0)
chain = template | llm

# ─── invoke chain ──────────────────────────────────────────────────────────
# วัตถุประสงค์: ส่ง variables ผ่าน dict
result = chain.invoke({
    "language": "Python",
    "task": "Write a function to merge two sorted lists"
})
print(result)
```

---

## ช่วงที่ 3 — Workshop: Streaming + Conversation History (50 นาที)

### Step 5: Streaming Output

```python
# ─── streaming: แสดง token ทีละตัว ────────────────────────────────────────
# วัตถุประสงค์: .stream() return generator — output แสดงผลแบบ real-time
# ทำให้ UX ดีขึ้น ผู้ใช้เห็น response ขณะที่ LLM กำลัง generate
import sys

llm = OllamaLLM(model="qwen2.5-coder:7b", temperature=0)

print("Streaming response:")
print("-" * 40)

# ─── iterate generator ─────────────────────────────────────────────────────
# วัตถุประสงค์: แต่ละ chunk เป็น string ของ token ที่ generate มาใหม่
for chunk in llm.stream("Explain what a Python decorator is in 3 bullet points"):
    print(chunk, end="", flush=True)

print("\n" + "-" * 40)
```

### Step 6: Conversation History

```python
# ─── conversation history ──────────────────────────────────────────────────
# วัตถุประสงค์: LLM stateless — ต้องส่ง history ทุกครั้ง
# เราจัดการ history เองโดย append ทุก message
from langchain_ollama import ChatOllama
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

chat = ChatOllama(model="qwen2.5-coder:7b", temperature=0)

# ─── initialize conversation ───────────────────────────────────────────────
# วัตถุประสงค์: system message กำหนด context สำหรับทั้ง conversation
conversation_history = [
    SystemMessage(content="You are a Python tutor. Keep answers brief and educational.")
]

print("Python Tutor Chatbot (type 'quit' to exit)")
print("=" * 50)

while True:
    # รับ input จาก user
    user_input = input("\nคุณ: ").strip()
    if user_input.lower() in ['quit', 'exit', 'q']:
        print("ลาก่อน!")
        break
    if not user_input:
        continue

    # ─── เพิ่ม user message ───────────────────────────────────────────────
    # วัตถุประสงค์: บันทึก user message ไว้ใน history
    conversation_history.append(HumanMessage(content=user_input))

    # ─── ส่ง history ทั้งหมดไป ───────────────────────────────────────────
    # วัตถุประสงค์: LLM ต้องเห็น context ทั้งหมดจึงจะ "จำ" การสนทนาได้
    response = chat.invoke(conversation_history)

    # ─── บันทึก AI response ───────────────────────────────────────────────
    # วัตถุประสงค์: เพิ่ม response ใน history เพื่อ conversation ต่อ
    conversation_history.append(AIMessage(content=response.content))

    print(f"\nAI: {response.content}")
    print(f"[History: {len(conversation_history)} messages]")
```

---

## ช่วงที่ 4 — สรุปและ Preview (20 นาที)

### สิ่งที่เรียนรู้วันนี้

| แนวคิด | สรุป |
|--------|------|
| **Token** | หน่วยที่ LLM ประมวลผล (~4 chars ภาษาอังกฤษ) |
| **Context Window** | จำนวน token สูงสุดต่อ request (32K tokens) |
| **Temperature** | ค่า 0.0 = deterministic, 1.0 = creative |
| **invoke()** | ส่ง prompt รับ response ครั้งเดียว |
| **stream()** | รับ response แบบ real-time token by token |
| **History** | LLM stateless ต้องส่ง history เองทุกครั้ง |
| **PromptTemplate** | Pattern สำหรับ reuse prompts |

### Preview Session 03

Session ถัดไปจะค้นพบว่า LLM **ไม่สามารถ**:
- รู้จัก codebase ของคุณโดยตรง
- ตอบเกี่ยวกับ internal APIs ที่ไม่ได้ public
- ไม่ hallucinate ตลอดเวลา

นี่คือ **motivation** ที่แท้จริงสำหรับ RAG pipeline

---

## แนวคิดสำคัญที่พบในครั้งนี้

| แนวคิด | คำอธิบายสั้น |
|--------|------------|
| **Token** | หน่วยพื้นฐานที่ LLM ประมวลผล ≠ คำ |
| **Context Window** | ขีดจำกัดของ "ความจำ" ต่อ request |
| **Temperature** | Randomness knob (0=deterministic, 1=creative) |
| **OllamaLLM** | LangChain wrapper สำหรับ Ollama models |
| **ChatOllama** | Chat version รองรับ roles (system/user/AI) |
| **LCEL** | LangChain Expression Language: `template | llm` |
| **Stateless** | LLM ไม่จำ — ต้องส่ง history เองทุกครั้ง |

---

## ปัญหาที่พบบ่อยและวิธีแก้

| ปัญหา | วิธีแก้ |
|-------|---------|
| `ConnectionRefusedError` | รัน `ollama serve` ใน terminal แยก |
| Response ช้ามาก | ปกติสำหรับ CPU, 7B model ใช้เวลา ~30-60 วินาที |
| `model not found` | รัน `ollama pull qwen2.5-coder:7b` ก่อน |
| `ImportError: langchain_ollama` | รัน `uv add langchain-ollama` |
| Stream ไม่แสดงทันที | เพิ่ม `flush=True` ใน `print()` |

---

## Session ถัดไป

**Session 03 — LLM กับ Code: จุดแข็งและข้อจำกัด**

จะเรียนรู้:
- ทดสอบว่า LLM รู้อะไรและไม่รู้อะไรได้ในทางปฏิบัติ
- Hallucination คืออะไรและเกิดขึ้นอย่างไร
- ทำไม LLM ถึงตอบผิดแต่ดูมั่นใจมาก
- ปัญหาอะไรที่ RAG แก้ได้จริง

---

## Checklist ก่อนออกจาก Session นี้

```
□ เรียก llm.invoke() ได้และเห็น response จาก qwen2.5-coder:7b
□ ทดลองเปลี่ยน temperature และเห็นความแตกต่างของ output
□ ใช้ .stream() แสดง token แบบ real-time ได้
□ สร้าง conversation history loop ที่จำการสนทนาได้
□ สร้าง PromptTemplate พร้อม variables ได้
□ เข้าใจว่า LLM "stateless" หมายความว่าอะไร
```
