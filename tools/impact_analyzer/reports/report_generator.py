# reports/report_generator.py
import json
import os
from datetime import datetime
from pathlib import Path

def write_json_report(report, out_path):
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

def write_text_report(report, out_path):
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    lines = []
    lines.append(f"Impact Analysis Report - {datetime.utcnow().isoformat()}Z")
    lines.append("="*60)
    lines.append("")
    for r in report.get("findings", []):
        lines.append(f"MODULE: {r['module']}")
        lines.append(f"  IMPACT: {r['impact']}")
        lines.append(f"  CONFIDENCE: {r['confidence']}")
        lines.append("  EVIDENCE:")
        for e in r.get("evidence", []):
            lines.append(f"    - {e}")
        if r.get("llm_explanation"):
            lines.append("  LLM Explanation:")
            for l in r["llm_explanation"].splitlines():
                lines.append("    " + l)
        lines.append("-"*40)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

# reports/report_generator.py
import os
import json

def _extract_text_from_completion(resp):
    """
    Robustly extract the assistant text from a Groq/OpenAI-style completion response.
    Returns a string or None.
    """
    try:
        # Try attribute access (library object)
        choice0 = resp.choices[0]
        # choice0.message may be object or dict
        msg = getattr(choice0, "message", None) or (choice0.get("message") if isinstance(choice0, dict) else None)
        if msg:
            # message content may be attr or dict key
            content = getattr(msg, "content", None) or (msg.get("content") if isinstance(msg, dict) else None)
            if content:
                return content.strip()
    except Exception:
        pass

    # Fallback: try to parse dict-like structure
    try:
        if isinstance(resp, dict):
            choices = resp.get("choices", [])
            if choices:
                msg = choices[0].get("message", {})
                content = msg.get("content") if isinstance(msg, dict) else None
                if content:
                    return content.strip()
    except Exception:
        pass

    # Last fallback: stringify but try to be shorter
    try:
        s = str(resp)
        # try to pull content between "content='" and "', role="
        import re
        m = re.search(r"content=('|\")(.{10,2000}?)('|\")", s, re.DOTALL)
        if m:
            return m.group(2).strip()
    except Exception:
        pass

    return None

def call_llm_for_explanation(prompt, config):
    """
    Use Groq (or other OpenAI-compatible) API and return clean text (or error string).
    """
   
    # prefer Groq API key if set
    key = ""
    if not key or not config.USE_LLM:
      print("No KEY Found")
      return None

    try:
        from groq import Groq
        client = Groq(A_KY=key)
        model = "groq/compound-mini" 

        resp = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are an assistant that generates concise technical impact explanations."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=480,
            temperature=0.0
        )

        # extract clean text
        text = _extract_text_from_completion(resp)
        if text:
            return text
        # fallback to JSON dump if nothing else
        try:
            return json.dumps(resp, default=str)[:2000]
        except Exception:
            return str(resp)[:2000]
    except Exception as e:
        return f"LLM call failed: {e}"