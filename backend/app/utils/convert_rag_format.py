from itertools import combinations
import re
# from app.tests.logger import logger
# # name == main -> use logging
# import logging as logger

def seperator_decision(output_str):
    if '$$$' in output_str:
        return '$$$'
    elif '\n' in output_str:
        return '\n'
    elif '\\n' in output_str:
        return '\\n'

def extract_role(sent_str):
    sent_lst = sent_str.split(':')
    sent_lst = [s.strip() for s in sent_lst]
    return sent_lst[1]

def extract_text_from_lst(sent_lst):
    if len(sent_lst) > 2:
        return ":".join(sent_lst[1:])
    else:
        return sent_lst[1]    

def extract_cwd(target_text, main_claim):
    row_lst = []
    role_str = ""
    for sent in target_text:
        if 'role' in sent:
            role_str = extract_role(sent)
            break
    node_prefix = {"claim": "c", "warrant": "w", "datum": "d"}
    relation_target_prefix = {"claim": "NA", "warrant": "c", "datum": "w"}
    relation_type = {"claim": "NA", "warrant": "support", "datum": "support"}
    warrant_num = 1
    for sent in target_text:
        sent = sent.replace('\n','').strip()
        sent_lst = sent.split(':')
        sent_type = sent_lst[0]
        if sent_type in node_prefix:
            node_id = f"{node_prefix[sent_type]}0000{warrant_num}_tmp"
            relation_target = "NA" if sent_type == "claim" else f"{relation_target_prefix[sent_type]}0000{warrant_num}_tmp"
            row_lst.append({
                "node_id": node_id,
                "node_type": sent_type,
                "role": role_str,
                "text": extract_text_from_lst(sent.split(':')),
                "relation_target": relation_target,
                "relation_type": relation_type[sent_type],
                "main_claim": main_claim
            })
        if sent_type == "datum":
            warrant_num += 1
    return row_lst

def option_2_clear(c_w_d_result_lst, role, main_claim):
    mc_dic = {"defense" : "mc00001", "prosecution" : "-mc00001"}
    for element in c_w_d_result_lst:
        if element['node_type'] == "claim":
            element['relation_target'] = mc_dic[role]
            element['relation_type'] = "support"
            element['main_claim'] = main_claim
        else:
            element['main_claim'] = main_claim
    return c_w_d_result_lst

def option_3_clear(c_w_d_result_lst, main_claim, target_node):
    for element in c_w_d_result_lst:
        if element['node_type'] == "claim":
            element['relation_target'] = target_node['node_id']
            element['relation_type'] = "attack"
            element['main_claim'] = main_claim
        else:
            element['main_claim'] = main_claim
    return c_w_d_result_lst

def extract_mc_claim(text):
    row = []
    for sent in text:
        if 'role' in sent or 'claim' in sent:
            role_str = sent.split(':')[1].strip()
            row.append(role_str)
    return row

def mc_lst_builder(mc_result_lst):
    mc_lst = []
    for i in range(0, len(mc_result_lst), 2):
        row = {
            "node_id": "mc00001" if i == 0 else "-mc00001",
            "node_type": "main_claim",
            "relation_target": "-mc00001" if i == 0 else "mc00001",
            "relation_type": "attack",
            "role": mc_result_lst[i],
            "text": mc_result_lst[i+1]
        }
        mc_lst.append(row)
    return mc_lst


def rag_converter(output_str, action_option, role, target_node=None, main_claim=None) -> list:
    # TODO: Change this to be more dynamic
    try:
        result_dic = {}
        if '### OUTPUT FORMAT ###' in output_str:
            seperate_output_lst = output_str.split("### OUTPUT FORMAT ###")
            seperate_output = seperate_output_lst[1].replace('\n','').strip()
        else:
            seperate_output = output_str.replace('\n','').strip()

        split_str = seperator_decision(seperate_output)
        split_text = seperate_output.split(split_str)

        if action_option == 1:
            mc_result_lst = extract_mc_claim(split_text)
            element_lst = mc_lst_builder(mc_result_lst)
            result_dic['is_root'] = True
            result_dic['nodes'] = element_lst
        elif action_option >= 2:
            c_w_d_result_lst = extract_cwd(split_text, main_claim)
            if action_option == 2:
                option_2_result = option_2_clear(c_w_d_result_lst, role, main_claim)
                result_dic['is_root'] = False
                result_dic['nodes'] = option_2_result
            else:
                option_3_result = option_3_clear(c_w_d_result_lst, main_claim, target_node)
                result_dic['is_root'] = False
                result_dic['nodes'] = option_3_result
        return result_dic
    except Exception as e:
        print(f"Error: {e}")
        logger.debug(f"Error: {e}")
        return {}
    

