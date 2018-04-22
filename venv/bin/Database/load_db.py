import os, sqlite3, tarfile, re
from datetime import datetime

PATCH_DOCK_DIR = '../Patch Dock/'
PYDOCK_DIR = '../PyDockWEB/'
SWARM_DOCK_DIR = '../Swarm Dock/'

SWARM_DOCK_NAME = 'Swarm Dock'
PYDOCK_NAME = 'pyDockWEB'
PATCH_DOCK_NAME = 'Patch Dock'
MOTHER_NATURE_NAME = 'Mother Nature'

GOOD_PAIRS_FILE = '../good_pairs.txt'
BAD_PAIRS_FILE = '../bad_pairs.txt'

PROTEIN_IDENTIFIER = 'protein'
RESULT_IDENTIFIER = 'result'

debug = True

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
    pdb_entry_id = cursor.execute('SELECT max(id) FROM Protein').fetchone()[0]
    if pdb_entry_id == None:
        pdb_entry_id = 1
    else:
        pdb_entry_id += 1
    # test for existence of pdb_id and chain pair
    if does_pdb_chain_exist(pdb_id, chain, cursor):
        return
    filename = pdb_id.upper() + '.pdb'
    file_path = SWARM_DOCK_DIR + 'pdb/' + filename
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

def parse_pair_file(filepath, table):
    if filepath == GOOD_PAIRS_FILE:
        does_dock = True
    else:
        does_dock = False
    # connect to db
    conn = sqlite3.connect('./workflow.db')
    cursor = conn.cursor()
    with open(filepath, 'r') as input_file:
        for line in input_file:
            # remove new line character
            line_split = line.strip('\n').split(' ')
            # get pdb id and chain for receptor
            receptor = line_split[0].split(':')
            receptor_pdb_id = receptor[0]
            if len(receptor) == 2:
                receptor_chain = receptor[1]
            else:
                receptor_chain = None
            # get pdb id and chain for ligand
            ligand = line_split[1].split(':')
            ligand_pdb_id = ligand[0]
            if len(ligand) == 2:
                ligand_chain = ligand[1]
            else:
                ligand_chain = None
            # insert data
            if table == PROTEIN_IDENTIFIER:
                insert_pdb(receptor_pdb_id, receptor_chain, cursor)
                insert_pdb(ligand_pdb_id, ligand_chain, cursor)
            elif table == RESULT_IDENTIFIER:
                insert_result(receptor_pdb_id, ligand_pdb_id, does_dock, cursor)
    # save and close connection
    conn.commit()
    conn.close()

def does_result_exist(receptor_pdb_id, ligand_pdb_id, tool_name, cursor):
    # expected length of results for each tool
    if tool_name == PATCH_DOCK_NAME:
        num_results = 1
    elif tool_name == SWARM_DOCK_NAME:
        num_results = 7
    elif tool_name == PYDOCK_NAME:
        num_results = 4
    elif tool_name == MOTHER_NATURE_NAME:
        num_results = 1
    # get tool id
    tool_id = cursor.execute('SELECT id FROM Tool WHERE name=:tool_name', {'tool_name': tool_name}).fetchone()[0]
    # get all the results
    results = cursor.execute('SELECT feature_id FROM Result WHERE rec_pdb_id=:receptor AND lig_pdb_id=:ligand '\
                             'AND tool_id=:tool AND feature_id=:feature',{ 'receptor' : receptor_pdb_id,
                                                                          'ligand' : ligand_pdb_id,
                                                                          'tool' : tool_id,
                                                                          'feature' : 1 }).fetchall()
    # test length of results
    if len(results) >= num_results: # include greater than in case multiple results have been stored
        return True
    else:
        return False

