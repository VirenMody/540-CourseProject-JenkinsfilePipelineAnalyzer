import logging
import os
import re
import project_utils

# TODO Update the following to paths for your system
CLONED_REPOS_DIR_PATH = 'C:/Users/Viren/Google Drive/1.UIC/540/guillermo_rojas_hernandez_viren_mody_courseproject/ClonedRepos/'
# CLONED_REPOS_DIR_PATH = '/home/guillermo/cs540/cloned_repos/'


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


# TODO Add function description
# TODO Error/exception handling (i.e. empty Jenkinsfile, empty triggers or stages)
# TODO Only include declarative pipelines?
def parse_triggers_and_stages(jenkinsfile):
    triggers = ['cron', 'pollSCM', 'upstream']
    triggers_found = []
    trigger_type = ''

    stages_found = []
    stage_name = ''
    num_stages = 0

    with open(jenkinsfile) as file:
        for line in file:
            line = line.strip('\n')
            if any(trig in line for trig in triggers):
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
                triggers_found.append({'Type': trigger_type, 'Value': trigger_value})

            if 'stage' in line and 'stages' not in line:
                num_stages += 1
                re_stages_pattern = r"stage\s*\(*\s*\'*\"*([A-Za-z]*)\'*\"*\s*\)*"
                stage_name = re.search(re_stages_pattern, line).group(1)
                logger.debug('LINE: %s', line)
                logger.debug('ADDING STAGE:  %s, Occurrence: %s', stage_name, num_stages)
                stages_found.append({'Name': stage_name, 'Occurrence': num_stages})

    logger.debug('TRIGGERS: %s', triggers_found)
    logger.debug('STAGES: %s', stages_found)
    return triggers_found, stages_found, num_stages


def main():
    configure_logger()

    # TODO Wrap each research question into a separate function??
    # Research Question #1
    logger.info('Analyzing for Research Question 1: How does the presence of triggers in a pipeline correlate with the number of stages in the pipeline?')
    # TODO Add code here to download Jenkinsfiles containing keyword 'triggers'
    username = 'testuser'
    repo_name = 'testrepo'
    jenkinsfile_path = CLONED_REPOS_DIR_PATH + username + repo_name + '/Jenkinsfile'

    #  Confirm Jenkinsfile does exist TODO error/exception handling...skip the file
    logger.info('%s exists? %s', jenkinsfile_path, os.path.isfile(jenkinsfile_path))

    # Parse triggers and stages from file
    triggers_data, stages_data, num_stages = parse_triggers_and_stages(jenkinsfile_path)

    df_headers_triggers = ['Username', 'RepositoryName', 'TriggerType', 'TriggerValue', 'NumStages']
    df_triggers = project_utils.create_df(df_headers_triggers)
    df_headers_stages = ['Username', 'RepositoryName', 'StageName', 'Occurrence', 'NumStages']
    df_stages = project_utils.create_df(df_headers_stages)
    for trigger in triggers_data:
        new_row = [[username, repo_name, trigger['Type'], trigger['Value'], num_stages]]
        df_triggers = project_utils.add_row_to_df(df_triggers, df_headers_triggers, new_row)
    for stage in stages_data:
        new_row = [[username, repo_name, stage['Name'], stage['Occurrence'], num_stages]]
        df_stages = project_utils.add_row_to_df(df_stages, df_headers_stages, new_row)

    print(df_triggers)
    print(df_stages)

if __name__ == '__main__':
    main()
