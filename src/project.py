from github3 import GitHub
import gh_search_utils
import requests
import pathlib
import itertools
import logging
import os
import re #regex

import project_utils


# TODO Skip invalid Jenkinsfiles (i.e. empty, imbalanced brackets, starts with pipeline or node)+


# TODO Update the following to paths for your system
CLONED_REPOS_DIR_PATH = 'C:/Users/Viren/Google Drive/1.UIC/540/guillermo_rojas_hernandez_viren_mody_courseproject/ClonedRepos/'
# CLONED_REPOS_DIR_PATH = '/home/guillermo/cs540/guillermo_rojas_hernandez_viren_mody_courseproject/ClonedRepos/'

GITHUB_USERNAME = 'virenmody'
GITHUB_ACCESS_TOKEN = 'feec9be9b75ded7680e74e1be28b47c50564c2ac'

# Retrieve logger to be used for both project.py and project_utils.py
logger = logging.getLogger('project')
""" Use this to appropriately categorize log types when logging
LOGGING LEVELS
DEBUG	Detailed information, typically of interest only when diagnosing problems.
INFO	Confirmation that things are working as expected.
WARNING	An indication that something unexpected happened, or indicative of some problem in the near future (e.g. ‘disk space low’). The software is still working as expected.
ERROR	Due to a more serious problem, the software has not been able to perform some function.
CRITICAL	A serious error, indicating that the program itself may be unable to continue running.
"""


def configure_logger():
    """
    Function configures logger level, format, and output stream
    """
    LOG_FILENAME = 'project.log'
    logger.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(levelname)s:%(filename)s: In %(funcName)s(): On Line: %(lineno)d: %(message)s')

    file_handler = logging.FileHandler(LOG_FILENAME)
    stream_handler = logging.StreamHandler()
    file_handler.setFormatter(formatter)
    stream_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)


# TODO Error/exception handling (i.e. empty Jenkinsfile, empty triggers or stages)
# TODO Only include declarative pipelines?
def parse_triggers_and_stages(jenkinsfile):
    """
    Function parses jenkinsfile for trigger and stage counts and info
    :param jenkinsfile: path to Jenkinsfile to parse
    :return: list of triggers, list of stages and number of triggers and stages
    """
    triggers = ['cron', 'pollSCM', 'upstream']
    triggers_found = []
    trigger_type = ''
    num_triggers = 0

    stages_found = []
    stage_name = ''
    num_stages = 0

    with open(jenkinsfile) as file:
        for line in file:
            line = line.strip('\n')
            if any(trig in line for trig in triggers):
                num_triggers += 1

                if 'cron' in line:
                    trigger_type = 'cron'
                elif 'pollSCM' in line:
                    trigger_type = 'pollSCM'
                elif 'upstream' in line:
                    trigger_type = 'upstream'

                # Retrieve trigger value from between parentheses and single quotes
                re_triggers_pattern = r"[A-Za-z]*\(\'*\"*(.+?)\'*\"*\)"
                trigger_value = re.search(re_triggers_pattern, line).group(1)
                logger.debug('LINE: %s', line)
                logger.debug('ADDING TRIGGER:  %s = %s', trigger_type, trigger_value)
                triggers_found.append({'Type': trigger_type, 'Value': trigger_value, 'Occurrence': num_triggers})

            if 'stage' in line and 'stages' not in line:
                num_stages += 1
                re_stages_pattern = r"stage\s*\(*\s*\'*\"*([A-Za-z]*)\'*\"*\s*\)*"
                stage_name = re.search(re_stages_pattern, line).group(1)
                logger.debug('LINE: %s', line)
                logger.debug('ADDING STAGE:  %s, Occurrence: %s', stage_name, num_stages)
                stages_found.append({'Name': stage_name, 'Occurrence': num_stages})

    logger.debug('TRIGGERS: %s', triggers_found)
    logger.debug('STAGES: %s', stages_found)
    return triggers_found, stages_found, num_stages, num_triggers


