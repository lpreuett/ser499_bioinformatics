import urllib, sys, re, os, tarfile

OUTPUT_DIR = './pyDockWEB/output'

if len(sys.argv) != 2:
    print('Usage: <pyDock results link>')
    sys.exit(1)

# get download_link
results_link = sys.argv[1]

with urllib.request.urlopen(results_link) as response:
    for line in response:
        line = line.decode('utf-8')
        if re.search('\(\d{4}\)', line) != None:
            project_num = re.search('\(\d{4}\)', line)
            break
        print(line)
    print(project_num[0][1:5])



'''
# build download_link to results download
download_link_split = download_link.split('/')
download_link_split[6] = download_link_split[5] + '.tar.gz'
download_link = "/".join(download_link_split)
'''