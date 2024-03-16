import streamlit as st


# TODO: Add update graph data method for comparing exsting graph data with new data and return the updated graph data


class DataManager:
    def __init__(self):
        # Initialize 'arguments' in session state if it does not exist
        if 'document_text' not in st.session_state:
            st.session_state['document_text'] = "성명불상의 보이스피싱 조직은 불특정 다수의 피해자들에게 \"저금리 대출을 해주겠으니 기존 대출금을 직원에게 상환하라\"는 취지로 거짓말하는 방법으로 금원을 편취하는 조직이며, 모든 범행을 계획하고 지시하는 '총책', 피해금을 입금받을 계좌 및 이와연결된 체크카드를 수집하는 '모집책', 위 체크카드를 전달받아 입금된 돈을 인출하여 보이스피싱 조직원에서 전달하는 '수거책 및 인출책' 등으로 구성되어 있다.\n피고인은 2020. 7. 2.경 성명불상자로부터 \"대출을 해주겠다, 체크카드를 보내주면 이자를 인출하는 용도로 사용한다\"는 제안을 받고 피고인의 체크카드를 성명불상자에게 넘겨주었으나 곧 보이스피싱 사기 범행에 이용되어 위 체크카드와 연결된 은행 계좌가 정지되자 체크카드가 범죄에 사용되었음을 인지하였음에도 위 성명불상자로부터 \"택배로 체크카드를 받아 체크카드에 입금된 돈을 인출해주면 인출액의 3%를 주겠다\"는 제안을 수락하여 '수거책 및 인출책' 역할을 하기로 하였다.\n성명불상의 보이스피싱 조직원은 2020. 7. 21.경 피해자 AF에게 은행직원을 사칭하며 '저금리로 대출을 해주겠다, 기존에 대출받은 1,000만원을 갚아야 되니 우리가 보내는 수금직원에게 상환하라'는 취지로 거짓말하여 이에 속은 피해자로 하여금 같은 달 24.경 울산 남구 AG 앞에서 현금을 가지고 기다리도록 하였다.\n피고인은 위 성명불상자와의 공모에 따라 2020. 7. 24. 17:30경 위 성명불상자가 알려준 주소인 위 장소에서 피해자에게 \"AD 대리이고 사원번호 AE번이다\"라는 취지로 자신을 소개하고 피해자로부터 875만원을 교부받았다."
            
        if 'arguments' not in st.session_state:
            st.session_state['arguments'] = {
                'nodes': [],
                'edges': [],
                'extensions': {
                    'grounded': [],
                }
            }
            
        if 'target_node_id' not in st.session_state:
            st.session_state['target_node_id'] = ''
        
        if 'target_reason' not in st.session_state:
            st.session_state['target_reason'] = ''
            
        if 'selected_role' not in st.session_state:
            st.session_state['selected_role'] = 'defense'

    def get_target_node(self):
        if st.session_state['target_node_id']:
            return self.get_node(st.session_state['target_node_id'])

    def get_node(self, node_id):
        for node in st.session_state['arguments']['nodes']:
            if node['node_id'] == node_id:
                return node
        return None

    def add_node(self, node):
        st.session_state['arguments']['nodes'].append(node)
    
    def add_edge(self, edge):
        st.session_state['arguments']['edges'].append(edge)
    
    def update_node(self, node_id, new_data):
        for node in st.session_state['arguments']['nodes']:
            if node['node_id'] == node_id:
                node.update(new_data)
                break
    
    def delete_node(self, node_id):
        # Delete node
        st.session_state['arguments']['nodes'] = [
            node for node in st.session_state['arguments']['nodes'] if node['node_id'] != node_id
        ]
        # Delete associated edges
        st.session_state['arguments']['edges'] = [
            edge for edge in st.session_state['arguments']['edges']
            if edge['from'] != node_id and edge['to'] != node_id
        ]
        # Update extensions here if necessary based on the node deletion
    
    def get_arguments(self):
        return st.session_state['arguments']
    
    def clear_document_text(self):
        st.session_state['document_text'] = ''
    
    def clear_arguments(self):
        st.session_state['arguments'] = {
            'nodes': [],
            'edges': [],
            'extensions': {
                'complete': [],
                'grounded': [],
                'preferred': []
            }
        }
        st.session_state['target_node_id'] = ''
        st.session_state['target_reason'] = ''
        st.session_state['selected_role'] = 'defense'