def analyze_research_question1():
    """
    Function downloads Jenkinsfiles, parses it, and analyzes the data to answer:
    Research Question #1: How does the number of triggers in a pipeline correlate with the number of stages in the pipeline?
    :return:
    """

    logger.info('Analyzing for Research Question 1: How does the number of triggers in a pipeline correlate with the number of stages in the pipeline?')
    # TODO Add code here to download Jenkinsfiles containing keyword 'triggers'
    username = 'testuser'
    repo_name = 'testrepo'
    jenkinsfile_path = CLONED_REPOS_DIR_PATH + username + repo_name + '/Jenkinsfile'

    #  Confirm Jenkinsfile does exist TODO error/exception handling...skip the file
    logger.info('%s exists? %s', jenkinsfile_path, os.path.isfile(jenkinsfile_path))

    # Parse triggers and stages from file
    triggers_data, stages_data, num_stages, num_triggers = parse_triggers_and_stages(jenkinsfile_path)

    combined_data = list(itertools.zip_longest(triggers_data, stages_data))
    df_headers = ['Username', 'RepositoryName', 'TriggerType', 'TriggerValue', 'TriggerOccurrence', 'StageName', 'StageOccurrence']
    df = project_utils.create_df(df_headers)
    for iteration, data in enumerate(combined_data):
        trigger, stage = data
        trigger_type = ''
        trigger_value = ''
        trigger_occurrence = ''
        stage_name = ''
        stage_occurrence = 0
        if trigger is not None:
            trigger_type = trigger['Type']
            trigger_value = trigger['Value']
            trigger_occurrence = trigger['Occurrence']
        if stage is not None:
            stage_name = stage['Name']
            stage_occurrence = stage['Occurrence']

        new_row = [[username, repo_name, trigger_type, trigger_value, trigger_occurrence, stage_name, stage_occurrence]]
        df = project_utils.add_row_to_df(df, df_headers, new_row)

        if iteration == 0:
            username = ''
            repo_name = ''

    print(df)

    # df_headers_triggers = ['Username', 'RepositoryName', 'TriggerType', 'TriggerValue', 'NumStages']
    # df_triggers = project_utils.create_df(df_headers_triggers)
    # df_headers_stages = ['Username', 'RepositoryName', 'StageName', 'Occurrence', 'NumStages']
    # df_stages = project_utils.create_df(df_headers_stages)
    # for trigger in triggers_data:
    #     new_row = [[username, repo_name, trigger['Type'], trigger['Value'], num_stages]]
    #     df_triggers = project_utils.add_row_to_df(df_triggers, df_headers_triggers, new_row)
    # for stage in stages_data:
    #     new_row = [[username, repo_name, stage['Name'], stage['Occurrence'], num_stages]]
    #     df_stages = project_utils.add_row_to_df(df_stages, df_headers_stages, new_row)
    #
    # print(df_triggers)
    # print(df_stages)


def main():
    configure_logger()

    logger.info('GITHUB_USERNAME: %s', GITHUB_USERNAME)
    logger.info('GITHUB_ACCESS_TOKEN: %s', GITHUB_ACCESS_TOKEN)
    logger.info('LOCAL_CLONED_REPO_PATH: %s', CLONED_REPOS_DIR_PATH)

    # Authenticate GitHub object
    git_hub = GitHub(GITHUB_USERNAME, GITHUB_ACCESS_TOKEN)

    # Create Query and Search GitHub
    query = "filename:jenkinsfile q=pipeline triggers stages"
    num_results = 2

    # Results are returned in tuples: ((github_object, raw_url))
    results = project_utils.search_by_code(git_hub, query, num_results)
    logger.info("Results from hw3_utils.search_by_code: %s", results)

    # Get file contents of all results (raw url is second item in tuple: results[i][1])
    for i in range(0, len(results)):
        res = requests.get(results[i][1])
        # print text of result
        logger.debug(res.text)
        # print the whole folder name
        logger.debug(results[i][2])
        github_repo_name = results[i][2]
        path_to_file = CLONED_REPOS_DIR_PATH + github_repo_name
        pathlib.Path(path_to_file).mkdir(parents=True, exist_ok=True)

        jenkinsfile_path = path_to_file + '/' + 'Jenkinsfile'
        with open(jenkinsfile_path, "wb") as file:
            file.write(res.content)

    # Research Question #1
    analyze_research_question1()

if __name__ == '__main__':
    main()
