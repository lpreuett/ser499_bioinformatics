import imaplib
import email
import sys
import datetime
import re

ORG_EMAIL = '@gmail.com'
EMAIL = 'ser499webscraper' + ORG_EMAIL
EMAIL_PWD = 'webscraping101'
SMPT_SERVER = 'imap.gmail.com'
SMPT_PORT = 993

debug = False

def read_mail(mail, from_email, receptor_id, ligand_id):
    try:
        # search for message
        rv, data = mail.search(None, 'FROM', from_email, '(UNSEEN)')
        
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
                if debug:
                    print("Local Date: {}".format(local_date.strftime("%a, %d %b %Y %H:%M:%S")))

            if msg.is_multipart():
                payload = msg.get_payload()[0].get_payload()
                if debug:
                    print('payload: {}'.format(payload))
            else:
                payload = msg.get_payload()
                if debug:
                    print('payload: {}'.format(payload))


            receptor_split = receptor_id.split(':')
            ligand_split = ligand_id.split(':')

            if len(receptor_split) == 1:
                receptor_split.append('')
            if len(ligand_split) == 1:
                ligand_split.append('')

            if debug:
                print('Searching for : {}{}_{}{}'.format(receptor_split[0], receptor_split[1].upper(), ligand_split[0], \
                                        ligand_split[1].upper()))
                print('Results of search: {}'.format(re.search('{}{}_{}{}'.format(receptor_split[0], receptor_split[1].upper(), ligand_split[0], \
                            ligand_split[1].upper()), payload)))

            if re.search('{}{}_{}{}'.format(receptor_split[0], receptor_split[1].upper(), ligand_split[0], \
                        ligand_split[1].upper()), payload) != None:
                # re source: https://stackoverflow.com/questions/9760588/how-do-you-extract-a-url-from-a-string-using-python
                print('link: {}'.format(re.search("(?P<url>https?://[^\s]+)", payload).group("url")))
                return
            else:
                # mark as unseen so the calling thread can find it
                mail.store(num, '-FLAGS', '(\SEEN)')

        raise ValueError('Email not found.')
    except:
        print('Error during link extraction')

from_email = sys.argv[1]
receptor_id = sys.argv[2]
ligand_id = sys.argv[3]

if debug:
    print('from_email {}'.format(from_email))
    print('receptor: {}'.format(receptor_id))
    print('ligand {}'.format(ligand_id))

# gmail server
mail = imaplib.IMAP4_SSL(SMPT_SERVER)
try:
    # login to email
    rv, data = mail.login(EMAIL, EMAIL_PWD)
except imaplib.IMAP4.error:
    print('Login failed!')
    sys.exit(1)

if debug:
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
    read_mail(mail, from_email, receptor_id, ligand_id)
    mail.close()
else:
    print('Error: unable to open inbox')

mail.logout()
