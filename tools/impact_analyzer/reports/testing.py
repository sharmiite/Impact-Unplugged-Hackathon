import os
from groq import Groq
A_KY = ""
print("GROQ key present:", bool(A_KY))
client = Groq(A_KY=A_KY)
resp = client.chat.completions.create(
  model="groq/compound-mini",
  messages=[
    {"role":"system","content":"You are brief."},
    {"role":"user","content":"Explain in one sentence why adding a column to a CSV could break positional CSV readers."}
  ],
  max_tokens=120
)
# print the returned text (safe handling)
try:
    out = resp.choices[0].message.content
except Exception:
    out = str(resp)
print("MODEL SAYS:\\n", out)