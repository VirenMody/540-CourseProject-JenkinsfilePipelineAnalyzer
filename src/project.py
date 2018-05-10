from github3 import GitHub
import requests
import pathlib
import itertools
import logging
import os
import re  # regex
import numpy
import csv

import project_utils

# TODO Artifacts Research Questions - Maybe correlation between tools and artifact file extensions?
# TODO Skip lines that start with comments??
# TODO Make sure code is commented and logged properly
# TODO Skip invalid Jenkinsfiles (i.e. empty, imbalanced brackets, starts with pipeline or node)
# TODO MAYBE - For each research question, put together a list of repositories with good Jenkinsfiles


# TODO Update the following to paths for your system
CLONED_REPOS_DIR_PATH = 'C:/Users/Viren/Google Drive/1.UIC/540/guillermo_rojas_hernandez_viren_mody_courseproject/ClonedRepos/'
# CLONED_REPOS_DIR_PATH = '/home/guillermo/cs540/guillermo_rojas_hernandez_viren_mody_courseproject/ClonedRepos/'

# Research Topic Number - Will be appended to the directory path to separate Jenkinsfiles by research topic
research_topic_num = 0

# Global git_hub object
git_hub = None

# Retrieve logger to be used for both project.py and project_utils.py
logger = logging.getLogger('project')


def configure_logger():
    """
    Function configures logger level, format, and output stream

    Source: https://docs.python.org/3/howto/logging.html
    Use this to appropriately categorize log types when logging
    LOGGING LEVELS
    DEBUG	Detailed information, typically of interest only when diagnosing problems.
    INFO	Confirmation that things are working as expected.
    WARNING	An indication that something unexpected happened, or indicative of some problem in the near future (e.g. ‘disk space low’). The software is still working as expected.
    ERROR	Due to a more serious problem, the software has not been able to perform some function.
    CRITICAL	A serious error, indicating that the program itself may be unable to continue running.
    """

    # TODO change logger level to your preference
    LOG_FILENAME = 'project.log'
    logger.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(levelname)s:%(filename)s: In %(funcName)s(): On Line: %(lineno)d: %(message)s')

    # Setup output log to console and to a file
    file_handler = logging.FileHandler(LOG_FILENAME)
    stream_handler = logging.StreamHandler()
    file_handler.setFormatter(formatter)
    stream_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)


def authenticate_github_object():
    """
    Function authenticates GitHub object using username and access token
    """
    GITHUB_USERNAME = 'virenmody'
    GITHUB_ACCESS_TOKEN = 'feec9be9b75ded7680e74e1be28b47c50564c2ac'

    # Authenticate GitHub object
    global git_hub
    git_hub = GitHub(GITHUB_USERNAME, GITHUB_ACCESS_TOKEN)

    logger.info('GITHUB_USERNAME: %s', GITHUB_USERNAME)
    logger.info('GITHUB_ACCESS_TOKEN: %s', GITHUB_ACCESS_TOKEN)
    logger.info('LOCAL_CLONED_REPO_PATH: %s', CLONED_REPOS_DIR_PATH)


