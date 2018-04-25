import subprocess
import time
import re
import sys
import threading
import multiprocessing as mp
import csv
import os
import tarfile
import sqlite3

PROCESS_NAME_PATCH_DOCK = 'patch_dock'
PATCH_DOCK_DIR = './Patch Dock'
PATCH_DOCK_SCORES_DIR = PATCH_DOCK_DIR + '/output'
PATCH_DOCK_START_FILE = PATCH_DOCK_DIR + '/patch_dock_form_submit_crawler.py'
PATCH_DOCK_READ_MAIL_FILE = 'read_mail.py'
PATCH_DOCK_GET_RESULTS_FILE = PATCH_DOCK_DIR + '/patch_dock_get_results.py'
PATCH_DOCK_FROM_EMAIL = 'ppdock@tau.ac.il'

SWARM_DOCK_DIR = './Swarm Dock'
SWARM_DOCK_OUTPUT_DIR = SWARM_DOCK_DIR + '/output'
PROCESS_NAME_SWARM_DOCK = 'swarm_dock'
SWARM_DOCK_START_FILE = SWARM_DOCK_DIR + '/swarm_dock_form_submit_crawler.py'
SWARM_DOCK_READ_MAIL_FILE = 'read_mail.py'
SWARM_DOCK_GET_RESULTS_FILE = SWARM_DOCK_DIR + '/swarm_dock_get_results.py'
SWARM_DOCK_FROM_EMAIL = 'lif-swarmdock@crick.ac.uk'
DOWNLOAD_PDB_FILE = SWARM_DOCK_DIR +'/download_pdb.py'

PYDOCK_DIR = './pyDockWEB'
PYDOCK_OUTPUT_DIR = PYDOCK_DIR + '/output'
PROCESS_NAME_PYDOCK = 'py_dock'
PYDOCK_READ_MAIL_FILE = 'read_mail.py'
PYDOCK_START_FILE = PYDOCK_DIR + '/pyDock_form_submit.py'
PYDOCK_GET_RESULTS_FILE = PYDOCK_DIR + '/pyDock_get_results.py'
PYDOCK_FROM_EMAIL = 'pydock@mmb.pdb.ub.es'

DB_DIR = './Database'
DB_FILENAME = 'workflow.db'

OUTPUT_DIR = './workflow_output'

MAX_NUM_WORKFLOW_PROCESSES = 1

def start_pydock_workflow(receptor_id, ligand_id, output):
    print('Receptor: {} Ligand: {}'.format(receptor_id, ligand_id))
    # check for stored results
    filename = receptor_id.split(':')[0].upper() + '_' + ligand_id.split(':')[0].upper() + '.tar.gz'
    if os.path.isdir(PYDOCK_OUTPUT_DIR) and os.path.isfile(PYDOCK_OUTPUT_DIR + '/' + filename):
        pydock_score = get_pydock_results_from_file(filename)
    else:
        # check mailbox for results first
        try:
            link = read_pydock_mail(receptor_id, ligand_id)
            received_pydock_msg = True
        except:
            # submit job to Patch Dock
            run_pydock_start(receptor_id, ligand_id)
            received_pydock_msg = False
        # get response from Patch Dock
        first_itr = True
        while (not received_pydock_msg):
            if first_itr:
                print('Waiting 30 minutes...')
                time.sleep(1800)  # 30 minute wait
                first_itr = False
            else:
                print('Waiting 5 minutes...')
                time.sleep(300)

            try:
                link = read_pydock_mail(receptor_id, ligand_id)
                received_py_dock_msg = True
            except:
                print('No response from PyDock.')

        pydock_score = get_pydock_results(link, receptor_id, ligand_id)

    print('PyDock Score for receptor: {} and ligand: {} is {}'.format(receptor_id, ligand_id, pydock_score))
    output.put((PROCESS_NAME_PYDOCK, receptor_id, ligand_id, pydock_score))

