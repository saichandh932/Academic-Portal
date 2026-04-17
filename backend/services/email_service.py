# -*- coding: utf-8 -*-
"""
backend/services/email_service.py
---------------------------------
Handles SMTP email dispatch for performance alerts.
"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from backend.config import Config

class EmailService:
    @staticmethod
    def send_low_performance_alert(student_email, student_id, subject_name, assessment_name, marks_obtained, max_marks):
        """
        Sends an automated guidance email to students scoring below the threshold.
        Returns: (bool success, str message)
        """
        if not Config.EMAIL_ENABLED:
            msg = f"[MOCK EMAIL] To: {student_email} | Subject: Low Performance in {subject_name}"
            print(msg)
            return True, "Mock sent successfully"

        # Real SMTP logic
        try:
            msg = MIMEMultipart()
            msg['From'] = f"{Config.SMTP_FROM_NAME} <{Config.SMTP_USER}>"
            msg['To'] = student_email
            msg['Subject'] = f"Academic Alert: Performance Guidance for {subject_name}"

            body = f"""
            Hello Student {student_id},

            This is an automated system notification regarding your recent performance in {subject_name}.

            Assessment: {assessment_name}
            Marks Secured: {marks_obtained} / {max_marks}

            Your recorded marks are currently below the safety threshold. We encourage you to focus on your studies and improve in the upcoming assessments.

            WARNING: Your marks are low. Please improve and contact your subject teacher for any further guidance or support.

            Best regards,
            {Config.SMTP_FROM_NAME}
            """
            
            msg.attach(MIMEText(body, 'plain'))

            server = smtplib.SMTP(Config.SMTP_HOST, Config.SMTP_PORT, timeout=10)
            if Config.SMTP_USE_TLS:
                server.starttls()
            
            server.login(Config.SMTP_USER, Config.SMTP_PASSWORD)
            server.send_message(msg)
            server.quit()
            
            return True, "Email sent successfully"
        except Exception as e:
            error_str = str(e)
            print(f"[EMAIL ERROR] Failed to send email to {student_email}: {error_str}")
            return False, error_str

    @staticmethod
    def send_absence_alert(student_email, student_id, subject_name, date_str, period):
        """
        Sends an automated notification to students marked as Absent.
        """
        period_str = f"Period {period}" if period else "Special Session"
        if not Config.EMAIL_ENABLED:
            msg = f"[MOCK EMAIL] To: {student_email} | Subject: Absence Alert - {subject_name} ({period_str})"
            print(msg)
            return True, "Mock sent successfully"

        try:
            msg = MIMEMultipart()
            msg['From'] = f"{Config.SMTP_FROM_NAME} <{Config.SMTP_USER}>"
            msg['To'] = student_email
            msg['Subject'] = f"Absence Notification: {subject_name} ({date_str} - {period_str})"

            body = f"""
            Hello Student {student_id},

            This is a notification regarding your attendance in the following session:

            Subject: {subject_name}
            Date: {date_str}
            Academic Slot: {period_str}
            Status: ABSENT

            Please note that consistent attendance is crucial for your academic success and to meet the required institutional threshold. If you believe this is an error, please contact your subject teacher immediately.


            Best regards,
            Department of CSE
            Vignan's Foundation for Science, Technology & Research
            """
            
            msg.attach(MIMEText(body, 'plain'))

            server = smtplib.SMTP(Config.SMTP_HOST, Config.SMTP_PORT, timeout=10)
            if Config.SMTP_USE_TLS:
                server.starttls()
            
            server.login(Config.SMTP_USER, Config.SMTP_PASSWORD)
            server.send_message(msg)
            server.quit()
            
            return True, "Absence email sent"
        except Exception as e:
            print(f"[EMAIL ERROR] Failed to send absence alert to {student_email}: {e}")
            return False, str(e)

    @staticmethod
    def send_bulk_absence_alerts(absent_records, subject_name, date_str, period):
        """Sends absence emails in a single batch process."""
        report = []
        for row in absent_records:
            reg_num = row.get('registration_number')
            target_email = row.get('email')
            if not target_email:
                target_email = f"{reg_num}@example.com"
            success, msg = EmailService.send_absence_alert(target_email, reg_num, subject_name, date_str, period)
            report.append({"reg_num": reg_num, "status": "Sent" if success else f"Error: {msg}"})
        return report

    @staticmethod
    def send_password_reset_email(target_email, registration_number, token):
        """
        Sends a secure link to reset the user's password.
        """
        # Construction of the public URL for resetting
        reset_link = f"{Config.FRONTEND_URL}/reset-password?token={token}"

        if not Config.EMAIL_ENABLED:
            msg = f"\n[MOCK EMAIL] To: {target_email}\n[MOCK EMAIL] Subject: Password Reset Request\n[MOCK EMAIL] Content: Your reset link is: {reset_link}\n"
            print(msg)
            return True, "Mock sent successfully"

        try:
            msg = MIMEMultipart()
            msg['From'] = f"{Config.SMTP_FROM_NAME} <{Config.SMTP_USER}>"
            msg['To'] = target_email
            msg['Subject'] = "Action Required: Reset Your Vignan Portal Password"

            body = f"""
            Hello,

            We received a request to reset the password for your Vignan Academic Portal account (ID: {registration_number}).

            To proceed with your password reset, please click the following link:
            {reset_link}

            This link is secure and will remain valid for the next 2 hours. If you did not request this, please ignore this email; no changes have been made to your account.

            Best regards,
            Academic Portal Admin Desk
            Vignan's Foundation for Science, Technology & Research
            """
            
            msg.attach(MIMEText(body, 'plain'))

            server = smtplib.SMTP(Config.SMTP_HOST, Config.SMTP_PORT, timeout=10)
            if Config.SMTP_USE_TLS:
                server.starttls()
            
            server.login(Config.SMTP_USER, Config.SMTP_PASSWORD)
            server.send_message(msg)
            server.quit()
            
            return True, "Reset email sent successfully"
        except Exception as e:
            print(f"[EMAIL ERROR] Reset failed for {target_email}: {e}")
            return False, str(e)