# TODO Error/exception handling (i.e. empty Jenkinsfile, empty triggers or stages)
# TODO Only include declarative pipelines?
def parse_triggers_and_stages(jenkinsfile):
    """
    Function parses jenkinsfile for trigger and stage counts and info
    :param jenkinsfile: path to Jenkinsfile to parse
    :return: list of triggers, list of stages and number of triggers and stages
    """

    logger.debug('Parsing Jenkinsfile: %s', jenkinsfile)
    triggers = ['cron', 'pollSCM', 'upstream']
    triggers_found = []
    trigger_type = ''
    num_triggers = 0

    stages_found = []
    num_stages = 0

    # Parse the Jenkinsfile line by line searching for keywords relevant to triggers and stages
    with open(jenkinsfile, errors='replace') as file:
        try:
            for line in file:
                line = line.strip('\n')

                # Skip files that use the 'pipelineTriggers' format
                if 'pipelineTriggers' in line:
                    return None, None, None, None

                # Parse and store data containing any of the 3 triggers: cron, pollSCM, upstream
                if any(trig in line for trig in triggers):
                    num_triggers += 1

                    if 'cron' in line:
                        trigger_type = 'cron'
                    elif 'pollSCM' in line:
                        trigger_type = 'pollSCM'
                    elif 'upstream' in line:
                        trigger_type = 'upstream'

                    # Retrieve trigger value/argument from between parentheses and/or single or double quotes
                    re_triggers_pattern = r"(?:'|\")(.*)(?:'|\")"
                    logger.debug('LINE: %s', line)
                    trigger_value = re.search(re_triggers_pattern, line).group(1)
                    logger.debug('ADDING TRIGGER:  %s = %s', trigger_type, trigger_value)
                    triggers_found.append({'Type': trigger_type, 'Value': trigger_value, 'Occurrence': num_triggers})

                # Parse and store data containing stage
                elif 'stage' in line and 'stages' not in line:
                    num_stages += 1

                    # Retrieve stage name from between parentheses and/or single or double quotes
                    re_stages_pattern = r"(?:'|\")(.*)(?:'|\")"
                    logger.debug('LINE: %s', line)
                    stage_name = re.search(re_stages_pattern, line).group(1)
                    logger.debug('ADDING STAGE:  %s, Occurrence: %s', stage_name, num_stages)
                    stages_found.append({'Name': stage_name, 'Occurrence': num_stages})

        # Catch AttributeErrors: Most commonly occurs when the above keywords are found in a context other than designed for (i.e. the word 'stage' is found in the comments)
        except AttributeError as error:
            logger.error('%s: SKIPPING THIS JENKINSFILE', error)
            return None, None, None, None
        except Exception as exception:
            logger.error('%s: SKIPPING THIS JENKINSFILE', exception)
            return None, None, None, None

    logger.debug('TRIGGERS: %s', triggers_found)
    logger.debug('STAGES: %s', stages_found)
    return triggers_found, stages_found, num_triggers, num_stages


def parse_tools(jenkinsfile):
    """
    Function parses jenkinsfile for trigger and stage counts and info
    :param jenkinsfile: path to Jenkinsfile to parse
    :return: list of triggers, list of stages and number of triggers and stages
    """
    logger.debug('Parsing Jenkinsfile: %s', jenkinsfile)
    tools = ['maven', 'jdk', 'nodejs']
    tools_found = []
    tool_type = ''
    num_tools = 0
    capture_tools = False

    with open(jenkinsfile, errors='replace') as file:
        logger.debug('Jenkinsfile Contents: %s', file)

        try:
            for line in file:
                line = line.strip('\n')

                if "tools" in line:
                    capture_tools = True
                    continue
                elif "}" in line and capture_tools is True:
                    capture_tools = False
                    break
                elif capture_tools is True:
                    num_tools += 1

                    # strip white space from beginning of line
                    str = line.lstrip()
                    # save the first part of the string before the space as a tool type
                    tool_type = str.partition(' ')[0]

                    # Retrieve trigger value from between parentheses and single quotes
                    re_tools_pattern = r"(?:\'|\")(.*)(?:\'|\")"
                    tool_value = re.search(re_tools_pattern, line).group(1)
                    logger.debug('LINE: %s', line)
                    logger.debug('ADDING TOOL:  %s = %s', tool_type, tool_value)
                    tools_found.append({'ToolType': tool_type, 'ToolVersion': tool_value, 'Occurrence': num_tools})


        # Catch AttributeErrors: Most commonly occurs when the above keywords are found in a context other than designed for (i.e. the word 'stage' is found in the comments)
        except AttributeError as error:
            logger.error('%s: Unique Pipeline Syntax--SKIPPING THIS JENKINSFILE', error)
            return None, None
        except Exception as exception:
            logger.error('%s: SKIPPING THIS JENKINSFILE', exception)
            return None, None

    logger.debug('TOOLS FOUND: %s', tools_found)

    return tools_found, num_tools


