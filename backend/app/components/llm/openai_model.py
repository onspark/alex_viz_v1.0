import os 
import json 
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_community.embeddings.sentence_transformer import (
    SentenceTransformerEmbeddings,
)
from langchain_core.prompts import PromptTemplate
from typing import List
from app.components.llm import ModelSettings
from app.logger import logger

class OpenAIModel:
    def __init__(self, model_type="gpt-4-turbo-generator"):
        self.model_type = model_type
        self.settings = self._get_settings()
        self.openai_api_key = ""
        self._get_openai_api_key(self.settings.get("api_key_path"))

    def _get_settings(self):
        modelsettings = ModelSettings()
        return modelsettings.get_setting(self.model_type)#use different setting if needed
        
    def _get_openai_api_key(self, api_key_path:str):
        load_dotenv(api_key_path)
        self.open_ai_key = os.getenv("OPEN_AI_API")
    
    def get_llm(self):
        llm = ChatOpenAI(
            temperature=self.settings.get("temperature", "0.7"), 
            openai_api_key = self.open_ai_key, 
            model_name= self.settings.get("model_name", "gpt-4-0125-preview")
            )
        return llm   

    def build_template(self, prompt_text_dir:str, input_variables:List):
        with open(prompt_text_dir, 'r', encoding='utf-8') as prompt:
            prompt_text = prompt.read()
        return PromptTemplate(input_variables=input_variables, template=prompt_text)
    
    def build_template_by_role(self, 
                               crime_fact,
                               opinions, 
                               role, 
                               main_claim,
                               target_node, 
                               history, 
                               action_option):
        
        # action_option: 1: INIT_MAIN_CLAIMS, 2: INIT_SUPPORTS, 3: GENERATE_ATTACKS
        prompt_choice = f"{role.lower()}_{action_option}"
        
        # TODO: defense_1 is set as default starting prompt for all roles.
        prompt_by_role = {
            "defense_1": "app/prompts/generate_claims.txt",
            "defense_2": "app/prompts/generate_defense_supports.txt",
            "defense_3": "app/prompts/generate_defense_attacks.txt",
            "prosecution_2": "app/prompts/generate_prosecution_supports.txt",
            "prosecution_3": "app/prompts/generate_prosecution_attacks.txt"
        }
        
        # Basic Instruction for each role
        query_by_role = {
            "init": "Generate the main claim for defense's and prosecution's side respectively following the instructions below.",
            "defense": "Generate 3 defense's arguments following the instructions below.",
            "prosecution": "Generate 3 prosecution's arguments follwing the instructions below. "
        }
        
        prompt_file = prompt_by_role[prompt_choice]
        with open(prompt_file, 'r', encoding='utf-8-sig') as f:
            template = f.read()
    
        defendant_opinion = opinions["defendant_opinion"]
        prosecutor_opinion = opinions["prosecutor_opinion"]
        
        reference_by_role = {
            "init": f"Defendant's Opinion: {defendant_opinion}\nProsecutor's Opinion: {prosecutor_opinion}",
            "defense": f"Defendant's Opinion: {defendant_opinion}",
            "prosecution": f"Prosecutor's Opinion: {prosecutor_opinion}"
        }

        reference_doc = reference_by_role[role]
        
        if action_option == 1:
            reference_doc = reference_by_role[role]
            reference_doc = f"Defendant's Opinion: {defendant_opinion}\nProsecutor's Opinion: {prosecutor_opinion}"
            # cf_template = template+"\n"+crime_fact+"\n## REFERENCE MATERIALS###\n{reference_doc}" + "\n### CLAIMS ###\n"
            cf_template = f"{template}\n{crime_fact}\n## REFERENCE MATERIALS###\n{reference_doc}\n### CLAIMS ###\n"
        
        elif action_option == 2:
            # INIT_SUPPORTS generates the first supportive argument for the main claim
            
            logger.debug(f"main_claim: {main_claim}")
            
            # cf_template = template+"\n"+crime_fact+"\n## REFERENCE MATERIALS ###\n{reference_doc}\n" + "\n###MAIN CLAIM###\n"+ main_claim + "\n### ARGUMENT NODES ###\n"
            cf_template = f"{template}\n{crime_fact}\n## REFERENCE MATERIALS ###\n{reference_doc}\n###MAIN CLAIM###\n{main_claim}\n### ARGUMENT NODES ###\n"
            
        else: 
            target_node_str = f"({target_node['node_type']}): {target_node['text']}" if target_node else "None"
            history = f"({history})"
            # cf_template = template+"\n"+crime_fact+"\n## REFERENCE MATERIALS ###\n{reference_doc}\n### ARGUMENT HISTORY ###\n"+history+"\n### TARGET NODE ###\n" + target_node_str + "\n###MAIN CLAIM###\n"+ main_claim + "\n### ARGUMENT NODES ###\n"
            
            cf_template = f"{template}\n{crime_fact}\n## REFERENCE MATERIALS ###\n{reference_doc}\n### ARGUMENT HISTORY ###\n{history}\n### TARGET NODE ###\n{target_node_str}\n###MAIN CLAIM###\n{main_claim}\n### ARGUMENT NODES ###\n"
            

        custom_rag_prompt = PromptTemplate.from_template(cf_template)
        return custom_rag_prompt, query_by_role[role]

