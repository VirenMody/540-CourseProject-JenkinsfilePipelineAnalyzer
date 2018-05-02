import pandas as pd
import logging

# Retrieve same logger as defined in project.py
logger = logging.getLogger('project')


df_headers = ['RepositoryName', 'PipelineConfigFile', 'TriggerType', 'TriggerValue', 'NumStages']
df_headers = ['RepositoryName', 'PipelineConfigFile', 'StageName', 'occurrence']

def create_df():
    """
    Function creates Python Pandas DataFrame used to store data from Jenkinsfile analysis
    :return: data_frame: DataFrame
    """
    data_frame = pd.DataFrame(columns=df_headers)
    logger.debug('Created DataFrame')
    return data_frame


def add_row_to_df(df, new_row):
    """
    Function inserts each new row of data found when analyzing Jenkinsfile into the DataFrame
    :param df: old Python Pandas DataFrame
    :param new_row: list of new data
    :return: df: updated
    """
    new_df = pd.DataFrame(new_row, columns=df_headers)
    df = df.append(new_df, ignore_index=True)
    return df