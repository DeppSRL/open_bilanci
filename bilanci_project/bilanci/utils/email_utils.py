def send_notification_email(msg_string):
    # Import smtplib for the actual sending function
    import smtplib

    # Import the email modules we'll need
    from email.mime.text import MIMEText

    # Create a text/plain message
    msg = MIMEText(msg_string)

    # me == the sender's email address
    # you == the recipient's email address
    from_addr = "root@openbilanci.it"
    to_addr = "stefano.vergani.it@gmail.com"
    msg['Subject'] = msg_string
    msg['From'] = from_addr
    msg['To'] = to_addr

    # Send the message via our own SMTP server, but don't include the
    # envelope header.
    s = smtplib.SMTP('localhost')
    s.sendmail(from_addr, [to_addr], msg.as_string())
    s.quit()