import pandas as pd
from datetime import datetime
import numpy as np
import re


def get_points(col):
    total_points = 0
    for i in col:
        if i == "low":
            total_points += 1
        elif i == "medium":
            total_points += 2
        else:
            total_points += 4

    return total_points


def contains_keyword(row, keyword):
    # row.fillna('', inplace=True)
    # if not (pd.isnull(row['title'])) and not (pd.isnull(row['description'])):
    #     combined = row['title'] + row['description']
    # elif pd.isna(row['title']):
    #     combined = row['description']
    # elif pd.isna(row['description']):
    #     combined = row['title']
    # else:
    #     combined = ""

    combined = row['title'] + row['description']

    if keyword in combined.lower():
        return True
    else:
        return False


def total_word_count(column):
    count = 0
    for cell in column:
        count += len(cell.split(" "))

    return count


def get_student_level_result(group_id_df, task_df, action_df):
    unique_group_id = group_id_df.group_id.unique()

    result_df = pd.DataFrame()
    for group in unique_group_id:
        student_id_list = group_id_df[group_id_df.group_id == group].account_id
        group_result_df = pd.DataFrame(student_id_list, columns=['account_id'])
        group_result_df['group_id'] = group

        for index, row in group_result_df.iterrows():
            this_student_account_id = row['account_id']
            # COMPLETING TASKS
            assigned_tasks_df = task_df[task_df["assignee_account_id"] == this_student_account_id]

            # number of tasks assigned
            group_result_df.loc[index, 'num_tasks_assigned'] = len(assigned_tasks_df)

            # number of points assigned
            num_points = get_points(assigned_tasks_df['workload'])
            group_result_df.loc[index, 'num_points_assigned'] = num_points

            # number of tasks done
            done_task_df = assigned_tasks_df[assigned_tasks_df['status'] == "completed"]
            group_result_df.loc[index, 'num_tasks_done'] = len(done_task_df)

            # PROJECT MANAGEMENT
            created_tasks_df = task_df[task_df["owner_account_id"] == this_student_account_id]

            # number of tasks created
            group_result_df.loc[index, 'num_tasks_created'] = len(created_tasks_df)

            # number of tasks created for other students
            created_for_others_df = created_tasks_df[created_tasks_df['assignee_account_id'] != this_student_account_id]
            group_result_df.loc[index, 'num_tasks_assigned_to_others'] = len(created_for_others_df)

            # number of meetings initiated
            meetings_df = created_tasks_df[created_tasks_df.apply(contains_keyword, args=("meet",), axis=1)]
            group_result_df.loc[index, 'num_meetings_initiated'] = len(meetings_df)

            # How many times did this student change the status of tasks that are assigned to other people?
            student_action_df = action_df[action_df.account_id == this_student_account_id]
            student_action_others_df = student_action_df[student_action_df['data.assignee_account_id'] != this_student_account_id]
            group_result_df.loc[index, 'num_status_change_for_others'] = len(student_action_others_df)

            # How many times did this student change the status of tasks that are assigned to themselves?
            student_action_df = action_df[action_df.account_id == this_student_account_id]
            student_action_self_df = student_action_df[
                student_action_df['data.assignee_account_id'] == this_student_account_id]
            group_result_df.loc[index, 'num_status_change_for_self'] = len(student_action_self_df)

            # How many task out of all tasks created by this student has task description?
            has_description_df = created_tasks_df[created_tasks_df['description'] != ""]
            group_result_df.loc[index, 'num_task_created_contain_description'] = len(has_description_df)

            # How many words in total are in the description?
            group_result_df.loc[index, 'num_words_in_description'] = total_word_count(has_description_df['description'])

        result_df = pd.concat([result_df, group_result_df], ignore_index=True)

        # group_result_df.to_csv("full_class_result.csv")
    result_df.to_csv("student_level_result.csv")
    return result_df


def get_task_level_result(task_df, action_df):
    task_id = task_df.id.unique()
    meaningful_task_id = []
    # filter out all tasks that has no actions associated with it
    for task in task_id:
        task_action_df = action_df[action_df['data.id'] == task]
        if len(task_action_df) > 0:
            meaningful_task_id.append(task)

    result_df = pd.DataFrame(meaningful_task_id, columns=['task_id'])
    for index, row in result_df.iterrows():
        current_task_id = row["task_id"]
        task_action_df = action_df[action_df['data.id'] == current_task_id]

        task_action_df = task_action_df.sort_values("created_on")
        task_action_df = task_action_df.reset_index()

        # how many times has this task been updated
        result_df.loc[index, "num_actions"] = len(task_action_df)

        # the "status" column is the status the task is moved into
        # how long has this task been in "inProgress" - What if it is in progress for multiple times?
        total_time_in_progress = 0
        num_times_in_progress = 0
        for i, action in task_action_df.iterrows():
            if action['data.status'] == 'inProgress':
                in_progress_timestamp = pd.to_datetime(action['created_on'])
                if (i-1) >= 0:
                    previous_action_timestamp = pd.to_datetime(task_action_df.loc[i-1, "created_on"])
                    time_difference = in_progress_timestamp - previous_action_timestamp
                    total_time_in_progress += time_difference.total_seconds()
                    num_times_in_progress += 1

        result_df.loc[index, "time_in_inProgress"] = total_time_in_progress
        result_df.loc[index, 'num_times_inProgress'] = num_times_in_progress

        total_time_under_review = 0
        num_times_under_review = 0
        for i, action in task_action_df.iterrows():
            if action['data.status'] == 'underReview':
                under_review_timestamp = pd.to_datetime(action['created_on'])
                if (i - 1) >= 0:
                    previous_action_timestamp = pd.to_datetime(task_action_df.loc[i - 1, "created_on"])
                    time_difference = under_review_timestamp - previous_action_timestamp
                    total_time_under_review += time_difference.total_seconds()
                    num_times_under_review += 1

        result_df.loc[index, "time_in_underReview"] = total_time_under_review
        result_df.loc[index, 'num_times_underReview'] = num_times_under_review

        result_df.to_csv("task_level_results.csv")
        return result_df
        # how long has this task been in  "underReview"


def get_group_level_result(group_id_df, student_result_df):
    unique_group_id = group_id_df.group_id.unique()
    result_df = pd.DataFrame()

    for group in unique_group_id:
        group_df = student_result_df[student_result_df['group_id'] == group]
        group_sum = group_df.sum(axis=0)
        result_df = result_df.append(group_sum, ignore_index=True)

    result_df = result_df.drop(columns=['account_id', 'num_tasks_assigned_to_others', 'num_status_change_for_others', 'num_status_change_for_self'])
    result_df.to_csv('group_level_result.csv')
    return result_df


if __name__ == '__main__':
    # task_df = pd.read_csv("sample_flattened/flattened_task.csv")
    # action_df = pd.read_csv("sample_flattened/flattened_activites.csv")
    group_id_df = pd.read_csv("group_id_key.csv")

    task_df = pd.read_csv("full_data/flattened_task.csv")
    action_df = pd.read_csv("full_data/flattened_activites.csv")

    task_df = task_df.fillna("")
    action_df = action_df[action_df.action != "login"]
    action_df = action_df[action_df.action != "click"]
    action_df = action_df[action_df.action != "visit"]
    action_df = action_df[action_df.type != "shared_url"]
    action_df = action_df[action_df.type != "feedback"]

    student_result_df = get_student_level_result(group_id_df, task_df, action_df)
    task_result_df = get_task_level_result(task_df, action_df)
    get_group_level_result(group_id_df, student_result_df)

