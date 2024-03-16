import streamlit as st 
from src.settings import logger
import requests
import json
import time

class ArgumentManager:
    def __init__(self, parent_container=None, data_manager=None):
        self._parent_container = parent_container
        self._data_manager = data_manager
        
        self.generation_rounds = 1
        self.current_role = st.session_state['selected_role']
        
        self._api_endpoint = "http://localhost:8000/api/v0.1.0/alex_viz"
        self._setup_toolbox()
        self._setup_button_group()
        self._setup_manager()
        self._setup_target_node_box()


    def _get_arguments(self, query: str, extension_data : dict)-> dict:
        try:
            arguments = self._data_manager.get_arguments()            
            
            logger.info(f"Starting argument generation for {self.current_role}...")
            
            # 1 for initiating a new argumentation graph, 3 for adding new attacks to the existing graph
            action_option = 3 if len(arguments["nodes"]) > 2 else 1
            
            input_dic = {
                "crime_fact":query, 
                'selected_extension': extension_data,
                'selected_role': self.current_role,
                "arguments": arguments,
                "target_node_id": "",
                "target_focused": False,
                "generation_rounds": self.generation_rounds,
                "action_option": action_option,
                }
            response = requests.post(self._api_endpoint, data=json.dumps(input_dic))             
            
            # response = requests.get(self._api_endpoint)
            response.raise_for_status()    
            
            return response.json()
        
        except requests.RequestException as e:
            logger.error(f"Request failed: {e}")
            return {"success": False, "data": {"arguments": {"nodes": [], "edges": [], "extensions": {}}, "target_node": {}, "target_reason": ""}}
    
    def _setup_toolbox(self):
        toolbox = self._parent_container.expander(":wrench: Argument Toolbox ")
        with toolbox:
            self.generation_rounds = st.number_input(":triangular_flag_on_post: Generation Rounds ", min_value=1, max_value=3, value=1, step=1, key="generation_rounds")           
            st.markdown(f":speech_balloon: Next Speaker  `{self.current_role.capitalize()}`")   
            # self.user_input = st.text_input("Your message", key="user_input")

    def _setup_manager(self):
        self._manager = self._parent_container.container(height=500, border=True)
        self._spinner_placeholder = self._manager.empty()

    def _setup_button_group(self):
        button_group = self._parent_container.container(border=True)
        with button_group:
            left, right = button_group.columns([1, 1])
            self.analysis_button = left.button("Run Analysis", type="secondary")
            self.clear_button = right.button("Clear ALL", type="primary")

    def _setup_target_node_box(self):
        target_node_box = self._parent_container.expander(":dart:  Target Node", expanded=True)
        with target_node_box:
            target_node = self._data_manager.get_target_node()
            if target_node:
                st.markdown(f"**{target_node['role'].capitalize()}** :red[{target_node['node_type'].upper()}({target_node['node_id']})]  \n\n{target_node['text']}")
                st.markdown(f"Reason :thought_balloon: : :gray[{st.session_state['target_reason'].replace('Explanation: ', '')}]")
            else:
                st.markdown("No target node selected yet.")

    def _handle_analysis(self):
        logger.info(f"Analysis button clicked")
        input_data = st.session_state['document_text']
        extension_data = st.session_state['extension_selection']

        in_progress = True
        start_time = time.time()

        with self._spinner_placeholder, st.spinner("Processing..."):
            
            result = self._get_arguments(input_data, extension_data)
            
            end_time = time.time()
            
            operation_time = end_time - start_time
            st.success(f"Operation finished in {operation_time:.2f}s.")

        # result = self._get_arguments("test") #receive query from user
        if result['success'] == True:
            st.session_state['arguments'] = result['data']['arguments']
            target_node =  result['data']['target_node']
            if target_node:
                st.session_state['target_node_id'] = target_node['node_id']
            st.session_state['target_reason'] = result['data']['target_reason']
            
            # Switch roles
            prev_role = result['data']['current_role']
            next_role = "defense" if prev_role == "prosecution" else "prosecution"
            logger.info(f"Switching roles from {prev_role} to {next_role}")
            st.session_state['selected_role'] = next_role
            st.rerun()
            
    def _handle_clear(self):
        logger.info(f"Clear button clicked")
        self._data_manager.clear_arguments()
        st.rerun()
        
    def _delete_node(self, node_id):
        self._data_manager.delete_node(node_id)
        # Update extensions and other related data as needed
        st.rerun()

    def render(self):
        
        if self.analysis_button:
            self._handle_analysis()
        
        if self.clear_button:
            self._handle_clear()
        
        arguments = self._data_manager.get_arguments()

        # TODO: Change later to use the extension option dynamically
        accepted_arguments = arguments.get('extensions', {}).get('grounded', [])
        avatar_images = {
            "prosecution": "src/static/avatar/prosecution.png", 
            "defense": "src/static/avatar/defense.png", 
            "prosecution_defeated": "src/static/avatar/prosecution_defeated.png",
            "defense_defeated": "src/static/avatar/defense_defeated.png"
            }
        
        
        messages = []
        
        for msg in arguments.get('nodes', []):
            avatar = ""
            colored_text = ""
            if msg['node_id'] in accepted_arguments:
                if msg['role'] == "prosecution":
                    avatar =avatar_images["prosecution"]
                else:
                    avatar = avatar_images["defense"]
                colored_text = f":blue[{msg['node_id']}] :red[({msg['node_type'].lower()})] {msg['text']}"
            else:
                if msg['role'] == "prosecution":
                    avatar = avatar_images["prosecution_defeated"]
                else:
                    avatar = avatar_images["defense_defeated"]
                colored_text = f":green[{msg['node_id']}] :orange[({msg['node_type'].lower()})] :gray[{msg['text']}]" 
            
            message = {
                    "author": msg["role"],
                    "avatar" : avatar,
                    "message": colored_text
                    }            
                
            messages.append(message)
            
        for message in messages:
            with self._manager:
                with st.chat_message(message["author"], avatar=message['avatar']):
                # with st.chat_message(message["author"]):
                    st.write(message["message"])
                       
            # with self._manager:
                
            #     avatar = {"role": msg["role"], "image": ":cop:" if msg["role"] == "prosecution" else ":bust_in_silhouette:"}
                
            #     message = st.chat_message(avatar['role'], avatar=avatar['image'])
            #     message.write(msg['text'])
                # left, right = st.columns([5, 1])
                # left.write(msg['text'])
                # delete_button = right.button("❌", key=f"del_{i}")
                # if delete_button:
                #     self._delete_node(msg["node_id"])
