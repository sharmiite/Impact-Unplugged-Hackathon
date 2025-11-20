# module_a.py
import csv
import random
import os

OUT = os.path.join("..","shared","module_a_output_usa.csv")
os.makedirs(os.path.dirname(OUT), exist_ok=True)

header = ["age","job","marital","education","default","balance","housing","loan","contact","day","month","duration","campaign","pdays","previous","poutcome","Target"]

jobs = ["admin","technician","services","management","retired"]
maritals = ["single","married","divorced"]
educations = ["secondary","tertiary","primary","unknown"]
contacts = ["cellular","telephone"]
targets = ["yes","no"]

def rand_row():
    return [
        str(random.randint(18,80)),                      # age
        random.choice(jobs),                              # job
        random.choice(maritals),                          # marital
        random.choice(educations),                        # education
        random.choice(["yes","no"]),                      # default
        str(random.randint(0,5000)),                      # balance
        random.choice(["yes","no"]),                      # housing
        random.choice(["yes","no"]),                      # loan
        random.choice(contacts),                          # contact
        str(random.randint(1,31)),                        # day
        random.choice(["jan","feb","mar","apr","may"]),   # month
        str(random.randint(10,5000)),                     # duration
        str(random.randint(1,10)),                        # campaign
        str(random.randint(-1,10)),                       # pdays
        str(random.randint(0,10)),                        # previous
        random.choice(["success","failure","other"]),     # poutcome
        random.choice(targets)                            # Target
    ]

if __name__ == "__main__":
    # write 20 rows
    with open(OUT, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(header)
        for _ in range(20):
            writer.writerow(rand_row())

    print("Module A: wrote", OUT)
