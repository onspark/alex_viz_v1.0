import streamlit as st 
from src.settings import logger
import requests
import json 


class DocumentViewer:
    def __init__(self, parent_container=None):
        self.parent_container = parent_container
        # self.api_endpoint = "http://localhost:8000/api/v0.1.0/test_case"
        # self.api_endpoint = "http://localhost:8000/api/v0.1.0/run_alex_viz"
        self.setup()

    def setup(self):
        file_upload_box = self.parent_container.expander("📂 Load Case From JSON")

        reader = self.parent_container.expander("📑 Case Description")
        with reader:
            self.document_text_area = st.text_area("Case Description", value=st.session_state['document_text'], height=300, label_visibility='collapsed')
            if self.document_text_area:
                st.session_state['document_text'] = self.document_text_area
                # logger.info(f"Document text: {st.session_state['document_text'][:15]}...")
        self.load_from_json(file_upload_box)
    
    def load_from_json(self, box):
        with box:
            uploaded_file = box.file_uploader("Upload JSON Files", type=['json'], accept_multiple_files=False)
            left, mid, right = box.columns([1, 1, 1])
            mid_btn = mid.button(":part_alternation_mark: **Visualize**")
            
            if mid_btn and uploaded_file:
                logger.info(f"Right button clicked with file: {uploaded_file}")
                data = json.load(uploaded_file)
                
                if data:
                    st.session_state['document_text'] = data.get('crime_fact','')
                    st.session_state['arguments'] = data['arguments']
                    target_node = data['target_node']
                    if target_node:
                        st.session_state['target_node_id'] = target_node['node_id']
                    st.session_state['target_reason'] = data['target_reason']
                    st.session_state['selected_role'] = data['current_role']
                    st.rerun()
                