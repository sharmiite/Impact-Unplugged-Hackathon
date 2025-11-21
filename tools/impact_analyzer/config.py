# config.py
import os

# Snapshots paths (relative to project root)
SNAPSHOT_BEFORE = r"D:\DMCJ_ACADEMY\Projects\MDHack\workspace\snapshots\before"
SNAPSHOT_AFTER  = r"D:\DMCJ_ACADEMY\Projects\MDHack\workspace\snapshots\after"


# Shared folder where modules write outputs (relative to project root)
SHARED_FOLDER = os.path.join("..","..","workspace\shared")


# Toggle LLM usage (True to call LLM)
USE_LLM = True

# Output report path
REPORT_JSON = os.path.join("..","..","docs","impact_report.json")
REPORT_TXT  = os.path.join("..","..","docs","impact_report.txt")