def search_and_download_jenkinsfiles(query, num_results):
    """
    Function searches GitHub for Jenkinsfiles with the given parameters and downloads them
    :param query: search query for jenkinsfiles
    :param num_results: number of results desired from search
    :return: repo_data: a list of data for each repo: username, repo-name, and path to downloaded jenkinsfile
    """

    # Results are returned in tuples: ((github_object, raw_url))
    logger.info('Searching GitHub for %s results with query: %s', num_results, query)
    results = project_utils.search_by_code(git_hub, query, num_results)
    logger.debug("Results from project.search_by_code: %s", results)

    # Increment research_topic_num for each research topic to separate jenkinsfiles that are downloaded
    global research_topic_num
    research_topic_num += 1
    repo_data = []
    # Get file contents of all results (raw url is second item in tuple: results[i][1])
    for i in range(0, len(results)):
        res = requests.get(results[i][1])

        # print the whole folder name
        logger.debug("Repository %s", i+1)
        logger.debug(results[i][2])

        # Print contents of Jenkinsfile
        logger.debug(res.text)

        github_repo_name = results[i][2]
        path_to_repo = CLONED_REPOS_DIR_PATH + str(research_topic_num) + '/' + github_repo_name
        pathlib.Path(path_to_repo).mkdir(parents=True, exist_ok=True)

        # Write file contents back to Jenkinsfile
        jenkinsfile_path = path_to_repo + '/' + 'Jenkinsfile'
        with open(jenkinsfile_path, "wb") as file:
            file.write(res.content)

        # Store GitHub username, repo name, and path to Jenkinsfile in a list to process
        github_repo_name_split = github_repo_name.split('/')
        username = github_repo_name_split[0]
        repo_name = github_repo_name_split[1]
        repo_dict = {'Username': username, 'RepoName': repo_name, 'Jenkinsfile_Path': jenkinsfile_path}
        repo_data.append(repo_dict)

    return repo_data


def analyze_research_question_triggers_stages():
    """
    Function retrieves Jenkinsfiles, parses it, and analyzes the data to answer:
    Research Question #1: How does the number of triggers in a pipeline correlate with the number of stages in the pipeline?
    """

    logger.info('Analyzing Jenkinsfiles for Research Question 1: How does the number of triggers in a pipeline correlate with the number of stages in the pipeline?')

    # Create DataFrame to store all data
    df_headers = ['RepoNum', 'Username', 'RepositoryName', 'TriggerType', 'TriggerValue', 'TriggerOccurrence', 'StageName', 'StageOccurrence']
    df = project_utils.create_df(df_headers)

    # Query for GitHub Jenkinsfile search ('pipeline' is used because our focus is on declarative pipeline syntax): TODO Change num_results as per your preference
    query = "filename:jenkinsfile q=pipeline triggers stage tools"
    num_results = 10
    repo_data = search_and_download_jenkinsfiles(query, num_results)
    logger.info('Results received from search: %s', repo_data)

    # For each repo from the search results, parse the Jenkinsfile for trigger and stage data, and store it for analysis
    stage_counts = []
    trigger_counts = []
    repo_num = 0
    for repo in repo_data:
        repo_num += 1
        username = repo['Username']
        repo_name = repo['RepoName']
        jenkinsfile_path = repo['Jenkinsfile_Path']

        # Skip Jenkinsfiles that do not exist
        if os.path.isfile(jenkinsfile_path) is False:
            logger.error('%s DOES NOT EXIST - SKIPPING REPO', jenkinsfile_path)
            repo_num -= 1
            continue

        # Parse triggers and stages from file
        triggers_data, stages_data, num_triggers, num_stages = parse_triggers_and_stages(jenkinsfile_path)

        # Skip repositories that don't use typical declarative pipeline syntax or cause parsing errors
        if triggers_data is None:
            repo_num -= 1
            continue

        # Store trigger and stage counts to calculate correlation coefficient
        trigger_counts.append(num_triggers)
        stage_counts.append(num_stages)

        # Store parsed data in DataFrame for analyzing
        combined_data = list(itertools.zip_longest(triggers_data, stages_data))
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

            repo_num_str = str(repo_num) if iteration == 0 else ''

            # Add parsed data to DataFrame
            new_row = [[repo_num_str, username, repo_name, trigger_type, trigger_value, trigger_occurrence, stage_name, stage_occurrence]]
            df = project_utils.add_row_to_df(df, df_headers, new_row)

            # Do not repeat username and repo_name for output readability
            if iteration == 0:
                username = ''
                repo_name = ''

        # Insert blank row for increased readability
        df = project_utils.add_blank_row_to_df(df, df_headers)

    logger.debug('Trigger Counts: %d:%s', len(trigger_counts), trigger_counts)
    logger.debug('Stage Counts:   %d:%s', len(stage_counts), stage_counts)
    correlation_coefficient = round(numpy.corrcoef(trigger_counts, stage_counts)[0, 1], 5)
    logger.info('Pearson Correlation Coefficient between Trigger and Stage Counts: %s', correlation_coefficient)

    csv_file = 'research_question_stages_triggers.csv'
    csv_header = [['Research Question 1: How does the number of triggers in a pipeline correlate with the number of stages in the pipeline?'],
                  ['Correlation Coefficient: ' + str(correlation_coefficient)],
                  ['\n'],
                  ['Parsed Jenkinsfile Data']]

    # Write to CSV file
    with open(csv_file, 'w+') as analysisFile:
        cw = csv.writer(analysisFile, dialect='excel', lineterminator='\n')
        cw.writerows(csv_header)

    # Write DataFrame to CSV file
    df.to_csv(csv_file, mode='a', header='false', sep=',', na_rep='', index=False)
    logger.info('Results written in /src folder to \'%s\' for \n\t\t\t\t\tResearch Question 1: How does the number of triggers in a pipeline correlate with the number of stages '
                'in the pipeline?', csv_file)


