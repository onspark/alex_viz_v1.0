from rouge import Rouge
from itertools import combinations
from collections import defaultdict

from app.components.llm import ModelSettings
from app.components.tools import LeapPrediction
from app.logger import logger

# TODO: Import threshold from settings

class Optimizer:
    def __init__(self, rag_result, arguments, crime_fact="", target_node=None, model_type="nli-context-coherency-verifier"):
        self.rouge_threshold = 0.8
        self.nli_threshold = 0.3
        
        self.nodes = arguments["nodes"]
        self.edges = arguments["edges"]
        
        self.rag_result = rag_result
        self.crime_fact = crime_fact
        self.target_node = target_node
        
        self.results = {node["node_id"]: {"aq_t2r":True, "aq_r2n":True, "cc_c2d":True, "cc_t2c":True} for node in self.rag_result["nodes"]}
        
        self.arg_quality_control_combinations = {}
        self.context_coherency_combinations = {}
        
        self.rouge = Rouge()
        
        settings = ModelSettings().get_setting(model_type)
        
        self.leap = LeapPrediction(settings.get("model_name_or_path"))
        # self.leap = LeapPrediction("app/models/koelectra_leap_v1.0.0")
    
    def _generate_combinations(self):
        '''
        [argument quality control]
        (1) target vs rag result nodes: avoid simple negations
        (2) rag result nodes vs nodes in argument network with same role: avoid redundancy

        [context coherency]
        (1) crime fact vs datum in rag result nodes (undetermined above threshold): avoid unrelated facts
        (2) target vs claims rag result nodes (contradiction): verify attacking relationship 
        '''  
        
        # (1) target vs rag result nodes 
        target_vs_rag_result = [(self.target_node, node) for node in self.rag_result["nodes"]]
        
        # (2) rag result nodes vs nodes in argument network with same role and same node type
        rag_nodes = [node for node in self.rag_result["nodes"]]
        nodes_by_role = [node for node in self.nodes if node["role"] == self.target_node["role"] and node['node_type'] != "main_claim"]
        rag_result_vs_nodes = [(rag_node, node) for rag_node in rag_nodes for node in nodes_by_role if rag_node["node_type"] == node["node_type"]]
        
        # (1) crime fact vs datum in rag result nodes
        crime_fact_vs_datums = [(self.crime_fact, node) for node in self.rag_result["nodes"] if node["node_type"] == "datum"]
        
        # (2) target vs claims rag result nodes
        target_vs_claims = [(self.target_node, node) for node in self.rag_result["nodes"] if node["node_type"] == "claim"]
        
                # Combine both lists and ensure unique combinations
        self.rouge_combinations = {"target_to_rag_node": target_vs_rag_result,  "rag_node_to_node": rag_result_vs_nodes}
        self.nli_combinations = {"cf_to_datum":crime_fact_vs_datums, "target_to_attack":target_vs_claims}
        
        
    def control_argument_quality(self):        
        for target_node, rag_node in self.rouge_combinations["target_to_rag_node"]:
           target_text = target_node["text"]
           rag_node_text = rag_node["text"]
           score = self.rouge.get_scores(target_text, rag_node_text)
           rouge_l_score = score[0]["rouge-l"]["f"]
           if rouge_l_score > self.rouge_threshold:
               logger.info(f"Rouge score between target and rag node: {rouge_l_score} exceeds threshold.")
               
               logger.debug(f"Target: {target_node['text']}")
               logger.debug(f"Rag node: {rag_node['text']}")
               
               self.results[rag_node["node_id"]]["aq_t2r"] = False
        
        for rag_node, node in self.rouge_combinations["rag_node_to_node"]:
            rag_node_text = rag_node["text"]
            node_text = node["text"]
            score = self.rouge.get_scores(rag_node_text, node_text)
            rouge_l_score = score[0]["rouge-l"]["f"]
            if rouge_l_score > self.rouge_threshold:
                logger.info(f"Rouge score between rag node and node: {rouge_l_score} exceeds threshold.")
                
                logger.debug(f"Rag node: {rag_node['text']}")
                logger.debug(f"Node: {node['text']}")
                
                self.results[rag_node["node_id"]]["aq_r2n"] = False
                
    def verify_context_coherency(self):
        for cf, datum in self.nli_combinations["cf_to_datum"]:
            score = self.leap.predict(cf, datum["text"])
            if score["scores"]["undetermined"] > (1-self.nli_threshold)*100:
                logger.info(f"Crime fact and datum seem to be unrelated. Undetermined Score: {score['scores']['undetermined']} is above threshold.")
                
                logger.debug(f"Crime fact: {cf}")
                logger.debug(f"Datum: {datum['text']}")
                
                self.results[datum["node_id"]]["cc_c2d"] = False

        for target, claim in self.nli_combinations["target_to_attack"]:
            score = self.leap.predict(target["text"], claim["text"])
            if score["scores"]["contrasts"] < (self.nli_threshold)*100:
                logger.info(f"Target and claim  do not seem to have an attacking relationship. Contrast Score: {score['scores']['contrasts']} is below threshold.")
                
                logger.debug(f"Target: {target['text']}")
                logger.debug(f"Claim: {claim['text']}")
                
                self.results[claim["node_id"]]["cc_t2c"] = False
                

    def optimize(self,filter_threshold=1):
        self._generate_combinations()
        self.control_argument_quality()
        self.verify_context_coherency()
        
        to_remove = set()
        for node_id, result in self.results.items():
            true_count = sum(value == True for value in result.values())
            if true_count <= filter_threshold:  # Node failed all checks or passed only one
                logger.debug(f"Node {node_id} failed all checks or passed only one. True count:{true_count}")
                to_remove.add(node_id)                
        
        # Direct mapping from node_id to node for quick access, and downstream relations
        node_dict = {node["node_id"]: node for node in self.rag_result["nodes"]}
        downstream_relations = {}
        for node in self.rag_result["nodes"]:
            target_id = node["relation_target"]
            if target_id and node["node_id"] not in to_remove:  # Consider only non-removed nodes for mapping
                if target_id in downstream_relations:
                    downstream_relations[target_id].append(node["node_id"])
                else:
                    downstream_relations[target_id] = [node["node_id"]]

        to_remove_expanded = set(to_remove)
        
        for node_id in to_remove:
            if node_id in node_dict:  # Ensure node exists in current mapping
                
                node_type = node_dict[node_id]["node_type"]
                
                if node_type == "claim":
                    if node_id in downstream_relations:
                        for related_node_id in downstream_relations[node_id]:
                            related_node_type = node_dict[related_node_id]["node_type"]
                            if related_node_type == "warrant":  # Remove warrant and datum related to the claim
                                to_remove_expanded.add(related_node_id)
                                # Look for downstream relations of the warrant
                                if related_node_id in downstream_relations: 
                                    for related_datum_id in downstream_relations[related_node_id]:
                                        if node_dict[related_datum_id]["node_type"] == "datum":  # Ensure it's a datum
                                            to_remove_expanded.add(related_datum_id)
                                
                elif node_type == "warrant":
                    if node_id in downstream_relations:
                        for related_node_id in downstream_relations[node_id]:
                            related_node_type = node_dict[related_node_id]["node_type"]
                            if related_node_type == "datum":  # Remove datum related to the warrant
                                to_remove_expanded.add(related_node_id)        
                elif node_type == "datum":
                    if node_id in downstream_relations:
                        for related_node_id in downstream_relations[node_id]:
                            related_node_type = node_dict[related_node_id]["node_type"]
                            if related_node_type == "warrant": # Remove warrant related to the datum
                                to_remove_expanded.add(related_node_id)

        logger.debug("Nodes to be removed: " + str(to_remove_expanded))
        # Filter out nodes to be removed from the result
        updated_rag_result = [node for node in self.rag_result["nodes"] if node["node_id"] not in to_remove_expanded]
        
        total_result = {"is_root":False, "nodes": updated_rag_result}

        return total_result
            
    
