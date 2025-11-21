# analyzer.py
import os
import json
import glob
from pathlib import Path

from config import SNAPSHOT_BEFORE, SNAPSHOT_AFTER, SHARED_FOLDER, REPORT_JSON, REPORT_TXT, USE_LLM
from parsers.csv_parser import extract_csv_header
from parsers.code_parser import analyze_python_file
from reports.report_generator import write_json_report, write_text_report, call_llm_for_explanation

def gather_headers_recursive(folder):
    mapping = {}
    if not folder or not os.path.isdir(folder):
        return mapping
    for full in glob.glob(os.path.join(folder, "**", "*.csv"), recursive=True):
        name = os.path.basename(full)
        hdr = extract_csv_header(full)
        mapping[name] = hdr
    return mapping

def list_changed_files(before_snapshot, after_snapshot):
    """
    Compare CSV headers found under before_snapshot and after_snapshot.
    Returns list of dicts: { filename, before_header, after_header }
    """
    files_before = gather_headers_recursive(before_snapshot)
    files_after  = gather_headers_recursive(after_snapshot)

    print("DEBUG: headers found in BEFORE snapshot:", files_before)
    print("DEBUG: headers found in AFTER  snapshot:", files_after)

    # fallback: if both snapshots are empty, try workspace/shared (live files)
    if not files_before and not files_after:
        live_shared = os.path.join(os.getcwd(), "..", "..", "shared")
        files_after = gather_headers_recursive(live_shared)
        print("DEBUG: snapshots empty — falling back to live shared folder:", live_shared)
        print("DEBUG: headers found in live shared:", files_after)

    changed = []
    keys = set(list(files_before.keys()) + list(files_after.keys()))
    for k in keys:
        b = files_before.get(k)
        a = files_after.get(k)
        if b != a:
            changed.append({"filename": k, "before_header": b, "after_header": a})
    return changed

def analyze_codebase(snapshot_root):
    """
    For each country folder, analyze python files for CSV usage/unpacking.
    Return mapping: { country: { rel_py_path: analysis_dict } }
    """
    results = {}
    if not os.path.isdir(snapshot_root):
        return results
    for country_dir in glob.glob(os.path.join(snapshot_root, "*")):
        print(f"Folders : {country_dir}")
        if not os.path.isdir(country_dir):
            continue
        country = os.path.basename(country_dir)
        results[country] = {}
        # consider .py files directly under the country folder
        for py in sorted([f for f in os.listdir(country_dir) if f.endswith(".py")]):
            full = os.path.join(country_dir, py)
            print(f"Files : {full}")
            analysis = analyze_python_file(full)
            # store keyed by relative path w.r.t. snapshot_root for stable comparison
            rel = os.path.relpath(full, snapshot_root)
            results[country][rel] = analysis
    return results

def _file_reads_to_basename_list(file_reads):
    """
    file_reads is a list of (lineno, value) where value may be:
      - a literal path like '../shared/module_b_output_india.csv'
      - a varname unresolved like 'IN'
      - a resolved path produced earlier (joined)
    We normalize to basenames where possible.
    """
    out = set()
    for fr in file_reads:
        if not fr:
            continue
        val = fr[1]
        if not val:
            continue
        # if it's a path-like string, extract basename
        try:
            bn = os.path.basename(val)
            out.add(bn)
        except Exception:
            out.add(str(val))
    return out

# def infer_impacts(changed_files, code_before, code_after):
#     """
#     Create findings by correlating changed CSVs with code usages.
#     code_before / code_after: mapping { country: { rel_py_path: analysis } }
#     """
#     findings = []

#     # Helper: iterate over all modules (countries) and python files in after-snapshot
#     countries = set(list(code_before.keys()) + list(code_after.keys()))

