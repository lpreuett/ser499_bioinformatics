import time, sys
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys

START_URL = 'https://life.bsc.es/pid/pydockweb/default/index'
EMAIL = 'ser499webscraper@gmail.com'

if len(sys.argv) != 3:
    print('Usage: -a receptor -a ligand')
    sys.exit(1)

receptor = sys.argv[1]
receptor_chain = ''
if ':' in receptor:
    receptor_chain = receptor.split(':')[1].upper()
    receptor = receptor.split(':')[0]

ligand = sys.argv[2]
ligand_chain = ''
if ':' in ligand:
    ligand_chain = ligand.split(':')[1].upper()
    ligand = ligand.split(':')[0]

options = Options()
options.add_argument("--headless")
browser = webdriver.Chrome(chrome_options=options) #Firefox(firefox_options=options)
browser.implicitly_wait(30)
actions = ActionChains(browser)
# load job submit page
browser.get(START_URL)
# enter project name
project_name = browser.find_element_by_name('project_name')
project_name.send_keys('{}_{}'.format(sys.argv[1], sys.argv[2]))
# enter email
email = browser.find_element_by_name('email')
email.send_keys(EMAIL)
# select option to enter PDB codes
operation_list = browser.find_elements_by_name('operation')

for radio_but in operation_list:
    if 'pdb_code' == radio_but.get_attribute('value'):
        actions.move_to_element(radio_but).click().perform()
        #radio_but.click()
# enter receptor pdb
rec_tb = browser.find_element_by_name('receptor_pdb_code')
actions.send_keys_to_element(rec_tb, receptor)
#rec_tb.send_keys(receptor)
# enter ligand pdb
lig_tb = browser.find_element_by_name('ligand_pdb_code')
actions.send_keys_to_element(lig_tb, ligand)
#lig_tb.send_keys(ligand)
# select agreement statement
agree_chkbx = browser.find_element_by_name('agreement')
actions.move_to_element_with_offset(agree_chkbx, 0, 20).click().perform()
#agree_chkbx.click()
# submit form
actions.move_to_element(browser.find_element_by_name('submit')).click().perform()

# select receptor chains
receptor_chains_list = browser.find_elements_by_name('chains_receptor')
if receptor_chain == '':
    # select all of the chains
    for chain in receptor_chains_list:
        actions.move_to_element(chain).click().perform()
else:
    # select only chains specified in chain list
    for chain in receptor_chains_list:
        if chain.get_attribute('value') in receptor_chain:
            actions.move_to_element(chain).click().perform()

# select ligand chains
ligand_chains_list = browser.find_elements_by_name('chains_ligand')
if ligand_chain == '':
    # select all of the chains
    for chain in ligand_chains_list:
        actions.move_to_element(chain).click().perform()
else:
    # select only chains specified in chain list
    for chain in ligand_chains_list:
        if chain.get_attribute('value') in ligand_chain:
            actions.move_to_element(chain).click().perform()
# continue to next page
actions.move_to_element(browser.find_element_by_name('submit')).click().perform()
# skip restraints and continue to submission page
btns = browser.find_elements_by_class_name('btn')
for btn in btns:
    if btn.get_attribute('value') == 'Next Step':
        actions.move_to_element(btn).click().perform()
# submit job
btns = browser.find_elements_by_class_name('btn')
for btn in btns:
    if btn.get_attribute('value') == 'Submit job':
        actions = ActionChains(browser)
        actions.move_to_element(btn).click().perform()
        #btn.send_keys(Keys.RETURN)
        print('job submitted')

browser.close()