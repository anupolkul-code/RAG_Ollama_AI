# Slide Deck: LLM คืออะไร — Token, Context, Temperature
> Session 02 | Module 1: Foundation & LLM | 14 slides

---

## Slide 1 — Title

**Local RAG for Programming — Session 02**

# LLM คืออะไร + ใช้งานผ่าน Code

**Key Message**: LLM ไม่ใช่กล่องดำ — เข้าใจ Token, Context, Temperature แล้วจะควบคุมผลลัพธ์ได้
- วันนี้: ทฤษฎี 50 นาที → Workshop 110 นาที
- เครื่องมือ: qwen2.5-coder:7b + LangChain บน Ollama

---

## Slide 2 — Week Overview

**Key Message**: สิ้น session นี้คุณควบคุม LLM ผ่าน code ได้ ไม่ใช่แค่คุยผ่าน chat

**Session นี้จะเรียน:**
- LLM ทำงานกับ **Token** (หน่วยย่อยของข้อความ) — ไม่ใช่ตัวอักษร
- เรียก LLM ผ่าน Python: `invoke` / `stream` / batch
- **Context Window** — ขอบเขตของความจำ LLM
- **Temperature** — ควบคุมความ creative ของคำตอบ
- สร้าง conversation ที่ "จำ" บริบทได้

**Building block** ก่อน Session 03 (LLM Limitations → RAG Motivation)

---

## Slide 3 — LLM ทำงานอย่างไร (ภาพรวม)

**Key Message**: LLM คือ next-token predictor — ไม่ใช่ search engine ไม่ใช่ database

```
Input Text ──► Tokenizer ──► Token IDs ──► Transformer ──► Probabilities ──► Next Token
  "Write a"        ↓             ↓                              ↓                ↓
               ["Write"," a"] [13838, 264]               P("function")=0.42  "function"
```

- **ไม่ได้ "รู้" ข้อเท็จจริง** — predict token ที่เหมาะสมจาก pattern ใน training data
- **ไม่มี "ความเข้าใจ"** — statistical pattern matching ขนาดใหญ่มาก
- **ผลลัพธ์ขึ้นกับ**: คุณภาพของ prompt + ขนาด context + temperature

---

## Slide 4 — Token คืออะไร?

**Key Message**: 1 token ≠ 1 คำ — ภาษาไทยใช้ token มากกว่าอังกฤษ 3 เท่า

```
คำ/ข้อความ              → Tokens                          จำนวน
──────────────────────────────────────────────────────────────
"Hello, world!"         → ["Hello", ",", " world", "!"]     4
"def fibonacci"         → ["def", " fib", "on", "acci"]     4
"สวัสดีครับ"            → ["ส","ว","ัส","ด","ี","ค","ร","ับ"] 8
"qwen2.5-coder:7b"      → ["q","wen","2",".","5","-","coder",":","7","b"] 10
```

**กฎประมาณ:**
| ภาษา | 1 token ≈ |
|------|-----------|
| English | 4 ตัวอักษร หรือ 0.75 คำ |
| ภาษาไทย | 1–2 ตัวอักษร (3x token ของ English) |
| Code | keyword = 1 token, identifier ยาว = หลาย token |

[FIGURE: แผนภาพแสดง tokenization ของ 3 ภาษาเปรียบเทียบกัน]

---

## Slide 5 — ทำไม Token ถึงสำคัญ?

**Key Message**: Token กำหนดต้นทุน, ความเร็ว, และขีดจำกัดของ LLM ทุกตัว

**3 เหตุผลที่ต้องเข้าใจ Token:**

1. **ต้นทุน (Cost)**
   - Cloud LLM เช่น GPT-4: ราคาต่อ 1,000 tokens (input + output)
   - ภาษาไทย = 3x ต้นทุน เทียบกับ English สำหรับข้อความเดียวกัน
   - Local Ollama: ฟรี แต่ใช้เวลา CPU ต่อ token

2. **ความเร็ว (Speed)**
   - qwen2.5-coder:7b บน CPU: ~5-15 tokens/วินาที
   - Prompt 1,000 tokens → รอ ~70-200 วินาที บน CPU