#     for change in changed_files:
#         fname = change["filename"]
#         for country in countries:
#             files_after = code_after.get(country, {})
#             files_before = code_before.get(country, {})
#             for relpath, analysis_after in files_after.items():
#                 analysis_before = files_before.get(relpath, {})
#                 # get list of basenames that this file reads (after and before)
#                 reads_after = _file_reads_to_basename_list(analysis_after.get("file_reads", []))
#                 reads_before = _file_reads_to_basename_list(analysis_before.get("file_reads", []))
#                 # detect if this file reads the changed fname in after OR started reading it newly
#                 reads_changed_after = fname in reads_after
#                 started_reading = (fname not in reads_before) and (fname in reads_after)
#                 if reads_changed_after:
#                     evidence = []
#                     # add which line opened it (from file_reads entries)
#                     for fr in analysis_after.get("file_reads", []):
#                         if os.path.basename(str(fr[1])) == fname:
#                             evidence.append(f"module file {os.path.normpath(relpath)} opens '{fr[1]}' (line {fr[0]})")
#                     # code-change evidence
#                     pos_after = analysis_after.get("positional_unpack_sites", [])
#                     pos_before = analysis_before.get("positional_unpack_sites", [])
#                     dict_after = analysis_after.get("dictreader_sites", [])
#                     dict_before = analysis_before.get("dictreader_sites", [])

#                     # determine risk and evidence
#                     risk = "Low"
#                     if pos_after:
#                         # if positional unpack exists after, high risk
#                         risk = "High"
#                         for ln, count, src in pos_after:
#                             evidence.append(f"positional unpacking at line {ln} expecting {count} fields -> source: {src.strip()}")
#                     elif dict_after:
#                         risk = "Low"
#                         for ln, src in dict_after:
#                             evidence.append(f"DictReader usage at line {ln} -> source: {src.strip()}")
#                     else:
#                         if analysis_after.get("csv_reader_sites"):
#                             risk = "Medium"
#                             for ln, src in analysis_after.get("csv_reader_sites"):
#                                 evidence.append(f"csv.reader usage at line {ln} -> source: {src.strip()}")
#                         else:
#                             evidence.append("No direct CSV-read heuristic found in this file.")

#                     # if this file began reading the file in AFTER snapshot, note it
#                     if started_reading:
#                         evidence.insert(0, f"Note: this file started reading '{fname}' in AFTER snapshot (was not present in BEFORE).")

#                     findings.append({
#                         "module": country,
#                         "file": relpath,
#                         "impact": f"Schema changed for '{fname}' (columns before: {change['before_header']}, after: {change['after_header']})",
#                         "confidence": risk,
#                         "evidence": evidence,
#                         "changed_file": fname
#                     })

#             # Additionally: detect files that had positional unpacking in AFTER but not reading the file directly,
#             # but might be indirectly affected if they read a file that maps to this changed file name via aliases.
#             # (This can be extended; for POC we focus on direct reads.)

#     return findings

def infer_impacts(changed_files, code_before, code_after):
    findings = []
    countries = set(list(code_before.keys()) + list(code_after.keys()))

    for change in changed_files:
        fname = change["filename"]
        for country in countries:
            files_after = code_after.get(country, {})
            files_before = code_before.get(country, {})
            # 1) detect modules that write this changed file in AFTER snapshot
            for relpath, analysis_after in files_after.items():
                writes_after = _file_reads_to_basename_list(analysis_after.get("file_writes", []))
                writes_before = _file_reads_to_basename_list(files_before.get(relpath, {}).get("file_writes", []))
                writes_changed_after = fname in writes_after
                started_writing = (fname not in writes_before) and (fname in writes_after)
                if writes_changed_after:
                    evidence = []
                    # show write lines
                    for fr in analysis_after.get("file_writes", []):
                        if os.path.basename(str(fr[1])) == fname:
                            evidence.append(f"module file {os.path.normpath(relpath)} writes to '{fr[1]}' (line {fr[0]})")

                    # header write details
                    hw_after = analysis_after.get("header_writes", [])
                    hw_before = files_before.get(relpath, {}).get("header_writes", [])
                    if hw_after:
                        for ln, hw in hw_after:
                            evidence.append(f"header write at line {ln} -> {hw}")
                    # determine risk by what readers might do (we'll check readers separately too)
                    risk = "Low"
                    # if positional unpack exists in any reader file in same country, we will mark higher later; for now mark medium
                    if hw_after and not hw_before:
                        risk = "Medium"

                    if started_writing:
                        evidence.insert(0, f"Note: this file started writing '{fname}' in AFTER snapshot (was not present in BEFORE).")

                    findings.append({
                        "module": country,
                        "file": relpath,
                        "impact": f"Code writes changed CSV '{fname}'. Schema before: {change['before_header']}, after: {change['after_header']}",
                        "confidence": risk,
                        "evidence": evidence,
                        "changed_file": fname
                    })

            # 2) existing logic: detect readers that read the changed file (unchanged)
            for relpath, analysis_after in files_after.items():
                analysis_before = files_before.get(relpath, {})
                reads_after = _file_reads_to_basename_list(analysis_after.get("file_reads", []))
                reads_before = _file_reads_to_basename_list(analysis_before.get("file_reads", []))
                reads_changed_after = fname in reads_after
                started_reading = (fname not in reads_before) and (fname in reads_after)
                if reads_changed_after:
                    evidence = []
                    for fr in analysis_after.get("file_reads", []):
                        if os.path.basename(str(fr[1])) == fname:
                            evidence.append(f"module file {os.path.normpath(relpath)} opens '{fr[1]}' (line {fr[0]})")

                    pos_after = analysis_after.get("positional_unpack_sites", [])
                    dict_after = analysis_after.get("dictreader_sites", [])
                    risk = "Low"
                    if pos_after:
                        risk = "High"
                        for ln, count, src in pos_after:
                            evidence.append(f"positional unpacking at line {ln} expecting {count} fields -> source: {src.strip()}")
                    elif dict_after:
                        risk = "Low"
                        for ln, src in dict_after:
                            evidence.append(f"DictReader usage at line {ln} -> source: {src.strip()}")
                    else:
                        if analysis_after.get("csv_reader_sites"):
                            risk = "Medium"
                            for ln, src in analysis_after.get("csv_reader_sites"):
                                evidence.append(f"csv.reader usage at line {ln} -> source: {src.strip()}")
                        else:
                            evidence.append("No direct CSV-read heuristic found in this file.")

                    if started_reading:
                        evidence.insert(0, f"Note: this file started reading '{fname}' in AFTER snapshot (was not present in BEFORE).")

                    findings.append({
                        "module": country,
                        "file": relpath,
                        "impact": f"Schema changed for '{fname}' (columns before: {change['before_header']}, after: {change['after_header']})",
                        "confidence": risk,
                        "evidence": evidence,
                        "changed_file": fname
                    })

    return findings

