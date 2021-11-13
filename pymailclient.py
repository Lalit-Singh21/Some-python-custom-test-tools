import sys
import os
import smtplib
import socket
import datetime
# Import the email modules we'll need
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

# Typical values for text_subtype are plain, html, xml
text_subtype = 'plain'
hostname=socket.gethostname()
# Set the "From" addresss
sender = hostname+'@testcycle.com'
# Modify the "To" list so add/remove email addresses
receivers = ['emails seperated by comma']

# Preparing message headers
message = MIMEMultipart()

message['Subject'] = 'Tested completed on %s at %s' %(hostname,datetime.datetime.now())
message['From'] = sender
message['To'] = ','.join(receivers)

# Prepare body of the email
content = 'Test mail services\nSuccess'
body = MIMEText(content.encode('utf-8'), text_subtype, 'utf-8')
message.attach(body)

# Read attachment file
summaryfile = sys.argv[1]
print(os.path.basename(summaryfile))
with open(summaryfile, "r") as f:
   part = MIMEBase('application', 'octet-stream')
   part.set_payload(f.read())
   encoders.encode_base64(part)
   part.add_header('Content-Disposition', 'attachment; filename=%s' %os.path.basename(summaryfile))
   message.attach(part)
   
try:
   # Using "sendmail" server enabled with "RELAY"
   # Lab box 10.77.68.78 is one of VM-Instances
   smtpObj = smtplib.SMTP('10.77.68.78','25')
   #smtpObj.set_debuglevel(True) # show communication with the server
   smtpObj.sendmail(sender, receivers, message.as_string())         
   print('Successfully sent email')
except SMTPException:
   print('Error: unable to send email')
