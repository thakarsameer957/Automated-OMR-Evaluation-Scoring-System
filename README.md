# Automated OMR Evaluation — MVP

This repository is an end-to-end **Minimal Viable Product (MVP)** for the Automated OMR Evaluation & Scoring System described in the project brief.

## What is included
- `omr_evaluator.py` — Core OMR evaluation logic using OpenCV (image preprocessing, sheet detection, bubble detection, scoring).
- `app.py` — Streamlit app to upload OMR images, run the evaluator, and export results (CSV).
- `sample_answer_keys.json` — Example answer keys for two sheet versions.
- `requirements.txt` — Python dependencies.
- `sample_images/` — Place your test images here (README inside folder).

## Quick setup (local)
1. Create and activate a Python virtual environment (recommended).
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Run Streamlit app:
   ```
   streamlit run app.py
   ```
4. In the web app upload an OMR image (jpg/png). Results will be shown and can be exported to CSV.

## Assumptions & Notes (MVP)
- This MVP assumes a standard OMR layout: **100 questions**, **4 choices** (A–D).
- The code tries a template-agnostic approach by detecting circular bubbles, sorting them into a grid of `ROWS x COLS`. Default grouping is `25 rows x 4 cols` (i.e., 25 rows each with 4 bubbles -> 100).
- For production: collect a few sample sheets, and tune parameters (bubble size, thresholds). Use ML classifier for ambiguous marks if needed.
- Two sample "versions" keys are provided in `sample_answer_keys.json`. The app allows selecting the version.

## Files to edit for customization
- `omr_evaluator.py`: tweak GRID_ROWS, GRID_COLS, and thresholds for your sheet type.
- `sample_answer_keys.json`: add your exam's answer keys.

## How to structure sample images
Put your test images into `sample_images/`. Recommended naming: `student_<id>_version<1 or 2>.jpg`.

## License
MIT