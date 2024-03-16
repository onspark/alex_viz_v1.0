
def save_json(data: dict, file_name_prefix: str = 'INIT'):
    import json 
    from datetime import datetime
    
    #get timestamp
    timestamp = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    
    with open(f'app/data/out/{timestamp}_{file_name_prefix}.json', 'w') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


def save_json_db(data: dict, file_name_prefix: str = 'SC'):
    import json 
    from datetime import datetime
    
    #get timestamp
    timestamp = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    
    with open(f'app/data/chroma_result/{timestamp}_{file_name_prefix}.json', 'w') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)