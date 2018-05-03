from github3 import GitHub
import urllib.request
import urllib3
import gh_search_utils
import requests
import logging


# Logging configuration
logging.basicConfig(filename='gh_search.log', level=logging.DEBUG)
logging.info('beginning of log file')

GITHUB_USERNAME = 'virenmody'
GITHUB_ACCESS_TOKEN = 'feec9be9b75ded7680e74e1be28b47c50564c2ac'

# TODO Update the following to paths where commits are downloaded
#LOCAL_CLONED_REPO_PATH = 'C:/Users/Viren/Google Drive/1.UIC/540/hw2/ClonedRepos/'
LOCAL_CLONED_REPO_PATH = '/home/guillermo/cs540/cloned_repos/'
#DB_PATH = 'C:/Users/Viren/Google Drive/1.UIC/540/hw2/guillermo_rojas_hernandez_viren_mody_hw2/src/'
DB_PATH = '/home/guillermo/cs540/guillermo_rojas_hernandez_viren_mody_courseproject/src/'

logging.info('GITHUB_USERNAME: %s', GITHUB_USERNAME)
logging.info('GITHUB_ACCESS_TOKEN: %s', GITHUB_ACCESS_TOKEN)
logging.info('LOCAL_CLONED_REPO_PATH: %s', LOCAL_CLONED_REPO_PATH)
logging.info('DB_PATH: %s', DB_PATH)

# Authenticate GitHub object
git_hub = GitHub(GITHUB_USERNAME, GITHUB_ACCESS_TOKEN)

# Create Query and Search GitHub
query = "filename:jenkinsfile q=node"
num_results = 10

# Results are returned in tuples: ((github_object, raw_url))
results = gh_search_utils.search_by_code(git_hub, query, num_results)
logging.info("Results from hw3_utils.search_by_code: %s", results)

# Get file contents of all results (raw url is second item in tuple: results[i][1])
for i in range(0, len(results)):
    res = requests.get(results[i][1])
    logging.debug(res.text)