# TODO Function documentation comments
def analyze_research_question_tools():
    """

    :return:
    """
    logger.info('Analyzing Jenkinsfiles for Research Question 2: What types of tools are used in the pipeline?')

    # Format Dataframe with variables that function will be filling in
    df_headers = ['RepoNum', 'Username', 'RepositoryName', 'ToolType', 'ToolVersion', 'TriggerOccurrence']
    df = project_utils.create_df(df_headers)

    # Create Query and Search GitHub (pipeline is used because our focus is on declarative pipeline syntax)
    # 'tools' is included in query to search for files that have the key word tools
    query = "filename:jenkinsfile q=pipeline tools"
    num_results = 50
    repo_data = search_and_download_jenkinsfiles(query, num_results)
    logger.info('Results received from search: %s', repo_data)
    logger.info('Number of Results received from search: %s', len(repo_data))

    repo_num = 0
    for repo in repo_data:
        repo_num += 1

        logger.debug('Repo Number: %s', repo_num)
        username = repo['Username']
        repo_name = repo['RepoName']
        jenkinsfile_path = repo['Jenkinsfile_Path']

        # Skip Jenkinsfiles that do not exist
        if os.path.isfile(jenkinsfile_path) is False:
            logger.error('%s DOES NOT EXIST - SKIPPING REPO', jenkinsfile_path)
            repo_num -= 1
            continue

        # Parse triggers and stages from file
        tool_data, num_tools = parse_tools(jenkinsfile_path)

        # Skip repositories that don't use typical declarative pipeline syntax or cause parsing errors
        if tool_data is None:
            logger.error('%s CAUSING PARSING ERRORS OR DOES NOT HAVE DECLARATIVE PIPELINE SYNTAX', jenkinsfile_path)
            repo_num -= 1
            continue

        # Store parsed data in DataFrame for analyzing
        iteration = 0
        for tool in tool_data:
            # tool = data
            tool_type = ''
            tool_value = ''
            tool_occurrence = ''
            if tool is not None:
                tool_type = tool['ToolType']
                tool_value = tool['ToolVersion']
                tool_occurrence = tool['Occurrence']

            repo_num_str = str(repo_num) if iteration == 0 else ''

            new_row = [[repo_num_str, username, repo_name, tool_type, tool_value, tool_occurrence]]
            logger.debug("Username: %s Repo Name: %s Tool Type: %s Tool Value: %s Tool Occurrence: %s",
                         username, repo_name, tool_type, tool_value, tool_occurrence)
            df = project_utils.add_row_to_df(df, df_headers, new_row)

            if iteration == 0:
                username = ''
                repo_name = ''

            iteration += 1

        # Insert blank row for increased readability
        df = project_utils.add_blank_row_to_df(df, df_headers)

    csv_file = 'research_question_tools.csv'
    csv_header = [['Research Question 1: What types of tools are used in the pipeline?'],
                  ['\n'],
                  ['Parsed Jenkinsfile Data']]

    # Write to CSV file
    with open(csv_file, 'w+') as analysisFile:
        cw = csv.writer(analysisFile, dialect='excel', lineterminator='\n')
        cw.writerows(csv_header)

    # Write DataFrame to CSV file
    df.to_csv(csv_file, mode='a', header='false', sep=',', na_rep='', index=False)
    logger.info('Results written in /src folder to \'%s\' for \n\t\t\t\t\tResearch Question 1: How does the number of triggers in a pipeline correlate with the number of stages '
                'in the pipeline?', csv_file)


