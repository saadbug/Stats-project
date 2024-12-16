import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.stats import norm, zscore
from tkinter import filedialog
from tkinter import Tk


# Input Module
def load_grades():
    """Allow the instructor to input student grades via a CSV or Excel file."""
    Tk().withdraw()  # Hides the root window
    file_path = filedialog.askopenfilename(title="Select a CSV or Excel File",
                                           filetypes=[("CSV files", "*.csv"), ("Excel files", "*.xlsx")])

    if file_path.endswith(".csv"):
        grades = pd.read_csv(file_path)
    elif file_path.endswith(".xlsx"):
        grades = pd.read_excel(file_path)
    else:
        raise ValueError("Unsupported file type. Please select a CSV or Excel file.")

    if 'Score' not in grades.columns:
        raise ValueError("The file must contain a 'Score' column with student grades.")

    return grades


# Statistical Analysis
def calculate_statistics(scores):
    """Calculate descriptive statistics for the input grades."""
    stats = {
        'Mean': np.mean(scores),
        'Variance': np.var(scores),
        'Skewness': pd.Series(scores).skew(),
        'Min': np.min(scores),
        'Max': np.max(scores)
    }
    return stats


def plot_distributions(scores, adjusted_scores=None):
    """Plot histograms and density plots of the grade distribution before and after adjustments."""
    plt.figure(figsize=(12, 6))

    sns.histplot(scores, kde=True, label="Original Grades", color="blue", bins=15)

    if adjusted_scores is not None:
        sns.histplot(adjusted_scores, kde=True, label="Adjusted Grades", color="orange", bins=15)

    plt.title("Grade Distributions")
    plt.xlabel("Scores")
    plt.ylabel("Frequency")
    plt.legend()
    plt.show()


# Grade Adjustment
def apply_absolute_grading(scores, thresholds):
    """Apply absolute grading based on fixed thresholds."""
    grades = []
    for score in scores:
        for grade, threshold in thresholds.items():
            if score >= threshold:
                grades.append(grade)
                break
    return grades


def apply_relative_grading(scores, grade_distribution):
    """Adjust grades to match a predefined distribution using z-score scaling."""
    sorted_scores = sorted(scores)
    percentiles = np.percentile(sorted_scores, np.linspace(0, 100, len(grade_distribution) + 1))

    adjusted_grades = []
    for score in scores:
        for i, boundary in enumerate(percentiles[1:], start=1):
            if score <= boundary:
                adjusted_grades.append(list(grade_distribution.keys())[i - 1])
                break
    return adjusted_grades


# Reporting and Visualization
def generate_report(original_scores, adjusted_scores, original_grades, adjusted_grades):
    """Provide a detailed report showing the original and adjusted grades."""
    report = pd.DataFrame({
        "Original Scores": original_scores,
        "Adjusted Scores": adjusted_scores,
        "Original Grades": original_grades,
        "Adjusted Grades": adjusted_grades
    })
    print(report.describe())
    return report


def save_report(report):
    """Save the report to a CSV file."""
    file_path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv")])
    if file_path:
        report.to_csv(file_path, index=False)
        print(f"Report saved to {file_path}")
    else:
        print("Save operation was cancelled.")


# Main Functionality
def main():
    print("Welcome to the Grading System")

    # Load grades
    grades_df = load_grades()
    scores = grades_df['Score'].values

    # Display statistics
    stats = calculate_statistics(scores)
    print("Original Statistics:", stats)

    # Plot original distribution
    plot_distributions(scores)

    # Choose grading method
    method = input("Choose grading method (absolute/relative): ").strip().lower()

    if method == "absolute":
        thresholds = {
            "A": 90,
            "A-": 80,
            "B": 70,
            "C": 60,
            "D": 50,
            "F": 0
        }
        original_grades = apply_absolute_grading(scores, thresholds)
        adjusted_grades = original_grades  # No adjustments in absolute grading

    elif method == "relative":
        grade_distribution = {
            "A": 0.2,
            "B": 0.3,
            "C": 0.3,
            "D": 0.15,
            "F": 0.05
        }
        adjusted_grades = apply_relative_grading(scores, grade_distribution)
        original_grades = ["N/A"] * len(scores)  # Original grades undefined in relative grading
    else:
        print("Invalid method chosen. Please restart.")
        return

    # Generate and save report
    report = generate_report(scores, scores, original_grades, adjusted_grades)
    save_report(report)

    # Plot adjusted distribution
    plot_distributions(scores, scores)


if __name__ == "__main__":
    main()
