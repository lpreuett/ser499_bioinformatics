import sys, os
from selenium import webdriver

START_URL = 'http://zdock.umassmed.edu/'
TEST_URL = 'http://httpbin.org/post'
EMAIL = 'lpreuett@asu.edu'


if len(sys.argv) != 3:
    print('Usage: -a receptor -a ligand')
    sys.exit(1)

print('cwd: {}'.format(os.getcwd()))

browser = webdriver.Firefox()

browser.get(START_URL)

# get receptor & ligand text inputs
receptor_input = browser.find_element_by_id('pdbid1')
ligand_input = browser.find_element_by_id('pdbid2')

receptor_input.send_keys(sys.argv[1])
ligand_input.send_keys(sys.argv[2])

# get email text input
email_input = browser.find_element_by_name('useremail')

email_input.send_keys(EMAIL)

# check skip residues
if (not browser.find_element_by_name("skipselect").is_selected()):
     browser.find_element_by_name("skipselect").click()

# click submit button
browser.find_element_by_name('upload').click()

print('Source: {}'.format(browser.page_source))

browser.quit()