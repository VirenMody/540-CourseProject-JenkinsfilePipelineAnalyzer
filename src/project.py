import matplotlib.pyplot as plt
from github3 import GitHub
import requests
import pathlib
import itertools
import logging
import os
import re  # regex
import numpy
import csv
import traceback
from random import shuffle

import unittest

import project_utils

# TODO Checked for balanced brackets
# TODO Change filename number for rq 1 and 2
# TODO In search_and_download_jenkinsfiles, skip repos containing 'node' and other issues (after this line res = requests.get(results[i][1]))
# TODO Artifacts Research Questions - Maybe correlation between tools and artifact file extensions?
# TODO What is the correlation between the presence of disableconcurrentbuilds() and hashes in triggers?
# TODO Research question involving Slack
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


def configure_logger(file_name, level):
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
    LOG_FILENAME = file_name
    logger.setLevel(level)
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
    triggers_data = []
    trigger_type = ''
    num_triggers = 0

    stages_data = []
    num_stages = 0

    # Parse the Jenkinsfile line by line searching for keywords relevant to triggers and stages
    try:
        with open(jenkinsfile, errors='replace') as file:
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
                    triggers_data.append({'Type': trigger_type,
                                           'Value': trigger_value,
                                           'Occurrence': num_triggers})

                # Parse and store data containing stage
                elif 'stage' in line and 'stages' not in line:
                    num_stages += 1

                    # Retrieve stage name from between parentheses and/or single or double quotes
                    re_stages_pattern = r"(?:'|\")(.*)(?:'|\")"
                    logger.debug('LINE: %s', line)
                    stage_name = re.search(re_stages_pattern, line).group(1)
                    logger.debug('ADDING STAGE:  %s, Occurrence: %s', stage_name, num_stages)
                    stages_data.append({'Name': stage_name,
                                         'Occurrence': num_stages})

    # Catch AttributeErrors: Most commonly occurs when the above keywords are found in a context other than designed for (i.e. the word 'stage' is found in the comments)
    except AttributeError as error:
        logger.error('%s: SKIPPING THIS JENKINSFILE', error)
        return None, None, None, None
    except Exception as exception:
        logger.error('%s: SKIPPING THIS JENKINSFILE', exception)
        return None, None, None, None

    logger.debug('TRIGGERS: %s', triggers_data)
    logger.debug('STAGES: %s', stages_data)
    return triggers_data, stages_data, num_triggers, num_stages


def parse_tools(jenkinsfile):
    """
    Function parses jenkinsfile for trigger and stage counts and info
    :param jenkinsfile: path to Jenkinsfile to parse
    :return: list of triggers, list of stages and number of triggers and stages
    """
    logger.debug('Parsing Jenkinsfile: %s', jenkinsfile)
    tools_found = []
    tool_type = ''
    num_tools = 0
    capture_tools = False

    with open(jenkinsfile, errors='replace') as file:
        logger.debug('Jenkinsfile Contents: %s', file)

        try:
            for line in file:
                line = line.strip('\n')

                if line[:2] == '//':
                    continue
                if "tools" in line:
                    capture_tools = True
                    continue
                elif "}" in line and capture_tools is True:
                    capture_tools = False
                    break
                elif capture_tools is True:

                    # strip white space from beginning of line
                    str = line.lstrip()
                    # save the first part of the string before the space as a tool type
                    tool_type = str.partition(' ')[0]

                    if tool_type == '{' or tool_type == '//':
                        continue
                    else:
                        num_tools += 1

                        # Retrieve trigger value from between parentheses and single quotes
                        re_tools_pattern = r"(?:\'|\")(.*)(?:\'|\")"
                        tool_value = re.search(re_tools_pattern, line).group(1)

                        # catch case of extra colon
                        if tool_type == 'nodejs:':
                            tool_type = 'nodejs'

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
    logger.info('Downloading repository results from GitHub Search')

    # Increment research_topic_num for each research topic to separate jenkinsfiles that are downloaded
    global research_topic_num
    research_topic_num += 1
    repo_data = []
    # Get file contents of all results (raw url is second item in tuple: results[i][1])
    for i in range(0, len(results)):
        res = requests.get(results[i][1])

        # print the whole folder name
        logger.debug('Downloading Repository %s: %s', i+1, results[i][2])

        # Print contents of Jenkinsfile
        # logger.debug(res.text)

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
    num_results = 200
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

    csv_file = 'research_question_1_stages_triggers.csv'
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

    return csv_file


