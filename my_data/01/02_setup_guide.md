# Slide Deck: Setup Guide — Windows
> Session 01 | Module 1: Foundation | 9 slides

---

## Slide 1 — Title
**Setup Guide: Windows**
ติดตั้ง Local RAG Stack บน Windows ตั้งแต่ต้น

---

## Slide 2 — สิ่งที่จะติดตั้ง
**Key Message**: ทุกอย่างติดตั้งผ่าน winget — package manager ของ Windows

**Checklist:**
- [ ] VS Code + Python extension
- [ ] Ollama (local LLM runner)
- [ ] uv (Python package manager)
- [ ] Models: qwen2.5-coder:7b + nomic-embed-text
- [ ] Python packages: LangChain, FAISS, Kuzu, Streamlit

**ใช้เวลาประมาณ:** 45-75 นาที (ขึ้นกับ internet speed)

**Disk ที่ต้องการ:** ~6 GB (models 5GB + packages 1GB)

---

## Slide 3 — Step 1: VS Code
**Key Message**: VS Code เป็น IDE หลักตลอดหลักสูตร

```powershell
# ติดตั้ง VS Code ผ่าน winget
winget install Microsoft.VisualStudioCode

# Extensions ที่แนะนำ (ติดตั้งใน VS Code):
# - Python (Microsoft)
# - Pylance
# - Python Debugger
# - GitLens (optional)
```

**หรือ:** ดาวน์โหลดจาก https://code.visualstudio.com/

**ตรวจสอบ:**
```powershell
code --version
# ควรได้: 1.XX.X
```

---

## Slide 4 — Step 2: Ollama
**Key Message**: Ollama ทำให้รัน LLM บน Windows ง่ายเหมือนรัน Node.js

```powershell
# ติดตั้ง Ollama
winget install Ollama.Ollama

# ✅ restart PowerShell หลังติดตั้ง

# ตรวจสอบ
ollama --version

# Ollama รันเป็น background service อัตโนมัติ
# ดูได้ที่ http://localhost:11434
```

**หมายเหตุ Windows:**
- Ollama จะรันเป็น system service อัตโนมัติ
- ถ้า `ollama: command not found` → restart terminal

---

## Slide 5 — Step 3: Pull Models
**Key Message**: Pull models ครั้งเดียว ใช้ได้ตลอด

```powershell
# LLM หลักสำหรับ code (4.7 GB)
ollama pull qwen2.5-coder:7b

# Embedding model (274 MB)
ollama pull nomic-embed-text

# ตรวจสอบ models ที่มี
ollama list
```

**ทางเลือก ถ้า RAM น้อย:**
```powershell
# Model เล็กกว่า (3.8 GB, RAM ~5GB)
ollama pull qwen2.5-coder:3b
```

**ทางเลือก ถ้า RAM เยอะ (≥16GB):**
```powershell
# Model ใหญ่กว่า แม่นยำกว่า (8.9 GB)
ollama pull qwen2.5-coder:14b
```

---

## Slide 6 — Step 4: uv + Project Setup
**Key Message**: uv สร้าง project พร้อม virtual environment ในคำสั่งเดียว

```powershell
# ติดตั้ง uv
winget install astral-sh.uv

# ✅ restart PowerShell

# สร้าง project
uv init coding-assistant --python 3.11
cd coding-assistant

# โครงสร้างที่ได้:
# coding-assistant/
# ├── .venv/           ← สร้างอัตโนมัติ
# ├── pyproject.toml   ← แทน requirements.txt
# ├── .python-version
# └── hello.py
```

---

## Slide 7 — Step 5: ติดตั้ง Python Packages
**Key Message**: ใช้ `uv add` แทน `pip install` เสมอ

```powershell
# ติดตั้งทุก package ในคำสั่งเดียว
uv add `
  langchain-ollama `
  langchain-community `
  langchain-core `
  faiss-cpu `
  kuzu `
  streamlit `
  pypdf `
  python-dotenv `
  networkx `
  matplotlib `
  rank-bm25 `
  numpy

# ตรวจสอบ
uv pip list
```

---

## Slide 8 — Step 6: ทดสอบ Setup
**Key Message**: รัน test_setup.py ต้องผ่านทุก ✅ ก่อนดำเนินการต่อ

```powershell
# รัน test script
uv run python test_setup.py
```

**ผลลัพธ์ที่ต้องการ:**
```
✓ Ollama connection: OK
✓ qwen2.5-coder:7b: OK (response: "OK")
✓ nomic-embed-text: vector 768 dims
✓ FAISS: version X.X.X
✓ Kuzu: ready
✓ Streamlit: version X.X.X
════════════════════
✓ ทุกอย่างพร้อมใช้งาน!
```

---

## Slide 9 — Troubleshooting Windows
**Key Message**: ปัญหาส่วนใหญ่แก้ได้ด้วย restart terminal

| ปัญหา | สาเหตุ | วิธีแก้ |
|-------|--------|---------|
| `ollama: not found` | PATH ยังไม่อัปเดต | Restart terminal |
| `uv: not found` | PATH ยังไม่อัปเดต | Restart terminal |
| Model pull ช้า | Internet / disk | รอหรือใช้ model เล็กกว่า |
| `faiss-cpu` install error | ไม่มี C++ runtime | `winget install Microsoft.VCRedist.x64.Latest` |
| Kuzu import error | version conflict | `uv add kuzu --upgrade` |
| RAM ไม่พอ | Model ใหญ่เกิน | ใช้ `qwen2.5-coder:3b` แทน |
| Ollama ไม่ตอบ | Service หยุด | `ollama serve` ใน terminal แยก |
