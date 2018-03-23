import subprocess
import time
import re
import sys
import threading
import multiprocessing as mp
import csv
import os

PROCESS_NAME_PATCH_DOCK = 'patch_dock'
PATCH_DOCK_START_FILE = 'patch_dock_form_submit_crawler.py'
PATCH_DOCK_READ_MAIL_FILE = 'read_mail.py'
PATCH_DOCK_GET_RESULTS_FILE = 'patch_dock_get_results.py'
PATCH_DOCK_FROM_EMAIL = 'ppdock@tau.ac.il'

DOWNLOAD_PDB_FILE ='download_pdb.py'

PROCESS_NAME_SWARM_DOCK = 'swarm_dock'
SWARM_DOCK_START_FILE = 'swarm_dock_form_submit_crawler.py'
SWARM_DOCK_READ_MAIL_FILE = 'read_mail.py'
SWARM_DOCK_GET_RESULTS_FILE = 'swarm_dock_get_results.py'
SWARM_DOCK_FROM_EMAIL = 'lif-swarmdock@crick.ac.uk'

OUTPUT_DIR = './workflow_output'

MAX_NUM_WORKFLOW_PROCESSES = 1

def run_patch_dock_start(receptor, ligand):
    patch_dock_start_process = subprocess.Popen(
            ['scrapy', 'runspider', PATCH_DOCK_START_FILE, '-a', 'receptor='+receptor, '-a', 'ligand='+ligand],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    communicateRes = patch_dock_start_process.communicate()
    stdout, stderr = communicateRes

    print('initial web scraper stdout: {} \n initial web scraper stderr: {}'.format(stdout, stderr))

    if ' line ' not in str(stderr):
        print('Successfully submitted job.')
    else:
        print('Error in run_patch_dock_start: {}'.format(stderr))
        raise Exception('run_patch_dock_start')

def read_patch_dock_mail(receptor, ligand):
    read_patch_dock_process = subprocess.Popen(['python', PATCH_DOCK_READ_MAIL_FILE, PATCH_DOCK_FROM_EMAIL, \
                                                receptor, ligand], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    communicateRes = read_patch_dock_process.communicate()
    stdout, stderr = communicateRes

    print('read mail stdout: {}'.format(stdout))
    print('read mail stderr: {}'.format(stderr))

    # re source: https://stackoverflow.com/questions/9760588/how-do-you-extract-a-url-from-a-string-using-python
    link = re.search("(?P<url>https?://[^\s]+)", str(stdout)).group("url").split('\\r')[0]
    # strip extra chars
    link = link.strip("\\n'")
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

def start_patch_dock_workflow(receptor_id, ligand_id, output):
    print('Receptor: {} Ligand: {}'.format(receptor_id, ligand_id))
    # submit job to Patch Dock
    run_patch_dock_start(receptor_id, ligand_id)

    # get response from Patch Dock
    received_patch_dock_msg = False
    iteration = 0
    while (not received_patch_dock_msg):
        if iteration == 0:
            print('Waiting 30 minutes...')
            time.sleep(1800)  # 30 minute wait
        else:
            print('Waiting 5 minutes...')
            time.sleep(300)

        try:
            link = read_patch_dock_mail(receptor_id, ligand_id)
            received_patch_dock_msg = True
        except:
            print('No response from Patch Dock.')

        iteration += 1

    patch_dock_score = get_patch_dock_results(link)

    print('Patch Dock Score for receptor: {} and ligand: {} is {}'.format(receptor_id, ligand_id, patch_dock_score))
    output.put(('patch dock', receptor_id, ligand_id, patch_dock_score))

def run_swarm_dock_start(receptor, ligand):
    swarm_dock_start_process = subprocess.Popen(
        ['python', SWARM_DOCK_START_FILE, receptor, ligand],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    communicateRes = swarm_dock_start_process.communicate()
    stdout, stderr = communicateRes

    print('swarm dock start stdout: {} \n swarm dock start stderr: {}'.format(stdout, stderr))

    if 'ID:' in str(stdout):
        print('Successfully submitted job.')
    else:
        print('Error in run_swarm_dock_start: {}'.format(stderr))
        raise Exception('run_swarm_dock_start')

def download_pdb(pdb_id):
    swarm_dock_start_process = subprocess.Popen(
        ['python', DOWNLOAD_PDB_FILE, pdb_id],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    communicateRes = swarm_dock_start_process.communicate()
    stdout, stderr = communicateRes

    print('download pdb {}: {} \n swarm dock start stderr: {}'.format(pdb_id, stdout, stderr))

    # verify pdb_id existence
    if ':' in pdb_id:
        save_file_name = pdb_id.split(':')[0]
    else:
        save_file_name = pdb_id

    save_file_name = save_file_name.upper()

    if not os.path.isfile('./Swarm Dock/pdb/' + save_file_name + '.pdb'):
        raise Exception('Error in download pdb: {} could not be downloaded'.format(pdb_id))

def read_swarm_dock_mail(receptor, ligand):
    read_swarm_dock_process = subprocess.Popen(['python', SWARM_DOCK_READ_MAIL_FILE, SWARM_DOCK_FROM_EMAIL, \
                                                receptor, ligand], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    communicateRes = read_swarm_dock_process.communicate()
    stdout, stderr = communicateRes

    print('read mail stdout: {}'.format(stdout))
    print('read mail stderr: {}'.format(stderr))

    # re source: https://stackoverflow.com/questions/9760588/how-do-you-extract-a-url-from-a-string-using-python
    link = re.search("(?P<url>https?://[^\s]+)", str(stdout)).group("url").split('\\r')[0]
    # strip extra chars
    link = link.strip("\\n'")
    print('link: {}'.format(link))
    return link

def get_swarm_dock_results(link, receptor, ligand):
    get_swarm_dock_process = subprocess.Popen(
        ['python', SWARM_DOCK_GET_RESULTS_FILE, link, receptor, ligand],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    communicateRes = get_swarm_dock_process.communicate()
    stdout, stderr = communicateRes

    print('stdout: {}'.format(str(stdout)))

    results = re.findall(r'[-]?[0-9]+[.]?[0-9]*', str(stdout))

    return results

def start_swarm_dock_workflow(receptor_id, ligand_id, output):
    print('Receptor: {} Ligand: {}'.format(receptor_id, ligand_id))
    # download pdbs
    download_pdb(receptor_id)
    download_pdb(ligand_id)
    # submit job to Patch Dock
    run_swarm_dock_start(receptor_id, ligand_id)

    # get response from Swarm Dock
    received_swarm_dock_msg = False
    iteration = 0
    while (not received_swarm_dock_msg):
        if iteration == 0:
            print('Waiting 30 minutes...')
            # time.sleep(1800)  # 30 minute wait
        else:
            print('Waiting 10 minutes...')
            time.sleep(300)

        try:
            link = read_swarm_dock_mail(receptor_id, ligand_id)
            received_swarm_dock_msg = True
        except:
            print('No response from Swarm Dock.')

        iteration += 1

    swarm_dock_score = get_swarm_dock_results(link, receptor_id, ligand_id)


    print('Swarm Dock Score for receptor: {} and ligand: {} is {}'.format(receptor_id, ligand_id, swarm_dock_score))
    output.put(('swarm dock', receptor_id, ligand_id, float(swarm_dock_score[0]), int(swarm_dock_score[1]), int(swarm_dock_score[2]),
                        int(swarm_dock_score[3]), int(swarm_dock_score[4]), float(swarm_dock_score[5]), float(swarm_dock_score[6])))

def write_output(results):
    # test for existence of pdb dir
    if not os.path.isdir(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    with open(OUTPUT_DIR + '/workflow_output.csv', 'w', newline='') as csvfile:
        for r in results:
            writer = csv.writer(csvfile, delimiter=' ')
            writer.writerow(r)

output = mp.Queue()

try:
    print('Arg1: {}'.format(sys.argv[1]))
except:
    print('Usage: workflow_manager.py <input_file>')
    sys.exit(1)

try:
    with open(sys.argv[1], 'r') as input_file:
        rec_lig_pairs = []
        for line in input_file:
            # remove new line character
            line = line.strip('\n')
            rec_lig_pairs.append(line.split(' '))
except:
    print('Unable to process file: {}'.format(sys.argv[1]))
    sys.exit(1)

# create processes
patch_dock_processes = [mp.Process(target=start_patch_dock_workflow, args=(pair[0], pair[1], output)) for pair in rec_lig_pairs]
swarm_dock_processes = [mp.Process(target=start_swarm_dock_workflow, args=(pair[0], pair[1], output)) for pair in rec_lig_pairs]

processes_executed = 0

# start processes
while processes_executed < len(patch_dock_processes):
    num_processes_to_start = len(patch_dock_processes) - processes_executed
    if num_processes_to_start <= MAX_NUM_WORKFLOW_PROCESSES:
        for i in range(num_processes_to_start):
            patch_dock_processes[processes_executed + i].start()
            swarm_dock_processes[processes_executed + i].start()
        for i in range(num_processes_to_start):
            patch_dock_processes[processes_executed + i].join()
            swarm_dock_processes[processes_executed + i].join()
        processes_executed += num_processes_to_start
    else:
        for i in range(MAX_NUM_WORKFLOW_PROCESSES):
            print('start: processes_executed {} i: {}'.format(processes_executed, i))
            patch_dock_processes[processes_executed + i].start()
            swarm_dock_processes[processes_executed + i].start()
        for i in range(MAX_NUM_WORKFLOW_PROCESSES):
            print('join: processes_executed {} i: {}'.format(processes_executed, i))
            patch_dock_processes[processes_executed + i].join()
            swarm_dock_processes[processes_executed + i].join()
        processes_executed += MAX_NUM_WORKFLOW_PROCESSES

patch_dock_results = [output.get() for p in patch_dock_processes]
swarm_dock_results = [output.get() for p in swarm_dock_processes]

write_output(patch_dock_results + swarm_dock_results)

print('Patch Dock Results: {}'.format(patch_dock_results))
print('Swarm Dock Results: {}'.format(swarm_dock_results))