def analyze_research_question_tools():
    """
    Function retrieves Jenkinsfiles, parses it, and analyzes the data to answer:
    Research Question #2: Which tools are most frequently and least frequently used in the pipeline?
    """
    logger.info('Analyzing Jenkinsfiles for Research Question 2: What types of tools are used in the pipeline?')

    # Format Dataframe with variables that function will be filling in
    df_headers = ['RepoNum', 'Username', 'RepositoryName', 'ToolType', 'ToolVersion', 'NumberOfTools']
    df = project_utils.create_df(df_headers)

    # Create Query and Search GitHub (pipeline is used because our focus is on declarative pipeline syntax)
    # 'tools' is included in query to search for files that have the key word tools
    query = "filename:jenkinsfile q=pipeline tools"
    num_results = 200
    repo_data = search_and_download_jenkinsfiles(query, num_results)
    logger.info('Results received from search: %s', repo_data)
    logger.info('Number of Results received from search: %s', len(repo_data))

    tools_dict = {}

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

                #add to tool type and tool occurrence dictionaries
                if tool_type not in tools_dict:
                    tools_dict[tool_type] = [1, [tool_value]]
                    logger.debug("Add key to tools_dict: %s Add value to tools_dict: %s", tool_type, tool_value)
                else:
                    current_value = tools_dict[tool_type]
                    current_value[1].append(tool_value)
                    current_value[0] = current_value[0]+1
                    tools_dict[tool_type] = current_value

            repo_num_str = str(repo_num) if iteration == 0 else ''

            new_row = [[repo_num_str, username, repo_name, tool_type, tool_value, tool_occurrence]]
            logger.debug("Username: %s Repo Name: %s Tool Type: %s Tool Value: %s Number of Tools: %s",
                         username, repo_name, tool_type, tool_value, tool_occurrence)
            df = project_utils.add_row_to_df(df, df_headers, new_row)

            if iteration == 0:
                username = ''
                repo_name = ''

            iteration += 1

        # Insert blank row for increased readability
        df = project_utils.add_blank_row_to_df(df, df_headers)

    total_tools = sum(i[0] for i in tools_dict.values())
    average_tools_per_repository = round(total_tools/repo_num, 4)

    percent_per_tool = ''
    for key in tools_dict:
        percent_per_tool += str(key) + ': ' + str(round(tools_dict[key][0]/total_tools, 2)) + ', '

    df_sections_summary = df.groupby('ToolType')['NumberOfTools'].count().reset_index()[1:]
    df_sections_summary.columns = ['Section', 'Count']
    df_sections_summary['Percentage'] = round(100 * df_sections_summary['Count'] / df_sections_summary['Count'].sum(), 2)
    logger.debug('\nRQ#3:\n%s', df_sections_summary)

    # Bar chart Number of Artifacts Archived per Section
    ax = df_sections_summary.plot(kind='bar',
                                  title="Number of Tools Per Section",
                                  # grid=True,
                                  # color='blue',
                                  x='Section',
                                  y='Count',
                                  rot=0,
                                  legend=True,
                                  fontsize=12)
    ax.set_xlabel("Section", fontsize=12)
    ax.set_ylabel("Number of Tools", fontsize=12)

    x_offset = -0.10
    y_offset = 1.0
    for p in ax.patches:
        b = p.get_bbox()
        val = "{:.0f}".format(b.y1 + b.y0)
        ax.annotate(val, ((b.x0 + b.x1) / 2 + x_offset, b.y1 + y_offset))
    plt.show()

    # Pie Chart Number and Percentage of Artifacts Archived per Section
    values = list(df_sections_summary.Count)
    colors = ['b', 'g', 'r', 'c']
    labels = list(df_sections_summary.Section)
    ex = 0.3
    explode = []
    for i in range(0, len(values)):
        if (values[i]/total_tools) < .1:
            explode.append(ex)
            # ex += .1
        else:
            explode.append(0)

    explode_tuple = tuple(explode)

    plt.pie(values,
            labels=values,
            explode=explode,
            shadow=False,
            pctdistance= 1.1,
            autopct='%.1f%%',
            labeldistance=1.2)
    plt.title('Number and Percentage of Build Tools')
    plt.legend(labels, loc=4)
    plt.show()

    csv_file = 'research_question_2_tools.csv'
    csv_header = [['Research Question 1: What types of tools are used in the pipeline?'],
                  ['Repositories with Jenkinsfiles downloaded from GitHub: ' + str(num_results)],
                  ['Number of Jenkinsfiles suitable for parsing: ' + str(repo_num)],
                  ['Number of Different Build Tools: ' + str(len(tools_dict))],
                  ['Different Types of Build Tools: ' + str(list(tools_dict.keys()))],
                  ['Average Number of Build Tools Used Per Repository: ' + str(average_tools_per_repository)],
                  ['Frequency of Build Tool Use by Repository: ' + percent_per_tool],
                  ['\n'],
                  ['Parsed Jenkinsfile Data']]

    logger.debug("Tools Dictionary: %s", tools_dict)

    # Write to CSV file
    with open(csv_file, 'w+') as analysisFile:
        cw = csv.writer(analysisFile, dialect='excel', lineterminator='\n')
        cw.writerows(csv_header)

    # Write DataFrame to CSV file
    df.to_csv(csv_file, mode='a', header='false', sep=',', na_rep='', index=False)
    logger.info('Results written in /src folder to \'%s\' for \n\t\t\t\t\tResearch Question 1: How does the number of triggers in a pipeline correlate with the number of stages '
                'in the pipeline?', csv_file)

    return csv_file


