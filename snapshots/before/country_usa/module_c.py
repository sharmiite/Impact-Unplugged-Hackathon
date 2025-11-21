# module_c.py
import csv
import os

IN = os.path.join("..","shared","module_b_output_usa.csv")

with open(IN, "r", newline="") as f:
    reader = csv.reader(f)
    header = next(reader)
    print("Module C: header length", len(header))
    print(header)
    for i, row in enumerate(reader, start=1):
        try:
            # positional unpacking for original schema (17 fields)
            (age, job, marital, education, default, balance,
             housing, loan, contact, day, month, duration,
             campaign, pdays, previous, poutcome, Target) = row
        except ValueError:
            print("Module C: positional unpacking failed on row", i)
            print("row length", len(row), "row data", row)
            break
        # process
        print("Row", i, "Target", Target)
