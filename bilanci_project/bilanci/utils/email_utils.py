from django.conf import settings

def send_notification_email(msg_string):
    # Import smtplib for the actual sending function
    import smtplib

    # Import the email modules we'll need
    from email.mime.text import MIMEText

    if settings.INSTANCE_TYPE is 'development':
        return

    # Create a text/plain message
    msg = MIMEText(msg_string)

    from_addr = "root@openbilanci.it"
    managers_email = [po[1] for po in settings.PROJECT_OWNERS]
    msg['Subject'] = msg_string
    msg['From'] = from_addr
    msg['To'] = ",".join(managers_email)

    # Send the message via our own SMTP server, but don't include the
    # envelope header.
    s = smtplib.SMTP('localhost')
    s.sendmail(from_addr, managers_email, msg.as_string())
    s.quit()