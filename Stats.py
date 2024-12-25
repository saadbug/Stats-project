import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from io import BytesIO

# --- Helper Functions ---

def calculate_relative_grades(scores, mean, std):
    grade_boundaries = {
        "A": (mean + 1.5 * std, mean + 2 * std),
        "A-": (mean + std, mean + 1.5 * std),
        "B+": (mean + 0.5 * std, mean + std),
        "B": (mean - 0.5 * std, mean + 0.5 * std),
        "B-": (mean - std, mean - 0.5 * std),
        "C+": (mean - (4 / 3) * std, mean - std),
        "C": (mean - (5 / 3) * std, mean - (4 / 3) * std),
        "C-": (mean - 2 * std, mean - (5 / 3) * std),
        "D": (mean - 2 * std, None),
        "F": (None, mean - 2 * std),
    }

    grades = []
    for score in scores:
        assigned = False
        for grade, (lower, upper) in grade_boundaries.items():
            if (lower is None or score >= lower) and (upper is None or score < upper):
                grades.append(grade)
                assigned = True
                break
        if not assigned:
            grades.append("F")

    return grades

def calculate_absolute_grades(scores, thresholds):
    grades = []
    for score in scores:
        for grade, threshold in thresholds.items():
            if score >= threshold:
                grades.append(grade)
                break
    return grades

def generate_summary_statistics(grades):
    return pd.DataFrame(grades.value_counts(), columns=["Count"])

def export_to_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        df.to_excel(writer, index=False)
    return output

# --- Streamlit App ---

st.title("University Grading System")

# Step 1: File Upload
st.header("1. Upload Student Scores")
file = st.file_uploader("Upload a CSV or Excel file containing student scores.", type=["csv", "xlsx"])

if file is not None:
    if file.name.endswith(".csv"):
        data = pd.read_csv(file)
    else:
        data = pd.read_excel(file)

    if "Scores" not in data.columns:
        st.error("The file must contain a column named 'Scores'.")
    else:
        st.success("File uploaded successfully!")
        scores = data["Scores"]

        # Step 2: Choose Grading Scheme
        st.header("2. Choose Grading Scheme")
        grading_scheme = st.radio(
            "Select the grading scheme:",
            ("Absolute Grading", "Relative Grading")
        )

        if grading_scheme == "Absolute Grading":
            st.subheader("Define Absolute Grade Thresholds")
            thresholds = {}
            for grade in ["A", "A-", "B+", "B", "B-", "C+", "C", "C-", "D", "F"]:
                thresholds[grade] = st.number_input(f"Enter minimum percentage for {grade}", min_value=0.0, max_value=100.0, step=0.1)

            grades = calculate_absolute_grades(scores, thresholds)

        else:
            st.subheader("Define Relative Grading Parameters")
            mean = scores.mean()
            std = scores.std()
            st.write(f"Mean: {mean:.2f}, Standard Deviation: {std:.2f}")
            # Remove any invalid or missing scores before calculating grades
            valid_scores = scores.dropna()  # Drop missing values
            valid_scores = valid_scores[
                valid_scores.apply(lambda x: isinstance(x, (int, float)))]  # Ensure scores are numeric

            if len(valid_scores) == 0:
                st.error("No valid scores found. Please ensure the 'Scores' column contains valid numeric values.")
            else:
                if grading_scheme == "Absolute Grading":
                    grades = calculate_absolute_grades(valid_scores, thresholds)
                else:
                    grades = calculate_relative_grades(valid_scores, mean, std)

                # Map grades back to the original dataset
                data["Grades"] = pd.Series(grades, index=valid_scores.index).reindex(data.index, fill_value="N/A")

        if scores.isnull().any():
            st.error("The 'Scores' column contains missing values. Please clean your data and try again.")
        else:
            if grading_scheme == "Absolute Grading":
                grades = calculate_absolute_grades(scores, thresholds)
            else:
                grades = calculate_relative_grades(scores, scores.mean(), scores.std())

            if len(grades) == len(scores):
                data["Grades"] = grades
            else:
                st.error(
                    "Error: Mismatch in the number of grades and scores. Please verify your data and grading logic.")

        # Step 3: Visualizations
        st.header("3. Visualizations")
        st.subheader("Grade Distribution")
        fig, ax = plt.subplots()
        sns.countplot(x="Grades", data=data, order=["A", "A-", "B+", "B", "B-", "C+", "C", "C-", "D", "F"], ax=ax)
        ax.set_title("Grade Distribution")
        st.pyplot(fig)

        st.subheader("Score Distribution")
        fig, ax = plt.subplots()
        sns.histplot(scores, kde=True, ax=ax)
        ax.set_title("Score Distribution")
        st.pyplot(fig)

        # Summary statistics
        st.subheader("Summary Statistics")
        grades_series = pd.Series(data["Grades"])
        summary = grades_series.value_counts().reset_index()
        summary.columns = ["Grade", "Count"]
        st.dataframe(summary)

        # Export results
        st.header("4. Export Results")
        export_file = export_to_excel(data)
        st.download_button(
            label="Download Grades as Excel",
            data=export_file.getvalue(),
            file_name="graded_students.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

        st.success("Grading process completed successfully!")
