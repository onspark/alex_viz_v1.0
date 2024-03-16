from app.logger import logger
import re

class ArgumentGraph:
    def __init__(self, data, arguments):
        self.data = data
        self.datum_start_num = 1
        self.warrant_start_num = 1
        self.claim_start_num = 1
        self.current_arguments = arguments

    def number_finder(self, node_id_str):
        numbers = re.findall(r'\d+', node_id_str)
        numbers_int = int("".join(numbers))
        return numbers_int

    def argument_counter(self):
        count_dic = {"main_claim" : 0, "claim": 0, "warrant": 0, "datum": 0}
        for element in self.current_arguments['nodes']:
            node_type = element['node_type']
            node_id = element['node_id']
            if node_type in count_dic:
                numbers_int = self.number_finder(node_id)
                if numbers_int > count_dic[node_type]:
                    count_dic[node_type] = numbers_int
        self.datum_start_num = count_dic['datum'] + 1
        self.warrant_start_num = count_dic['warrant'] + 1
        self.claim_start_num = count_dic['claim'] + 1
        #logger.debug(f"self.datum_start_num: {self.datum_start_num}")
        #logger.debug(f"self.warrant_start_num: {self.warrant_start_num}")
        #logger.debug(f"self.claim_start_num: {self.claim_start_num}")

    def generate_label(self, node_type, new_number):
        prefix = {"datum": "D_", "claim": "C_", "warrant": "W_", "main_claim": "MC_"}
        as_aspic_plus = f"{prefix[node_type]}{new_number:02d}"
        label = f"{as_aspic_plus.upper()}"
        return label

    def name_change_dic_generator(self):
        new_node_id_dic = {}
        node_type_prefix = {"main_claim":"mc","datum": "d", "claim": "c", "warrant": "w"}
        logger.info(f"self.data : {self.data}")
        for element in self.data['nodes']:
            old_name = element['node_id']
            node_type = element['node_type']
            target_id = 0
            if node_type == 'datum':
                target_id = self.datum_start_num
                self.datum_start_num += 1
            elif node_type == 'claim':
                target_id = self.claim_start_num
                self.claim_start_num += 1
            elif node_type == 'warrant':
                target_id = self.warrant_start_num
                self.warrant_start_num += 1
            new_name = ""
            if node_type == 'main_claim':
                new_name = old_name
            else:
                new_name = f"{node_type_prefix[node_type]}{target_id:05d}"
            new_node_id_dic[old_name] = new_name
        return new_node_id_dic

    def initialize_nodes_and_edges(self):
        if len(self.current_arguments['nodes']) > 1:
            self.argument_counter()
        
        new_node_id_dic = self.name_change_dic_generator()
        #logger.debug(f"new_node_id_dic : {new_node_id_dic}")
 
        logger.info(f"self.data : {self.data}")

        new_nodes = []
        new_edges = []
        # for node in self.data:
        for node in self.data['nodes']:

            node_type = node['node_type']
            node_id = node['node_id']
            new_name = new_node_id_dic[node_id]
            new_number = self.number_finder(new_name)
            label = self.generate_label(node_type, new_number)

            new_nodes.append({
                "node_id": new_name,
                "node_type": node_type,
                "role": node['role'],
                "label": label,
                "text": node['text']
            })
            new_edges.append({
                "from": new_node_id_dic[node_id],
                "to": new_node_id_dic[node['relation_target']] if node['relation_target'] in new_node_id_dic else node['relation_target'],
                "edge_type": node["relation_type"]
            })
        return new_nodes, new_edges


    def to_graph(self):
        new_nodes, new_edges = self.initialize_nodes_and_edges()
        logger.debug(f"new_nodes : {new_nodes}")
        logger.debug(f"new_edges : {new_edges}")
        if len(self.current_arguments['nodes']) > 1:
            old_nodes = self.current_arguments['nodes']
            old_edges = self.current_arguments['edges']
            old_nodes += new_nodes
            old_edges += new_edges
            result = {"nodes":old_nodes, "edges":old_edges}
        else:
            result = {"nodes":new_nodes, "edges":new_edges}
        return result


