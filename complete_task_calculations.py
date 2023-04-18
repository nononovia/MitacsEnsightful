import pandas as pd
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
    row.fillna('', inplace=True)
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
        print(combined)
        return True
    else:
        return False


if __name__ == '__main__':

    task_df = pd.read_csv("sample_flattened/flattened_task.csv")

    unique_owner_id = task_df.owner_account_id.unique()
    unique_assignee_id = task_df.assignee_account_id.dropna().unique()

    combined_id = np.concatenate((unique_owner_id, unique_assignee_id))
    id_list = set(combined_id)

    result_df = pd.DataFrame(id_list, columns=['account_id'])

    for index, row in result_df.iterrows():
        this_student_account_id = row['account_id']
        # COMPLETING TASKS
        assigned_tasks_df = task_df[task_df["assignee_account_id"] == this_student_account_id]

        # number of tasks assigned
        result_df.loc[index, 'num_tasks'] = len(assigned_tasks_df)

        # number of points assigned
        num_points = get_points(assigned_tasks_df['workload'])
        result_df.loc[index, 'num_points'] = num_points

        # number of tasks done
        done_task_df = assigned_tasks_df[assigned_tasks_df['status'] == "completed"]
        result_df.loc[index, 'num_tasks_done'] = len(done_task_df)

        # PROJECT MANAGEMENT
        created_tasks_df = task_df[task_df["owner_account_id"] == this_student_account_id]

        # number of tasks created
        result_df.loc[index, 'num_tasks_created'] = len(created_tasks_df)

        # number of tasks created for other students
        created_for_others_df = created_tasks_df[created_tasks_df['assignee_account_id'] != this_student_account_id]
        result_df.loc[index, 'num_tasks_assigned_to_others'] = len(created_for_others_df)

        # number of meetings initiated
        meetings_df = created_tasks_df[created_tasks_df.apply(contains_keyword, args=("meet",), axis=1)]
        result_df.loc[index, 'num_meetings_initiated'] = len(meetings_df)


    print("")
