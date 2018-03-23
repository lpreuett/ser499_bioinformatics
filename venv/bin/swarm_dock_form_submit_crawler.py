import requests, sys, urllib3, json, os
from selenium import webdriver
from selenium.webdriver.firefox.options import Options

START_URL = 'https://bmm.crick.ac.uk/~svc-bmm-swarmdock/submit.cgi'
EMAIL = 'ser499webscraper@gmail.com'

if len(sys.argv) != 3:
    print('Usage: -a receptor -a ligand')
    sys.exit(1)


options = Options()
options.add_argument("--headless")
browser = webdriver.Firefox(firefox_options=options)
browser.implicitly_wait(30)

browser.get(START_URL)

receptor = sys.argv[1]
if ':' in receptor:
    receptor = receptor.split(':')[0]

ligand = sys.argv[2]
if ':' in ligand:
    ligand = ligand.split(':')[0]

# upload receptor file
rec_file = browser.find_element_by_name('receptorfile')
rec_file.send_keys(os.getcwd() + '/Swarm Dock/pdb/{}.pdb'.format(receptor.upper()))

# upload ligand file
lig_file = browser.find_element_by_name('ligandfile')
lig_file.send_keys(os.getcwd() + '/Swarm Dock/pdb/{}.pdb'.format(ligand.upper()))

# set email
email_input = browser.find_element_by_name('email')
email_input.send_keys(EMAIL)

# set job name
job_name_input = browser.find_element_by_name('jobname')
job_name_input.send_keys(sys.argv[1] + '_' + sys.argv[2])

# submit job
browser.find_element_by_name('formSubmitBut').click()

# get job ID
content_div = browser.find_element_by_id('content')

print('content {}'.format(content_div.text))

browser.quit()