3. **ขีดจำกัด (Context Limit)**
   - ไม่สามารถส่ง token เกิน context window ได้
   - นี่คือ **root problem** ที่ RAG แก้ไข

---

## Slide 6 — Context Window

**Key Message**: Context window คือ "ความจำ" ของ LLM — มีขีดจำกัด และนั่นคือปัญหาหลัก

```
┌─────────────────────────────────────────────────┐
│  Context Window: 32,768 tokens                  │
│                                                  │
│  ┌──────────────┐  ┌───────────────────────────┐│
│  │   Input      │  │       Output              ││
│  │  (Prompt)    │  │     (Response)            ││
│  │  ~24,576 tok │  │      ~8,192 tok           ││
│  └──────────────┘  └───────────────────────────┘│
└─────────────────────────────────────────────────┘
```

**qwen2.5-coder:7b = 32,768 tokens ≈**
- ไฟล์ Python 1,000 บรรทัด (ภาษาอังกฤษ)
- ไฟล์ Python 300 บรรทัด (ถ้ามี comment ภาษาไทย)
- Codebase จริงอาจมี **100,000+ บรรทัด** → ส่งไม่ได้ในครั้งเดียว

**→ นี่คือ motivation หลักของ RAG** (Session 07–12)

---

## Slide 7 — Temperature คืออะไร?

**Key Message**: Temperature = knob ที่ควบคุมความ "สร้างสรรค์" ของ LLM

[FIGURE: sliding scale จาก 0.0 ถึง 2.0 พร้อม label ใต้แต่ละจุด]

```
0.0          0.3          0.7          1.0          >1.0
 │            │            │            │             │
 ▼            ▼            ▼            ▼             ▼
Deterministic  Stable    Balanced    Creative      Chaotic
ตอบเหมือนกัน  คงที่+      สมดุล      หลากหลาย     ไม่แนะนำ
ทุกครั้ง      เล็กน้อย
```

| Use Case | Temperature |
|----------|------------|
| Code generation | **0.0** |
| Code review / debugging | 0.1–0.3 |
| Technical documentation | 0.3–0.5 |
| Creative writing | 0.7–0.9 |
| Brainstorming | 0.9–1.0 |

**Rule of thumb: coding tasks → temperature=0 เสมอ**

---

## Slide 8 — Temperature: ตัวอย่างจริง

**Key Message**: temperature=0 ให้ผล reproducible, temperature=1.0 ให้ผลแตกต่างทุกครั้ง

**Prompt:** "Suggest a variable name for storing user email"

```
temp=0.0 (รัน 3 ครั้ง):
  → user_email
  → user_email  
  → user_email

temp=1.0 (รัน 3 ครั้ง):
  → email_address
  → recipient_email
  → user_contact_info
```

**ผลกระทบต่อ code quality:**
- temp=0.0: unit test ผ่านสม่ำเสมอ, reproducible
- temp=1.0: creative แต่อาจได้ code ที่แตกต่างกันทุกครั้ง

[EXAMPLE: Workshop Step 2 — ทดลอง temperature ด้วยตนเอง]

---

## Slide 9 — Sampling Strategies (เพิ่มเติม)

**Key Message**: Temperature ไม่ใช่แค่ parameter เดียว — top_p และ top_k ก็มีผล

**3 parameters ที่ควบคุม randomness:**

| Parameter | คืออะไร | ค่าที่แนะนำ |
|-----------|---------|------------|
| `temperature` | scale probability distribution | 0.0 สำหรับ code |
| `top_p` | nucleus sampling — เลือกจาก top P% | 0.9 (default) |
| `top_k` | เลือกจาก top K tokens เท่านั้น | 40 (default) |

**สำหรับ coding tasks:**
```python
llm = OllamaLLM(
    model="qwen2.5-coder:7b",
    temperature=0,       # deterministic
    top_p=1.0,           # ไม่จำกัด nucleus
    top_k=1              # เลือก token ที่ดีที่สุดเสมอ
)
```

---

## Slide 10 — Context Window ใน Practice

**Key Message**: Context สะสมทุก turn — ต้องบริหารจัดการไม่ให้เกิน limit

