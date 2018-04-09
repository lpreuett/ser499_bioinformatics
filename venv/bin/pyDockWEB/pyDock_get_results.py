import urllib, sys, re, os, tarfile, re

OUTPUT_DIR = './pyDockWEB/output'
CWD = '/Users/larry/PycharmProjects/SER499_web_scraper/venv/bin'

debug = False

if len(sys.argv) != 4:
    print('Usage: <pyDock results link> <receptor PDBID> <ligand PDBID>')
    sys.exit(1)

# get download_link
results_link = sys.argv[1]
# get receptor pdb id
rec = sys.argv[2].split(':')[0].upper()
# get ligand pdb id
lig = sys.argv[3].split(':')[0].upper()

# verify current working directory
if os.getcwd() != CWD:
    os.chdir(CWD)

# check for existence of output directories
if not os.path.isdir(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

outfile_name = rec + '_' + lig +'.tar.gz'

# check for file existence
if not os.path.isfile(OUTPUT_DIR + '/' + outfile_name):
    # url opener
    urlOpener = urllib.request.URLopener()

    with urllib.request.urlopen(results_link) as response:
        for line in response:
            line = line.decode('utf-8')
            if re.search('\(\d{4}\)', line) != None:
                project_num = re.search('\(\d{4}\)', line)[0][1:5]
                break
    # build download_link to results download
    # https://life.bsc.es/pid/archive/pydockweb/2018-03-27_23:22:04_YTAQPZG3UI4GBTGT/project7753.tgz
    download_link_split = results_link.split('/')
    download_link_split.insert(4, 'archive')
    download_link_split.append('project' + project_num + '.tgz')
    download_link_split = download_link_split[0:6] + download_link_split[8:]
    download_link = '/'.join(download_link_split)

    if debug:
        print('Download link: {}'.format(download_link))
    # download file
    urllib.request.urlretrieve(download_link, OUTPUT_DIR + '/' + outfile_name)

# extract .tar.gz
tar = tarfile.open(OUTPUT_DIR + '/' + outfile_name)
# build results file name
tar_members = tar.getmembers()
for m in tar_members:
    if re.search('\w+\.ene', m.name):
        RESULTS_FILE = m.name
results_file = tar.extractfile(RESULTS_FILE)

line_num = 0
for line in results_file:
    if line_num == 2:
        # top result
        decoded_line = line.decode('utf-8')
        outputs = re.findall('(-?\d+\.\d+)', decoded_line)
        results = ' '.join(outputs)
        break

    line_num += 1

print('results: {}'.format(results))