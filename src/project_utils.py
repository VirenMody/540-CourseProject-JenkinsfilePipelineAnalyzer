import pandas as pd
import logging

# Retrieve same logger as defined in project.py
logger = logging.getLogger('project')


def create_df(df_headers):
    """
    Function creates Python Pandas DataFrame used to store data from Jenkinsfile analysis
    :param df_headers: list of column headers
    :return: data_frame: DataFrame
    """
    data_frame = pd.DataFrame(columns=df_headers)
    logger.debug('Created DataFrame')
    return data_frame


def add_row_to_df(df, df_headers, new_row):
    """
    Function inserts each new row of data found when analyzing Jenkinsfile into the DataFrame
    :param df: old Python Pandas DataFrame
    :param df_headers: list of column headers
    :param new_row: list of new data
    :return: df: updated
    """
    new_df = pd.DataFrame(new_row, columns=df_headers)
    df = df.append(new_df, ignore_index=True)
    return df


def add_blank_row_to_df(df, df_headers):
    """
    Function adds a blank row to the DataFrame for increased readability
    :param df_headers: list of column headers
    :param df: DataFrame to add row to
    :return: DataFrame with blank row added
    """
    blank_row = [[''] * len(df_headers)]
    new_df = pd.DataFrame(blank_row, columns=df_headers)
    df = df.append(new_df, ignore_index=True)
    return df


def search_by_code(git_hub, my_query, num):
    """
    Function that searches Github code based on the given query and returns the requested number of results
    :param git_hub: authenticated GitHub object
    :param my_query: search query (i.e. java, closed, etc.)
    :param num: number of results to retrieve
    :return: results: tuple with Github search results object, raw url, and repository name with username
    """
    try:
        code_search_result = git_hub.search_code(query=my_query, number=num)
    except Exception as err:
        logger.error("GitHub Connection Error ", exc_info=True)
        raise

    results = []
    for item in code_search_result:
        result_object = item

        try:
            result_url = item.html_url
        except AttributeError as err:
            logger.error("Attribute html_url not found in 'item' object: ", exc_info=True)
            raise

        # Get string with blob hash: ("ref=98234745")
        blob_hash_string = item._uri[4]

        # split string at = and save only the hash value
        blob_hash = blob_hash_string.split('=')[1]
        logger.debug("Github blob hash: %s", blob_hash)

        # create raw URL from repository details and blob hash
        raw_url = "https://raw.githubusercontent.com/" + item.repository.full_name + '/' + blob_hash + '/' + item.path
        logger.debug("raw_url: %s", raw_url)

        results.append((result_object, raw_url, item.repository.full_name))

    return results
