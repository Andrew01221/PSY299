
import pandas as pd
import numpy as np
import scipy.stats as st
from transformers import pipeline
import math

def get_column_name_from_index(df, index):
    if 0 <= index < len(df.columns):
        return df.columns[index]
    else:
        raise IndexError("Column index out of range")

def create_global_preference_list(y1, x1, x2, dataframe, num_rows):
    temp_list = []
    global_preference_list = []

    for j in range(y1,num_rows + y1):
        if j not in list_of_removals:
            for i in range(x1, x2 + 1):
                temp_list.append(dataframe.at[j,get_column_name_from_index(dataframe,i)])
            global_preference_list.append(temp_list)
            temp_list=[]
    return global_preference_list

def create_preference_matrix():
    # automate this process
    items = int(input("Please input the number of items that the participants must rank: "))
    contents = []
    rows = []
    cols = []
    k = 0 

    for i in range(items):
        rows.append(str(i))
        cols.append(str(i))
        sub_contents = []
        for j in range(items):
            if j == k:
                sub_contents.append("imp")
            else:
                sub_contents.append(0)
        contents.append(sub_contents)
        k = k + 1
    matrix = pd.DataFrame(np.array(contents), index = rows, columns = cols)
    return matrix, items

# Model for determining if an item is food 
classifier = pipeline('zero-shot-classification', model='facebook/bart-large-mnli')

candidate_labels = ['food', 'non-food']

def is_ingestible(item):
    result = classifier(item, candidate_labels)
    # Check the label with the highest score
    top_label = result['labels'][0]
    return top_label == 'food'

# print(is_ingestible("orange")) WARNING THE AI MODEL THINKS THAT THIS IS NOT INGESTIBLE SO WE NEED TO DOUBLE CHECK WITH IT

# End for model for determining if an item is food 

# 1. Convert Qualtrics data into table

path = "Official Test Results.csv"

data = pd.read_csv(path)

# 1. End converting Qualtrics data into table


# 2. Find eligible data (this code will be omitted on GitHub)
# Filter for consent
consent_column_name = str(input("Please input the name of the column in which the consent data are contained: "))

consent_column = data[consent_column_name]

list_of_removals = []

start_consent_row_number = int(input("Please input the number of the first row minus two in that column: "))
end_consent_row_number = int(input("Please input the number of the last row minus two in that column: "))

for i in range(start_consent_row_number, end_consent_row_number + 1): 
    if int(consent_column[i]) == 2:
        list_of_removals.append(i)

# End filter for consent

# Filter for food items 

attention_column_name = str(input("Please input the name of the column in which the attention data are contained: "))

attention_column = data[attention_column_name]


start_attention_row_number = int(input("Please input the number of the first row minus two in that column: "))
end_attention_row_number = int(input("Please input the number of the last row minus two in that column: "))

food_removal = []

for i in range(start_attention_row_number, end_attention_row_number + 1):
    if is_ingestible(str(attention_column[i])) == False and i not in list_of_removals:
        list_of_removals.append(i)
        food_removal.append(i)

print("Check to see if the following rows within the Attention column actually do not contain food items:")
print(food_removal)


# End filter for food items 

# Filter for empty responses (only checks one column)
num_rank_set = int(input("Please input the number of rank sets: ")) 
for i in range(num_rank_set):
    response_column_name = str(input("Please input the name of the column in which the response data is contained: "))
    start_response_row_number = int(input("Please input the number of the first row minus two in that column: "))
    end_response_row_number = int(input("Please input the number of the last row minus two in that column: "))
    response_column = data[response_column_name]
    for i in range(start_response_row_number, end_response_row_number + 1):
        try:
            math.isnan(int(response_column[i]))
        except:
            if i not in list_of_removals:
                list_of_removals.append(i)

print("List of removals:")
print(list_of_removals)

data = data.drop(list_of_removals)

# End filter for responses

# End finding eligible data


# 3. Organize choices

# How many sets of ranks

sets_of_ranks = num_rank_set

for k in range(sets_of_ranks):
    y1 = int(input("Please input the number of the highest row minus two that contains a rank value of interest: "))
    x1 = int(data.columns.get_loc(str(input("Please input the name of the column that contains the leftmost rank value of interest: "))))
    x2 = int(data.columns.get_loc(str(input("Please input the name of the column that contains the rightmost rank value of interest: "))))
    rows = int(input(f"Please input the number of rows (Example: 2 to 7 is 6 rows, not 5 rows (regardless of removals)):" ))
    global_preference_list = create_global_preference_list(y1, x1, x2, data, rows)

num_of_people = len(global_preference_list)

preference_matrix, items = create_preference_matrix()

# End organizing choices


# 4. Fit choices into matrix + compute z-scores

for i in range(num_of_people):
    individual_choices = global_preference_list[i]
    for r in range(items):
        for l in range(items):
            if r != l:
                if individual_choices[r] > individual_choices[l]:
                    preference_matrix.at[str(r), str(l)] = float(preference_matrix.at[str(r), str(l)]) + 1

print(preference_matrix)


for r in range(items):
    for l in range(items):
        if r != l:
            preference_matrix.at[str(r), str(l)] = st.norm.ppf(float(preference_matrix.at[str(r), str(l)]) / num_of_people)

print(preference_matrix)

z_score_list = []

for r in range(items):
    average = 0
    for l in range(items):
        if r != l:
            average = preference_matrix.at[str(l), str(r)] + average
    z_score_list.append(average / (items - 1))

# End fitting choices into dataframe + computing z-scores

print(z_score_list)

# 5. Compute scale

scale_list = []

smallest_value = min(z_score_list)

for p in range(items):
   scale_list.append(z_score_list[p] - smallest_value)

print(scale_list)

# End computing scale
