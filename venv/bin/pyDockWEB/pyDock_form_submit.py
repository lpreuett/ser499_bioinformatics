import time, sys
from selenium import webdriver
from selenium.webdriver.firefox.options import Options

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
browser = webdriver.Firefox(firefox_options=options)
browser.implicitly_wait(60)
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
        radio_but.click()
# enter receptor pdb
rec_tb = browser.find_element_by_name('receptor_pdb_code')
rec_tb.send_keys(receptor)
# enter ligand pdb
lig_tb = browser.find_element_by_name('ligand_pdb_code')
lig_tb.send_keys(ligand)
# select agreement statement
browser.find_element_by_name('agreement').click()
# submit form
browser.find_element_by_name('submit').click()

# select receptor chains
receptor_chains_list = browser.find_elements_by_name('chains_receptor')
if receptor_chain == '':
    # select all of the chains
    for chain in receptor_chains_list:
        chain.click()
else:
    # select only chains specified in chain list
    for chain in receptor_chains_list:
        if chain.get_attribute('value') in receptor_chain:
            chain.click()

# select ligand chains
ligand_chains_list = browser.find_elements_by_name('chains_ligand')
if ligand_chain == '':
    # select all of the chains
    for chain in ligand_chains_list:
        chain.click()
else:
    # select only chains specified in chain list
    for chain in ligand_chains_list:
        if chain.get_attribute('value') in ligand_chain:
            chain.click()
# continue to next page
browser.find_element_by_name('submit').click()
# skip restraints and continue to submission page
btns = browser.find_elements_by_class_name('btn')
for btn in btns:
    if btn.get_attribute('value') == 'Next Step':
        btn.click()
# submit job
btns = browser.find_elements_by_class_name('btn')
for btn in btns:
    if btn.get_attribute('value') == 'Submit job':
        btn.click()
        print('job submitted')

browser.close()