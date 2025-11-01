import pandas as pd
import os


def categorize_students_attendance(df, threshold=75):
    """
    Categorize students into defaulters and non-defaulters based on attendance percentage.
    
    Args:
        df: DataFrame containing student data
        threshold: Attendance percentage threshold (default: 75)
        
    Returns:
        tuple: (defaulter_students, non_defaulter_students, defaulter_count, non_defaulter_count)
    """
    try:
        # Validate required columns
        if 'Attendance Percentage' not in df.columns:
            return None, None, None, None
        
        # Categorize students
        defaulter_students = df[df['Attendance Percentage'] < threshold].copy()
        non_defaulter_students = df[df['Attendance Percentage'] >= threshold].copy()
        
        defaulter_count = len(defaulter_students)
        non_defaulter_count = len(non_defaulter_students)
        
        # Add classification column
        df['Classification'] = df['Attendance Percentage'].apply(
            lambda x: 'Defaulter' if x < threshold else 'Non-Defaulter'
        )
        
        return df, defaulter_students, non_defaulter_students, defaulter_count, non_defaulter_count
        
    except Exception as e:
        print(f"Error in categorize_students_attendance: {e}")
        return None, None, None, None


def predict_defaulters(file_path, threshold=75, teacher_name="", teacher_email=""):
    """
    Main function to process Excel file and classify students.
    
    Args:
        file_path: Path to the uploaded Excel file
        threshold: Attendance percentage threshold
        teacher_name: Name of the class teacher
        teacher_email: Email of the class teacher
        
    Returns:
        dict: Results containing all categorized data and statistics
    """
    try:
        # Read Excel file
        if not os.path.exists(file_path):
            return {"error": "File not found"}
        
        # Try reading as Excel first, then CSV
        try:
            df = pd.read_excel(file_path)
        except:
            try:
                df = pd.read_csv(file_path)
            except Exception as e:
                return {"error": f"Unable to read file: {str(e)}"}
        
        # Validate required columns
        required_columns = ['Attendance Percentage']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            return {
                "error": f"Missing required columns: {', '.join(missing_columns)}"
            }
        
        # Categorize students
        results_df, defaulter_students, non_defaulter_students, defaulter_count, non_defaulter_count = \
            categorize_students_attendance(df, threshold)
        
        if results_df is None:
            return {"error": "Failed to categorize students"}
        
        # Prepare results
        results = {
            "success": True,
            "total_students": len(df),
            "defaulter_count": defaulter_count,
            "non_defaulter_count": non_defaulter_count,
            "threshold": threshold,
            "teacher_name": teacher_name,
            "teacher_email": teacher_email,
            "data": results_df.to_dict(orient='records'),
            "defaulter_data": defaulter_students.to_dict(orient='records'),
            "non_defaulter_data": non_defaulter_students.to_dict(orient='records')
        }
        
        return results
        
    except Exception as e:
        return {"error": f"Error processing file: {str(e)}"}


def save_results_to_excel(results, output_path):
    """
    Save the classification results to an Excel file.
    
    Args:
        results: Results dictionary from predict_defaulters
        output_path: Path to save the Excel file
        
    Returns:
        str: Path to the saved file or None if error
    """
    try:
        if results.get("error"):
            return None
        
        df = pd.DataFrame(results["data"])
        df.to_excel(output_path, index=False)
        
        return output_path
        
    except Exception as e:
        print(f"Error saving results to Excel: {e}")
        return None