def parse_archiveArtifacts(jenkinsfile):
    """
    Function parses jenkinsfile for 'archiveArtifacts' data: What artifacts are being archived, artifact file extensions, which sections artifacts are being archived,
    fingerprint attribute, and onlyIfSuccessful
    :param jenkinsfile: path to Jenkinsfile to parse
    :return: TODO determine return type
    """

    logger.debug('Parsing Jenkinsfile: %s', jenkinsfile)

    # List used as a stack to keep track of which section 'archiveArtifacts' is in
    post_conditions = ['always', 'changed', 'fixed', 'regression', 'aborted', 'failure', 'success', 'unstable', 'cleanup']
    section_stack = []
    artifacts_data = []
    num_artifacts = 0

    # Parse the Jenkinsfile line by line searching for 'archiveArtifacts' keyword and relevant keywords (i.e fingerprint)
    try:
        with open(jenkinsfile, errors='replace') as file:
            file_lines = file.readlines()
            for idx, line in enumerate(file_lines):
                line = line.strip()

                # Skip lines that are comments
                if line.startswith('//'):
                    continue

                # TODO Keep or remove files containing 'node'?
                # # Skip Jenkinsfiles that contain 'node' - a possible indicator for scripted pipelines
                # if 'node' in line:
                #     logger.warning('WARNING: Detected possible scripted pipeline - SKIPPING THIS JENKINSFILE!')
                #     return None, None

                # If there's an opening bracket, push section name onto the stack
                if '{' in line:

                    # For lines with both opening and closing brackets: if balanced, skip line, if imbalanced, skip Jenkinsfile for unparseable format
                    if '}' in line:
                        if line.count('{') == line.count('}'):
                            continue
                        else:
                            logger.warning('WARNING: Unparseable format - SKIPPING THIS JENKINSFILE!')
                            return None, None

                    line = line.replace('{', '').replace(' ', '')
                    # Skip the Jenkinsfile if formatting doesn't follow typical Jenkinsfile formats (open brackets on same line as section header i.e. stage('Build') { )
                    if line == '':
                        logger.warning('WARNING: Unparseable format - SKIPPING THIS JENKINSFILE!')
                        return None, None

                    section_stack.append(line)

                # If there's a closing bracket, pop it off
                if '}' in line:
                    section_stack.pop()

                # Extract all artifact data the line containing 'archiveArtifact' (i.e. artifact, extension, section, etc.)
                if 'archiveArtifact' in line:
                    num_artifacts += 1
                    artifact = ''
                    extension = ''
                    fingerprint = 'false'
                    onlyIfSuccessful = 'N/A'
                    section = ''
                    section_name = 'N/A'

                    # Retrieve 'archivedArtifact' from between single or double quotes, then extract only name & extension without the path
                    re_artifact_pattern = r"(?:'|\")(.*)(?:'|\")"
                    logger.debug('LINE: %s', line)
                    archived_artifact = re.search(re_artifact_pattern, line).group(1)
                    artifact = pathlib.Path(archived_artifact).name
                    logger.debug('EXTRACTED ARTIFACT: %s', artifact)

                    # Extract artifact file extension and join them if there are multiple
                    extension = ''.join(pathlib.Path(artifact).suffixes)
                    # If there is no extension, it either indicates all files in a directory or the file has no extension at all
                    if extension == '':
                        if artifact.endswith('*'):
                            extension = 'All'
                        else:
                            extension = 'None'
                    logger.debug('EXTRACTED EXTENSION: %s', extension)

                    # Extract fingerprint boolean (true, false) from line
                    # re_fingerprint_pattern = r"fingerprint:\s(.*)"
                    re_fingerprint_pattern = r"fingerprint\s*:\s*(true|false)"
                    if 'fingerprint' in line:
                        fingerprint = re.search(re_fingerprint_pattern, line).group(1)
                    # If the fingerprint is not on the current line, check the following and previous lines to accommodate different formats
                    else:
                        # Update regex pattern to accommodate different formats
                        re_fingerprint_pattern = r"(?:'|\")(.*)(?:'|\")"
                        if idx + 1 < len(file_lines):
                            next_line = file_lines[idx+1]
                            if 'fingerprint' in next_line and 'archivedArtifact' not in next_line:
                                fingerprint = re.search(re_fingerprint_pattern, file_lines[idx+1]).group(1)

                        # TODO Remove fingerprint check in previous line?
                        # if fingerprint == '' and idx - 1 >= 0:
                        #     prev_line = file_lines[idx-1]
                        #     if 'fingerprint' in prev_line and 'archivedArtifact' not in prev_line:
                        #         fingerprint = re.search(re_fingerprint_pattern, file_lines[idx-1]).group(1)

                        # If the fingerprint is not a boolean and is an artifact, set the boolean to true
                        if fingerprint != 'true' and fingerprint != 'false':
                            logger.debug('EXTRACTED NON-BOOLEAN FINGERPRINT ARTIFACT: %s', fingerprint)
                            fingerprint = 'true'
                    logger.debug('EXTRACTED FINGERPRINT: %s', fingerprint)

                    # Extract onlyIfSuccessful boolean from line
                    re_onlyIfSuccessful_pattern = r"onlyIfSuccessful:\s(true|false)"
                    if 'onlyIfSuccessful' in line:
                        onlyIfSuccessful = re.search(re_onlyIfSuccessful_pattern, line).group(1)
                    logger.debug('EXTRACTED onlyIfSuccessful: %s', onlyIfSuccessful)

                    # Extract the section the artifact is found in from the section_stack
                    logger.debug('SECTION_STACK: %s', section_stack)
                    for section in reversed(section_stack):
                        logger.debug('Looking at section: %s', section)
                        if 'stage' in section and 'stages' not in section:
                            re_stages_pattern = r"(?:'|\")(.*)(?:'|\")"
                            section_name = re.search(re_stages_pattern, section).group(1)
                            section = 'stage'
                            break
                        elif any(section in condition for condition in post_conditions):
                            section_name = section
                            section = 'post-' + section
                            break
                        elif 'steps' not in section and 'Archive' not in section:
                            logger.debug('FOUND NONSTAGE NONPOST SECTION: %s in %s', section, jenkinsfile)
                    logger.debug('EXTRACTED SECTION-SECTION_NAME: %s-%s', section, section_name)

                    artifacts_data.append({'Artifact': artifact,
                                            'Extension': extension,
                                            'fingerprint': fingerprint,
                                            'onlyIfSuccessful': onlyIfSuccessful,
                                            'ParentSection': section,
                                            'SectionName': section_name,
                                            'Occurrence': num_artifacts})

            if section_stack:
                logger.warning('WARNING: STACK IS NOT EMPTY - Jenkinsfile brackets are imbalanced - SKIPPING THIS JENKINSFILE!')
                return None, None

    # Catch:
    # - IndexErrors: Most commonly occurs when there's an imbalance in opening and closing brackets in section_stack
    # - AttributeErrors: Most commonly occurs when the above keywords are found in a context other than designed for (i.e. the word 'stage' is found in the comments)
    except IndexError as error:
        logger.error('ERROR: %s - Jenkinsfile brackets are imbalanced - SKIPPING THIS JENKINSFILE', error)
        traceback.print_stack()
        return None, None
    except AttributeError as error:
        logger.error('ERROR: %s - SKIPPING THIS JENKINSFILE', error)
        traceback.print_stack()
        return None, None
    except Exception as exception:
        logger.error('EXCEPTION: %s - SKIPPING THIS JENKINSFILE', exception)
        traceback.print_stack()
        return None, None

    logger.debug('ARTIFACTS: %s', artifacts_data)
    logger.debug('NUMBER OF ARTIFACTS: %s', num_artifacts)
    return artifacts_data, num_artifacts


