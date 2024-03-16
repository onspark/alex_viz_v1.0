from app.logger import logger

from app.components.llm import OpenAIModel
from app.components.generator import RagGenerator
from app.components.optimizer import Optimizer
from app.components.formalizer import Formalizer
from app.utils import get_discourse_history, rag_converter, ArgumentGraph, get_subgraph_nodes, save_json

from collections import defaultdict
from langchain.chains import LLMChain
from enum import Enum, auto

from typing import Dict, Any


class ActionOption(Enum):
    INIT_MAIN_CLAIMS = auto() #1
    INIT_SUPPORTS = auto() #2
    GENERATE_ATTACKS = auto() #3
    HALT = auto() #4

class TargetSelector:
    def __init__(self) -> None:
        self.openai_selector = OpenAIModel(model_type="gpt-4-turbo-selector")  
        self.selector_model = self.openai_selector.get_llm()
    
    def _parse_out_response(self, response):
        '''
        Parses out the response from the model
        '''
        logger.debug(f"Response in _parse_out_response: {response}")

        if response.endswith("###"): # remove ### at the end of the response if it exists
            response = response[:-3]
        try:
            response_list = response.split("###")
            ID_text = response_list[0]
            Exlanation_text = response_list[1]
            node_id = ID_text.split(":")[1].lower().strip()
            explanation = Exlanation_text.strip()
            return node_id, explanation
        except Exception as e:
            logger.error(f"Error parsing response: {e}")
            return None, None
    
    def select_weak_node(self, crime_fact, target_candidates_text):
        '''
        Selects a weak node to attack        
        ''' 
        if len(target_candidates_text) == 0:
            return None
        
        template_dir = "app/prompts/select_weak_node.txt"
        prompt = self.openai_selector.build_template(template_dir, input_variables=['crime_fact', 'arguments_text'])
        
        weak_node_selector_chain = LLMChain(
            llm = self.selector_model,
            prompt= prompt,
            output_key="response",
            verbose=True
        )
        
        next_target_response = weak_node_selector_chain.invoke({
            "crime_fact": crime_fact,
            "arguments_text": target_candidates_text
        })
        logger.debug(f"Next target response: {next_target_response}")
        
        
        if isinstance(next_target_response, dict) and "response" in next_target_response:
            response = next_target_response["response"]
        
            next_target, target_reason = self._parse_out_response(response)
        
            return next_target, target_reason
        else:
            return None, None
        
        
