# test_omr.py
import json
from omr_evaluator import evaluate_image

img = "omr1.jpg"   # <-- replace with your actual image filename
keyfile = "sample_answer_keys.json"

with open(keyfile, "r") as f:
    keys = json.load(f)

key_name = "Set A" if "Set A" in keys else list(keys.keys())[0]
answer_key = keys[key_name]

res, overlay = evaluate_image(img, answer_key, save_overlay_path="overlay_test.jpg")
print("Total:", res["total_score"])
print("Per-subject:", res["per_subject"])