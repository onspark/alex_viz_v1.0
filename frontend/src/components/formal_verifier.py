import streamlit as st 
from src.settings import logger
import requests


class FormalVerifier:
    def __init__(self, parent_container=None, clicked_node_id='', data_manager=None):
        self._parent_container = parent_container
        self._clicked_node_id = clicked_node_id
        self._data_manager = data_manager
        self._render_verifier()

    def _render_verifier(self):
        """Render the formal verifier UI components."""
        verifier = self._parent_container.container()
        with verifier:
            self._render_clicked_node_id()
            self._render_colored_text()

    def _render_clicked_node_id(self):
        """Display the clicked node expanded label."""
        if self._clicked_node_id:
            clicked_node_label_expanded = self._data_manager.get_node(self._clicked_node_id).get("label_expanded", {})
        else:
            clicked_node_label_expanded = "No node selected."            
        st.markdown(f"Clicked Node Formula: `{clicked_node_label_expanded}`")

    def _render_colored_text(self):
        """Display colored text."""
        if self._clicked_node_id:
            role = self._data_manager.get_node(self._clicked_node_id).get("role", "")
            text = self._data_manager.get_node(self._clicked_node_id).get("text", "")
        else:
            role = ""
            text = ""
        
        st.markdown(f'''
            :red[{role.upper()}]\n
            :gray[{text}]
                    ''')
        
        """
        st.markdown('''
            :red[Streamlit] :orange[can] :green[write] :blue[text] :violet[in]
            :gray[pretty] :rainbow[colors].''')
        """
        

