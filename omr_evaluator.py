"""
omr_evaluator.py — Full 100 Questions (A–D only)
"""
import cv2
import numpy as np
import json
import argparse
from PIL import Image, ImageDraw

# Config - adjust if needed
GRID_ROWS = 100   # 100 questions
GRID_COLS = 4     # A–D options
BUBBLE_MIN_AREA = 50
BUBBLE_MAX_AREA = 12000
FILL_THRESHOLD_RATIO = 0.2  # lower = more sensitive

def load_image(path):
    img = cv2.imdecode(np.fromfile(path, dtype=np.uint8), cv2.IMREAD_COLOR)
    if img is None:
        raise FileNotFoundError(f"Image not found or cannot be read: {path}")
    return img

def detect_sheet_and_warp(image):
    h, w = image.shape[:2]
    target_width = 1200
    scale = target_width / float(w)
    resized = cv2.resize(image, (target_width, int(h * scale)))
    return resized

def find_bubble_contours(warped):
    gray = cv2.cvtColor(warped, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5,5), 0)
    _, thresh = cv2.threshold(
        blurred, 0, 255,
        cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU
    )

    cnts, _ = cv2.findContours(
        thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
    )
    bubble_contours = []
    for c in cnts:
        area = cv2.contourArea(c)
        if area < BUBBLE_MIN_AREA or area > BUBBLE_MAX_AREA:
            continue
        x, y, w, h = cv2.boundingRect(c)
        aspect = w / float(h)
        if 0.6 <= aspect <= 1.4:
            bubble_contours.append((x, y, w, h, c))

    bubble_contours = sorted(bubble_contours, key=lambda b: (b[1], b[0]))
    return bubble_contours, thresh

def group_bubbles_into_grid(bubble_contours):
    if not bubble_contours:
        return []

    centers = [((x + w/2), (y + h/2), w, h, c)
               for (x,y,w,h,c) in bubble_contours]
    centers_sorted = sorted(centers, key=lambda t: (t[1], t[0]))

    rows = []
    row_height = (centers_sorted[-1][1] - centers_sorted[0][1]) / GRID_ROWS
    for i in range(GRID_ROWS):
        y_min = centers_sorted[0][1] + i * row_height
        y_max = y_min + row_height
        row = [c for c in centers_sorted if y_min <= c[1] < y_max]

        if not row and rows:
            row = rows[-1]
        elif not row:
            continue

        rows.append(sorted(row, key=lambda t: t[0]))

    grid = []
    for r in rows:
        if len(r) < GRID_COLS:
            r = r + [r[-1]] * (GRID_COLS - len(r))
        grid.append(r[:GRID_COLS])

    return grid

def evaluate_grid(grid, thresh_img):
    overlays = []
    flattened = []
    h, w = thresh_img.shape
    for row in grid:
        for cx, cy, bw, bh, cnt in row:
            x1, y1 = int(cx - bw/2), int(cy - bh/2)
            x2, y2 = int(cx + bw/2), int(cy + bh/2)
            x1, y1 = max(0, x1), max(0, y1)
            x2, y2 = min(w-1, x2), min(h-1, y2)
            roi = thresh_img[y1:y2, x1:x2]
            fill_ratio = cv2.countNonZero(roi) / float(roi.size) if roi.size > 0 else 0
            flattened.append(((x1,y1,x2,y2), fill_ratio))
            overlays.append(((x1,y1,x2,y2), fill_ratio))

    questions = {}
    choices = ['A','B','C','D']
    for i in range(0, len(flattened), GRID_COLS):
        q_index = (i // GRID_COLS) + 1
        group = flattened[i:i+GRID_COLS]
        sel = ""
        max_ratio = 0
        for j, (bbox, ratio) in enumerate(group):
            if ratio > max_ratio and ratio >= FILL_THRESHOLD_RATIO:
                max_ratio = ratio
                sel = choices[j]
        questions[str(q_index)] = sel
    return questions, overlays

def score_questions(questions, answer_key):
    total = 0
    per_subject = [0]*5
    for qidx_str, ans in answer_key.items():
        try:
            qidx = int(qidx_str)
        except ValueError:
            continue
        predicted = questions.get(str(qidx), "")
        if predicted == ans:
            total += 1
            subj = (qidx-1)//20
            per_subject[subj] += 1
    return total, per_subject

def annotate_warped(warped, overlays):
    pil = Image.fromarray(cv2.cvtColor(warped, cv2.COLOR_BGR2RGB))
    draw = ImageDraw.Draw(pil)
    for (x1,y1,x2,y2), ratio in overlays:
        color = (0,255,0) if ratio >= FILL_THRESHOLD_RATIO else (255,0,0)
        draw.rectangle([x1,y1,x2,y2], outline=color, width=2)
    return cv2.cvtColor(np.array(pil), cv2.COLOR_RGB2BGR)

def evaluate_image(path, answer_key, save_overlay_path=None):
    image = load_image(path)
    warped = detect_sheet_and_warp(image)
    bubble_contours, thresh = find_bubble_contours(warped)
    grid = group_bubbles_into_grid(bubble_contours)
    questions, overlays = evaluate_grid(grid, thresh)
    total, per_subject = score_questions(questions, answer_key)
    overlay_img = annotate_warped(warped, overlays)
    if save_overlay_path:
        cv2.imwrite(save_overlay_path, overlay_img)
    return {
        "total_score": total,
        "per_subject": per_subject,
        "predicted_answers": questions
    }

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("image_path", help="Path to OMR image")
    parser.add_argument("answer_key_json", help="Answer key JSON file")
    parser.add_argument("overlay_out", help="Output overlay image path")
    parser.add_argument("--set", default="A", help="Which answer set to use (A or B)")
    args = parser.parse_args()

    with open(args.answer_key_json, "r") as f:
        data = json.load(f)

    # ✅ handle Set A/Set B or flat
    set_key = f"Set {args.set.upper()}"
    if set_key in data:
        answer_key = data[set_key]
    elif "answers" in data:
        answer_key = data["answers"]
    else:
        answer_key = data

    result = evaluate_image(args.image_path, answer_key, args.overlay_out)

    print("\n✅ Evaluation complete!")
    print("Total Score:", result["total_score"])
    print("Per Subject:", result["per_subject"])
    print("Predicted Answers:", result["predicted_answers"])

if __name__ == "__main__":
    main()
