import pathlib
content = open("agent/nodes_gemini.py", "r", encoding="utf-8").read()
pathlib.Path("agent/nodes.py").write_text(content, encoding="utf-8")
print("nodes.py updated!")
