# RAG Ollama — Local Offline AI

ระบบ RAG (Retrieval-Augmented Generation) ที่ทำงานได้ **100% offline** บนเครื่อง
โดยใช้ [Ollama](https://ollama.com) เป็น LLM และ [FAISS](https://github.com/facebookresearch/faiss) เป็น vector database

---

## ความสามารถ

-  โหลดข้อมูลได้หลายรูปแบบ: **PDF, TXT, MD, DOCX, CSV, JSON, XLSX, URL**
-  ค้นหาข้อมูลที่เกี่ยวข้องด้วย semantic search
-  ถามตอบผ่าน **Web UI** (เบราว์เซอร์) หรือ terminal แบบ interactive
-  ตรวจจับไฟล์ใหม่อัตโนมัติ ไม่ embed ซ้ำ
-  ดึงข้อมูลจากเว็บได้ (ต้องมีเน็ตครั้งแรก)
-  ทำงาน offline ได้ทั้งหมดหลังจาก setup

---

##  สิ่งที่ต้องติดตั้งก่อน

### 1. ติดตั้ง Ollama
ดาวน์โหลดจาก [https://ollama.com](https://ollama.com) แล้วติดตั้ง

### 2. ดาวน์โหลด model ที่ต้องการใช้
```bash
# Model สำหรับสร้างคำตอบ (เลือก 1 อัน)
ollama pull scb10x/llama3.1-typhoon2-8b-instruct   # ภาษาไทย แนะนำ
ollama pull qwen2.5-coder:7b                        # เขียนโค้ด

# Model สำหรับ embedding (จำเป็นต้องมี)
ollama pull nomic-embed-text
```

### 3. ติดตั้ง uv (Python package manager)
```bash
pip install uv
```

---

##  วิธีติดตั้งและรัน

### ขั้นที่ 1: Clone โปรเจกต์
```bash
git clone https://github.com/<your-username>/RAG_Ollama.git
cd RAG_Ollama
```

### ขั้นที่ 2: ติดตั้ง dependencies
```bash
uv sync
```

### ขั้นที่ 3: เปิด Ollama server
```bash
ollama serve
```
> เปิดค้างไว้ใน terminal แยก

### ขั้นที่ 4: รันโปรแกรม

** แบบ Web App (แนะนำ)** — เปิดเบราว์เซอร์ได้เลย
```bash
uv run .\app.py
```
แล้วเปิดเบราว์เซอร์ที่ **http://localhost:5000**

** แบบ Terminal** — ถามตอบผ่าน command line
```bash
uv run .\chat.py
```

---

##  โครงสร้างโปรเจกต์

```
RAG_Ollama/
├── app.py               ←  Web App (Flask) — รันเพื่อเปิดเบราว์เซอร์
├── chat.py              ←  Terminal Chat — รันเพื่อถามคำถามใน terminal
├── rag_loader.py        ← library: load, embed, query
├── web/                 ← หน้าเว็บ
│   ├── index.html       ← หน้าหลัก
│   ├── style.css        ← สไตล์ (Dark Mode)
│   └── app.js           ← JavaScript
├── my_data/             ← วางไฟล์ข้อมูลที่นี่
├── my_knowledge_base/   ← สร้างอัตโนมัติ
├── pyproject.toml       ← dependencies
└── uv.lock
```

---

##  วิธีเพิ่มข้อมูลให้ AI เรียนรู้

### วิธีที่ 1: เพิ่มไฟล์
1. วางไฟล์ (PDF, TXT, DOCX ฯลฯ) ลงใน `my_data/`
2. รัน `uv run .\chat.py` — ระบบ embed อัตโนมัติ

### วิธีที่ 2: เพิ่ม URL (ต้องมีเน็ตครั้งแรก)
แก้ไข `MY_URLS` ใน `chat.py`:
```python
MY_URLS = [
    "https://en.wikipedia.org/wiki/Python_(programming_language)",
    # เพิ่ม URL อื่นได้ที่นี่
]
```
แล้วรัน `uv run .\chat.py` — ดึงและ embed ให้อัตโนมัติ

---

##  การใช้งาน Web App

หลังจากรัน `uv run .\app.py` และเปิดเบราว์เซอร์ที่ `http://localhost:5000` จะมี 3 แท็บ:

| แท็บ | คำอธิบาย |
|------|----------|
|  **ถามตอบ** | พิมพ์คำถาม กด Enter รับคำตอบจาก AI |
|  **จัดการไฟล์** | ลากวางไฟล์อัปโหลด, ดูสถานะ, ลบไฟล์ได้ |
|  **Embed ข้อมูล** | กด embed ไฟล์ใหม่หรือ URL ทั้งหมด |

> **หมายเหตุ:** ต้องเปิด `ollama serve` ไว้ใน terminal แยกก่อนเสมอ

---

##  การตั้งค่า Model

แก้ได้ใน `rag_loader.py`:
```python
EMBED_MODEL = "nomic-embed-text"                          # embedding model
CHAT_MODEL  = "scb10x/llama3.1-typhoon2-8b-instruct"     # chat model
```

---

##  Dependencies หลัก

| Package | ใช้ทำอะไร |
|---------|----------|
| `langchain` | RAG pipeline |
| `langchain-ollama` | เชื่อมกับ Ollama |
| `faiss-cpu` | vector database |
| `nomic-embed-text` | embedding model (via Ollama) |
| `pypdf` | โหลด PDF |
| `beautifulsoup4` | ดึงข้อมูลจากเว็บ |
| `flask` | Web App server |