if __name__ == "__main__":
    import json 
    # with open('/home/hmc/Desktop/work/alex_viz/backend/app/tests/data/sample_aspic_IN.json') as f:
    #     data = json.load(f)
    
    # argument_graph = ArgumentGraph(data)
    # formatted_data = argument_graph.format_to_aspic_plus()
        
    # #logger.debug(formatted_data)
    # with open('/home/hmc/Desktop/work/alex_viz/backend/app/tests/data/sample_aspic_OUT2.json', 'w') as f:
    #     json.dump(formatted_data, f, indent=4, ensure_ascii=False)

    data = [
    {
        "node_id": "c00001_tmp",
        "node_type": "claim",
        "role": "prosecution",
        "text": " 피고인은 피해자 C에게 거짓된 신분을 사용하여 접근함으로써 사기 행위의 첫 단계를 실행하였습니다.",
        "relation_target": "-mc00001",
        "relation_type": "support",
        "main_claim": "피고인은 고도의 계획 하에 피해자 C에게 접근, 거짓된 신분을 이용해 피해자를 기망하였으며, 이는 명백한 사기 행위로서 피해자에게 경제적 손실을 입혔습니다."
    },
    {
        "node_id": "w00001_tmp",
        "node_type": "warrant",
        "role": "prosecution",
        "text": " 사기 범죄에서 거짓 신분 사용은 피해자의 신뢰를 얻고, 그들을 속여 자금을 이용하게 하는 전형적인 방법입니다.",
        "relation_target": "c00001_tmp",
        "relation_type": "support",
        "main_claim": "피고인은 고도의 계획 하에 피해자 C에게 접근, 거짓된 신분을 이용해 피해자를 기망하였으며, 이는 명백한 사기 행위로서 피해자에게 경제적 손실을 입혔습니다."
    },
    {
        "node_id": "d00001_tmp",
        "node_type": "datum",
        "role": "prosecution",
        "text": " 2015. 7. 7.경 불상의 장소에서 피고인이 피해자 C에게 전화하여 'D 경위입니다. 선생님 명의의 SC제일은행 계좌가 불법 자금 세탁에 이용되었습니다.'라고 말한 사실",
        "relation_target": "w00001_tmp",
        "relation_type": "support",
        "main_claim": "피고인은 고도의 계획 하에 피해자 C에게 접근, 거짓된 신분을 이용해 피해자를 기망하였으며, 이는 명백한 사기 행위로서 피해자에게 경제적 손실을 입혔습니다."
    },
    {
        "node_id": "c00002_tmp",
        "node_type": "claim",
        "role": "prosecution",
        "text": " 피고인은 피해자를 기망하여 범죄에 이용된 계좌 정보를 제공받기 위한 목적으로 행동하였습니다.",
        "relation_target": "-mc00001",
        "relation_type": "support",
        "main_claim": "피고인은 고도의 계획 하에 피해자 C에게 접근, 거짓된 신분을 이용해 피해자를 기망하였으며, 이는 명백한 사기 행위로서 피해자에게 경제적 손실을 입혔습니다."
    },
    {
        "node_id": "w00002_tmp",
        "node_type": "warrant",
        "role": "prosecution",
        "text": " 가짜 경찰 신분을 이용하여 피해자에게 접근하고, 불법 자금 세탁에 관련된 계좌 정보를 요구하는 것은 사기 행위의 목적을 달성하기 위한 전략입니다.",
        "relation_target": "c00002_tmp",
        "relation_type": "support",
        "main_claim": "피고인은 고도의 계획 하에 피해자 C에게 접근, 거짓된 신분을 이용해 피해자를 기망하였으며, 이는 명백한 사기 행위로서 피해자에게 경제적 손실을 입혔습니다."
    },
    {
        "node_id": "d00002_tmp",
        "node_type": "datum",
        "role": "prosecution",
        "text": " 피고인이 '피해자로 등록하려면 우리가 안내하는 사이트에 들어가서 선생님이 사용하였다.'라고 말하여 피해자 C로 하여금 거짓된 사이트에 접속하게 하여 계좌 정보를 제공받으려 한 사실",
        "relation_target": "w00002_tmp",
        "relation_type": "support",
        "main_claim": "피고인은 고도의 계획 하에 피해자 C에게 접근, 거짓된 신분을 이용해 피해자를 기망하였으며, 이는 명백한 사기 행위로서 피해자에게 경제적 손실을 입혔습니다."
    },
    {
        "node_id": "c00003_tmp",
        "node_type": "claim",
        "role": "prosecution",
        "text": " 이 사건은 피고인이 고도의 계획 하에 실행한 명백한 사기 행위로서, 피해자 C에게 경제적 손실을 입혔습니다.",
        "relation_target": "-mc00001",
        "relation_type": "support",
        "main_claim": "피고인은 고도의 계획 하에 피해자 C에게 접근, 거짓된 신분을 이용해 피해자를 기망하였으며, 이는 명백한 사기 행위로서 피해자에게 경제적 손실을 입혔습니다."
    },
    {
        "node_id": "w00003_tmp",
        "node_type": "warrant",
        "role": "prosecution",
        "text": " 피해자의 신뢰를 얻기 위해 가장한 후, 그들의 개인적인 정보를 요구하는 행위는 사기 범죄에서 자주 관찰되는 패턴이며, 이는 피해자에게 경제적 손실을 초래합니다.",
        "relation_target": "c00003_tmp",
        "relation_type": "support",
        "main_claim": "피고인은 고도의 계획 하에 피해자 C에게 접근, 거짓된 신분을 이용해 피해자를 기망하였으며, 이는 명백한 사기 행위로서 피해자에게 경제적 손실을 입혔습니다."
    },
    {
        "node_id": "d00003_tmp",
        "node_type": "datum",
        "role": "prosecution",
        "text": " 피고인이 피해자 C에게 전화하여 거짓된 신분을 사용하고, 피해자로 하여금 거짓된 사이트에 접속하게 함으로써 계좌 정보를 제공받으려 한 사실",
        "relation_target": "w00003_tmp",
        "relation_type": "support",
        "main_claim": "피고인은 고도의 계획 하에 피해자 C에게 접근, 거짓된 신분을 이용해 피해자를 기망하였으며, 이는 명백한 사기 행위로서 피해자에게 경제적 손실을 입혔습니다."
    }
    ]
    
    argument = {"nodes": 
                [{'node_id': 'mc00001', 'node_type': 'mc', 'role': 'defense', 'text': '피고인 mc', 'label': '[DEF]MC_01'},
                {'node_id': '-mc00001', 'node_type': 'mc', 'role': 'prosecution', 'text': '검사 mc', 'label': '[PRO]MC_01'},
                {'node_id': 'c00001', 'node_type': 'claim', 'role': 'defense', 'text': ' 피고인 C1', 'label': '[PRO]C_01'},
                {'node_id': 'w00001', 'node_type': 'warrant', 'role': 'defense', 'text': ' 피고인 w1', 'label': '[PRO]W_01'},
                {'node_id': 'd00001', 'node_type': 'datum', 'role': 'defense', 'text': ' 피고인 D1', 'label': '[PRO]D_01'},
                {'node_id': 'c00002', 'node_type': 'claim', 'role': 'defense', 'text': ' 피고인 C2', 'label': '[PRO]C_02'},
                {'node_id': 'w00002', 'node_type': 'warrant', 'role': 'defense', 'text': ' 피고인 W2', 'label': '[PRO]W_02'},
                {'node_id': 'c00003', 'node_type': 'claim', 'role': 'defense', 'text': ' 피고인 C3', 'label': '[PRO]C_03'}],
                "edges": [{'from': 'mc00001', 'to': '-mc00001', 'edge_type': 'attack'},
                          {'from': 'mc00001', 'to': 'mc00001', 'edge_type': 'attack'},
                          {'from': 'c00001', 'to': 'mc00001', 'edge_type': 'support'},
                          {'from': 'w00001', 'to': 'c00001', 'edge_type': 'support'},
                          {'from': 'd00001', 'to': 'w00001', 'edge_type': 'support'},
                          {'from': 'c00002', 'to': 'mc00001', 'edge_type': 'support'},
                          {'from': 'w00002', 'to': 'c00002', 'edge_type': 'support'},
                          {'from': 'c00003', 'to': 'mc00001', 'edge_type': 'support'}]}

    # history argument exists
    # argument_graph = ArgumentGraph(data, argument)
    # No history argument
    argument_graph = ArgumentGraph(data)
    formatted_data = argument_graph.to_graph()
    #logger.debug(f"formatted_data : {formatted_data}")