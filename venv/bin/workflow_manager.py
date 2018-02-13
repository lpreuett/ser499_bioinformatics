import subprocess
import time
import re

PATCH_DOCK_START_FILE = 'patch_dock_form_submit_crawler.py'
PATCH_DOCK_READ_MAIL_FILE = 'patch_dock_read_mail.py'
PATCH_DOCK_GET_RESULTS_FILE = 'patch_dock_get_results.py'

def run_patch_dock_start(receptor, ligand):
    patch_dock_start_process = subprocess.Popen(
            ['scrapy', 'runspider', PATCH_DOCK_START_FILE, '-a', 'receptor='+receptor, '-a', 'ligand='+ligand],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    communicateRes = patch_dock_start_process.communicate()
    stdout, stderr = communicateRes

    print('stdout: {} \nstderr: {}'.format(stdout, stderr))

    if ' line ' not in str(stderr):
        print('Successfully submitted job.')
    else:
        print('Error in run_patch_dock_start: {}'.format(stderr))
        raise Exception('run_patch_dock_start')

def read_patch_dock_mail():
    read_patch_dock_process = subprocess.Popen(['python', PATCH_DOCK_READ_MAIL_FILE], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    communicateRes = read_patch_dock_process.communicate()
    stdout, stderr = communicateRes

    # re source: https://stackoverflow.com/questions/9760588/how-do-you-extract-a-url-from-a-string-using-python
    link = re.search("(?P<url>https?://[^\s]+)", str(stdout)).group("url").split('\\r')[0]
    print('link: {}'.format(link))
    return link

def get_patch_dock_results(link):
    get_patch_dock_process = subprocess.Popen(
        ['scrapy', 'runspider', PATCH_DOCK_GET_RESULTS_FILE, '-a', 'link='+link],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    communicateRes = get_patch_dock_process.communicate()
    stdout, stderr = communicateRes

    print('stdout: {}'.format(str(stdout)))

    return int(re.search(r'\d+', str(stdout)).group())




# get receptor
receptor = input('Enter receptor ID: ')
# get ligand
ligand = input('Enter ligand ID: ')

# submit job to Patch Dock
run_patch_dock_start(receptor, ligand)

# get response from Patch Dock
received_patch_dock_msg = False
iteration = 0
while(not received_patch_dock_msg):
    if iteration == 0:
        print('Waiting 30 minutes...')
        time.sleep(1800)  # 30 minute wait
    else:
        print('Waiting 5 minutes...')
        time.sleep(300)

    try:
        link = read_patch_dock_mail()
        received_patch_dock_msg = True
    except:
        print('No response from Patch Dock.')

    iteration += 1

patch_dock_score = get_patch_dock_results(link)

print('Patch Dock Score for receptor: {} and ligand: {} is {}'.format(receptor, ligand, patch_dock_score))