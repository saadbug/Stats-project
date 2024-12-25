import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from io import BytesIO

# --- Helper Functions ---

def calculate_absolute_grades(scores, thresholds):
    """
    Assign grades based on absolute grade thresholds.
    """
    grades = []
    for score in scores:
        for grade, threshold in thresholds.items():
            if score >= threshold:
                grades.append(grade)
                break
    return grades

def calculate_relative_grades(scores, mean, std):
    """
    Assign grades using mean and standard deviation (predefined formula).
    """
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

def calculate_relative_grades_percentile(scores, percentages):
    """
    Assign grades using user-defined percentages for each grade.
    """
    scores_sorted = scores.sort_values(ascending=False).reset_index(drop=True)
    n = len(scores)
    grades = pd.Series(index=scores.index, dtype="object")

    cumulative_percentage = 0
    start_index = 0
    for grade, percentage in percentages.items():
        cumulative_percentage += percentage
        end_index = int(np.ceil(cumulative_percentage / 100 * n))
        grades[scores_sorted.index[start_index:end_index]] = grade
        start_index = end_index

    return grades

def export_to_excel(df):
    """
    Export data to an Excel file.
    """
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
            st.subheader("Define Absolute Grade Boundaries")
            custom_boundaries = st.checkbox("Define your own grade boundaries", value=False)

            if custom_boundaries:
                thresholds = {}
                for grade in ["A", "A-", "B+", "B", "B-", "C+", "C", "C-", "D", "F"]:
                    thresholds[grade] = st.number_input(
                        f"Enter minimum percentage for {grade}", min_value=0.0, max_value=100.0, step=0.1)
            else:
                thresholds = {
                    "A": 90,
                    "A-": 85,
                    "B+": 80,
                    "B": 75,
                    "B-": 70,
                    "C+": 65,
                    "C": 60,
                    "C-": 55,
                    "D": 50,
                    "F": 0,
                }
                st.write("Using default boundaries:", thresholds)

            grades = calculate_absolute_grades(scores, thresholds)

        else:
            st.subheader("Relative Grading Options")
            relative_grading_choice = st.radio(
                "Choose a relative grading method:",
                ("User-Defined Percentages", "Predefined Formula")
            )

            if relative_grading_choice == "User-Defined Percentages":
                st.write("Specify the percentages for A and F grades. Remaining grades will be distributed proportionally.")

                # User inputs for A and F percentages
                percentage_a = st.number_input("Percentage of students receiving A grade", min_value=0.0, max_value=100.0, step=0.1)
                percentage_f = st.number_input("Percentage of students receiving F grade", min_value=0.0, max_value=100.0, step=0.1)

                remaining_percentage = 100.0 - (percentage_a + percentage_f)
                if remaining_percentage < 0:
                    st.error("The total percentage of A and F exceeds 100%. Please adjust your inputs.")
                else:
                    # Proportional distribution of remaining grades
                    remaining_grades = ["A-", "B+", "B", "B-", "C+", "C", "C-", "D"]
                    proportional_percentage = remaining_percentage / len(remaining_grades)
                    percentages = {"A": percentage_a, "F": percentage_f}
                    percentages.update({grade: proportional_percentage for grade in remaining_grades})

                    grades = calculate_relative_grades_percentile(scores, percentages)

            else:  # Predefined Formula
                mean = scores.mean()
                std = scores.std()
                st.write(f"Using default boundaries: Mean = {mean:.2f}, Std Dev = {std:.2f}")
                grades = calculate_relative_grades(scores, mean, std)

        data["Grades"] = grades

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
        summary = data["Grades"].value_counts().reset_index()
        summary.columns = ["Grade", "Count"]
        st.dataframe(summary)

        # Explicit grade order for sorting
        grade_order = ["A", "A-", "B+", "B", "B-", "C+", "C", "C-", "D", "F"]

        # Convert the Grades column to a categorical type with the specified order
        data["Grades"] = pd.Categorical(data["Grades"], categories=grade_order, ordered=True)

        # Sort the data by Grades
        data = data.sort_values("Grades")

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