def enrich_with_llm(findings, config):
    print(f"Findings : {findings}")
    print("For each finding, craft a small prompt with evidence and call LLM for friendly explanation & suggestions.")
    
    for f in findings:
        prompt_lines = []
        prompt_lines.append(f"File changed: {f['changed_file']}")
        prompt_lines.append(f"Confidence: {f['confidence']}")
        prompt_lines.append("Evidence:")
        for e in f["evidence"]:
            prompt_lines.append(" - " + e)
        prompt_lines.append("")
        prompt_lines.append("Provide a concise technical explanation why this module might break (one short paragraph), and give up to 3 recommended test case scenario to do testing or remediation steps.")
        prompt = "\n".join(prompt_lines)
        llm_out = None
        print(f"Prompt : {prompt}")
        try:
            llm_out = call_llm_for_explanation(prompt, config)
        except Exception as e:
            llm_out = f"LLM unavailable: {e}"
        f["llm_explanation"] = llm_out
    return findings

def main():
    print("Impact Analyzer starting...")
    # 1. find changed shared files
    changed = list_changed_files(SNAPSHOT_BEFORE, SNAPSHOT_AFTER)
    print(f"Detected {len(changed)} changed shared files.")
    # 2. analyze code in both snapshots
    code_before = analyze_codebase(SNAPSHOT_BEFORE)
    code_after  = analyze_codebase(SNAPSHOT_AFTER)
    print("Analyzed code for modules (before):", list(code_before.keys()))
    print("Analyzed code for modules (after) :", list(code_after.keys()))
    # 3. infer impacts (considering changed CSVs and code diffs)
    findings = infer_impacts(changed, code_before, code_after)
    print(f"Inferred {len(findings)} findings.")
    # 4. call LLM optionally to enrich
    if USE_LLM and findings:
        print("Entering LLM Model")
        try:
            import config as cfg
            findings = enrich_with_llm(findings, cfg)
        except Exception as e:
            print("LLM enrichment failed:", e)
    # 5. assemble report
    report = {
        "summary": {
            "changed_files": changed,
            "findings_count": len(findings)
        },
        "findings": findings
    }
    # 6. write reports
    write_json_report(report, REPORT_JSON)
    write_text_report(report, REPORT_TXT)
    print("Reports written to:", REPORT_JSON, REPORT_TXT)
    print("Done.")

if __name__ == "__main__":
    main()