def rq3_write_to_csv(df_sections_raw, df_sections):
    """
    Function writes data for research question 3 to csv files
    :param df_sections_raw:
    :param df_sections:
    """
    csv_file = 'research_question_3_artifacts_sections.csv'
    csv_q3_header = [['Research Question #3: In which pipeline sections or pipeline directives are artifacts most frequently and least frequently archived?'],
                     ['Answer: ']]
    csv_parsed_data_header = [['\n'], ['Jenkinsfile Parsed Data for Artifacts and Sections']]

    # Write RQ3 Header to CSV file
    with open(csv_file, 'w+') as analysisFile:
        cw = csv.writer(analysisFile, dialect='excel', lineterminator='\n')
        cw.writerows(csv_q3_header)

    # Write DataFrame to CSV file
    df_sections.to_csv(csv_file, mode='a', header='false', sep=',', na_rep='', index=False)

    # Write Parsed Data Header to CSV file
    with open(csv_file, 'a') as analysisFile:
        cw = csv.writer(analysisFile, dialect='excel', lineterminator='\n')
        cw.writerows(csv_parsed_data_header)

    # Write DataFrame to CSV file
    df_sections_raw.to_csv(csv_file, mode='a', header='false', sep=',', na_rep='', index=False)
    logger.info('Results written in /src folder to \'%s\' for \n\t\t\t\t\tResearch Question #3 In which pipeline sections or pipeline directives are artifacts most frequently '
                'and least frequently archived?', csv_file)


def rq3_chart_data(df_sections):
    """
    Function charts rq3 data to bar graph and pie chart
    :param df_sections:
    """
    # Bar chart RQ3: Number of Artifacts Archived per Section
    ax = df_sections.plot(kind='bar',
                          title="RQ3: Number of Artifacts Archived Per Section",
                          x='Section',
                          y='NumArtifacts',
                          rot=0,
                          legend=False,
                          fontsize=12)
    ax.set_xlabel("Section", fontsize=12)
    ax.set_ylabel("Number of Archived Artifacts", fontsize=12)

    # Annotate bar graph with values of each bar
    x_offset = -0.10
    y_offset = 0.3
    for p in ax.patches:
        b = p.get_bbox()
        val = "{:.0f}".format(b.y1 + b.y0)
        ax.annotate(val, ((b.x0 + b.x1) / 2 + x_offset, b.y1 + y_offset))
    plt.show()

    # Pie Chart RQ3: Number and Percentage of Artifacts Archived per Section
    values = list(df_sections['NumArtifacts'])
    labels = list(df_sections['Section'])
    plt.pie(values,
            labels=values,
            counterclock=True,
            autopct='%.1f%%',
            labeldistance=1.1)
    plt.title('RQ3: Number and Percentage of Artifacts Archived Per Section')
    plt.legend(labels, loc=3)
    plt.show()


