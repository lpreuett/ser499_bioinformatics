import urllib, sys, os

PDB_DIR = './Swarm Dock/pdb'
PDB_FILE_EXT = '.pdb'
PDB_DOWNLOAD_ADDRESS = 'https://files.rcsb.org/download/'

if len(sys.argv) != 2:
    print('Usage: download_pdb.py <pdb_id>')
    sys.exit(1)

pdb_chain = sys.argv[1]

if ':' in pdb_chain:
    pdb_id = pdb_chain.split(':')[0]
else:
    pdb_id = pdb_chain

pdb_id = pdb_id.upper() + PDB_FILE_EXT

urlOpener = urllib.request.URLopener()

# test for existence of pdb dir
if not os.path.isdir(PDB_DIR):
    os.makedirs(PDB_DIR)

if not os.path.isfile(PDB_DIR + '/' + pdb_id):
    urlOpener.retrieve(PDB_DOWNLOAD_ADDRESS + pdb_id, PDB_DIR + '/' + pdb_id)