def run_pydock_start(receptor, ligand):
    pydock_start_process = subprocess.Popen(
            ['python', PYDOCK_START_FILE, receptor, ligand],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    communicateRes = pydock_start_process.communicate()
    stdout, stderr = communicateRes

    print('initial web scraper stdout: {} \n initial web scraper stderr: {}'.format(stdout, stderr))

    if ' line ' not in str(stderr):
        print('Successfully submitted PyDock job.')
    else:
        print('Error in run_pydock_start: {}'.format(stderr))
        raise Exception('run_pydock_start')

def read_pydock_mail(receptor, ligand):
    read_pydock_process = subprocess.Popen(['python', PYDOCK_READ_MAIL_FILE, PYDOCK_FROM_EMAIL, \
                                                receptor, ligand], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    communicateRes = read_pydock_process.communicate()
    stdout, stderr = communicateRes

    print('read mail stdout: {}'.format(stdout))
    print('read mail stderr: {}'.format(stderr))

    # re source: https://stackoverflow.com/questions/9760588/how-do-you-extract-a-url-from-a-string-using-python
    link = re.search("(?P<url>https?://[^\s]+)", str(stdout)).group("url").split('\\r')[0]
    # strip extra chars
    link = link.strip("\\n'")
    print('link: {}'.format(link))
    return link

def get_pydock_results(link, receptor, ligand):
    get_pydock_process = subprocess.Popen(
        ['python', PYDOCK_GET_RESULTS_FILE, link, receptor ,ligand],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    communicateRes = get_pydock_process.communicate()
    stdout, stderr = communicateRes

    print('stdout: {}'.format(str(stdout)))

    results = re.findall(r'[-]?[0-9]+[.]?[0-9]*', str(stdout))

    return results

def get_pydock_results_from_file(filename):
    # extract .tar.gz
    tar = tarfile.open(PYDOCK_OUTPUT_DIR + '/' + filename)
    tar_members = tar.getmembers()
    RESULTS_FILE = None
    for m in tar_members:
        if re.search('\w+\.ene', m.name):
            RESULTS_FILE = m.name
    results_file = tar.extractfile(RESULTS_FILE)

    results = None
    line_num = 0
    for line in results_file:
        if line_num == 2:
            # top result
            decoded_line = line.decode('utf-8')
            outputs = re.findall('(-?\d+\.\d+)', decoded_line)
            results = ' '.join(outputs)
            break

        line_num += 1

    return results.rstrip().split(' ')

def run_patch_dock_start(receptor, ligand):
    patch_dock_start_process = subprocess.Popen(
            ['scrapy', 'runspider', PATCH_DOCK_START_FILE, '-a', 'receptor='+receptor, '-a', 'ligand='+ligand],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    communicateRes = patch_dock_start_process.communicate()
    stdout, stderr = communicateRes

    print('initial web scraper stdout: {} \n initial web scraper stderr: {}'.format(stdout, stderr))

    if ' line ' not in str(stderr):
        print('Successfully submitted Patch Dock job.')
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

def get_patch_dock_results_from_file(filename):
    with open(PATCH_DOCK_SCORES_DIR + '/' + filename, 'r') as file:
        line = file.readline()
    return line

def patch_dock_save_score(receptor_id, ligand_id, score):
    if not os.path.isdir(PATCH_DOCK_DIR):
        os.mkdir(PATCH_DOCK_DIR)
    if not os.path.isdir(PATCH_DOCK_SCORES_DIR):
        os.mkdir(PATCH_DOCK_SCORES_DIR)

    filename = receptor_id.split(':')[0].upper() + '_' + ligand_id.split(':')[0].upper() + '.txt'
    with open(PATCH_DOCK_SCORES_DIR + '/' + filename, 'w') as file:
        file.write(str(score))

def start_patch_dock_workflow(receptor_id, ligand_id, output):
    print('Receptor: {} Ligand: {}'.format(receptor_id, ligand_id))
    # check for stored results
    filename = receptor_id.split(':')[0].upper() + '_' + ligand_id.split(':')[0].upper() + '.txt'
    if os.path.isdir(PATCH_DOCK_SCORES_DIR) and os.path.isfile(PATCH_DOCK_SCORES_DIR + '/' + filename):
        patch_dock_score = get_patch_dock_results_from_file(filename)
    else:
        # check mailbox for results first
        try:
            link = read_patch_dock_mail(receptor_id, ligand_id)
            received_patch_dock_msg = True
        except:
            # submit job to Patch Dock
            run_patch_dock_start(receptor_id, ligand_id)
            received_patch_dock_msg = False
        # get response from Patch Dock
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
        patch_dock_save_score(receptor_id, ligand_id, patch_dock_score)

    print('Patch Dock Score for receptor: {} and ligand: {} is {}'.format(receptor_id, ligand_id, patch_dock_score))
    output.put((PROCESS_NAME_PATCH_DOCK, receptor_id, ligand_id, patch_dock_score))

def run_swarm_dock_start(receptor, ligand):
    swarm_dock_start_process = subprocess.Popen(
        ['python', SWARM_DOCK_START_FILE, receptor, ligand],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    communicateRes = swarm_dock_start_process.communicate()
    stdout, stderr = communicateRes

    print('swarm dock start stdout: {} \n swarm dock start stderr: {}'.format(stdout, stderr))

    if 'ID:' in str(stdout):
        print('Successfully submitted Swarm Dock job.')
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

def get_swarm_dock_results_from_file(filename):
    RESULTS_FILENAME = 'sds/clusters_standard.txt'
    # extract .tar.gz
    tar = tarfile.open(SWARM_DOCK_OUTPUT_DIR + '/' + filename)
    results_file = tar.extractfile(RESULTS_FILENAME)

    results = None
    is_first_line = True
    for line in results_file:
        if is_first_line:
            is_first_line = False
            continue
        # select first result with 3 or less members
        # decode line
        decoded_line = line.decode('utf8')
        # count number of members
        members_start = decoded_line.find('[')
        members_finish = decoded_line.find(']')
        members = decoded_line[members_start + 1:members_finish].split('|')
        if len(members) <= 3:
            results = decoded_line.split(' ')
            results = results[1:3] + results[4:]
            results = ' '.join(results)
            break
    # returns array of scores
    return results.rstrip().split(' ')

def start_swarm_dock_workflow(receptor_id, ligand_id, output):
    print('Receptor: {} Ligand: {}'.format(receptor_id, ligand_id))
    # check if results are stored
    filename = receptor_id.split(':')[0].upper() + '_' + ligand_id.split(':')[0].upper() + '.tar.gz'
    if os.path.isdir(SWARM_DOCK_OUTPUT_DIR) and os.path.isfile(SWARM_DOCK_OUTPUT_DIR + '/' + filename):
        swarm_dock_score = get_swarm_dock_results_from_file(filename)
    else:
        received_swarm_dock_msg = False
        # check mailbox for results first
        try:
            link = read_swarm_dock_mail(receptor_id, ligand_id)
            received_swarm_dock_msg = True
        except:
            # download pdbs
            download_pdb(receptor_id)
            download_pdb(ligand_id)
            # submit job to Patch Dock
            try:
                run_swarm_dock_start(receptor_id, ligand_id)
            except:
                print('Error submitting swarm dock job')
                sys.exit(1)

        # get response from Swarm Dock
        iteration = 0
        while (not received_swarm_dock_msg):
            if iteration == 0:
                print('Waiting 30 minutes...')
                time.sleep(1800)  # 30 minute wait
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
    output.put((PROCESS_NAME_SWARM_DOCK, receptor_id, ligand_id, float(swarm_dock_score[0]), int(swarm_dock_score[1]), int(swarm_dock_score[2]),
                        int(swarm_dock_score[3]), int(swarm_dock_score[4]), float(swarm_dock_score[5]), float(swarm_dock_score[6])))

def write_output(results):
    # test for existence of pdb dir
    if not os.path.isdir(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    with open(OUTPUT_DIR + '/workflow_output.csv', 'w', newline='') as csvfile:
        for r in results:
            writer = csv.writer(csvfile, delimiter=' ')
            writer.writerow(r)


def does_pdb_chain_exist(pdb_id, chain, cursor):
    # test for existence of pdb_id and chain
    results = cursor.execute('SELECT chain FROM Protein WHERE pdb_id=:pdb_id', {'pdb_id': pdb_id})

    for result in results.fetchall():
        if result != None and chain == result[0]:
            # pdb_id and chain pair already exists
            return True
    # The pair does not exist
    return False

def insert_pdb(pdb_id, chain, cursor):
    # test for existence of pdb_id and chain pair
    if does_pdb_chain_exist(pdb_id, chain, cursor):
        return
    pdb_entry_id = cursor.execute('SELECT max(id) FROM Protein').fetchone()[0]
    if pdb_entry_id == None:
        pdb_entry_id = 1
    else:
        pdb_entry_id += 1
    filename = pdb_id.upper() + '.pdb'
    file_path = SWARM_DOCK_DIR + 'pdb/' + filename
    # verify file exists
    if not os.path.isfile(file_path):
        # download if file does not exist
        download_pdb(pdb_id)
    f_stat = os.stat(file_path)
    date = datetime.fromtimestamp(f_stat.st_birthtime).date()
    if chain == None:
        insert_sql = 'INSERT INTO Protein VALUES ' + "({}, \'{}\', {}, \'{}\', \'{}\')".format(pdb_entry_id, pdb_id,
                                                                                               chain, filename,
                                                                                               date)
    else:
        insert_sql = 'INSERT INTO Protein VALUES ' + "({}, \'{}\', \'{}\', \'{}\', \'{}\')".format(pdb_entry_id, pdb_id,
                                                                                                   chain, filename,
                                                                                                   date)
    if debug:
        print('insert_sql: {}'.format(insert_sql))
    cursor.execute(insert_sql)

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

# create connection to db
conn = sqlite3.connect('{}/{}'.format(DB_DIR, DB_FILENAME))
# get db cursor
cursor = conn.cursor()

# insert pdbs into db
for pair in rec_lig_pairs:
    rec_split = pair[0].split(':')
    rec = rec_split[0]
    if len(rec_split) > 1:
        rec_chain = pair[0].split(':')[1]
    else:
        rec_chain = None
    lig_split = pair[1].split(':')
    lig = lig_split[0]
    if len(lig_split) > 1:
        lig_chain = lig_split[1]
    else:
        lig_chain = None
    if not does_pdb_chain_exist(rec, rec_chain, cursor):
        db_insert_pdb(rec, rec_chain, cursor)
    if not does_pdb_chain_exist(lig, lig_chain, cursor):
        db_insert_pdb(lig, lig_chain, cursor)

# save changes to db
conn.commit()
conn.close()

# create processes
patch_dock_processes = [mp.Process(target=start_patch_dock_workflow, args=(pair[0], pair[1], output)) for pair in rec_lig_pairs]
swarm_dock_processes = [mp.Process(target=start_swarm_dock_workflow, args=(pair[0], pair[1], output)) for pair in rec_lig_pairs]
pydock_processes = [mp.Process(target=start_pydock_workflow, args=(pair[0], pair[1], output)) for pair in rec_lig_pairs]

processes_executed = 0

# start processes
while processes_executed < len(patch_dock_processes):
    num_processes_to_start = len(patch_dock_processes) - processes_executed
    if num_processes_to_start <= MAX_NUM_WORKFLOW_PROCESSES:
        for i in range(num_processes_to_start):
            patch_dock_processes[processes_executed + i].start()
            swarm_dock_processes[processes_executed + i].start()
            pydock_processes[processes_executed + i].start()
        for i in range(num_processes_to_start):
            patch_dock_processes[processes_executed + i].join()
            swarm_dock_processes[processes_executed + i].join()
            pydock_processes[processes_executed + i].join()
        processes_executed += num_processes_to_start
    else:
        for i in range(MAX_NUM_WORKFLOW_PROCESSES):
            print('start: processes_executed {} i: {}'.format(processes_executed, i))
            patch_dock_processes[processes_executed + i].start()
            swarm_dock_processes[processes_executed + i].start()
            pydock_processes[processes_executed + i].start()
        for i in range(MAX_NUM_WORKFLOW_PROCESSES):
            print('join: processes_executed {} i: {}'.format(processes_executed, i))
            patch_dock_processes[processes_executed + i].join()
            swarm_dock_processes[processes_executed + i].join()
            pydock_processes[processes_executed + i].join()
        processes_executed += MAX_NUM_WORKFLOW_PROCESSES

patch_dock_results = [output.get() for p in patch_dock_processes]
swarm_dock_results = [output.get() for p in swarm_dock_processes]
pydock_results = [output.get() for p in pydock_processes]

write_output(patch_dock_results + swarm_dock_results + pydock_results)

print('Patch Dock Results: {}'.format(patch_dock_results))
print('Swarm Dock Results: {}'.format(swarm_dock_results))
print('PyDock Results: {}'.format(pydock_results))

print('Concatenated Results: {}'.format(patch_dock_results + swarm_dock_results + pydock_results))
