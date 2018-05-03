import urllib.request
from unidiff import PatchSet
import subprocess
import pandas as pd
from git import Repo, exc
import logging


def clone_repo(owner, name, directory, commit_type):
    """
    Function clones repository and returns local path to the repository
    :param owner: username
    :param name: repository name
    :param directory: where to clone repos
    :param commit_type: 'current' or 'parent' to distinguish pr commit and parent commit
    :return: local path to cloned repository
    """

    git_url = 'https://github.com/' + owner + '/' + name + '.git'
    # Path to locally cloned repo. commit_type distinguishes between pr commit and parent commit
    repo_dir = directory + owner + name + commit_type
    try:
        print('Cloning ' + owner + '/' + name + ' to repo directory: ' + repo_dir)
        cloned_repo = Repo.clone_from(git_url, repo_dir)
        assert cloned_repo.__class__ is Repo  # clone an existing repository
        return repo_dir

    # TODO Replace with logging
    except exc.GitError as err:
        print('***** CAUGHT ERROR: CODE: 128 ******\n', err)
        print('*************************************************************************************************************')
        print('Cloned repositories still exist from the last run.\nPlease delete Cloned Repository directory.\nThen run again.')
        print('*************************************************************************************************************\n\n')
        exit(128)

def search_by_code(git_hub, my_query, num):
    """
    :param git_hub: authenticated GitHub object
    :param my_query: search query (i.e. java, closed, etc.)
    :param num: number of results to retrieve
    :return: results: tuple with username, repo name, issue number, and the pull request object
    """
    try:
        code_search_result = git_hub.search_code(query=my_query, number=num)
    except Exception as err:
        logging.error("GitHub Connection Error ", exc_info=True)
        raise

    results = []
    for item in code_search_result:
        result_object = item

        try:
            result_url = item.html_url
        except AttributeError as err:
            logging.error("Attribute html_url not found in 'item' object: ", exc_info=True)
            raise

        # Get string with blob hash: ("ref=98234745")
        blob_hash_string = item._uri[4]

        # split string at = and save only the hash value
        blob_hash = blob_hash_string.split('=')[1]
        logging.debug("Github blob hash: %s", blob_hash)

        # create raw URL from repository details and blob hash
        raw_url = "https://raw.githubusercontent.com/" + item.repository.full_name + '/' + blob_hash + '/' + item.path
        logging.debug("raw_url: %s", raw_url)

        results.append((result_object, raw_url))

    return results


# Check if script is running as main
if __name__ == "__main__":
    logging.basicConfig(filename='hw3_utils.log', level=logging.DEBUG)
    logging.info('Beginning of log file')
    logging.info("Utils running as main")
