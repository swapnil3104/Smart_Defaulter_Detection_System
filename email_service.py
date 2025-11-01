import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
import os

def send_email(recipient_email, teacher_name, results_file_path, results_data, teacher_details, graph_file_path=None, is_student=False):
    # Email configuration
    sender_email = "pswapnil3104@gmail.com"
    sender_password = "ujdz edgj vswe lvyl"  # App password generated from Google Account

    # Create message
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = recipient_email

    if is_student:
        msg['Subject'] = "Attendance Warning Notice"
        # Student email template
        body = """
        <html>
            <body>
                <h2 style="color: #2C3E50;">Dear Student,</h2>
                <p style="font-size: 16px;">
                    We hope this message finds you well. 
                </p>
                <p style="font-size: 16px;">
                    This is to inform you that your attendance is currently below the threshold of <strong>75%</strong>. 
                    Regular attendance is crucial for your academic success and engagement in the learning process.
                </p>
                <p style="font-size: 16px;">
                    Please take the necessary steps to improve your attendance. If you are facing any issues, do not hesitate to reach out for support.
                </p>
                <p style="font-size: 16px;">
                    Thank you for your attention to this matter.
                </p>
                <p style="font-size: 16px;">
                    Regards,<br>
                    Swapnil Patil,<br>
                    Class Teacher<br>
                    TY CSE,<br>
                    ADCET
                </p>
            </body>
        </html>
        """
    else:
        msg['Subject'] = f"Student Defaulter Analysis Report - {teacher_details.get('class_name', '')}"
        # Teacher email template
        body = f"""
        <html>
            <body>
                <h2 style="color: #2C3E50;">Dear {teacher_name},</h2>
                <p style="font-size: 16px;">
                    Your student defaulter analysis report is ready. Here are the summary results:
                </p>
                <div style="font-size: 16px; margin: 20px 0;">
                    <p><strong>Total Students:</strong> {results_data['total_students']}</p>
                    <p><strong>Defaulters:</strong> {results_data['defaulter_count']}</p>
                    <p><strong>Non-Defaulters:</strong> {results_data['non_defaulter_count']}</p>
                    <p><strong>Threshold:</strong> {results_data['threshold']}%</p>
                </div>
                <p style="font-size: 16px;">
                    Please find the detailed report attached with this email.
                </p>
                <p style="font-size: 16px;">
                    Regards,<br>
                    {teacher_name},<br>
                    {teacher_details.get('teacher_designation', '')}<br>
                    {teacher_details.get('class_name', '')},<br>
                    {teacher_details.get('department', '')}<br>
                    {teacher_details.get('college_name', '')}
                </p>
            </body>
        </html>
        """

    msg.attach(MIMEText(body, 'html'))

    # Attach the results file for teacher emails
    if not is_student and os.path.exists(results_file_path):
        with open(results_file_path, 'rb') as f:
            attachment = MIMEApplication(f.read(), _subtype='xlsx')
            attachment.add_header('Content-Disposition', 'attachment', 
                               filename=os.path.basename(results_file_path))
            msg.attach(attachment)

    # Attach graph file if provided
    if graph_file_path and os.path.exists(graph_file_path):
        with open(graph_file_path, 'rb') as f:
            attachment = MIMEApplication(f.read(), _subtype='pdf')
            attachment.add_header('Content-Disposition', 'attachment', 
                               filename=os.path.basename(graph_file_path))
            msg.attach(attachment)

    try:
        # Create server connection
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        
        # Login
        server.login(sender_email, sender_password)
        
        # Send email
        server.send_message(msg)
        server.quit()
        return True, "Email sent successfully"
    except Exception as e:
        return False, str(e)