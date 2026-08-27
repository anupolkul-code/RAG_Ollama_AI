# Slide Deck 1: Chunking Strategies for Code

> Session 07 | Module 3: Vector DB & Embeddings | 11 slides

---

## Slide 1 - Why Can't We Just Embed the Whole File?

**Key Message:** Embedding ทั้งไฟล์ทำให้ retrieval แย่ — ต้องแบ่งเป็น chunks ก่อน

- LLM embedding models มี **token limit** (~8,192 tokens)
- ไฟล์ Python ทั่วไปมี 100–2,000+ บรรทัด — ใหญ่เกินไป
- ถ้า embed ทั้งไฟล์ vector จะ "เฉลี่ย" ทุกอย่างรวมกัน → ค้นหาแม่นยำน้อย
- Chunk เล็กกว่า = vector แม่นยำกว่า = ค้นหาได้ตรงกว่า

[FIGURE: Diagram showing a large Python file on left, arrow pointing to 3 small chunks on right. Each chunk has its own vector. A query vector matches chunk 2 but not the whole file vector.]

---

## Slide 2 - The Chunking Spectrum

**Key Message:** มี chunking strategies หลายแบบ ต่างกันที่ trade-off ระหว่าง simplicity กับ semantic quality

- **Fixed-size**: ตัดทุก N ตัวอักษร — ง่ายแต่อาจตัดกลาง function
- **By sentence/paragraph**: ดีสำหรับ prose ไม่ดีสำหรับ code
- **By function**: ตาม Python syntax — แต่ละ chunk = 1 function ที่สมบูรณ์
- **By class**: ทั้ง class รวม methods — ดีสำหรับ OOP context
- **Hybrid**: function ก่อน แล้ว split อีกถ้าใหญ่เกินไป

[FIGURE: Spectrum bar from "Simple but imprecise" (Fixed-size) to "Complex but precise" (Semantic/Function). Highlight "By Function" as the recommended approach for code.]

---

## Slide 3 - Fixed-Size Chunking — The Naive Approach

**Key Message:** Fixed-size chunking ใช้ง่ายแต่ไม่เข้าใจโครงสร้างโค้ด ทำให้ context แตกหัก

[EXAMPLE: 
Before chunking (500-char limit):
```python
def load_data(path):
    """Load CSV data."""
    df = pd.read_csv(path)
    return df

def process_data(df):   # ← CHUNK BOUNDARY cuts here!
    """Process the data."""
    df = df.dropna()
    return df.describe()
```

After fixed chunking:
- Chunk 1: `def load_data...` + `def process_data(df):`
- Chunk 2: `"""Process...` + `df = df.dropna()...`

Result: Chunk 2 makes no sense without context!
]

- **Problem:** ตัดกลาง function signature หรือ docstring ได้
- **Problem:** Chunk ที่ได้ไม่ใช่ "unit of code" ที่มีความหมาย
- **ใช้ได้กับ:** Documents ทั่วไป, Markdown, prose text

---

## Slide 4 - AST-Based Function Chunking

**Key Message:** Python `ast` module ช่วยให้เราตัด chunk ตาม function boundary ได้อย่างแม่นยำ

- `ast.parse(source)` → แปลง source code เป็น syntax tree
- `ast.walk(tree)` → iterate ทุก node ใน tree
- `ast.FunctionDef` → node ที่แทน function definition
- `node.lineno` / `node.end_lineno` → บรรทัดเริ่มต้น/สิ้นสุด
- `ast.get_docstring(node)` → ดึง docstring ออกมาได้

[FIGURE: Python source code on left. AST tree in middle (showing Module → FunctionDef nodes for load_data and process_data). On right, two clean separate chunks, one per function, each complete and self-contained.]

---

## Slide 5 - AST Parsing — Live Demo

**Key Message:** AST parsing แยก function nodes ได้ชัดเจน พร้อม metadata ครบ

[EXAMPLE:
```python
import ast

source = """
def add(a, b):
    "Add two numbers."
    return a + b

def multiply(a, b):
    "Multiply two numbers."
    return a * b
"""

tree = ast.parse(source)
for node in ast.walk(tree):
    if isinstance(node, ast.FunctionDef):
        print(f"Function: {node.name}")
        print(f"  Lines: {node.lineno}–{node.end_lineno}")
        print(f"  Docstring: {ast.get_docstring(node)}")
```

Output:
```
Function: add
  Lines: 2–4
  Docstring: Add two numbers.
Function: multiply
  Lines: 6–8
  Docstring: Multiply two numbers.
```
]

---

## Slide 6 - Chunk Metadata — What to Store

**Key Message:** Metadata เก็บควบคู่กับ vector — ใช้สำหรับ filter และ citation ในภายหลัง

| Metadata Field | ประเภท | ใช้ทำอะไร |
|----------------|--------|-----------|
| `source` | string | path ของไฟล์ต้นฉบับ |
| `file_name` | string | ชื่อไฟล์ (ไม่มี path) |
| `function_name` | string | ชื่อ function |
| `line_start` | int | บรรทัดเริ่มต้น |
| `line_end` | int | บรรทัดสิ้นสุด |
| `docstring` | string | description ของ function |