class Operator:
    def __init__(self, user_input: Dict[str, Any]):
        self.crime_fact = user_input.crime_fact
        self.selected_extension = user_input.selected_extension
        self._arguments = user_input.arguments
        self.target_node_id = user_input.target_node_id
        self.target_node = None
        self.target_reason = ""
        self.target_focused = user_input.target_focused
        self.generation_rounds = user_input.generation_rounds
        
        if self.target_node_id:
            self.target_node = [node for node in self._arguments["nodes"] if node["node_id"] == self.target_node_id][0]
        
        self.main_claims = {"defense": None, "prosecution": None}
        
        self.current_role = user_input.selected_role
        
        action_option = user_input.action_option
        if action_option == 1:
            self.action = ActionOption.INIT_MAIN_CLAIMS
        elif action_option == 2: # Cannot be selected in the current version
            self.action = ActionOption.INIT_SUPPORTS
        elif action_option == 3:
            self.action = ActionOption.GENERATE_ATTACKS
        
        self.target_selector = TargetSelector()


    @property
    def result(self) -> Dict[str, Any]:
        """
        Returns:
            Dict[str, Any]: A dictionary with the current state of arguments, target node, and target reason.
        """
        return {
            "arguments": self._arguments,
            "target_node": self.target_node,
            "target_reason": self.target_reason,
            "current_role": self.current_role
        }
        
    def halt(self, halt_reason=""):
        '''
        Halts process under following conditions:
        1. User requests to halt (from frontend)
        2. Optimizer raises exception (no more acceptable counterarguments to be found)
        3. While node list is not empty, extensions are none (all arguments were attacked)
        5. While node list of role is not empty, extensions do not contain any nodes of that role (one side has no more acceptable arguments)
        
        '''
        self.action = ActionOption.HALT
        logger.info(f"Operator halted. {halt_reason}")
        
    def _select_action(self):
        '''
        Selects next action: after initialization, next action should be generate or halt
        role = depending on the starting role, the role will change taking turns
        '''
        selected_extension_nodes = self._arguments["extensions"][self.selected_extension]
        
        if self.target_focused == True and self.target_node_id:
            # If target is focused, only attack children nodes to the target node 
            target_connected_node_ids = get_subgraph_nodes(edges=self._arguments['edges'], target_node_id=self.target_node_id) #newly added attacks
            selected_extension_nodes =  list(set(selected_extension_nodes) & set(target_connected_node_ids)) # get intersection of the two lists
            logger.debug(f"Selected extension nodes: {selected_extension_nodes}")
            

        attackable_nodes  = [f"{node['node_id']}: ({node['node_type']}) {node['text']}" for node in self._arguments['nodes'] if node['node_id'] in selected_extension_nodes and node['role'] != self.current_role]
        
        
        logger.debug(f"Attackable nodes: {attackable_nodes}")
        
        if len(attackable_nodes) == 0 and self.action == ActionOption.GENERATE_ATTACKS:
            return None, "No more acceptable targets to be found."
        else: 
            try:
                attackable_nodes_to_text = "\n".join(attackable_nodes)
                
                logger.debug(f"Looking for weak node in extension ({self.selected_extension}): {attackable_nodes_to_text}")
                
                next_target, target_reason = self.target_selector.select_weak_node(self.crime_fact, attackable_nodes_to_text)     
                
                if not next_target:
                    return None, "Next target could not be found."
                
                return next_target, target_reason

            except Exception as e: 
                logger.error(f"Error selecting next action: {e}")
                return None, None 
                         
    def run_generator(self):
        '''
        Runs the generator
        '''
        logger.debug(f"Running generator for {self.current_role}")
        generator = RagGenerator()
        if self.action == ActionOption.INIT_MAIN_CLAIMS:
            history = "" 
            main_claim = ""
            
        elif self.action == ActionOption.INIT_SUPPORTS:
            history = ""
            main_claim = self.main_claims[self.current_role]
            
        else:
            extensions = self._arguments["extensions"][self.selected_extension]
            history = get_discourse_history(self._arguments, self.target_node, extensions)
            main_claim=self.main_claims[self.current_role]
        
        rag_generator_result = generator.execute_langchain(
            crime_fact=self.crime_fact, 
            role=self.current_role, 
            main_claim=main_claim,
            target_node=self.target_node,
            history=history,
            action_option=self.action.value
        )
                    
        if rag_generator_result is None:
            logger.debug("Generator returned None. Halting operator.")
            self.halt("Nothing was generated.")
        else:
            logger.debug(f"Received generator result!")       
            return rag_generator_result
           
    def run_optimizer(self, rag_result):
        '''
        Use optimizer to drop weak arguments
        ''' 
        logger.debug(f"Running optimizer...")
        optimizer = Optimizer(
            rag_result=rag_result,
            arguments=self._arguments,
            crime_fact=self.crime_fact,
            target_node=self.target_node
        )
        optimized_output = optimizer.optimize(filter_threshold=1)
        # logger.debug(f"Optimizer returned: {optimized_output}")
        return optimized_output
        
    def run_formalizer(self):
        logger.debug(f"Running formalizer...")        
        # formalizer needs access to all arguments in the network
        arguments = self._arguments
        nodes = arguments['nodes']
        edges = arguments['edges']
        # logger.debug(f"Nodes for formalizer: {nodes}")
        # logger.debug(f"Edges for formalizer: {edges}")
        
        
        save_json(data=arguments, file_name_prefix = "tmp_formalizer")
        
        
        formalizer = Formalizer(nodes, edges)
        argumentation_theory = formalizer.get_argumentation_theory()
        
        af = argumentation_theory.create_abstract_argumentation_framework('af')
        
        updated_node_labels = formalizer.get_updated_node_labels()
        logger.debug(f"Updated node labels {updated_node_labels}")
        
        # Update the nodes
        for node in nodes:
            if node['node_id'] in updated_node_labels:
                node['label_expanded'] = updated_node_labels[node['node_id']]
        
        
        # Calculate the extensions
        extensions = defaultdict(list)
        
        # semantics_spec = ['complete', 'grounded', 'preferred']
        semantics_spec = ['grounded']
        
        for semantics in semantics_spec:
            try: 
                extensions[semantics] = formalizer.get_extensions_as_node_ids(af, semantics)    
            except Exception as e:
                logger.error(f"Error getting extensions: {e}")
                extensions[semantics] = []
        
        # Update arguments
        self._arguments = {
            "nodes": nodes,
            "edges": edges,
            "extensions": extensions
        }
        
        if extensions:
            logger.debug(f"Extensions: {extensions}")
            logger.debug("Formalizer ran successfully. Argumentation Network updated.")
        
    
    def _initialize_argument_network(self):
        '''
        Initializes the argument network with the main claims and basic supports. We skip the optimizer here and only use the formalizer to calculate the extensions.
        
        In this step, we are skipping the optimizer and formalizer. No calculation for extension needed.
        
        '''
        main_claims_result = self.run_generator()        
        
        for node in main_claims_result["nodes"]:
            if node["role"] in self.main_claims:
                self.main_claims[node["role"]] = node["text"]
        # Assume result is List[Dict]
        main_claim_graph = ArgumentGraph(data=main_claims_result, arguments=self._arguments)
        main_claim_graph_data = main_claim_graph.to_graph()
        self._arguments["nodes"] = main_claim_graph_data["nodes"]
        self._arguments["edges"] = main_claim_graph_data["edges"]
        logger.debug(f"Arguments after main claim generation: {self._arguments}")
        logger.info("Starting support generation...")
        
        self.action = ActionOption.INIT_SUPPORTS
        for role, claim in self.main_claims.items():
            logger.debug(f"Main claim for {role}: {claim}")
            self.current_role = role
            support_result = self.run_generator()
            arg_graph = ArgumentGraph(data=support_result, arguments=self._arguments)
            arg_graph_data = arg_graph.to_graph()
            self._arguments["nodes"] = arg_graph_data["nodes"]
            self._arguments["edges"] = arg_graph_data["edges"]
            # logger.debug(f"self._arguments in init_support: {self._arguments}")
        
        # Converts to nodes and edges
        # logger.debug(f"Formatted arguments: {formatted_arguments}")
        initial_extensions = {"grounded": [node["node_id"] for node in self._arguments["nodes"] if node["node_type"] != "main_claim"]} 
        self._arguments["extensions"] = initial_extensions
    
        # logger.debug(f"Arguments after support generation: {self._arguments}")
        
        self.action = ActionOption.GENERATE_ATTACKS # After initialization, next action should be generate or halt
        
        
    def generate_attacks(self):
        rag_result = self.run_generator()
        optimized_result = self.run_optimizer(rag_result)
        arg_graph = ArgumentGraph(data= optimized_result, arguments= self._arguments)
        optimized_argument_network = arg_graph.to_graph()
        self._arguments = optimized_argument_network
        self.run_formalizer()

        
    def run(self):
        '''
        Action sequence:
        1. Initialization: Populate the argument network with the main claims and basic supports
            1.1. Generate main claims for both sides [ActionOption.INITIALIZE_MAIN_CLAIMS]
            1.2. Generate supports for the current role (attach to the main claim) - target node is set to the main claim [ActionOption.INITIALIZE_SUPPORTS]
        2. Generate attacks for the current role (attach to the target node) - target node is selected from the extensions [ActionOption.GENERATE_ATTACKS]
        3. Run optimizer to drop weak arguments
        4. Run formalizer to formalize the arguments
        5. Repeat 2-5 until no more targets are found or optimizer raises exception
        6. Halt the process [ActionOption.HALT]
        '''
        
        # if user action_option is 3, then we start from generating attacks
            
        if self.action == ActionOption.INIT_MAIN_CLAIMS:
            self._initialize_argument_network()
        else: 
            counter = 1
            while self.action != ActionOption.HALT:

                
                # Get main claims
                main_claims = [node for node in self._arguments["nodes"] if node["node_type"] == "main_claim"]
                for claim in main_claims:
                    if claim["role"] in self.main_claims:
                        self.main_claims[claim["role"]] = claim["text"]   
                
                if counter > self.generation_rounds:
                    self.halt("Generation rounds exceeded.")
                    break
                if self.main_claims[self.current_role] is None:
                    self.halt(f"Main claim for {self.current_role} not found.")
                    break
                
                logger.info(f"Running operator for the {counter}th time. Generating arguments for {self.current_role}...")
                
                next_target, target_reason = self._select_action() #selects weak node from the current role's extensions
                
                if next_target is None:
                    self.halt(target_reason) # Shows the reason why the operator halted
                    break
                
                logger.info(f"Next target id: {next_target}, {target_reason}")                
                self.target_node_id = next_target
                self.target_node = [node for node in self._arguments["nodes"] if node["node_id"] == self.target_node_id][0]
                self.generate_attacks()
                self.target_reason = target_reason
                if self.generation_rounds > 1:
                    self.current_role = "defense" if self.current_role == "prosecution" else "prosecution" # switch roles
                counter += 1
        logger.info(f"Operator finished running.")

        
if __name__ == "__main__":
    operator = Operator("crime fact", {}, "node1", True, 1)

    
    
    
        
        