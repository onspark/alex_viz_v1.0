from py_arg.aspic_classes.argumentation_system import ArgumentationSystem
from py_arg.aspic_classes.argumentation_theory import ArgumentationTheory
from py_arg.aspic_classes.defeasible_rule import DefeasibleRule
from py_arg.aspic_classes.literal import Literal
from py_arg.aspic_classes.strict_rule import StrictRule
from collections import defaultdict

from py_arg.aspic_classes.instantiated_argument import InstantiatedArgument

from py_arg.algorithms.semantics.get_admissible_sets import get_admissible_sets
from py_arg.algorithms.semantics.get_complete_extensions import get_complete_extensions
from py_arg.algorithms.semantics.get_eager_extension import get_eager_extension
from py_arg.algorithms.semantics.get_grounded_extension import get_grounded_extension
from py_arg.algorithms.semantics.get_ideal_extension import get_ideal_extension
from py_arg.algorithms.semantics.get_preferred_extensions import get_preferred_extensions
from py_arg.algorithms.semantics.get_semistable_extensions import get_semistable_extensions
from py_arg.algorithms.semantics.get_stable_extensions import get_stable_extensions

from app.utils import convert_node_ids_to_labels
from app.logger import logger


class Formalizer: 
    def __init__(self, nodes, edges):
        
        self.original_nodes = nodes
        
        self.nodes = [(node['node_id'], node['node_type']) for node in nodes if node['node_type'] != 'main_claim'] # We exclude the main claims
        self.edges = [(edge['from'], edge['to'], edge['edge_type']) for edge in edges if 'mc' not in edge['to'] and 'mc' not in edge['from']] # We exclude the main claims
        
        self.language = {}
        self.defeasible_rules = []
        self.ordinary_premises = []
        self.contraries_and_contradictories = {}
        
    def initialize_argumentation_theory(self):
        self._initialize_language_and_contraries()
        self._initialize_defeasible_rule()
      
    def _initialize_language_and_contraries(self):
        # Remove prefix from literals and duplicates
        literals = [literal_str[1:] if literal_str[0] in ["-","~"] else literal_str for literal_str, node_type in self.nodes if node_type in ['datum', 'claim']]
        
        literals = list(set(literals))
        
        for literal_str in literals:
            self.language[literal_str] = Literal(literal_str)
            # Initialize contraries for both positive and negated literals
            self.language['-' + literal_str] = Literal('-' + literal_str)
            self.language['~' + literal_str] = Literal('~' + literal_str)
            self.contraries_and_contradictories[literal_str] = [self.language['-' + literal_str]]
            self.contraries_and_contradictories['-' + literal_str] = [self.language[literal_str]]
            self.contraries_and_contradictories['~' + literal_str] = [self.language[literal_str]]
            
            self.warrant_id_to_defeasible_rule = defaultdict(list)
            self.defeasible_rules_to_warrant_node_ids = defaultdict(list)
            
    def _initialize_defeasible_rule(self):
        '''
        1. Convert warrants to defeasible rules in the form of datum => claim
        2. Map the created defeasible rules to the warrant node ids for later use
        3. Iterate through the edges and create defeasible rules based on their relationships.
        3.1. If the to edge is a warrant, replace it with the defeasible rule created from the warrant.
        
        Possible patterns:
        [support]
        1) d-w-c = d=>c
        2) c-mc = c=>mc
        
        [attack]
        1) c-d = c=>-d
        2) c-w = c=>-w
        3) c-c = c=>-c
        4) mc-mc = mc=>-mc
        
        '''
        
        # Create defeasible rules from warrants
        self._convert_warrants_to_defeasible_rules()
    
        # skip dw and wc relations in edges
        relations_to_convert = [edge for edge in self.edges if not (edge[0].startswith("d") and edge[1].startswith("w")) and not (edge[0].startswith("w") and edge[1].startswith("c"))]

        for from_node, to_node, edge_type in relations_to_convert:
            antecedent = from_node
            consequent = to_node
            if to_node.startswith("w"): # Likely an attack
                node_defrule = self.warrant_id_to_defeasible_rule.get(to_node)
                consequent = self._get_defeasible_rule_literal(node_defrule, edge_type) #returns defeasible rule literal considering negation
            else:
                if edge_type == "attack":
                    if  consequent.startswith("-"): # Already a negated literal
                        consequent = consequent[1:]
                    else:
                        consequent = "-" + consequent
            
            defrule = self._create_defeasible_rule(antecedent, consequent)
            
             
    def _convert_warrants_to_defeasible_rules(self):
        # warrant triples 
        warrant_triples = {node_id: {"from":"", "to":""} for node_id, node_type in self.nodes if node_type == "warrant"}
        
        for from_node, to_node, edge_type in self.edges:
            if edge_type == "support":
                if from_node.startswith("d") and to_node.startswith("w"):
                    warrant_triples[to_node]["from"] = from_node
                elif from_node.startswith("w") and to_node.startswith("c"):
                    warrant_triples[from_node]["to"] = to_node
        
        # Add a dummy datum if w-c exists but not d-w
        dummy_count = 0
        for k, v in warrant_triples.items():
            if v["from"] == "" and v["to"] != "":
                warrant_triples[k] = {"from": f"dummy{dummy_count:02d}", "to": v["to"]}
                dummy_count += 1
        
        # Check if there are any incomplete triples
        incomplete_triples = [k for k, v in warrant_triples.items() if v["from"] == "" or v["to"] == ""]
        if incomplete_triples:
            # raise ValueError(f"Incomplete warrant triples: {incomplete_triples}")
            logger.debug(f"Incomplete warrant triples: {incomplete_triples}")
        
        for warrant_id, relations in warrant_triples.items():
            from_node = relations["from"]
            to_node = relations["to"]
            created_defrule = self._create_defeasible_rule(from_node, to_node)
            if created_defrule:
                self.warrant_id_to_defeasible_rule[warrant_id] = created_defrule
                self.defeasible_rules_to_warrant_node_ids[str(created_defrule)] = warrant_id 
            
    def _create_defeasible_rule(self, premise, conclusion):
        """ Create and store a new DefeasibleRule. """
        rule_id = f'd{len(self.defeasible_rules) + 1}'
        try:
            #check whether premise or conclusion is a defeasible rule or string
            if isinstance(premise, str):
                premise = self.language[str(premise)]
            if isinstance(conclusion, str):
                conclusion = self.language[str(conclusion)]
            new_rule = DefeasibleRule(rule_id, {premise}, conclusion) #if defeasible rule, use Literal object
            self.defeasible_rules.append(new_rule)
            self._add_defeasible_rule_literals_to_language(new_rule)
            return new_rule
        except Exception as e:
            logger.debug(f"Error in creating defeasible rule - {e}, {premise}, {conclusion}")    
            return None

    
    def _add_defeasible_rule_literals_to_language(self, defeasible_rule):
        """ Add the literals of a defeasible rule to the language. """
        defeasible_rule_literal = Literal.from_defeasible_rule(defeasible_rule)
        defeasible_rule_literal_negation = Literal.from_defeasible_rule_negation(defeasible_rule)
        
        self.language[str(defeasible_rule_literal)] = defeasible_rule_literal
        self.language[str(defeasible_rule_literal_negation)] = defeasible_rule_literal_negation
        self.contraries_and_contradictories[str(defeasible_rule_literal)] = [defeasible_rule_literal_negation]
        self.contraries_and_contradictories[str(defeasible_rule_literal_negation)] = [defeasible_rule_literal]
        
    def _get_defeasible_rule_literal(self, defrule, edge_type="support"):
        """ Convert a warrant to a defeasible rule literal using defrule_from_warrants. """
        if defrule is None:
            raise ValueError(f"Invalid warrant {defrule}, no defeasible rule found")
        
        if edge_type == "support":
            return Literal.from_defeasible_rule(defrule)
        elif edge_type == "attack":
            # logger.debug(f"Returning negation of defeasible rule literal, {Literal.from_defeasible_rule_negation(defrule)}")
            return Literal.from_defeasible_rule_negation(defrule)

    def get_argumentation_theory(self):
        
        self.initialize_argumentation_theory()
        
        # Include only 'datum' and 'claim' types as ordinary premises
        self.ordinary_premises = [self.language[literal_str] for literal_str, node_type in self.nodes if node_type in ['datum']]
        strict_rules = []
        axioms = []
        arg_sys = ArgumentationSystem(self.language, self.contraries_and_contradictories, strict_rules, self.defeasible_rules)
        arg_theory = ArgumentationTheory(arg_sys, axioms, self.ordinary_premises)
        return arg_theory    
    

    def get_updated_node_labels(self):
        node_id_to_labels = convert_node_ids_to_labels(
            self.original_nodes, 
            self.defeasible_rules, 
            self.defeasible_rules_to_warrant_node_ids)
        logger.debug("Node labels:", node_id_to_labels)
        return node_id_to_labels                 
    
    def get_af_extensions(self, argumentation_framework, semantics_specification='admissible'):
        """ Get extensions as nodes. """
        
        logger.info(f"Calculating extensions for {semantics_specification} extensions...")
        
        if semantics_specification == "admissible":
            return get_admissible_sets(argumentation_framework)
        elif semantics_specification == "complete":
            return get_complete_extensions(argumentation_framework)
        elif semantics_specification == "grounded":
            return get_grounded_extension(argumentation_framework)
        elif semantics_specification == "ideal":
            return get_ideal_extension(argumentation_framework)
        elif semantics_specification == "preferred":
            return get_preferred_extensions(argumentation_framework)
        elif semantics_specification == "semistable":
            return get_semistable_extensions(argumentation_framework)
        elif semantics_specification == "stable":
            return get_stable_extensions(argumentation_framework)
        elif semantics_specification == "eager":
            return get_eager_extension(argumentation_framework)
        else:
            raise ValueError(f"Invalid semantics specification: {semantics_specification}")
    
    def get_extensions_as_node_ids(self, argumentation_framework, semantics_specification='admissible'):
        
        extensions = self.get_af_extensions(argumentation_framework, semantics_specification)
        
        accepted_arguments = []
        
        if len(extensions) > 1 and semantics_specification=="complete": # Get intersection of extensions for minimum accepted arguments
            extensions = set.intersection(*map(set, extensions))
        
        for argument in extensions:
            # check for defeasible rules with d and c => convert to warrant and add the claim to accepted arguments
            premise = str(list(argument.premises)[0])
            conclusion = str(argument.conclusion)
            defrules = list(argument.defeasible_rules)

            if len(defrules) == 0: # Argument is a warrant
                accepted_arguments.append(premise)
            elif "d" in premise and "c" in conclusion and len(defrules) == 1: # Argument is a warrant 
                argument = str(defrules[0])
                warrant = self.defeasible_rules_to_warrant_node_ids[argument]
                accepted_arguments.append(warrant)
                accepted_arguments.append(conclusion)

        return accepted_arguments
                