[EXAMPLE:
```python
doc = Document(
    page_content="def load_csv(path):\n    return pd.read_csv(path)",
    metadata={
        "source": "/project/utils.py",
        "file_name": "utils.py",
        "function_name": "load_csv",
        "line_start": 12,
        "line_end": 14,
        "docstring": "Load CSV file into DataFrame",
    }
)
```
]

---

## Slide 7 - Handling Edge Cases in Parsing

**Key Message:** โค้ดจริงมี edge cases เยอะ — ต้องจัดการ gracefully ไม่งั้น pipeline พัง

- **Syntax errors:** ไฟล์ที่ parse ไม่ได้ → catch `SyntaxError`, skip และ log
- **Very large functions:** function ที่ยาวกว่า 2,000 chars → sub-chunk อีกครั้ง
- **Nested functions:** function ภายใน function → ตัดสินใจว่าจะรวมหรือแยก
- **Empty functions:** `pass` body → อาจไม่คุ้มค่า embed
- **Encoding errors:** ไฟล์ที่ไม่ใช่ UTF-8 → ใช้ `errors="replace"`

[EXAMPLE:
```python
def safe_extract(filepath: str) -> list[dict]:
    try:
        with open(filepath, "r", encoding="utf-8", errors="replace") as f:
            source = f.read()
        tree = ast.parse(source)
        return extract_functions_from_tree(tree, source, filepath)
    except SyntaxError as e:
        print(f"Skipping {filepath}: {e}")
        return []
    except Exception as e:
        print(f"Error in {filepath}: {e}")
        return []
```
]

---

## Slide 8 - Chunking Statistics — Know Your Data

**Key Message:** วิเคราะห์ chunk statistics ก่อน embed เพื่อเข้าใจ distribution และ ตัดสินใจ strategy

[EXAMPLE:
```python
import statistics

chunks = parse_all_files("./project")
lengths = [len(c["code"]) for c in chunks]

print(f"Total chunks: {len(chunks)}")
print(f"Avg length: {statistics.mean(lengths):.0f} chars")
print(f"Median: {statistics.median(lengths):.0f} chars")
print(f"Max: {max(lengths)} chars (might need sub-chunking)")
print(f"Min: {min(lengths)} chars (might be too short to embed)")
```

Sample output:
```
Total chunks: 47
Avg length: 312 chars
Median: 218 chars
Max: 2847 chars  ← needs sub-chunking!
Min: 23 chars    ← too short?
```
]

- Functions < 50 chars อาจไม่มีข้อมูลเพียงพอสำหรับ embedding
- Functions > 2,000 chars ควร sub-chunk ก่อน embed

---

## Slide 9 - Class Chunking vs Function Chunking

**Key Message:** เลือก chunking strategy ตามโครงสร้างของ codebase — class-level ดีกว่าสำหรับ OOP

[FIGURE: Two columns. Left: "Function Chunking" — shows 3 separate chunks for __init__, process(), validate() from the same class. Right: "Class Chunking" — shows 1 large chunk containing the entire class. Arrow shows that for queries like "how does UserProcessor work?", class chunk is better. For "how does validate() work?", function chunk is better.]

**When to use Function Chunking:**
- Codebase มี utility functions อิสระ
- Query จะถามถึง specific functionality
- Functions ส่วนใหญ่มีความยาวพอเหมาะ

**When to use Class Chunking:**
- โค้ดมีการออกแบบ OOP ชัดเจน
- Query จะถามถึง behavior ของ object
- Methods มีความเกี่ยวข้องกันสูง

---

## Slide 10 - Chunking Best Practices

**Key Message:** Good chunking = good retrieval — ลงทุนเวลากับ chunking คุ้มค่ากว่าปรับ embedding

1. **เลือก strategy ตาม codebase structure** — อย่าใช้ fixed-size กับ code
2. **เก็บ metadata ให้ครบ** — source, function_name, line numbers
3. **ตั้ง size limits** — ไม่ใหญ่เกิน ~2,000 chars, ไม่เล็กเกิน ~50 chars
4. **Handle errors gracefully** — อย่าให้ไฟล์เดียวทำให้ทั้ง pipeline พัง
5. **วิเคราะห์ statistics ก่อน embed** — เข้าใจ distribution ของ chunks
6. **Test retrieval หลัง build** — ทำ smoke test ด้วย queries ที่รู้คำตอบ

[FIGURE: Pipeline checklist: Parse files → Handle errors → Check chunk sizes → Create Documents with metadata → Embed → Save index → Test with sample queries]

---

## Slide 11 - Recap — What We Learned

**Key Message:** Chunking strategy มีผลโดยตรงต่อคุณภาพของ RAG pipeline ทั้งระบบ

- **Fixed-size**: ง่าย แต่ไม่เหมาะกับ code
- **Function-level (AST)**: แนะนำสำหรับ Python codebase
- **Metadata**: เก็บ source, function_name, line numbers ไว้เสมอ
- **Edge cases**: parse errors, ขนาด chunk, nested functions
- **Evaluation**: วัด precision/recall ด้วย test cases ที่รู้คำตอบ

**Next: Slide Deck 2 → สร้าง FAISS Index และ search**
