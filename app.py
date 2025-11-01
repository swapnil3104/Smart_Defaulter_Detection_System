from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import os
from werkzeug.utils import secure_filename
from datetime import datetime
from defaulter_predict import predict_defaulters, save_results_to_excel
from email_service import send_email
from graph_generator import generate_attendance_graphs
import traceback
import pandas as pd

app = Flask(__name__)
CORS(app)  # Enable CORS for React frontend

# Configuration
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['RESULTS_FOLDER'] = 'results'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['ALLOWED_EXTENSIONS'] = {'xlsx', 'xls', 'csv'}

# Create directories if they don't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['RESULTS_FOLDER'], exist_ok=True)


def allowed_file(filename):
    """Check if the file has an allowed extension."""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']


@app.route('/')
def index():
    """Health check endpoint."""
    return jsonify({
        "status": "OK",
        "message": "Student Defaulter Classification System API"
    })


@app.route('/upload', methods=['POST'])
def upload_file():
    """Handle file upload and process defaulter classification."""
    try:
        # Check if all required fields are present
        if 'file' not in request.files:
            return jsonify({"error": "No file provided"}), 400
        
        if 'teacher_name' not in request.form or 'teacher_email' not in request.form:
            return jsonify({"error": "Teacher name and email are required"}), 400
        
        file = request.files['file']
        teacher_name = request.form['teacher_name'].strip()
        teacher_email = request.form['teacher_email'].strip()
        threshold = int(request.form.get('threshold', 75))
        
        # Validate inputs
        if not teacher_name:
            return jsonify({"error": "Teacher name cannot be empty"}), 400
        
        if not teacher_email:
            return jsonify({"error": "Teacher email cannot be empty"}), 400
        
        if file.filename == '':
            return jsonify({"error": "No file selected"}), 400
        
        if not allowed_file(file.filename):
            return jsonify({"error": "Invalid file type. Only .xlsx, .xls, and .csv files are allowed"}), 400
        
        # Save uploaded file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = secure_filename(file.filename)
        file_ext = filename.rsplit('.', 1)[1].lower()
        unique_filename = f"{timestamp}_{filename}"
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        file.save(file_path)
        
        # Process the file
        results = predict_defaulters(
            file_path=file_path,
            threshold=threshold,
            teacher_name=teacher_name,
            teacher_email=teacher_email
        )
        
        # Check for processing errors
        if results.get("error"):
            # Clean up uploaded file
            if os.path.exists(file_path):
                os.remove(file_path)
            return jsonify(results), 400
        
        # Save results to Excel
        results_filename = f"results_{timestamp}.xlsx"
        results_path = os.path.join(app.config['RESULTS_FOLDER'], results_filename)
        saved_path = save_results_to_excel(results, results_path)
        
        if saved_path:
            results["results_file"] = results_filename
        
        # Prepare response
        response_data = {
            "success": True,
            "message": "File processed successfully",
            "results": {
                "total_students": results["total_students"],
                "defaulter_count": results["defaulter_count"],
                "non_defaulter_count": results["non_defaulter_count"],
                "threshold": results["threshold"],
                "results_file": results_filename if saved_path else None
            },
            "data": results["data"]  # Include all student data with classification
        }
        
        return jsonify(response_data), 200
        
    except ValueError as e:
        return jsonify({"error": f"Invalid threshold value: {str(e)}"}), 400
    except Exception as e:
        print(f"Error processing upload: {traceback.format_exc()}")
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500


@app.route('/download/<filename>', methods=['GET'])
def download_file(filename):
    """Download a results file."""
    try:
        file_path = os.path.join(app.config['RESULTS_FOLDER'], filename)
        
        if not os.path.exists(file_path):
            return jsonify({"error": "File not found"}), 404
        
        if not filename.startswith('results_'):
            return jsonify({"error": "Invalid file access"}), 403
        
        return send_file(file_path, as_attachment=True)
        
    except Exception as e:
        return jsonify({"error": f"Error downloading file: {str(e)}"}), 500