# python -m app.components.formalizer.aspic_formalizer
if __name__ == "__main__":
    
    
    # data ={
    #     "nodes": [
    #         {"node_id": "mc1", "node_type": "main_claim"},
    #         {"node_id": "-mc1", "node_type": "main_claim"},
    #         {"node_id": "d_1", "node_type": "datum"},
    #         {"node_id": "d_2", "node_type": "datum"},
    #         {"node_id": "d_3", "node_type": "datum"},
    #         {"node_id": "d_4", "node_type": "datum"},
    #         {"node_id": "d_5", "node_type": "datum"},
    #         {"node_id": "d_6", "node_type": "datum"},
    #         {"node_id": "d_7", "node_type": "datum"},
    #         {"node_id": "c_1", "node_type": "claim"},
    #         {"node_id": "c_2", "node_type": "claim"},
    #         {"node_id": "c_3", "node_type": "claim"},
    #         {"node_id": "c_4", "node_type": "claim"},
    #         {"node_id": "c_5", "node_type": "claim"},
    #         {"node_id": "c_6", "node_type": "claim"},
    #         {"node_id": "c_7", "node_type": "claim"},
    #         {"node_id": "w_1", "node_type": "warrant"},
    #         {"node_id": "w_2", "node_type": "warrant"},
    #         {"node_id": "w_3", "node_type": "warrant"},
    #         {"node_id": "w_4", "node_type": "warrant"},
    #         {"node_id": "w_5", "node_type": "warrant"},
    #         {"node_id": "w_6", "node_type": "warrant"},
    #         {"node_id": "w_7", "node_type": "warrant"}
    #     ],
    #     "edges": [
    #         {"from": "d_1", "to": "w_1", "edge_type": "support"},
    #         {"from": "w_1", "to": "c_1", "edge_type": "support"},
    #         {"from": "d_2", "to": "w_2", "edge_type": "support"},
    #         {"from": "w_2", "to": "c_2", "edge_type": "support"},
    #         {"from": "d_3", "to": "w_3", "edge_type": "support"},
    #         {"from": "w_3", "to": "c_3", "edge_type": "support"},
    #         {"from": "d_4", "to": "w_4", "edge_type": "support"},
    #         {"from": "w_4", "to": "c_4", "edge_type": "support"},
    #         {"from": "d_5", "to": "w_5", "edge_type": "support"},
    #         {"from": "w_5", "to": "c_5", "edge_type": "support"},
    #         {"from": "d_6", "to": "w_6", "edge_type": "support"},
    #         {"from": "w_6", "to": "c_6", "edge_type": "support"},
    #         {"from": "d_7", "to": "w_7", "edge_type": "support"},
    #         {"from": "w_7", "to": "c_7", "edge_type": "support"},
    #         {"from": "c_1", "to": "mc_1", "edge_type": "support"},
    #         {"from": "c_2", "to": "c_1", "edge_type": "support"},
    #         {"from": "c_3", "to": "c_1", "edge_type": "attack"},
    #         {"from": "c_4", "to": "c_1", "edge_type": "attack"},
    #         {"from": "c_5", "to": "c_1", "edge_type": "attack"},
    #         {"from": "c_6", "to": "w_2", "edge_type": "attack"},
    #         {"from": "c_7", "to": "w_4", "edge_type": "attack"}
    #     ]
    # }

    # formalizer = Formalizer(data["nodes"],data["edges"])
    # argumentation_theory = formalizer.get_argumentation_theory()

    # import time 
    # start_time = time.time()

    # af = argumentation_theory.create_abstract_argumentation_framework('af')


    # extensions = formalizer.get_extensions_as_node_ids(af, 'complete')
    
    # print(extensions)
    
    import json 
    
    file_name = "app/data/samples/sample_aspic_OUT_test.json"
    
    with open(file_name, "r") as f:
        graph_data = json.load(f)['data']['arguments']
        
    # file_name = "app/data/out/2024-03-12-02-06-10_tmp_formalizer_test.json"
    # with open(file_name, "r") as f:
    #     graph_data = json.load(f)

    import time 
    
    aspic_generator = Formalizer(graph_data['nodes'], graph_data['edges'])
    argumentation_theory = aspic_generator.get_argumentation_theory()
    af = argumentation_theory.create_abstract_argumentation_framework('af')
    
        # All undercutters
    all_underminers = [(argument_a, argument_b)
        for argument_a in argumentation_theory.all_arguments
        for argument_b in argumentation_theory.all_arguments
        if argumentation_theory.undermines(argument_a, argument_b)]
    print('*Underminers:*')
    for attack in all_underminers:
        print(attack)
        
    # All undercutters
    all_undercutters = [(argument_a, argument_b)
        for argument_a in argumentation_theory.all_arguments
        for argument_b in argumentation_theory.all_arguments
        if argumentation_theory.undercuts(argument_a, argument_b)]
    print('*Undercutters:*')
    for attack in all_undercutters:
        print(attack)
        
    # All rebuttals
    all_rebuttals = [(argument_a, argument_b)
        for argument_a in argumentation_theory.all_arguments
        for argument_b in argumentation_theory.all_arguments
        if argumentation_theory.rebuts(argument_a, argument_b)]
    print('*rebuttals:*')
    for attack in all_rebuttals:
        print(attack)
        
    for idx,argument in enumerate(argumentation_theory.all_arguments):
        print(f"{idx+1}/{len(argumentation_theory.all_arguments)}")
        print('The argument is: ' + str(argument))
        print('Conclusion: ' + str(argument.conclusion))
        print('Premises: {' + ', '.join(str(premise) for premise in argument.premises) + '}')
        print('Strict rules: {' + ', '.join(str(rule) for rule in argument.strict_rules) + '}')
        print('Defeasible rules: {' + ', '.join(str(rule) for rule in argument.defeasible_rules) + '}')
        print('Top rule: ' + str(argument.top_rule))
    # print('Premises:',aspic_generator.ordinary_premises)
    # print('Defeasible Rules:', [f"d{idx+1}:{rule}"for idx, rule in enumerate(aspic_generator.defeasible_rules)])
    extensions = defaultdict(list)
    
    # semantics_spec = ['complete', 'grounded', 'preferred', 'semistable', 'stable'] 
    semantics_spec = ['grounded']
    start_time = time.time()
    print("Start time:", start_time)
    for semantics in semantics_spec:
        try:
            print(f"Getting {semantics} extensions for {len(argumentation_theory.all_arguments)} arguments.")
            extensions[semantics] = aspic_generator.get_extensions_as_node_ids(af, semantics_specification=semantics)
        except Exception as e:
            print(semantics, e)

    print('all extensions:', extensions)
    
    end_time = time.time()
    print("End time:", end_time)    
    # Convert seconds to minutes and seconds
    minutes = int((end_time - start_time) // 60)
    seconds = int((end_time - start_time) % 60)
    print("Finished in:", minutes, "minutes and", seconds, "seconds")

    
    