def insert_result(receptor, ligand, does_dock, cursor):
    result_entry_id = cursor.execute('SELECT max(id) FROM Result').fetchone()[0]
    if result_entry_id == None:
        result_entry_id = 1
    else:
        result_entry_id += 1

    feature_id = 1
    # build filename
    filename = '{}_{}.txt'.format(receptor.upper(), ligand.upper())
    # insert patch dock data
    if os.path.isfile(PATCH_DOCK_DIR+'/output/'+filename) \
            and not does_result_exist(receptor, ligand, PATCH_DOCK_NAME, cursor):
        # get score
        patch_dock_score = get_patch_dock_results_from_file(filename)
        # get tool id
        tool_id = cursor.execute('SELECT id FROM Tool WHERE name=:tool_name', {'tool_name': PATCH_DOCK_NAME}).fetchone()[0]
        # insert score
        insert_sql = 'INSERT INTO Result VALUES ' + "({}, \'{}\', \'{}\', {}, {}, {})".format(result_entry_id,
                                                                                              receptor, ligand,
                                                                                              feature_id,
                                                                                              patch_dock_score,
                                                                                              tool_id)
        cursor.execute(insert_sql)
        result_entry_id += 1

    # build filename
    filename = '{}_{}.tar.gz'.format(receptor.upper(), ligand.upper())
    # insert swarm dock data
    if os.path.isfile(SWARM_DOCK_DIR+'/output/'+filename) \
        and not does_result_exist(receptor, ligand, SWARM_DOCK_NAME, cursor):
        swarm_dock_scores = get_swarm_dock_results_from_file(filename)
        # get tool id
        tool_id = cursor.execute('SELECT id FROM Tool WHERE name=:tool_name', {'tool_name': SWARM_DOCK_NAME}).fetchone()[0]
        # insert score
        for score in swarm_dock_scores:
            insert_sql = 'INSERT INTO Result VALUES ' + "({}, \'{}\', \'{}\', {}, {}, {})".format(result_entry_id,
                                                                                                  receptor, ligand,
                                                                                                  feature_id,
                                                                                                  score,
                                                                                                  tool_id)
            cursor.execute(insert_sql)
            result_entry_id += 1

    # insert pydock data
    if os.path.isfile(PYDOCK_DIR+'/output/'+filename) \
            and not does_result_exist(receptor, ligand, PYDOCK_NAME, cursor):
        pydock_scores = get_pydock_results_from_file(filename)
        # get tool id
        tool_id = cursor.execute('SELECT id FROM Tool WHERE name=:tool_name', {'tool_name': PYDOCK_NAME}).fetchone()[0]
        # insert score
        for score in pydock_scores:
            insert_sql = 'INSERT INTO Result VALUES ' + "({}, \'{}\', \'{}\', {}, {}, {})".format(result_entry_id,
                                                                                                  receptor, ligand,
                                                                                                  feature_id,
                                                                                                  score,
                                                                                                  tool_id)
            cursor.execute(insert_sql)
            result_entry_id += 1

    if not does_result_exist(receptor, ligand, MOTHER_NATURE_NAME, cursor):
        if does_dock:
            mother_nature_score = 1
        else:
            mother_nature_score = 0
        feature_id = 1
        # get tool id
        tool_id = cursor.execute('SELECT id FROM Tool WHERE name=:tool_name', {'tool_name': MOTHER_NATURE_NAME}).fetchone()[0]
        # insert score
        insert_sql = 'INSERT INTO Result VALUES ' + "({}, \'{}\', \'{}\', {}, {}, {})".format(result_entry_id, receptor,
                                                                                          ligand, feature_id, mother_nature_score,
                                                                                          tool_id)
        cursor.execute(insert_sql)

def load_data(table):
    #try:
    parse_pair_file(GOOD_PAIRS_FILE, table)
    parse_pair_file(BAD_PAIRS_FILE, table)
    #except Exception as e:
    #    print('Error while loading database with {} file information:\n{}'.format(table, str(e)))

def get_swarm_dock_results_from_file(filename):
    RESULTS_FILENAME = 'sds/clusters_standard.txt'
    SWARM_DOCK_OUTPUT_DIR = SWARM_DOCK_DIR + '/output'
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
    return [float(i) for i in results.rstrip().split(' ')]

def get_patch_dock_results_from_file(filename):
    PATCH_DOCK_SCORES_DIR = PATCH_DOCK_DIR + '/output'
    with open(PATCH_DOCK_SCORES_DIR + '/' + filename, 'r') as file:
        line = file.readline()
    return line

def get_pydock_results_from_file(filename):
    PYDOCK_OUTPUT_DIR = PYDOCK_DIR + '/output'
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

    return [float(i) for i in results.rstrip().split(' ')]

load_data(RESULT_IDENTIFIER)