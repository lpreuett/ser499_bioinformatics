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
import importlib.util
from datetime import datetime

# import Classifier
knn_classifier_spec = importlib.util.spec_from_file_location('KNN_Classifier', './Classifiers/KNN_Classifier_V2.py')
knn_classifier = importlib.util.module_from_spec(knn_classifier_spec)
knn_classifier_spec.loader.exec_module(knn_classifier)

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

debug = True

def start_pydock_workflow(receptor_id, ligand_id, output):
    tool_id = 2
    new_results = False
    # check for stored results
    rec = receptor_id.split(':')[0]
    lig = ligand_id.split(':')[0]
    if results_exist(rec, lig, tool_id):
        pydock_score = get_results(rec, lig, tool_id)
    else:
        new_results = True
        # check mailbox for results first
        try:
            link = read_pydock_mail(receptor_id, ligand_id)
            received_pydock_msg = True
        except:
            # submit job to Patch Dock
            attempts = 0
            while not run_pydock_start(receptor_id, ligand_id) and attempts < 3:
                attempts += 1

            if attempts == 3:
                print('Error submitting pydock job')
                sys.exit(1)
            else:
                print('Successfully submitted PyDock job.')
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
        if new_results:
            insert_results(rec, lig, tool_id, pydock_score)

    print('PyDock Score for receptor: {} and ligand: {} is {}'.format(receptor_id, ligand_id, pydock_score))
    output.put((PROCESS_NAME_PYDOCK, receptor_id, ligand_id, pydock_score))

