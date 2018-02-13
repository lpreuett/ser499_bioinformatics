import imaplib
import email
import sys
import datetime
import re

ORG_EMAIL = '@gmail.com'
FROM_EMAIL = 'ser499webscraper' + ORG_EMAIL
FROM_PWD = 'webscraping101'
SMPT_SERVER = 'imap.gmail.com'
SMPT_PORT = 993

def read_mail(mail):
    try:

        # search for message
        rv, data = mail.search(None, 'FROM', 'ppdock@tau.ac.il', '(UNSEEN)')
        
        if rv != 'OK':
            print('Error: no messages found')
            return
        
        for num in data[0].split():
            rv, data = mail.fetch(num, '(RFC822)')
            if rv != 'OK':
                print('Error: unable to open message')
                return
            
            msg = email.message_from_bytes(data[0][1])
            hdr = email.header.make_header(email.header.decode_header(msg['Subject']))
            subject = str(hdr)

            date_tuple = email.utils.parsedate_tz(msg['Date'])
            if date_tuple:
                local_date = datetime.datetime.fromtimestamp(
                    email.utils.mktime_tz(date_tuple))
                print("Local Date: {}".format(local_date.strftime("%a, %d %b %Y %H:%M:%S")))

            if msg.is_multipart():
                payload = msg.get_payload()[0].get_payload()
                print('payload: {}'.format(payload))
            else:
                payload = msg.get_payload()
                print('payload: {}'.format(payload))

            # re source: https://stackoverflow.com/questions/9760588/how-do-you-extract-a-url-from-a-string-using-python
            print('link: {}'.format(re.search("(?P<url>https?://[^\s]+)", payload).group("url")))

    except:
        print('Error during link extraction')


# gmail server
mail = imaplib.IMAP4_SSL(SMPT_SERVER)
try:
    # login to email
    rv, data = mail.login(FROM_EMAIL, FROM_PWD)
except imaplib.IMAP4.error:
    print('Login failed!')
    sys.exit(1)

print('Login: rv: {} \n data: {}'.format(rv, data))

'''
lists mailboxes 
rv, mailboxes = mail.list()
if rv == 'OK':
    print('Mailboxes: {}'.format(mailboxes))
'''

rv, data = mail.select('inbox')
if rv == 'OK':
    print('Processing mailbox')
    read_mail(mail)
    mail.close()
else:
    print('Error: unable to open inbox')

mail.logout()