if __name__ == '__main__':
    output_str1 = """
    id: defendant1 $$$
    role: defendant $$$
    claim: 피고인은 보이스피싱 사기 범행의 실체를 명확히 인지하지 못한 채 성명불상자의 제안을 수락하였으며, 범죄에 이용될 것이라는 의도를 가지고 있지 않았다. 따라서 고의성이 부족하므로 무죄를 주장한다.$$$
    id: prosecution1 $$$
    role: prosecution $$$
    claim: 피고인은 보이스피싱 조직의 '수거책 및 인출책' 역할을 자발적으로 수행하였으며, 체크카드가 범죄에 사용되었음을 인지한 후에도 다시 범행에 가담한 점으로 미루어 볼 때, 분명한 고의가 있었다. 따라서 피고인은 사기 범행에 적극적으로 가담한 것으로 간주되어야 한다.$$$$
    """

    action_option = 3

    output_str2 = """
    id: prosecution1$$$
    role: prosecution $$$
    claim: 피고인은 보이스피싱 조직의 '수거책 및 인출책' 역할을 자발적으로 수행하였다. $$$
    warrant: 피고인이 체크카드가 범죄에 사용됨을 알고 있었음에도 불구하고, 보이스피싱 조직원으로부터 체크카드를 이용한 범죄 계획에 다시 참여할 것을 제안받았을 때 이를 수락한 행위는 피고인의 자발적인 범행 참여를 명백히 보여준다. $$$
    datum: 피고인은 2020. 7. 2.경 성명불상자로부터 "대출을 해주겠다, 체크카드를 보내주면 이자를 인출하는 용도로 사용한다"는 제안을 받고 피고인의 체크카드를 성명불상자에게 넘겨주었으나, 체크카드와 연결된 은행 계좌가 정지되자 체크카드가 범죄에 사용되었음을 인지하였음에도 불구하고, 성명불상자로부터 "택배로 체크카드를 받아 체크카드에 입금된 돈을 인출해주면 인출액의 3%를 주겠다"는 제안을 수락하였다. $$$

    id: prosecution2 $$$
    role: prosecution $$$
    claim: 피고인은 보이스피싱 범행의 실행에 직접적으로 관여하였다. $$$
    warrant: 피고인이 피해자로부터 금원을 직접 수령한 행위는 보이스피싱 범행의 실행단계에 피고인이 직접적으로 관여하였음을 입증한다. $$$
    datum: 피고인은 2020. 7. 24. 17:30경 성명불상자와의 공모에 따라 울산 남구 AG 앞에서 피해자 AF에게 "AD 대리이고 사원번호 AE번이다"라는 취지로 자신을 소개하고 피해자로부터 875만원을 교부받았다. $$$

    id: prosecution3 $$$
    role: prosecution $$$
    claim: 피고인은 보이스피싱 조직과의 공모를 통해 사기 범행에 적극적으로 참여하였다. $$$
    warrant: 피고인이 성명불상자와의 사전 공모를 통해 피해자로부터 금원을 수령하는 역할을 수행한 것은, 보이스피싱 사기 범행에 있어서 피고인의 적극적인 역할 및 공모를 명백히 보여준다. $$$
    datum: 피고인은 성명불상의 보이스피싱 조직원과의 공모에 따라, 2020. 7. 24. 17:30경 울산 남구 AG 앞에서 피해자 AF로부터 875만원을 수령한 사실이 있다. $$$
    """
    role = "prosecution"

    target_node = {"text":"피고인은 보이스피싱 범죄에 대한 명확한 지식이 없었으므로 고의성이 결여되었다는 점을 주장한다.", "node_type":"claim", "node_id":"c00001", "role":"defense"}

    result = rag_converter(output_str2, target_node=target_node, action_option=action_option, role=role, main_claim="피고인은 유죄다")
    print(f"result : {result}")