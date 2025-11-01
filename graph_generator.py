import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import os

def generate_attendance_graphs(df, class_info, output_folder):
    """Generate attendance analysis graphs and save as PDF"""
    
    # Create subplots
    fig, axs = plt.subplots(5, 1, figsize=(10, 20))

    # Display class and class teacher info
    class_info_text = f'Student Attendance Report\nClass: {class_info["class_name"]}\nClass Teacher: {class_info["teacher_name"]}\n'
    axs[0].text(0.5, 1.1, class_info_text, fontsize=14, fontweight='bold', 
                horizontalalignment='center', transform=axs[0].transAxes)

    # Gender Distribution
    gender_counts = df['Gender'].value_counts()
    axs[0].pie(gender_counts, labels=gender_counts.index, autopct='%1.1f%%', startangle=140)
    axs[0].set_title('Distribution of Gender')
    total_students = gender_counts.sum()
    explanation_text = f"""
    This pie chart shows the distribution of gender among students.
    - Male students: {gender_counts.get('Male', 0)}
    - Female students: {gender_counts.get('Female', 0)}
    Total Students: {total_students}
    """
    axs[0].text(0.5, -0.15, explanation_text, horizontalalignment='center', 
                verticalalignment='center', transform=axs[0].transAxes, wrap=True)

    # Defaulter Distribution
    threshold = class_info.get('threshold', 75)
    defaulter_count = (df['Attendance Percentage'] < threshold).sum()
    non_defaulter_count = (df['Attendance Percentage'] >= threshold).sum()
    labels = ['Defaulter', 'Non-Defaulter']
    axs[1].pie([defaulter_count, non_defaulter_count], labels=labels, 
               autopct='%1.1f%%', startangle=140)
    axs[1].set_title('Attendance Category')
    defaulter_explanation = f"""
    This pie chart shows the distribution of defaulter among students.
    - Defaulter students: {defaulter_count}
    - Non-defaulter students: {non_defaulter_count}
    Total Students: {total_students}
    """
    axs[1].text(0.5, -0.3, defaulter_explanation, horizontalalignment='center', 
                verticalalignment='center', transform=axs[1].transAxes, wrap=True)

    # Bar Chart
    axs[2].bar(labels, [defaulter_count, non_defaulter_count], color=['red', 'green'])
    axs[2].set_title('Defaulter vs Non-Defaulter Counts')
    bar_explanation = f"""
    This bar chart compares the counts of defaulters and non-defaulters based on attendance percentage:
    - Defaulter: Students with attendance below {threshold}%
    - Non-Defaulter: Students with attendance {threshold}% or higher
    Total Students: {total_students}
    """
    axs[2].text(0.5, -0.3, bar_explanation, horizontalalignment='center', 
                verticalalignment='center', transform=axs[2].transAxes, wrap=True)

    # Scatter Plot
    defaulter_student = df[df['Attendance Percentage'] < threshold]
    girls = defaulter_student[defaulter_student['Gender'] == 'Female']
    boys = defaulter_student[defaulter_student['Gender'] == 'Male']
    
    axs[3].scatter(range(len(girls)), girls['Attendance Percentage'], 
                  color='red', label='Defaulter (Girls)', alpha=0.5)
    axs[3].scatter(range(len(boys)), boys['Attendance Percentage'], 
                  color='blue', label='Defaulter (Boys)', alpha=0.5)
    
    axs[3].text(len(girls), girls['Attendance Percentage'].mean() if not girls.empty else 0, 
                f'Count: {len(girls)}', fontsize=12, color='red', ha='center')
    axs[3].text(len(boys), boys['Attendance Percentage'].mean() if not boys.empty else 0, 
                f'Count: {len(boys)}', fontsize=12, color='blue', ha='center')
    
    axs[3].set_title('Defaulter Students Attendance (Separated by Gender)')
    axs[3].legend()
    
    scatter_explanation = """
    This scatter plot shows the attendance percentage of defaulter students, separated by gender.
    - Red points represent defaulter girls.
    - Blue points represent defaulter boys.
    """
    axs[3].text(0.5, -0.3, scatter_explanation, horizontalalignment='center', 
                verticalalignment='center', transform=axs[3].transAxes, wrap=True)

    # Defaulter Table
    defaulter_students = df[df['Attendance Percentage'] < threshold]
    table_data = defaulter_students[['Roll Number', 'Name', 'Attendance Percentage']]
    
    axs[4].axis('off')
    table = axs[4].table(cellText=table_data.values, colLabels=table_data.columns, 
                        loc='upper center')
    table.auto_set_font_size(False)
    table.set_fontsize(10)
    table.scale(1, 2)
    axs[4].set_title('Defaulter Students Table', fontsize=12, pad=20)
    axs[4].title.set_position([.5, 1.1])

    plt.tight_layout()

    # Save to PDF
    timestamp = pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')
    pdf_filename = f"Attendance_Report_{class_info['class_name']}_{timestamp}.pdf"
    pdf_path = os.path.join(output_folder, pdf_filename)
    
    with PdfPages(pdf_path) as pdf:
        plt.savefig(pdf, format='pdf')
    
    plt.close()
    return pdf_path