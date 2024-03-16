import re

# Expand defrules
def expand_defrule(defrule, defrule_ids):
    # Split the defrule into parts
    parts = defrule.split('=>')
    expanded_parts = []
    for part in parts:
        negation = '-' if part.startswith('-') else ''
        part_id = part.lstrip('-')
        # Check if the part is a defrule reference
        if part_id in defrule_ids or negation + part_id in defrule_ids:
            # If it is a reference, get the referenced defrule and expand it
            referenced_defrule = defrule_ids.get(part_id) or defrule_ids.get(negation + part_id)
            # Recursively expand the referenced defrule
            expanded_part = expand_defrule(referenced_defrule, defrule_ids)
            if negation:
                expanded_parts.append(f"-({expanded_part})")
            else:
                expanded_parts.append(expanded_part)
        else:
            # If not a reference, just add the part as it is
            expanded_parts.append(negation + part_id)
    return '=>'.join(expanded_parts)

def convert_ids_to_labels(defrule, node_label):
    # Convert node IDs in the defrule to their corresponding labels
    defrule_with_labels = defrule
    for id, label in node_label.items():
        # Escape special regex characters in id if any
        escaped_id = re.escape(id)
        # Replace all occurrences of the id with its label
        defrule_with_labels = re.sub(r'\b{}\b'.format(escaped_id), label, defrule_with_labels)
    return defrule_with_labels

# Adjust the process_and_expand_defrules function to include the updated label conversion
def process_and_expand_defrules(defrule_ids, defrule_to_warrant, node_label):
    # Merge into a single dictionary
    warrant_to_defrule = {
        warrant: {'defrule_id': defrule_id, 'defrule': defrule}
        for defrule, warrant in defrule_to_warrant.items()
        for defrule_id, defrule_expression in defrule_ids.items()
        if defrule == defrule_expression
    }

    # Expand defrules for each warrant and convert node IDs to labels
    for warrant, info in warrant_to_defrule.items():
        expanded_defrule = expand_defrule(info['defrule'], defrule_ids)
        info['defrule'] = expanded_defrule
        info['defrule_in_label'] = convert_ids_to_labels(expanded_defrule, node_label)

    return warrant_to_defrule

def convert_node_ids_to_labels(nodes, defeasible_rules, defrule_to_warrant):
    '''
    node_labels: dict of node_id: node_label
    defeasible_rules: list of defeasible rules
    defrule_to_warrant: dict of defrule: warrant
    '''
    node_labels = {node["node_id"]:node["label"] for node in nodes}
    defrule_ids = {f"d{idx+1}":str(defrule) for idx,defrule in enumerate(defeasible_rules)} # Should be in order
    warrant_to_defrule_expanded = process_and_expand_defrules(defrule_ids, defrule_to_warrant, node_labels)
    # print(warrant_to_defrule_expanded)
    try:    
        for node_id, node_label in node_labels.items():
            if node_id.startswith("w"):
                node_labels[node_id] = warrant_to_defrule_expanded[node_id]['defrule_in_label']
                
        return node_labels
    except Exception as e:
        raise ValueError(f"Error in converting node ids to labels: {e}")