def analyze_research_question_3_artifacts_sections(df):
    """
    Function processes artifacts DataFrame for
    Research Question #3: In which pipeline sections or pipeline directives are artifacts most frequently and least frequently archived?
    :param df:
    """
    # Research Question #3: In which pipeline sections or pipeline directives are artifacts most frequently and least frequently archived?
    df_sections_raw = df.drop(['Extension', 'fingerprint', 'onlyIfSuccessful'], axis=1)
    df_sections = df.groupby('ParentSection')['Occurrence'].count().reset_index()
    df_sections.columns = ['Section', 'NumArtifacts']
    df_sections['Percentage'] = round(100 * df_sections['NumArtifacts'] / df_sections['NumArtifacts'].sum(), 1)
    df_sections.sort_values(by='NumArtifacts', inplace=True, ascending=False)
    df_sections.reset_index(inplace=True, drop=True)
    logger.debug('\nRQ#3:\n%s', df_sections)

    rq3_write_to_csv(df_sections_raw, df_sections)
    rq3_chart_data(df_sections)


def rq4_write_to_csv(df_extensions_raw, df_extensions, others_str):
    """
    Function writes data for research question 4 to csv files
    :param df_extensions_raw:
    :param df_extensions:
    :param others_str:
    """
    csv_file = 'research_question_4_artifacts_extensions.csv'
    csv_q4_header = [['Research Question #4: Which file extensions are most frequently and least frequently archived?(.exe, .jar, everything, etc.)'],
                     ['Note: '],
                     ['When analyzing 200 Jenkinsfiles, there are many extension types which occur less than 3% of the time.'],
                     ['Here is the list of those extensions: ' + others_str],
                     ['To prevent these from overshadowing other prominent extension types, they were grouped into one extension labeled Other,'],
                     ['and their occurrences were averaged. You will see this in the first table below. To see them ungrouped, look at the 2nd table below.'],
                     ['Answer: ']]
    csv_parsed_data_header = [['\n'], ['Jenkinsfile Parsed Data for Artifacts and Extensions']]
    # Write RQ4 Header to CSV file
    with open(csv_file, 'w+') as analysisFile:
        cw = csv.writer(analysisFile, dialect='excel', lineterminator='\n')
        cw.writerows(csv_q4_header)

    # Write DataFrame to CSV file
    df_extensions.to_csv(csv_file, mode='a', header='false', sep=',', na_rep='', index=False)

    # Write Parsed Data Header to CSV file
    with open(csv_file, 'a') as analysisFile:
        cw = csv.writer(analysisFile, dialect='excel', lineterminator='\n')
        cw.writerows(csv_parsed_data_header)

    # Write DataFrame to CSV file
    df_extensions_raw.to_csv(csv_file, mode='a', header='false', sep=',', na_rep='', index=False)
    logger.info('Results written in /src folder to \'%s\' for \n\t\t\t\t\tResearch Question #4 Which file extensions are most frequently and least frequently archived?(.exe, '
                '.jar, everything, etc.)', csv_file)


def rq4_chart_data(df_extensions):
    """
    Function charts rq4 data to bar graph and pie chart
    :param df_extensions:
    """
    # Bar chart RQ4: Number of Artifacts per Extension
    ax = df_extensions.plot(kind='bar',
                            title="RQ4: Number of Artifacts Archived Per Extension",
                            x='Extension',
                            y='NumArtifacts',
                            rot=0,
                            legend=False,
                            fontsize=12)
    ax.set_xlabel("Extension", fontsize=12)
    ax.set_ylabel("Number of Archived Artifacts", fontsize=12)

    # Annotate bar graph with values of each bar
    x_offset = -0.10
    y_offset = 0.8
    for p in ax.patches:
        b = p.get_bbox()
        val = "{:.0f}".format(b.y1 + b.y0)
        ax.annotate(val, ((b.x0 + b.x1) / 2 + x_offset, b.y1 + y_offset))
    plt.show()

    # Pie Chart Number and Percentage of Artifacts Archived per Extension
    values = list(df_extensions['NumArtifacts'])
    labels = list(df_extensions['Extension'])
    plt.pie(values,
            labels=values,
            autopct='%.1f%%',
            labeldistance=1.1,
            counterclock=False)
    plt.title('RQ4: Number and Percentage of Artifacts Archived Per Extension')
    plt.legend(labels, loc="lower right", fontsize=9)
    plt.show()


