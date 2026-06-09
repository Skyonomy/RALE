import json
from tools.forensic_compositor import ForensicCompositor
from PIL import Image

# create dummy image
img = Image.new("RGB", (1024, 1024), "white")
import io
buffered = io.BytesIO()
img.save(buffered, format="PNG")
raw_binary = buffered.getvalue()

vision_result = {
    "labels": [
        {
            "number": 1,
            "location_name": "Main Exhibition Hall",
            "ymin": 457.0,
            "xmin": 100.0,
            "ymax": 830.0,
            "xmax": 399.0,
            "semantic_reason": "The large grey building with intricate roof details on the left, serving as a primary structure."
        }
    ]
}

try:
    res = ForensicCompositor.composite_teacher_map(raw_binary, vision_result)
    print("Success! Length:", len(res))
except Exception as e:
    import traceback
    traceback.print_exc()