def run_pydock_start(receptor, ligand):
    pydock_start_process = subprocess.Popen(
            ['python', PYDOCK_START_FILE, receptor, ligand],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    communicateRes = pydock_start_process.communicate()
    stdout, stderr = communicateRes

    if debug:
        print('initial web scraper stdout: {} \n initial web scraper stderr: {}'.format(stdout, stderr))

    if ' line ' not in str(stderr) and 'job submitted' in str(stdout):
        return True
    else:
        if debug:
            print('Error in run_pydock_start: {}'.format(stderr))
        return False

def read_pydock_mail(receptor, ligand):
    read_pydock_process = subprocess.Popen(['python', PYDOCK_READ_MAIL_FILE, PYDOCK_FROM_EMAIL, \
                                                receptor, ligand], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    communicateRes = read_pydock_process.communicate()
    stdout, stderr = communicateRes

    if debug:
        print('read mail stdout: {}'.format(stdout))
        print('read mail stderr: {}'.format(stderr))

    # re source: https://stackoverflow.com/questions/9760588/how-do-you-extract-a-url-from-a-string-using-python
    link = re.search("(?P<url>https?://[^\s]+)", str(stdout)).group("url").split('\\r')[0]
    # strip extra chars
    link = link.strip("\\n'")
    if debug:
        print('link: {}'.format(link))
    return link

def get_pydock_results(link, receptor, ligand):
    get_pydock_process = subprocess.Popen(
        ['python', PYDOCK_GET_RESULTS_FILE, link, receptor ,ligand],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    communicateRes = get_pydock_process.communicate()
    stdout, stderr = communicateRes

    if debug:
        print('stdout: {}'.format(str(stdout)))

    results = re.findall(r'[-]?[0-9]+[.]?[0-9]*', str(stdout))

    return [float(r) for r in results]

def run_patch_dock_start(receptor, ligand):
    patch_dock_start_process = subprocess.Popen(
            ['scrapy', 'runspider', PATCH_DOCK_START_FILE, '-a', 'receptor='+receptor, '-a', 'ligand='+ligand],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    communicateRes = patch_dock_start_process.communicate()
    stdout, stderr = communicateRes

    if debug:
        print('initial web scraper stdout: {} \n initial web scraper stderr: {}'.format(stdout, stderr))

    if ' line ' not in str(stderr):
        return True
    else:
        if debug:
            print('Error in run_patch_dock_start: {}'.format(stderr))
        return False

def read_patch_dock_mail(receptor, ligand):
    read_patch_dock_process = subprocess.Popen(['python', PATCH_DOCK_READ_MAIL_FILE, PATCH_DOCK_FROM_EMAIL, \
                                                receptor, ligand], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    communicateRes = read_patch_dock_process.communicate()
    stdout, stderr = communicateRes

    if debug:
        print('read mail stdout: {}'.format(stdout))
        print('read mail stderr: {}'.format(stderr))

    # re source: https://stackoverflow.com/questions/9760588/how-do-you-extract-a-url-from-a-string-using-python
    link = re.search("(?P<url>https?://[^\s]+)", str(stdout)).group("url").split('\\r')[0]
    # strip extra chars
    link = link.strip("\\n'")
    if debug:
        print('link: {}'.format(link))
    return link

def get_patch_dock_results(link):
    get_patch_dock_process = subprocess.Popen(
        ['scrapy', 'runspider', PATCH_DOCK_GET_RESULTS_FILE, '-a', 'link='+link],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    communicateRes = get_patch_dock_process.communicate()
    stdout, stderr = communicateRes

    if debug:
        print('stdout: {}'.format(str(stdout)))

    return [int(re.search(r'\d+', str(stdout)).group())]

def start_patch_dock_workflow(receptor_id, ligand_id, output):
    tool_id = 1
    new_results = False
    # check for stored results
    rec = receptor_id.split(':')[0]
    lig = ligand_id.split(':')[0]
    if results_exist(rec, lig, tool_id):
        patch_dock_score = get_results(rec, lig, tool_id)
    else:
        new_results = True
        # check mailbox for results first
        try:
            link = read_patch_dock_mail(receptor_id, ligand_id)
            received_patch_dock_msg = True
        except:
            # submit job to Patch Dock
            attempts = 0
            while not run_patch_dock_start(receptor_id, ligand_id) and attempts < 3:
                attempts += 1
            if attempts == 3:
                print('Error submitted Patch Dock job')
                sys.exit(1)
            else:
                print('Successfully submitted Patch Dock job')
            received_patch_dock_msg = False
        # get response from Patch Dock
        first_itr = True
        while (not received_patch_dock_msg):
            if first_itr:
                print('Patch Dock: Waiting 30 minutes...')
                time.sleep(1800)  # 30 minute wait
                first_itr = False
            else:
                print('Patch Dock: Waiting 5 minutes...')
                time.sleep(300)

            try:
                link = read_patch_dock_mail(receptor_id, ligand_id)
                received_patch_dock_msg = True
            except:
                print('No response from Patch Dock.')

        patch_dock_score = get_patch_dock_results(link)
        if new_results:
            insert_results(rec, lig, tool_id, patch_dock_score)

    print('Patch Dock Score for receptor: {} and ligand: {} is {}'.format(receptor_id, ligand_id, patch_dock_score))
    output.put((PROCESS_NAME_PATCH_DOCK, receptor_id, ligand_id, patch_dock_score))

def run_swarm_dock_start(receptor, ligand):
    swarm_dock_start_process = subprocess.Popen(
        ['python', SWARM_DOCK_START_FILE, receptor, ligand],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    communicateRes = swarm_dock_start_process.communicate()
    stdout, stderr = communicateRes

    if debug:
        print('swarm dock start stdout: {} \n swarm dock start stderr: {}'.format(stdout, stderr))

    if 'ID:' in str(stdout):
        return True
    else:
        if debug:
            print('Error in run_swarm_dock_start: {}'.format(stderr))
        return False

def download_pdb(pdb_id):
    swarm_dock_start_process = subprocess.Popen(
        ['python', DOWNLOAD_PDB_FILE, pdb_id],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    communicateRes = swarm_dock_start_process.communicate()
    stdout, stderr = communicateRes

    if debug:
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

    if debug:
        print('read mail stdout: {}'.format(stdout))
        print('read mail stderr: {}'.format(stderr))

    # re source: https://stackoverflow.com/questions/9760588/how-do-you-extract-a-url-from-a-string-using-python
    link = re.search("(?P<url>https?://[^\s]+)", str(stdout)).group("url").split('\\r')[0]
    # strip extra chars
    link = link.strip("\\n'")
    if debug:
        print('link: {}'.format(link))
    return link

def get_swarm_dock_results(link, receptor, ligand):
    get_swarm_dock_process = subprocess.Popen(
        ['python', SWARM_DOCK_GET_RESULTS_FILE, link, receptor, ligand],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    communicateRes = get_swarm_dock_process.communicate()
    stdout, stderr = communicateRes

    if debug:
        print('stdout: {}'.format(str(stdout)))

    results = re.findall(r'[-]?[0-9]+[.]?[0-9]*', str(stdout))

    return results

def start_swarm_dock_workflow(receptor_id, ligand_id, output):
    tool_id = 3
    new_results = False
    # check if results are stored
    rec = receptor_id.split(':')[0]
    lig = ligand_id.split(':')[0]
    if results_exist(rec, lig, tool_id):
        swarm_dock_score = get_results(rec, lig, tool_id)
    else:
        received_swarm_dock_msg = False
        new_results = True
        # check mailbox for results first
        try:
            link = read_swarm_dock_mail(receptor_id, ligand_id)
            received_swarm_dock_msg = True
        except:
            # submit job to Patch Dock
            attempts = 0
            while not run_swarm_dock_start(receptor_id, ligand_id) and attempts < 3:
                attempts += 1

            if attempts == 3:
                print('Error submitting Swarm Dock job')
                sys.exit(1)
            else:
                print('Successfully submitted Swarm Dock job')

        # get response from Swarm Dock
        first_itr = True
        while (not received_swarm_dock_msg):
            if first_itr:
                print('Swarm Dock: Waiting 30 minutes...')
                time.sleep(1800)  # 30 minute wait
                first_itr = False
            else:
                print('Swarm Dock: Waiting 10 minutes...')
                time.sleep(300)

            try:
                link = read_swarm_dock_mail(receptor_id, ligand_id)
                received_swarm_dock_msg = True
            except:
                print('No response from Swarm Dock.')

        swarm_dock_score = get_swarm_dock_results(link, receptor_id, ligand_id)
        if new_results:
            insert_results(rec, lig, tool_id, swarm_dock_score)

    print('Swarm Dock Score for receptor: {} and ligand: {} is {}'.format(receptor_id, ligand_id, swarm_dock_score))
    output.put((PROCESS_NAME_SWARM_DOCK, receptor_id, ligand_id, swarm_dock_score))

def insert_results(rec, lig, tool, output):
    # very output
    expected_results = get_expected_results(tool)
    if len(output) != expected_results:
        raise Exception('Insert Results: Invalid output dimension for tool: {}\nrec: {} lig: {} output: {}'.format(tool, rec, lig, output))
    # create connection to db
    conn = sqlite3.connect('{}/{}'.format(DB_DIR, DB_FILENAME))
    # get db cursor
    cursor = conn.cursor()
    # build query
    query = 'SELECT max(feature_id) FROM Result WHERE rec_pdb_id=:rec AND lig_pdb_id=:lig AND tool_id=:tool'
    dictionary = { 'rec': rec, 'lig': lig, 'tool': tool }
    results = cursor.execute(query, dictionary).fetchone()
    feature_id = results[0]
    if feature_id is None:
        feature_id = 1
    else:
        feature_id += 1

    for score in output:
        query = 'INSERT INTO Result(\'rec_pdb_id\', \'lig_pdb_id\', \'feature_id\', \'feature_value\', \'tool_id\') VALUES ' \
            '(\'{}\', \'{}\', {}, {}, {})'.format(rec, lig, feature_id, score, tool)
        cursor.execute(query)

    conn.commit()
    conn.close()

def get_results(rec, lig, tool):
    # create connection to db
    conn = sqlite3.connect('{}/{}'.format(DB_DIR, DB_FILENAME))
    # get db cursor
    cursor = conn.cursor()
    expected_results = get_expected_results(tool)

    # get largest feature id
    query = 'SELECT max(feature_id) FROM Result WHERE rec_pdb_id=:rec AND lig_pdb_id=:lig AND tool_id=:tool'
    dictionary = {'rec': rec, 'lig': lig, 'tool': tool}
    results = cursor.execute(query, dictionary).fetchall()
    feature_id = results[0][0]
    if feature_id is None:
        conn.close()
        return None

    while feature_id >= 1:
        # build query
        query = 'SELECT feature_value FROM Result WHERE rec_pdb_id=:rec AND lig_pdb_id=:lig AND tool_id=:tool AND feature_id=:feature_id'
        dictionary = {'rec': rec, 'lig': lig, 'tool': tool, 'feature_id': feature_id}
        # get results
        results = cursor.execute(query, dictionary).fetchall()

        if len(results) == expected_results:
            conn.close()
            return [i[0] for i in results]
        else:
            feature_id -= 1

    conn.close()
    return None

def get_expected_results(tool):
    # set expected results
    if tool == 1 or tool == 4:
        expected_results = 1
    elif tool == 2:
        expected_results = 4
    elif tool == 3:
        expected_results = 7

    return expected_results

def results_exist(rec, lig, tool):
    # create connection to db
    conn = sqlite3.connect('{}/{}'.format(DB_DIR, DB_FILENAME))
    # get db cursor
    cursor = conn.cursor()
    # build query
    query = 'SELECT * FROM Result WHERE rec_pdb_id=:rec AND lig_pdb_id=:lig AND tool_id=:tool'
    dictionary = { 'rec': rec, 'lig': lig, 'tool': tool}
    # get results
    results = cursor.execute(query, dictionary).fetchall()

    # set expected results
    expected_results = get_expected_results(tool)

    if len(results) >= expected_results:
        return True
    else:
        return False

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
    file_path = SWARM_DOCK_DIR + '/pdb/' + filename
    # verify file exists
    if not os.path.isfile(file_path):
        # download if file does not exist
        download_pdb(pdb_id)
    f_stat = os.stat(file_path)
    date = datetime.fromtimestamp(f_stat.st_birthtime).date()
    insert_sql = 'INSERT INTO Protein VALUES (?, ?, ?, ?, ?)'

    if debug:
        print('insert_sql: {}'.format(insert_sql))

    cursor.execute(insert_sql, (pdb_entry_id, pdb_id, chain, filename, date))

def build_scores_for_classifier(patch_dock_results, swarm_dock_results, pydock_results):
    if not len(patch_dock_results) == len(swarm_dock_results) == len(pydock_results):
        raise Exception('Improperly formatted results:\nNum patch dock results: {}\n Num swarm dock results: {}'
                        '\n Num pydock results: {}'.format(len(patch_dock_results), len(swarm_dock_results), len(pydock_results)))

    results = []
    rec_lig_pairs = []
    for i in range(len(patch_dock_results)):
        rec = patch_dock_results[i][1]
        lig = patch_dock_results[i][2]
        rec_lig_pairs.append([rec, lig])
        # assert we are building a score using the same inputs
        assert swarm_dock_results[i][1] == rec, 'Swarm Dock receptor: {} does not match Patch Dock recptor: {}'.format(
                    swarm_dock_results[i][1], rec)
        assert swarm_dock_results[i][2] == lig, 'Swarm Dock ligand: {} does not match Patch Dock ligand: {}'.format(
            swarm_dock_results[i][2], lig)
        assert pydock_results[i][1] == rec, 'pyDock receptor: {} does not match Patch Dock recptor: {}'.format(
            pydock_results[i][1], rec)
        assert pydock_results[i][2] == lig, 'pyDock ligand: {} does not match Patch Dock ligand: {}'.format(
            pydock_results[i][2], lig)
        # get scores
        patch_dock_score = patch_dock_results[i][3]
        swarm_dock_score = swarm_dock_results[i][3]
        pydock_score = pydock_results[i][3]
        results.append(patch_dock_score + swarm_dock_score + pydock_score)

    return results, rec_lig_pairs

def get_workflow_results_from_queue(queue, num_results):
    patch_dock_results = []
    swarm_dock_results = []
    pydock_results = []
    for i in range(num_results):
        r = queue.get()
        if r[0] == PROCESS_NAME_PATCH_DOCK:
            patch_dock_results.append(r)
        elif r[0] == PROCESS_NAME_SWARM_DOCK:
            swarm_dock_results.append(r)
        elif r[0] == PROCESS_NAME_PYDOCK:
            pydock_results.append(r)
        else:
            raise Exception('Improperly formatted output result: {}'.format(r))

    return (patch_dock_results, swarm_dock_results, pydock_results)


output = mp.Queue()

try:
    with open(sys.argv[1], 'r') as input_file:
        rec_lig_pairs = []
        for line in input_file:
            # remove new line character
            line = line.strip('\n')
            rec_lig_pairs.append(line.split(' '))
except:
    print('Usage: workflow_manager.py <input_file>')
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
    insert_pdb(rec, rec_chain, cursor)
    insert_pdb(lig, lig_chain, cursor)

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
            if debug:
                print('start: processes_executed {} i: {}'.format(processes_executed, i))
            patch_dock_processes[processes_executed + i].start()
            swarm_dock_processes[processes_executed + i].start()
            pydock_processes[processes_executed + i].start()
        for i in range(num_processes_to_start):
            if debug:
                print('join: processes_executed {} i: {}'.format(processes_executed, i))
            patch_dock_processes[processes_executed + i].join()
            swarm_dock_processes[processes_executed + i].join()
            pydock_processes[processes_executed + i].join()
        processes_executed += num_processes_to_start
    else:
        for i in range(MAX_NUM_WORKFLOW_PROCESSES):
            if debug:
                print('start: processes_executed {} i: {}'.format(processes_executed, i))
            patch_dock_processes[processes_executed + i].start()
            swarm_dock_processes[processes_executed + i].start()
            pydock_processes[processes_executed + i].start()
        for i in range(MAX_NUM_WORKFLOW_PROCESSES):
            if debug:
                print('join: processes_executed {} i: {}'.format(processes_executed, i))
            patch_dock_processes[processes_executed + i].join()
            swarm_dock_processes[processes_executed + i].join()
            pydock_processes[processes_executed + i].join()
        processes_executed += MAX_NUM_WORKFLOW_PROCESSES

patch_dock_results, swarm_dock_results, pydock_results = get_workflow_results_from_queue(output,
                                                                len(patch_dock_processes) + len(swarm_dock_processes) +
                                                                len(pydock_processes))

#write_output(patch_dock_results + swarm_dock_results + pydock_results)
classifier_input_data, rec_lig_pairs = build_scores_for_classifier(patch_dock_results, swarm_dock_results, pydock_results)

# create classifier
classifier = knn_classifier.KNN_Classifier(5)

classification_results = classifier.classify_data(classifier_input_data, len(classifier_input_data))

for i in range(len(classification_results)):
    if classification_results[i] == 1:
        out_stmt_modifier = ''
    else:
        out_stmt_modifier = 'not '

    print('Receptor {} and Ligand {} do {}dock.'.format(rec_lig_pairs[i][0], rec_lig_pairs[i][1], out_stmt_modifier))

if debug:
    print('Patch Dock Results: {}'.format(patch_dock_results))
    print('Swarm Dock Results: {}'.format(swarm_dock_results))
    print('PyDock Results: {}'.format(pydock_results))
    print('Concatenated Results: {}'.format(patch_dock_results + swarm_dock_results + pydock_results))
    print('Classifier input data: {}'.format(classifier_input_data))
    print('Classification results: {}'.format(classification_results))