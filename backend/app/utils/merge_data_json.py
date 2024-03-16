import os
import json
import glob
from convert_rag_format import extract_role

path = '/data/user04/playground/alex_viz/backend/app/data/new_computer_fraud'

def change_role_name(role):
    if role == 'defense':
        return 'defendant_opinion'
    elif role == 'prosecution':
        return 'prosecutor_opinion'

def split_open_ai(element):
    row = []
    target = element['openai_response'].replace('\n','')
    target_lst = target.split('$$$')
    for sent in target_lst:
        if 'role' in sent:
            role_str = extract_role(sent)
            role_result = change_role_name(role_str)
            row.append(role_result)
        elif 'argument' in sent:
            arg_str = " ".join(sent.split(':')[1:]).strip()
            row.append(arg_str)
    return row

def check_duplicate(total_data):
    id_lst = []
    final_lst = []
    for element in total_data:
        if element['case_id'] not in id_lst:
            id_lst.append(element['case_id'])
            final_lst.append(element)
        else:
            pass
    print(f"Total data: {len(total_data)}")
    return final_lst

def make_one_json(total_data):
    path = r'/data/user04/playground/alex_viz/backend/app/data'
    fname = '0313_new_computer_fraud.json'
    fpath = os.path.join(path, fname)
    with open(fpath, 'w', encoding='utf-8') as f:
        json.dump(total_data, f, ensure_ascii=False, indent=4)

def merge_json():
    total_data = []
    files = glob.glob(f"{path}/*.json")
    for file in files:
        with open(file, 'r', encoding='utf-8-sig') as f:
            data = json.load(f)
            for element in data:
                target = split_open_ai(element)
                element['opinion_result'] = target
                total_data.append(element)
    final_lst = check_duplicate(total_data)
    print(f"final_lst : {len(final_lst)}")
    make_one_json(final_lst)
    # return total_data
if __name__ == "__main__":
    merge_json()