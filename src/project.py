import logging
import project_utils

# TODO Repository search for Jenkinsfile + other keywords


def rq_trigger_to_num_stages():
    triggers = ['cron', 'pollSCM', 'upstream']
    triggers_found = []
    num_stages = 0
    with open('testjenkinsfile2') as jenkinsfile:
        for line in jenkinsfile:
            line = line.strip('\n')
            # print(line)
            if any(trigger in line for trigger in triggers):
                triggers_found.append(line)
            if 'stage' in line:
                num_stages += 1
    num_stages -= 1
    print(triggers_found, ' ', num_stages)


# logging configurations
""" LOGGING LEVELS 
DEBUG	Detailed information, typically of interest only when diagnosing problems.
INFO	Confirmation that things are working as expected.
WARNING	An indication that something unexpected happened, or indicative of some problem in the near future (e.g. ‘disk space low’). The software is still working as expected.
ERROR	Due to a more serious problem, the software has not been able to perform some function.
CRITICAL	A serious error, indicating that the program itself may be unable to continue running.
"""
LOG_FILENAME = 'project.log'
logger = logging.getLogger('project')
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(levelname)s:%(filename)s: %(message)s')

file_handler = logging.FileHandler(LOG_FILENAME)
stream_handler = logging.StreamHandler()
file_handler.setFormatter(formatter)
stream_handler.setFormatter(formatter)

logger.addHandler(file_handler)
logger.addHandler(stream_handler)

# logging.basicConfig(filename=None, level=logging.DEBUG,
#                     format='%(levelname)s:%(name)s: %(message)s')

project_utils.create_df()
records = {'john': 55, 'tom': 66}
logger.debug('Records: %s', records)

rq_trigger_to_num_stages()
