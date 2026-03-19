with open('backend_stderr.log', 'r', encoding='utf-8', errors='replace') as f:
    content = f.read()

needle = "ContentItem' object has no attribute"
idx = content.find(needle)
if idx >= 0:
    start = max(0, idx - 1500)
    print(content[start:idx+500])
else:
    print("Not found")
