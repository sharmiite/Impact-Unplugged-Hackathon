# module_b.py
import csv
import os

IN = os.path.join("..","shared","module_a_output_usa.csv")
OUT = os.path.join("..","shared","module_b_output_usa.csv")
os.makedirs(os.path.dirname(OUT), exist_ok=True)

# Module B inserts a new column after 'balance'
insert_after = "balance"
new_col = "new_flag"   # added column - cahnge 1

with open(IN, "r", newline="") as fin:
    reader = csv.reader(fin)
    rows = list(reader)

orig_header = rows[0]
if insert_after in orig_header:
    idx = orig_header.index(insert_after) + 1
else:
    idx = len(orig_header)
new_header = orig_header[:idx] + [new_col] + orig_header[idx:] # change 2

with open(OUT, "w", newline="") as fout:
    writer = csv.writer(fout)
    writer.writerow(new_header)
    for r in rows[1:]:
        try:
            balance = int(r[orig_header.index("balance")])
        except Exception:
            balance = 0
        flag = "high" if balance > 1000 else "low" 
        new_row = r[:idx] + [flag] + r[idx:] # change 3
        writer.writerow(new_row)

print("Module B: read", IN, "and wrote", OUT, "with inserted column", new_col)
