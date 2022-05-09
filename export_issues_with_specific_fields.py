"""Export Jira issues to csv with only requested fields"""
import csv
import json
from flatten_json import flatten
import time
from datetime import datetime
from typing import List, Dict, Any, Optional, Union

from jira import JIRA
import credentials


def _get_value_for_cascading_select_field(field_path: str, issue: Dict[str, Any]) -> str:
    """
    Get value for cascading select list field.
    
    :param field_path: json path to field (from path_to_fields.json)
    :param issue: raw Jira Issue instance
    :return: str with parent and child options separated by -
    """
    # if field is not cascading select list, return
    if '|' not in field_path:
        return ''

    nest = issue
    values = []

    for path_part in field_path.split('.'):
        # check if field level reached
        if '|' in path_part:
            # add parent option
            values.append(nest.get('value'))
            # add child option
            child_option = nest.get('child')
            if child_option:
                values.append(child_option.get('value'))

            break
        nest = nest.get(path_part)

    if len(values) == 2:
        return '-'.join(values)
    elif len(values) == 1:
        return values[0]
    else:
        return ''


def _get_value_for_multiple_choice_field(field_path: str, issue: Dict[str, Any]) -> Optional[str]:
    """
    Get value for multiple select list field
    
    :param field_path: json path to field (from path_to_fields.json)
    :param issue: raw Jira Issue instance
    :return: str with values separated by |
    """

    # if field is not multiple select list, return
    if '..' not in field_path:
        return ''

    nest = issue
    values = []

    for path_part in field_path.split('.'):
        # check if field level reached
        if isinstance(nest, list):
            values = [
                # FIXME works only if value on -1 lvl from field
                nest[i].get('value')
                for i in range(len(nest))
            ]
            break
        if nest:
            nest = nest.get(path_part)
        else:
            return ''
    return '|'.join(values)


def get_field_values(issue: Dict[str, Any], fields: List[str]) -> Optional[list[Union[str, None]]]:
    """
    Get fields value for issue
    :param issue: raw Jira Issue instance
    :param fields: field names from path_to_fields.json
    :return: field values in requested order
    """
    # read field paths from config file
    with open('path_to_fields.json', 'r', encoding='UTF8') as config:
        path_to_fields = json.load(config)

    # flatten raw Issue
    issue_field_values = flatten(issue, separator='.')
    # filter meta values
    filtered_field_values = []

    for field in fields:
        field_path = path_to_fields.get(field)

        # check if field is multiple select list
        if '..' in field_path:
            filtered_field_values.append(
                _get_value_for_multiple_choice_field(field_path, issue)
            )
            continue

        # check if field is cascading select list
        if '|' in field_path:
            filtered_field_values.append(
                _get_value_for_cascading_select_field(field_path, issue)
            )
            continue

        # add field value to final list
        filtered_field_values.append(
            issue_field_values.get(field_path)
        )

    return filtered_field_values


def export_issues(jql: str, fields: List[str]) -> None:
    """
    Export Jira issues to csv by JQL using provided fields.
   
    :param jql: JQL statement
    :param fields: field names from path_to_fields.json
    :return: Create {curr_date}_exported_issues.csv in script directory
    """

    # create connection to Jira
    creds = credential.init_config()
    jira = JIRA(
        options={'server': creds.server_url},
        basic_auth=(creds.username, creds.password)
    )

    curr_date = datetime.now().strftime("%m-%d-%Y-%H-%M-%S")
    page_num = 0
    # Jira REST API uses pagination to provide better perfomance
    # you can specify batch_size here (optimal 50-500)
    batch_size = 100  # > 1!

    with open(f'{curr_date}_exported_issues.csv', 'w', encoding='UTF8') as output:
        writer = csv.writer(output)
        # write header row to file
        writer.writerow(fields)

        # iterate throw pages
        while True:
            # get new page (only requested fields will be returned)
            print(f'exporting {page_num} page..
                  f'\n{page_num * batch_size} exported')
            issues_batch = jira.search_issues(
                jql,
                maxResults=batch_size,
                startAt=page_num * batch_size,
                fields=fields
            )

            for issue in issues_batch:
                # write row to csv with issue field values (one row for each issue)
                writer.writerow(
                    get_field_values(issue=issue.raw, fields=fields)
                )

            # if processed batch size lower than total batch size, then it is the end of export
            if len(issues_batch) < batch_size:
                break
            else:
                page_num += 1
                # you can set pause manually here, but please keep it
                # your Jira administrator will be angry if you don't :)
                time.sleep(batch_size / 500)
    # TODO print current script directory
    print(f'\nExport saved to {curr_date}_exported_issues.csv in script directory')


if __name__ == '__main__':
    print('export stated at: ', datetime.now().strftime("%m/%d/%Y %I:%M:%S %p"))
    # TODO get that params from user input
    jql_request = 'project = TT'
    fields_to_export = [
        'key',
        'status',
        'summary',
        'City',
        'created',
        'updated',
        'issuetype'
    ]
    export_issues(jql_request, fields_to_export)
    print('export ended at: ', datetime.now().strftime("%m/%d/%Y %I:%M:%S %p"))