def analyze_research_question_4_artifacts_extensions(df):
    """
    Function processes artifacts DataFrame for
    Research Question #4: Which file extensions are most frequently and least frequently archived?(.exe, .jar, everything, etc.)
    :param df:
    """
    # Research Question #4: Which file extensions are most frequently and least frequently archived?(.exe, .jar, everything, etc.)
    df_extensions_raw = df.groupby(['Extension'])['Occurrence'].count().reset_index()
    df_extensions_raw.columns = ['Extension', 'NumArtifacts']
    df_extensions_raw.sort_values(by='NumArtifacts', inplace=True, ascending=False)
    df_extensions_raw['Percentage'] = round(100 * df_extensions_raw['NumArtifacts'] / df_extensions_raw['NumArtifacts'].sum(), 1)
    df_extensions = df_extensions_raw.copy(deep=True)

    # Identify all extension types that occur less than 3% of the time
    others_list = list(df_extensions.loc[df_extensions['Percentage'] < 3.0, 'Extension'])
    others_str = ", ".join(others_list)
    # Group these extensions with frequency < 3% together as 'Other', average(mean) their occurrences/frequency as 1 extension type ('Other') to properly highlight the more
    # frequent extensions
    df_extensions.loc[df_extensions['Percentage'] < 3.0, 'Extension'] = 'Other'
    df_extensions = df_extensions.groupby('Extension')['NumArtifacts'].mean().astype(int).reset_index()
    df_extensions['Percentage'] = round(100 * df_extensions['NumArtifacts'] / df_extensions['NumArtifacts'].sum(), 1)
    df_extensions.sort_values(by='NumArtifacts', inplace=True, ascending=False)
    logger.debug('\nRQ#4:\n%s', df_extensions_raw)
    logger.debug('\nRQ#4:\n%s', df_extensions)
    logger.debug('Other: extensions with frequency less than 3 percent of the time: %s', others_list)

    rq4_write_to_csv(df_extensions_raw, df_extensions, others_str)
    rq4_chart_data(df_extensions)


def rq5_write_to_csv(df_fingerprint_raw, df_fingerprint_tf):
    """
    Function writes data for research question 5 to csv files
    :param df_fingerprint_tf: dataframe with number and percentage of artifacts that have fingerprint set to true and false
    :param df_fingerprint_raw:
    """
    csv_file = 'research_question_5_fingerprint_tf.csv'
    csv_q5_header = [['Research Question #5: What percentage of archived artifacts are archived with a fingerprint?'],
                     ['Answer: ']]
    csv_parsed_data_header = [['\n'], ['Jenkinsfile Parsed Data for Artifacts and Fingerprints']]
    # Write RQ5 Header to CSV file
    with open(csv_file, 'w+') as analysisFile:
        cw = csv.writer(analysisFile, dialect='excel', lineterminator='\n')
        cw.writerows(csv_q5_header)

    # Write DataFrame to CSV file
    df_fingerprint_tf.to_csv(csv_file, mode='a', header='false', sep=',', na_rep='', index=False)

    # Write Parsed Data Header to CSV file
    with open(csv_file, 'a') as analysisFile:
        cw = csv.writer(analysisFile, dialect='excel', lineterminator='\n')
        cw.writerows(csv_parsed_data_header)

    # Write DataFrame to CSV file
    df_fingerprint_raw.to_csv(csv_file, mode='a', header='false', sep=',', na_rep='', index=False)
    logger.info('Results written in /src folder to \'%s\' for \n\t\t\t\t\tResearch Question #5: What percentage of archived artifacts are archived with a fingerprint?', csv_file)


def rq6_write_to_csv(df_fingerprint_raw, df_fingerprint_extension):
    """
    Function writes data for research question 6 to csv files
    :param df_fingerprint_extension: dataframe with number and percentage of artifacts groupedby fingerprint and extension
    :param df_fingerprint_raw:
    """
    csv_file = 'research_question_6_fingerprint_extension.csv'
    csv_q6_header = [['Research Question #6: Which archived artifact file extensions are most frequently and least frequently fingerprinted?'],
                     ['Answer: ']]
    csv_parsed_data_header = [['\n'], ['Jenkinsfile Parsed Data for Artifacts, Fingerprints and Extensions']]
    # Write RQ6 Header to CSV file
    with open(csv_file, 'w+') as analysisFile:
        cw = csv.writer(analysisFile, dialect='excel', lineterminator='\n')
        cw.writerows(csv_q6_header)

    # Write DataFrame to CSV file
    df_fingerprint_extension.to_csv(csv_file, mode='a', header='false', sep=',', na_rep='', index=False)

    # Write Parsed Data Header to CSV file
    with open(csv_file, 'a') as analysisFile:
        cw = csv.writer(analysisFile, dialect='excel', lineterminator='\n')
        cw.writerows(csv_parsed_data_header)

    # Write DataFrame to CSV file
    df_fingerprint_raw.to_csv(csv_file, mode='a', header='false', sep=',', na_rep='', index=False)
    logger.info('Results written in /src folder to \'%s\' for \n\t\t\t\t\tResearch Question #6: Which archived artifact file extensions are most frequently and least frequently '
                'fingerprinted?', csv_file)