# python -m app.components.optimizer.optimizer  
if __name__ == "__main__":
    import json 
    
    target_node = {"node_id": "c00003", "node_type": "claim", "role": "defendant", "text": "피고인은 보이스피싱 혐의를 부정하고 있다.", "label": "C_01"}

    with open("app/data/samples/sample_rag_formatted_response.json", "r", encoding="utf8") as f:
        rag_output = json.load(f)

    with open("app/data/samples/sample_aspic_OUT.json","r", encoding="utf8") as f:
        arguments = json.load(f)["data"]["arguments"]

    input_crime_fact = "성명불상의 보이스피싱 조직은 불특정 다수의 피해자들에게 \"저금리 대출을 해주겠으니 기존 대출금을 직원에게 상환하라\"는 취지로 거짓말하는 방법으로 금원을 편취하는 조직이며, 모든 범행을 계획하고 지시하는 '총책', 피해금을 입금받을 계좌 및 이와연결된 체크카드를 수집하는 '모집책', 위 체크카드를 전달받아 입금된 돈을 인출하여 보이스피싱 조직원에서 전달하는 '수거책 및 인출책' 등으로 구성되어 있다.\n피고인은 2020. 7. 2.경 성명불상자로부터 \"대출을 해주겠다, 체크카드를 보내주면 이자를 인출하는 용도로 사용한다\"는 제안을 받고 피고인의 체크카드를 성명불상자에게 넘겨주었으나 곧 보이스피싱 사기 범행에 이용되어 위 체크카드와 연결된 은행 계좌가 정지되자 체크카드가 범죄에 사용되었음을 인지하였음에도 위 성명불상자로부터 \"택배로 체크카드를 받아 체크카드에 입금된 돈을 인출해주면 인출액의 3%를 주겠다\"는 제안을 수락하여 '수거책 및 인출책' 역할을 하기로 하였다.\n성명불상의 보이스피싱 조직원은 2020. 7. 21.경 피해자 AF에게 은행직원을 사칭하며 '저금리로 대출을 해주겠다, 기존에 대출받은 1,000만원을 갚아야 되니 우리가 보내는 수금직원에게 상환하라'는 취지로 거짓말하여 이에 속은 피해자로 하여금 같은 달 24.경 울산 남구 AG 앞에서 현금을 가지고 기다리도록 하였다.\n피고인은 위 성명불상자와의 공모에 따라 2020. 7. 24. 17:30경 위 성명불상자가 알려준 주소인 위 장소에서 피해자에게 \"AD 대리이고 사원번호 AE번이다\"라는 취지로 자신을 소개하고 피해자로부터 875만원을 교부받았다."
        
    optimizer = Optimizer(rag_output, arguments, input_crime_fact, target_node)

    result = optimizer.optimize(filter_threshold=2)
    
    print(result)
    