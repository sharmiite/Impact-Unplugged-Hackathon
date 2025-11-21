# module_d.py
import csv
import os

IN = os.path.join("..","shared","module_b_output_india.csv")

with open(IN, "r", newline="") as f:
    reader = csv.DictReader(f)
    print("Module D: fields", reader.fieldnames)
    for i, row in enumerate(reader, start=1):
        target = row.get("Target")
        new_flag = row.get("new_flag")
        print("Row", i, "Target", target, "new_flag", new_flag)
