import os
import re
from flask import Flask, request, jsonify
from google_sheets import get_sheet_data, update_sheet_with_certificate_link
from google_drive import authenticate_drive, download_file_from_drive, upload_certificate
from certificate import generate_certificate
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
app = Flask(__name__)

def url_to_id(url):
    match = re.search(r'/d/([a-zA-Z0-9_-]+)|id=([a-zA-Z0-9_-]+)', url)
    if match:
        return match.group(1) or match.group(2)
    return None

def extract_drive_id(url):
    pattern = r'folders/([-a-zA-Z0-9_]+)'
    match = re.search(pattern, url)
    
    if match:
        return match.group(1)  # Extract the ID
    else:
        return None  

def send_emails(sheet_url, subject, body):
    load_dotenv()  # Load environment variables from .env file
    smtp_server = os.getenv('SMTP_SERVER')
    smtp_port = int(os.getenv('SMTP_PORT'))
    smtp_user = os.getenv('SMTP_USER')
    smtp_password = os.getenv('SMTP_PASSWORD')

    sheet_data = get_sheet_data(sheet_url)

    for row in sheet_data:
        if row.get('Attendance') == 'TRUE' and row.get('certificate_link'):  # Check if attendance is marked TRUE and certificate link is present
            to_email = row.get('email-id')
            cert_link = row.get('certificate_link')

            # Create the email
            msg = MIMEMultipart()
            msg['From'] = smtp_user
            msg['To'] = to_email
            msg['Subject'] = subject

            # Email body
            body_with_link = f"{body}\n\nYour certificate: {cert_link}"
            msg.attach(MIMEText(body_with_link, 'plain'))

            # Send the email
            try:
                with smtplib.SMTP(smtp_server, smtp_port) as server:
                    server.starttls()  # Try TLS encryption
                    server.login(smtp_user, smtp_password)
                    server.sendmail(smtp_user, to_email, msg.as_string())
                    print(f"Email sent to {to_email} successfully!")
            except smtplib.SMTPAuthenticationError as e:
                print(f"Authentication error: {e}")
                return {"message": f"Failed to send email to {to_email}. Error: Authentication failed."}, 500
            except smtplib.SMTPException as e:
                print(f"SMTP error: {e}")
                return {"message": f"Failed to send email to {to_email}. Error: SMTP error."}, 500
            except Exception as e:
                print(f"Error: {e}")
                return {"message": f"Failed to send email to {to_email}. Error: {str(e)}"}, 500

    return {"message": "Emails sent successfully!"}

@app.route('/generate-certificates', methods=['POST'])
def generate_certificates():
    data = request.json
    sheet_url = data['sheet_url']
    drive_folder_id = extract_drive_id(data['drive_folder_id']) #
    template_file_id = url_to_id(data['template_path']) #
    coords = tuple(data['coords'])  
    email_subject = data['email_subject']
    email_body = data['email_body']
    font_size=int(data['font_size'])
    font_style=data['font_style']
    font_color=data['font_color']
    max_width=int(data['max_width'])

    # Step 1: Get data from Google Sheets
    sheet_data = get_sheet_data(sheet_url)

    # Step 2: Authenticate Google Drive
    drive_service = authenticate_drive('credentials_sheets.json')
    
    template_path = 'template.png'  # download to current working directory


    download_file_from_drive(drive_service, template_file_id, template_path)
    print(f"File downloaded to {template_path}")
    
    # Step 3: Process each row
    for index, row in enumerate(sheet_data, start=2):  # Assuming first row is headers
        if row['Attendance'] and row['Attendance'] == 'TRUE':  # Check if attendance is marked
            if 'Name' in row and row['Name']:  # Check if 'Name' column is not empty
                name = row['Name']
                usn = row['USN']
                
                # Step 4: Generate certificate
                cert_path = generate_certificate(template_path, name, usn, coords,font_size,font_style,max_width,font_color)
                
                # Step 5: Upload to Google Drive
                cert_link = upload_certificate(drive_service, drive_folder_id, cert_path, f"{usn}.pdf")
                
                # Step 6: Update Google Sheets with the certificate link
                update_sheet_with_certificate_link(sheet_url, index, cert_link)
                
                # Step 7: Remove the pdf file created locally
                os.remove(cert_path)
    os.remove(template_path)  # delete the file
    email_response = send_emails(sheet_url, email_subject, email_body)

    if isinstance(email_response, tuple):  # Check if email_response is a tuple
        return jsonify({"message": "Certificates generated but failed to send emails."}), 500
    else:
        if email_response.get('message') == "Emails sent successfully!":
            return jsonify({"message": "Certificates generated and emails sent successfully!"})
        else:
            return jsonify({"message": "Certificates generated but failed to send emails."}), 500



if __name__ == '__main__':
    app.run(debug=True)