def rq5_chart_data(df_fingerprint_tf):

    """
    Function charts rq5 data to bar graph and pie chart
    :param df_fingerprint_tf:
    """
    # Bar chart RQ5: Number of Artifacts Archived Fingerprinted
    ax = df_fingerprint_tf.plot(kind='bar',
                                title="RQ5: Number of Artifacts Archived that are Fingerprinted",
                                x='fingerprint',
                                y='NumArtifacts',
                                rot=0,
                                legend=False,
                                fontsize=12)
    ax.set_xlabel("Extension", fontsize=12)
    ax.set_ylabel("Number of Archived Artifacts", fontsize=12)

    # Annotate bar graph with values of each bar
    x_offset = -0.10
    y_offset = 0.8
    for p in ax.patches:
        b = p.get_bbox()
        val = "{:.0f}".format(b.y1 + b.y0)
        ax.annotate(val, ((b.x0 + b.x1) / 2 + x_offset, b.y1 + y_offset))
    plt.show()

    # Pie Chart RQ5: Number and Percentage of Archived Artifacts Fingerprinted
    values = list(df_fingerprint_tf['NumArtifacts'])
    labels = list(df_fingerprint_tf['fingerprint'])
    plt.pie(values,
            labels=values,
            shadow=False,
            autopct='%.1f%%',
            labeldistance=1.1)
    plt.title('RQ5: Number and Percentage of Archived Artifacts that are Fingerprinted')
    plt.legend(labels, loc=4)
    plt.show()


def rq6_chart_data(df_fingerprint_extension):

    """
    Function charts rq5 data to bar graph and pie chart
    :param df_fingerprint_extension:
    """
    # Bar chart RQ6: Number of Artifacts Archived Fingerprinted Per Extension
    ax = df_fingerprint_extension.plot(kind='bar',
                                       title="RQ6: Number of Artifacts Archived Fingerprinted Per Extension",
                                       x='Extension',
                                       y='NumArtifacts',
                                       rot=0,
                                       legend=False,
                                       fontsize=12)
    ax.set_xlabel("Extension", fontsize=12)
    ax.set_ylabel("Number of Archived Artifacts", fontsize=12)

    # Annotate bar graph with values of each bar
    x_offset = -0.10
    y_offset = 0.8
    for p in ax.patches:
        b = p.get_bbox()
        val = "{:.0f}".format(b.y1 + b.y0)
        ax.annotate(val, ((b.x0 + b.x1) / 2 + x_offset, b.y1 + y_offset))
    plt.show()

    # Pie Chart RQ6: Number and Percentage of Archived Artifacts Fingerprinted Per Extension
    values = list(df_fingerprint_extension['NumArtifacts'])
    labels = list(df_fingerprint_extension['Extension'])
    plt.pie(values,
            labels=values,
            counterclock=False,
            autopct='%.1f%%',
            pctdistance=.7,
            labeldistance=1.1)
    plt.title('RQ6: Number and Percent of Archived Artifacts Fingerprinted Per Extension')
    plt.legend(labels, loc=3, fontsize=10)
    plt.show()


def analyze_research_question_56_artifacts_fingerprints(df):
    """
    Function processes artifacts DataFrame for
    Research Question #5: What percentage of archived artifacts are archived with a fingerprint?
    Research Question #6: Which archived artifact file extensions are most frequently and least frequently fingerprinted?
    :param df:
    """

    # Research Question #5 and #6: What percentage of archived artifacts are archived with a fingerprint? Which archived artifact file extensions are most frequently and least
    # frequently fingerprinted?
    df_fingerprint_raw = df.drop(['Artifact', 'onlyIfSuccessful', 'ParentSection', 'SectionName'], axis=1)
    logger.debug('\nRQ#56:\n%s', df_fingerprint_raw)

    # Research Question #5 What percentage of archived artifacts are archived with a fingerprint? tf is for true/false
    df_fingerprint_tf = df_fingerprint_raw.drop(['RepoNum', 'Username', 'RepositoryName', 'Extension'], axis=1)
    df_fingerprint_tf = df_fingerprint_tf.groupby('fingerprint').size().reset_index()
    df_fingerprint_tf.columns = ['fingerprint', 'NumArtifacts']
    df_fingerprint_tf['Percentage'] = round(100 * df_fingerprint_tf['NumArtifacts'] / df_fingerprint_tf['NumArtifacts'].sum(), 1)
    # logger.debug(df_fingerprint_tf.set_index('fingerprint').loc["false", "Percentage"])
    logger.debug('\nRQ#5:\n%s', df_fingerprint_tf)

    # Research Question #6: Which archived artifact file extensions are most frequently and least frequently fingerprinted?
    df_fingerprint_extension = df_fingerprint_raw.drop(['RepoNum', 'Username', 'RepositoryName'], axis=1)
    df_fingerprint_extension = df_fingerprint_extension.groupby(['fingerprint', 'Extension']).size().reset_index()
    df_fingerprint_extension.columns = ['fingerprint', 'Extension', 'NumArtifacts']
    df_fingerprint_extension.sort_values(['fingerprint', 'NumArtifacts'], ascending=[False, False], inplace=True)
    df_fingerprint_extension.reset_index(inplace=True, drop=True)
    df_fingerprint_extension = df_fingerprint_extension[df_fingerprint_extension['fingerprint'] == 'true']
    df_fingerprint_extension['Percentage'] = round(100 * df_fingerprint_extension['NumArtifacts'] / df_fingerprint_extension['NumArtifacts'].sum(), 1)
    # Filter out values that occur less than 2% of the time
    df_fingerprint_extension = df_fingerprint_extension[df_fingerprint_extension['Percentage'] >= 2.0]
    df_fingerprint_extension.reset_index(inplace=True, drop=True)
    df_fingerprint_extension['Percentage'] = round(100 * df_fingerprint_extension['NumArtifacts'] / df_fingerprint_extension['NumArtifacts'].sum(), 1)
    logger.debug('\nRQ#6:\n%s', df_fingerprint_extension)

    rq5_write_to_csv(df_fingerprint_raw, df_fingerprint_tf)
    rq6_write_to_csv(df_fingerprint_raw, df_fingerprint_extension)

    rq5_chart_data(df_fingerprint_tf)
    rq6_chart_data(df_fingerprint_extension)