@app.route('/send-email', methods=['POST'])
def send_email_report():
    """Send email with the analysis report."""
    try:
        data = request.json
        required_fields = [
            'teacher_email', 'teacher_name', 'results_file', 'results',
            'teacher_designation', 'class_name', 'department', 'college_name'
        ]
        if not all(key in data for key in required_fields):
            return jsonify({"error": "Missing required data"}), 400

        file_path = os.path.join(app.config['RESULTS_FOLDER'], data['results_file'])
        if not os.path.exists(file_path):
            return jsonify({"error": "Results file not found"}), 404

        teacher_details = {
            'teacher_designation': data['teacher_designation'],
            'class_name': data['class_name'],
            'department': data['department'],
            'college_name': data['college_name']
        }

        # Generate graphs
        df = pd.read_excel(file_path) if file_path.endswith(('.xlsx', '.xls')) else pd.read_csv(file_path)
        
        class_info = {
            'teacher_name': data['teacher_name'],
            'class_name': data['class_name'],
            'threshold': data['results']['threshold']
        }
        
        # Generate graphs and get PDF path
        graph_path = generate_attendance_graphs(df, class_info, app.config['RESULTS_FOLDER'])
        
        success, message = send_email(
            recipient_email=data['teacher_email'],
            teacher_name=data['teacher_name'],
            results_file_path=file_path,
            results_data=data['results'],
            teacher_details=teacher_details,
            graph_file_path=graph_path
        )

        if success:
            return jsonify({"message": "Email sent successfully", "graph_path": os.path.basename(graph_path)}), 200
        else:
            return jsonify({"error": f"Failed to send email: {message}"}), 500

    except Exception as e:
        print(f"Error sending email: {traceback.format_exc()}")
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500

@app.route('/send-student-email', methods=['POST'])
def send_student_email():
    """Send warning email to defaulter students."""
    try:
        data = request.json
        required_fields = ['results_file']
        if not all(key in data for key in required_fields):
            return jsonify({"error": "Missing required data"}), 400

        file_path = os.path.join(app.config['RESULTS_FOLDER'], data['results_file'])
        if not os.path.exists(file_path):
            return jsonify({"error": "Results file not found"}), 404

        # Read the results file
        df = pd.read_excel(file_path) if file_path.endswith(('.xlsx', '.xls')) else pd.read_csv(file_path)
        
        # Filter defaulter students
        defaulters = df[df['Classification'] == 'Defaulter']
        
        if defaulters.empty:
            return jsonify({"message": "No defaulter students found"}), 200

        # Send emails to all defaulter students
        success_count = 0
        failed_count = 0
        failed_emails = []

        for _, student in defaulters.iterrows():
            if 'Email' in student and pd.notna(student['Email']):
                success, message = send_email(
                    recipient_email=student['Email'],
                    teacher_name=None,
                    results_file_path=None,
                    results_data=None,
                    teacher_details=None,
                    is_student=True
                )
                if success:
                    success_count += 1
                else:
                    failed_count += 1
                    failed_emails.append(f"{student['Email']}: {message}")

        return jsonify({
            "message": f"Sent {success_count} emails successfully, {failed_count} failed",
            "failed_emails": failed_emails if failed_emails else None
        }), 200

    except Exception as e:
        print(f"Error sending student emails: {traceback.format_exc()}")
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500

@app.route('/generate-graphs', methods=['POST'])
def generate_graphs():
    """Generate attendance graphs without sending email."""
    try:
        data = request.json
        required_fields = ['results_file', 'teacher_name', 'class_name', 'threshold']
        
        if not all(key in data for key in required_fields):
            return jsonify({"error": "Missing required data"}), 400
        
        file_path = os.path.join(app.config['RESULTS_FOLDER'], data['results_file'])
        if not os.path.exists(file_path):
            return jsonify({"error": "Results file not found"}), 404
            
        df = pd.read_excel(file_path) if file_path.endswith(('.xlsx', '.xls')) else pd.read_csv(file_path)
        
        class_info = {
            'teacher_name': data['teacher_name'],
            'class_name': data['class_name'],
            'threshold': data['threshold']
        }
        
        graph_path = generate_attendance_graphs(df, class_info, app.config['RESULTS_FOLDER'])
        
        return jsonify({
            "message": "Graphs generated successfully",
            "graph_path": os.path.basename(graph_path)
        }), 200
        
    except Exception as e:
        print(f"Error generating graphs: {traceback.format_exc()}")
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500

@app.route('/download-graph/<filename>', methods=['GET'])
def download_graph(filename):
    """Download a graph file."""
    try:
        if not filename.endswith('.pdf'):
            return jsonify({"error": "Invalid file type"}), 400

        file_path = os.path.join(app.config['RESULTS_FOLDER'], filename)
        
        if not os.path.exists(file_path):
            return jsonify({"error": "Graph file not found"}), 404
        
        return send_file(file_path, as_attachment=True)
        
    except Exception as e:
        return jsonify({"error": f"Error downloading graph: {str(e)}"}), 500

    except Exception as e:
        print(f"Error sending email: {traceback.format_exc()}")
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500


@app.errorhandler(413)
def too_large(e):
    """Handle file too large error."""
    return jsonify({"error": "File is too large. Maximum size is 16MB"}), 413


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)