```
Turn 1:  System(100) + User(50)                     = 150 tokens
Turn 2:  System(100) + User(50) + AI(200) + User(30) = 380 tokens
Turn 3:  ... + AI(300) + User(40)                   = 720 tokens
...
Turn 20: อาจถึง 15,000 tokens หรือมากกว่า
```

**Strategies เมื่อ context เกิน:**
1. **Truncation** — ตัด message เก่าสุดออก
2. **Summarization** — สรุป history เป็น 1 block
3. **RAG** — ดึงเฉพาะส่วนที่เกี่ยวข้องมา (Session 07+)
4. **Sliding window** — เก็บแค่ N turn ล่าสุด

[FIGURE: แผนภาพ context ที่สะสมขึ้นตาม turn]

---

## Slide 11 — LLM ≠ Search Engine

**Key Message**: LLM generate ข้อมูล ไม่ได้ retrieve — นั่นคือเหตุผลที่มัน hallucinate

```
Search Engine          LLM
     │                  │
     ▼                  ▼
รับ query           รับ prompt
     │                  │
     ▼                  ▼
Match กับ index      Predict next token
     │                  │
     ▼                  ▼
Return documents    Generate text
(ของจริงใน DB)      (อาจเป็นข้อมูลที่แต่งขึ้น)
```

**ผลลัพธ์:**
- LLM อาจ "hallucinate" — สร้างข้อมูลที่ไม่มีจริง
- LLM ไม่รู้ข้อมูลหลัง training cutoff
- LLM ไม่รู้จัก codebase ส่วนตัวของคุณ

**→ RAG แก้ปัญหานี้ด้วยการ inject context จริงๆ เข้าไปใน prompt**

---

## Slide 12 — Stateless LLM

**Key Message**: LLM ไม่มี memory — ต้องส่ง history ทุกครั้ง เราจัดการเอง

```python
# ❌ LLM ไม่จำสิ่งนี้:
llm.invoke("ฉันชื่อ Alice")
llm.invoke("ฉันชื่ออะไร")  # ตอบ: "ฉันไม่ทราบชื่อของคุณ"

# ✓ ต้องส่ง history เอง:
messages = [
    HumanMessage("ฉันชื่อ Alice"),
    AIMessage("สวัสดีครับ Alice!"),
    HumanMessage("ฉันชื่ออะไร"),
]
chat.invoke(messages)  # ตอบ: "คุณชื่อ Alice ครับ"
```

**เปรียบเทียบ:**
- Phone call: ต้องอธิบายทุกอย่างใหม่ทุกครั้งที่โทร
- Human memory: จำบริบทข้ามวัน ข้ามเดือน

---

## Slide 13 — สรุป Session 02 Theory

**Key Message**: Token + Context + Temperature + Stateless = พื้นฐานทุกอย่างของ LLM development

| แนวคิด | สรุป 1 ประโยค |
|--------|-------------|
| **Token** | หน่วยพื้นฐาน (~4 chars EN, 1-2 chars TH) |
| **Context Window** | จำนวน token สูงสุด = ขีดจำกัด "ความจำ" ต่อ request |
| **Temperature** | 0=deterministic, 1=creative — coding ใช้ 0 เสมอ |
| **Stateless** | LLM ไม่จำ — เราต้องส่ง history เองทุก request |
| **Hallucination** | LLM generate ไม่ retrieve — อาจสร้างข้อมูลเท็จ |
| **Context Problem** | Codebase ใหญ่กว่า context window → ต้องการ RAG |

---

## Slide 14 — Preview ช่วงถัดไป

**Key Message**: ทฤษฎีเสร็จแล้ว — ถึงเวลาเขียน code จริง

**Workshop ช่วงที่ 2 (60 นาที):**
- Step 1: Basic LLM invoke
- Step 2: Temperature experiment
- Step 3: ChatOllama + System Prompt
- Step 4: PromptTemplate + LCEL chain

**Workshop ช่วงที่ 3 (50 นาที):**
- Step 5: Streaming output
- Step 6: Conversation history loop

**เปิด terminal แล้วรัน:**
```powershell
# ตรวจสอบว่า Ollama พร้อม
ollama list
# ควรเห็น qwen2.5-coder:7b และ nomic-embed-text
```