def analyze_research_questions_artifacts():
    """
    Function retrieves Jenkinsfiles, parses it, and analyzes the data to answer:
    Research Question #3: In which pipeline sections or pipeline directives are artifacts most frequently and least frequently archived?
    Research Question #4: Which file extensions are most frequently and least frequent archived?(.exe, .jar, everything, etc.)
    Research Question #5: What percentage of archived artifacts are archived with a fingerprint?
    """

    logger.info('Analyzing Jenkinsfiles for Research Questions:\n#3: In which pipeline sections or pipeline directives are artifacts most frequently and least frequently '
                'archived?\n#4: Which file extensions are most frequently and least frequent archived?(.exe, .jar, everything, etc.)\n#5: '
                'What percentage of archived artifacts are archived with a fingerprint?')

    # Create DataFrame to store all data
    df_headers = ['RepoNum', 'Username', 'RepositoryName', 'Artifact', 'Extension', 'Fingerprint', 'OnlyIfSuccessful', 'InSection', 'SectionName']
    df = project_utils.create_df(df_headers)

    # Query for GitHub Jenkinsfile search ('pipeline' is used because our focus is on declarative pipeline syntax): TODO Change num_results as per your preference
    query = "filename:jenkinsfile q=pipeline archiveartifacts tools"
    num_results = 10
    repo_data = search_and_download_jenkinsfiles(query, num_results)
    logger.info('Results received from search: %s', repo_data)

    # For each repo from the search results, parse the Jenkinsfile for data on 'archivedartifacts', and store it for analysis
    repo_num = 0
    for repo in repo_data:
        repo_num += 1
        username = repo['Username']
        repo_name = repo['RepoName']
        jenkinsfile_path = repo['Jenkinsfile_Path']

        # Skip Jenkinsfiles that do not exist
        if os.path.isfile(jenkinsfile_path) is False:
            logger.error('%s DOES NOT EXIST - SKIPPING REPO', jenkinsfile_path)
            repo_num -= 1
            continue

        # Parse triggers and stages from file
        triggers_data, stages_data, num_triggers, num_stages = parse_triggers_and_stages(jenkinsfile_path)

        # Skip repositories that don't use typical declarative pipeline syntax or cause parsing errors
        if triggers_data is None:
            repo_num -= 1
            continue

        # Store parsed data in DataFrame for analyzing
        combined_data = list(itertools.zip_longest(triggers_data, stages_data))
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

            repo_num_str = str(repo_num) if iteration == 0 else ''

            # Add parsed data to DataFrame
            new_row = [[repo_num_str, username, repo_name, trigger_type, trigger_value, trigger_occurrence, stage_name, stage_occurrence]]
            df = project_utils.add_row_to_df(df, df_headers, new_row)

            # Do not repeat username and repo_name for output readability
            if iteration == 0:
                username = ''
                repo_name = ''

        # Insert blank row for increased readability
        df = project_utils.add_blank_row_to_df(df, df_headers)


def main():
    configure_logger()
    authenticate_github_object()

    # Research Question #1: How does the number of triggers in a pipeline correlate with the number of stages in the pipeline?
    # analyze_research_question_triggers_stages()

    # Research Question #2
    analyze_research_question_tools()

    # TODO Update this comment
    # Research Questions #3, 4, 5
    # analyze_research_questions_artifacts()


if __name__ == '__main__':
    main()
