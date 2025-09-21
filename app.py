"""
Streamlit app for OMR Evaluation — Final Version
"""
import streamlit as st
import json, os
import pandas as pd
from omr_evaluator import evaluate_image
import cv2

st.set_page_config(page_title="OMR Evaluator", layout="wide")
st.title("Automated OMR Evaluator")

st.markdown("""
Upload a clear photo of a filled OMR sheet (jpg/png).  
This app assumes 100 questions and 5 subjects (20 each).  
Subjects: Python, Data Analysis, MySQL, Power BI, Advanced Stats.
""")

# --- Inputs ---
rollno = st.text_input("Enter Roll No")
student_name = st.text_input("Enter Student Name")

uploaded_file = st.file_uploader("Upload OMR image", type=["jpg","jpeg","png"])
answer_keys_file = "sample_answer_keys.json"
keys = {}
if os.path.exists(answer_keys_file):
    with open(answer_keys_file, "r") as f:
        keys = json.load(f)

selected_key = st.selectbox("Select Answer Key (Set A/Set B)", options=list(keys.keys()) if keys else ["v1"])

if uploaded_file is not None:
    tmp_path = "tmp_uploaded.jpg"
    with open(tmp_path, "wb") as f:
        f.write(uploaded_file.read())
    st.image(tmp_path, caption="Uploaded image", use_column_width=True)

    if st.button("Run Evaluation"):
        st.info("Evaluating... please wait")
        try:
            answer_key = keys.get(selected_key, {})
            res, overlay_img = evaluate_image(tmp_path, answer_key, save_overlay_path="overlay_result.jpg")

            # --- Scores ---
            st.success("Evaluation completed")
            st.image(overlay_img, caption="Detected Bubbles", use_column_width=True)

            per_subj = res["per_subject"]

            # Format result row
            result_row = {
                "RollNo": rollno,
                "Name": student_name,
                "Python": per_subj[0],
                "Data Analysis": per_subj[1],
                "MySQL": per_subj[2],
                "Power BI": per_subj[3],
                "Adv Stats": per_subj[4],
                "Total": res["total_score"]
            }
            result_df = pd.DataFrame([result_row])
            st.subheader("Student Result")
            st.table(result_df)

            # --- Download CSV ---
            csv = result_df.to_csv(index=False).encode("utf-8")
            st.download_button("Download Student CSV",
                               data=csv,
                               file_name=f"{rollno}_{student_name}_result.csv",
                               mime="text/csv")

            # --- Save to batch file ---
            os.makedirs("results", exist_ok=True)
            batch_path = "results/batch_results.xlsx"
            if os.path.exists(batch_path):
                existing = pd.read_excel(batch_path)
                updated = pd.concat([existing, result_df], ignore_index=True)
            else:
                updated = result_df
            updated.to_excel(batch_path, index=False)

            st.success(f"Result appended to {batch_path}")

        except Exception as e:
            st.error(f"Error: {e}")
