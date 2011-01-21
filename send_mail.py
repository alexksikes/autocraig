# Author : Alex Ksikes
# Parts from Python Network Programming

# requires:
# - a configured smtp sever

from email.MIMEText import MIMEText
from email.MIMEMultipart import MIMEMultipart
from email.MIMEBase import MIMEBase
from email import Utils, Encoders
import mimetypes, smtplib, sys

def genpart(data, contentype):
    maintype, subtype = contentype.split('/')
    if maintype == 'text':
        retval = MIMEText(data, _subtype=subtype)
    else:
        retval = MIMEBase(maintype, subtype)
        retval.set_payload(data)
        Encoders.encode_base64(retval)
    return retval

def attachment(filename):
    fd = open(filename, 'rb')
    mimetype, mimeencoding = mimetypes.guess_type(filename)
    if mimeencoding or (mimetype is None):
        mimetype = 'application/octet-stream'
    retval = genpart(fd.read(), mimetype)
    retval.add_header('Content-Disposition', 'attachment', filename=filename)
    fd.close()
    return retval

class Mailer:
    def __init__(self, server='localhost', verbose=False):
        self.server = server
        self.verbose = verbose
        
    def compose(self, to_addrs=[], from_addr='', subject='', message='', cc_addrs=[], 
                bcc_addrs=[], content_type='text/plain', attachments=[]):
        
        self.subject = subject
        self.to_addrs = to_addrs
        self.from_addr = from_addr
        
        if not attachments and content_type == 'text/plain':
            msg = MIMEText(message)
        else:
            msg = MIMEMultipart()
        
        # should be refactored
        msg['To'] = ','.join(to_addrs)
        msg['From'] = from_addr
        if cc_addrs:
            msg['Cc'] = ','.join(cc_addrs)
        msg['Subject'] = subject
        msg['Date'] = Utils.formatdate(localtime=1)
        msg['Message-ID'] = Utils.make_msgid()
        
        if content_type != 'text/plain':
            body = MIMEMultipart('alternative')
            body.attach(genpart(message, content_type))
            msg.attach(body)
        
        for a in attachments:
            msg.attach(attachment(a))
        
        self.msg = msg.as_string()
        
    def send(self):
        s = smtplib.SMTP(self.server)
        if self.verbose:
            s.set_debuglevel(1)
        s.sendmail(self.from_addr, self.to_addrs, self.msg)
        s.close()
        if self.verbose:
            print "Message successfully sent %d recipient(s)" % len(self.to_addrs)

def send_mail(to_addrs=[], from_addr='', subject='', message='', cc_addrs=[], 
              bcc_addrs=[], content_type='text/plain', attachments=[], verbose=False):
    m = Mailer(verbose=verbose)
    m.compose(to_addrs, from_addr, subject, message, cc_addrs, bcc_addrs, content_type, attachments)
    m.send()

def usage():
    print "Usage: python mail.py [options] message_file"
    print
    print "Description:" 
    print "Sends an email using python email library"
    print
    print "Options:" 
    print "-m, --mail : email_1@hostname,...,email_n@hostname"
    print "-c, --content-type: content type"
    print "-a, --attachments : files to be attached"
    print "-s, --subject : subject of the email"
    print "-f, --from : from of the email"
    print "-r, --reply : and reply of the email sent"
    print "--cc : carbon copy"
    print "-v, --verbose : show all"
    print
    print "Email bugs/suggestions to Alex Ksikes (alex.ksikes@gmail.com)" 
    
import sys, getopt
def main():
    try:
        opts, args = getopt.getopt(sys.argv[1:], "m:c:a:s:f:r:vh", 
                        ["mail=", "content-type=", "attachments=", 
                         "subject=", "from=", "reply=", "cc=", 
                         "verbose", "help"])
    except getopt.GetoptError:
        usage()
        sys.exit(2)
    
    content_type = 'text/plain'
    to_addrs, cc_addrs, attachments = [], [], []
    subject = from_addr = reply = ''
    verbose = False
    for o, a in opts:
        if o  in ("-m", "--mail"):
            to_addrs = a.split(',')
        elif o in ("-c", "--content-type"):
            content_type = a   
        elif o in ("-a", "--attachments"):
            attachments = a.split()   
        elif o in ("-s", "--subject"):
            subject = a
        elif o in ("-f", "--from"):
            from_addr = a  
        elif o in ("--cc"):
            cc_addrs = a.split(',')
        elif o in ("-v", "--verbose"):
            verbose = True  
        elif o in ("-h", "--help"):
            usage()
            sys.exit()
    if len(args) < 1:
        usage()
    else:
        send_mail(to_addrs=to_addrs, from_addr=from_addr, subject=subject, message=open(sys.argv[-1]).read(), 
             cc_addrs=cc_addrs, content_type=content_type, attachments=attachments, verbose=verbose)
      
if __name__ == '__main__':
    main()
