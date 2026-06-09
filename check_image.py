import json
import base64

with open('static/js/cached_runs.js', 'r') as f:
    content = f.read()

# content is: const CACHED_RUNS = {...};
# strip the prefix
content = content.replace('const CACHED_RUNS = ', '').strip()
if content.endswith(';'):
    content = content[:-1]

data = json.loads(content)

first_key = list(data.keys())[0]
b64_str = data[first_key]['teacher_image_b64']

with open('test_image.png', 'wb') as f:
    f.write(base64.b64decode(b64_str))

print("Saved test_image.png")
