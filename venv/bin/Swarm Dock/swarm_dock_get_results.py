import urllib, sys, os, tarfile

debug = False

OUTPUT_DIR = './Swarm Dock/output'
RESULTS_FILENAME = 'sds/clusters_standard.txt'

if len(sys.argv) != 4:
    print('Usage: swarm_dock_get_results.py <link_to_results> <receptor pdb id> <ligand pdb id>')
    sys.exit(1)

# get download_link
download_link = sys.argv[1]
# build download_link to results download
download_link_split = download_link.split('/')
download_link_split[6] = download_link_split[5] + '.tar.gz'
download_link = "/".join(download_link_split)

# store receptor
rec = sys.argv[2]
if ':' in rec:
    rec = rec.split(':')[0]

rec = rec.upper()

# store ligand
lig = sys.argv[3]
if ':' in lig:
    lig = lig.split(':')[0]

lig = lig.upper()

if debug:
    print('download_link: {}'.format(download_link))

urlOpener = urllib.request.URLopener()

# test for existence of pdb dir
if not os.path.isdir(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

# name file
out_file_name = rec + '_' + lig + '.tar.gz'

# check for file existence
if not os.path.isfile(OUTPUT_DIR + '/' + out_file_name):
    # download file
    urlOpener.retrieve(download_link, OUTPUT_DIR + '/' + out_file_name)

# extract .tar.gz
tar = tarfile.open(OUTPUT_DIR + '/' + out_file_name)
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
    members = decoded_line[members_start+1:members_finish].split('|')
    if len(members) <= 3:
        results = decoded_line.split(' ')
        results = results[1:3] + results[4:]
        results = ' '.join(results)
        break

print('results: {}'.format(results))