def analyze_research_questions_artifacts():
    """
    Function retrieves Jenkinsfiles, parses it, and analyzes the data to answer:
    Research Question #3: In which pipeline sections or pipeline directives are artifacts most frequently and least frequently archived?
    Research Question #4: Which file extensions are most frequently and least frequently archived?(.exe, .jar, everything, etc.)
    Research Question #5: What percentage of archived artifacts are archived with a fingerprint?
    Research Question #6: Which archived artifact file extensions are most frequently and least frequently fingerprinted?
    """

    logger.info('Analyzing Jenkinsfiles for Research Questions:\n#3: In which pipeline sections or pipeline directives are artifacts most frequently and least frequently '
                'archived?\n#4: Which file extensions are most frequently and least frequent archived?(.exe, .jar, everything, etc.)\n#5: '
                'What percentage of archived artifacts are archived with a fingerprint?')

    # Create DataFrame to store all data
    df_headers = ['RepoNum', 'Username', 'RepositoryName', 'Artifact', 'Extension', 'fingerprint', 'onlyIfSuccessful', 'ParentSection', 'SectionName', 'Occurrence']
    df = project_utils.create_df(df_headers)

    # Query for GitHub Jenkinsfile search ('pipeline' is used because our focus is on declarative pipeline syntax): TODO Change num_results as per your preference
    query = "filename:jenkinsfile q=pipeline archiveartifacts"
    num_results = 200

    repo_data = search_and_download_jenkinsfiles(query, num_results)
    logger.info('Results received from search: %s', repo_data)

    # For each repo from the search results, parse the Jenkinsfile for data on 'archiveArtifacts', and store it for analysis
    repo_num = 0
    total_num_artifacts = 0
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

        # Parse 'archiveArtifacts' data from Jenkinsfile
        artifacts_data, num_artifacts = parse_archiveArtifacts(jenkinsfile_path)

        # Skip repositories that don't use typical declarative pipeline syntax or cause parsing errors
        if artifacts_data is None:
            repo_num -= 1
            continue

        total_num_artifacts += num_artifacts

        # Store parsed data in DataFrame for analyzing
        for iteration, data in enumerate(artifacts_data):
            artifact = data['Artifact']
            extension = data['Extension']
            fingerprint = data['fingerprint']
            onlyIfSuccessful = data['onlyIfSuccessful']
            parent_section = data['ParentSection']
            section_name = data['SectionName']
            occurrence = data['Occurrence']

            # repo_num_str = str(repo_num) if iteration == 0 else ''
            repo_num_str = str(repo_num)

            # Add parsed data to DataFrame
            df_headers = ['RepoNum', 'Username', 'RepositoryName', 'Artifact', 'Extension', 'fingerprint', 'onlyIfSuccessful', 'ParentSection', 'SectionName', 'Occurrence']
            new_row = [[repo_num_str, username, repo_name, artifact, extension, fingerprint, onlyIfSuccessful, parent_section, section_name, occurrence]]
            df = project_utils.add_row_to_df(df, df_headers, new_row)

    logger.info('Total Number of Repos Analyzed: %s', repo_num)
    logger.info('Total Number of Artifacts: %s', total_num_artifacts)
    avg_artifacts_per_repo = round((total_num_artifacts/repo_num), 2)
    logger.info('Average Number of Artifacts Per Repo: %s', avg_artifacts_per_repo)

    csv_file = 'research_question_artifacts_raw_data.csv'
    # Write DataFrame to CSV file
    df.to_csv(csv_file, header='false', sep=',', na_rep='', index=False)
    logger.info('Raw parsed data on artifacts written in /src folder to \'%s\'', csv_file)

    analyze_research_question_3_artifacts_sections(df)
    analyze_research_question_4_artifacts_extensions(df)
    analyze_research_question_56_artifacts_fingerprints(df)

    return csv_file


def main():

    configure_logger('project.log', logging.DEBUG)
    authenticate_github_object()

    # Research Question #1: How does the number of triggers in a pipeline correlate with the number of stages in the pipeline?
    analyze_research_question_triggers_stages()

    # Research Question #2
    analyze_research_question_tools()

    # Research Questions #3, 4, 5, 6 on 'archiveArtifacts'
    analyze_research_questions_artifacts()


if __name__ == '__main__':
    main()