if __name__ == "__main__":
    
    nodes = [{'node_id': 'c00001', 'node_type': 'claim', 'role': 'defendant', 'text': '(피고인은 사기 범행에 공모 또는 가담하지 않았다.)', 'label': 'C_01'}, {'node_id': '-c00001', 'node_type': 'claim', 'role': 'prosecution', 'text': '피고인은 자신의 행위가 보이스피싱 사기 범행에 가담하는 것임을 미필적으로라도 인식하면서 이를 용이한 채 성명불상의 보이스피싱 조직원들과 순차적 또는 암묵적 의사결합 아래 피해자들이 송금한 돈을 체크카드를 이용하여 인출하여 위 성명불상자에게 송금하거나 피해자들로부터 피해금을 교부받아 위 성명불상자에게 전달하는 등 사기 범행에 대한 본질적인 기여를 하였다고 봄이 상당하다.', 'label': 'C_02'}, {'node_id': 'd00001', 'node_type': 'datum', 'role': 'defendant', 'text': '피고인은 (보이스피싱에 사용된 현금을 수거하였다.)', 'label': 'D_01'}, {'node_id': 'w00001', 'node_type': 'warrant', 'role': 'defendant', 'text': '피고인은 피고인이 수거한 현금이 보이스피싱 사기 범행으로 인한 피해금이라는 인식이 없었다고 주장한다.', 'label': 'W_01'}, {'node_id': 'd00002', 'node_type': 'datum', 'role': 'defendant', 'text': '성명불상자로부터 대출이 될 떄까지 다른 일거리를 주겠다는 제안을 받고, 이를 수락하여, 인출액의 3%를 받기로 하고 편의점 택배로 체크카드를 받아서 현금인출기에서 돈을 인출하여 무통장 송금하는 일을 하기로 하였다.', 'label': 'D_02'}, {'node_id': 'w00002', 'node_type': 'warrant', 'role': 'defendant', 'text': '(피고인은 보이스피싱 조직원에게 지시를 받아 행동한 것일 뿐 사기에 가담할 의도는 없었다.)', 'label': 'W_02'}, {'node_id': 'd00003', 'node_type': 'datum', 'role': 'prosecution', 'text': '피해자로부터 현금을 교부받을 때 피해자에게 피고인의 본명을 숨기고 AD대리라고 거짓 소개하였다.', 'label': 'D_03'}, {'node_id': 'w00003', 'node_type': 'warrant', 'role': 'prosecution', 'text': '(피해자에게 본명을 고의적으로 숨기고 거짓 소개를 하면서 자신의 행위가 범행이라는 인식이 있었다.)', 'label': 'W_03'}, {'node_id': 'd00004', 'node_type': 'datum', 'role': 'prosecution', 'text': '피고인은 성명불상자로부터 타인 명의의 체크카드를 10여개를 편의점 택배의 방법으로 수령하였고, 성명불상자로부터 텔레그램을 이용하여 비밀번호를 전달받아 현금을 인출하여 성명불상자가 알려준 회사나 외국인 명의 계좌로 100만원씩 무통장 입금하였고, 성명불상자의 지시에 따라 수령한 체크카드를 버리기도 하였으며', 'label': 'D_04'}, {'node_id': 'w00004', 'node_type': 'warrant', 'role': 'prosecution', 'text': '(피고인이 성명불상자로부터 체크카드를 선불하라는 등 이례적인 요청에 응하며 그의 행위가 범행이라는 인식이 있었다)', 'label': 'W_04'}, {'node_id': 'd00005', 'node_type': 'datum', 'role': 'prosecution', 'text': '(피해금이라는 인식이 있었다.)', 'label': 'D_05'}, {'node_id': 'w00005', 'node_type': 'warrant', 'role': 'prosecution', 'text': '(수거한 현금이 미필적으로나마 피해금이라는 인식이 있었으므로 사기범행에 가담하였다.)', 'label': 'W_05'}, {'node_id': 'd00006', 'node_type': 'datum', 'role': 'prosecution', 'text': '(조직원의 제안에 응하였다.)', 'label': 'D_06'}, {'node_id': 'w00006', 'node_type': 'warrant', 'role': 'prosecution', 'text': '(조직원의 제안에 응하여 본질적으로 범행에 기여하였으므로 사기범행에 가담하였다)', 'label': 'W_06'}]
    
    defrule_ids = {
        'd1': 'd00001=>c00001', 'd2': 'd00002=>c00001', 'd3': 'd00005=>-c00001',
        'd4': 'd00006=>-c00001', 'd5': 'd00003=>-d1', 'd6': 'd00004=>-d1'
    }
    
    defeasible_rules = ['d00001=>c00001', 'd00002=>c00001', 'd00005=>-c00001', 'd00006=>-c00001', 'd00003=>-d1', 'd00004=>-d1'] 
    
    defrule_to_warrant = {'d00001=>c00001': 'w00001', 'd00002=>c00001': 'w00002', 'd00005=>-c00001': 'w00005', 'd00006=>-c00001': 'w00006', 'd00003=>-d1': 'w00003', 'd00004=>-d1': 'w00004'}
    # Process and expand defrules
        
    nodes = convert_node_ids_to_labels(nodes, defeasible_rules, defrule_to_warrant)
    print(nodes)