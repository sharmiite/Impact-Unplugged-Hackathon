# IAIS-AI (Impact Analyzer Intelligence System – AI)

## Overview
IAIS-AI is an intelligent, AI-driven Change Impact Analysis System designed to automatically detect, analyze, and visualize the downstream effects of code and data model changes across large, multi-module applications.

Traditional impact analysis is slow, manual, error-prone, and difficult to scale.  
IAIS-AI solves these issues using:

- Static code analysis (Python AST)
- CSV schema diffing (before/after snapshots)
- Dependency mapping
- LLM-powered explanations (Groq API)
- Interactive visualization using D3.js

IAIS-AI helps developers, testers, release engineers, and architects instantly understand:
- What changed  
- Where impact originates  
- Who is affected  
- Severity of breakage  
- Recommended tests & remediation steps  

---

## Architecture

```
User Input [BEFORE/AFTER] → Snapshot Diff [ CSV Diff , Code Diff ] → Static Code Analyzer [AST Parsing,File Reads/Writes,Positional Unpacking,DictReader Safety]   → Dependency Engine [ Map CSV → Modules ,Detect Breakage Risk ,Generate Findings ]   →  LLM Explanation Layer [(Groq – compound-mini),Human-readable summary,Remediation steps] →  Impact Report Generator [ JSON Report ,Text Report,HTML Viewer ], D3.js Impact Graph [Writer → File ,File → Reader , Risk Highlight]


 

---

## Folder Structure

```
workspace/
├── snapshots/
│   ├── before/
│   ├── after/
├── tools/
│   └── impact_analyzer/
│        ├── analyzer.py
│        ├── config.py
│        ├── parsers/
│        ├── graph/
│        ├── reports/
│        └── add_llm_explanations.py
└── docs/
     ├── impact_report.json
     ├── impact_report.txt
     └── impact_report_viewer.html
```

---

## Execution Details

### 1. Create Virtual Environment
```
cd workspace/tools/impact_analyzer
python -m venv venv
.
env\Scripts\Activate.ps1
```

### 2. Install Dependencies
```
pip install -r requirements.txt
```

### 3. Configure Groq API Key
```
setx GROQ_API_KEY "sk-xxxx..."
```

Restart terminal & verify:
```
python -c "import os; print(os.environ['GROQ_API_KEY'])"
```

### 4. Update config.py
```
SNAPSHOT_BEFORE = r"...snapshots/before"
SNAPSHOT_AFTER  = r"...snapshots/after"
USE_LLM = True
GROQ_MODEL = "groq/compound-mini"
```

### 5. Run Analyzer
```
python analyzer.py
```

### 6. View Report
Open:
```
docs/impact_report_viewer.html
```

---

## Core Functionalities
- CSV Schema Diffing  
- Python AST Code Scanning  
- Dependency Graph Building  
- Risk Level Detection  
- LLM Explanations (Groq)  
- D3.js Interactive Visualization  

---

## Example Finding
```
Changed File: module_b_output_india.csv
Risk: HIGH
Reason: positional CSV unpacking will break due to added column
Tests: schema mismatch test, end-to-end flow test, boundary data test
```

---

## Impact Graph Explanation
- Blue Nodes: Changed CSV files  
- Teal Nodes: Modules reading or writing CSVs  
- Edges:  
  - writer → file  
  - file → reader  
- Shows full ripple effect  
- Helps instantly identify downstream breakage  

---

## Limitations & Future Enhancements
- Only Python modules supported 
- CSV-based flow  
- Future: Multiple programming language support , SQL parsing, multi-language support, CI/CD integration, PDF export  , Other file support

---

## Target Users
- Developers  
- QA Testers  
- Release Engineers  
- Architects  
- DevOps Teams  

---

## Conclusion
IAIS-AI transforms change impact analysis by automating discovery, dependency mapping, risk detection, and test recommendations — all visualized through an interactive impact graph.

Perfect for complex, multi-module systems where a single small change can trigger cascading failures.
