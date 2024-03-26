import json
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings.sentence_transformer import SentenceTransformerEmbeddings
from app.logger import logger

class ChromaSearcher:
    def __init__(self):
        self.get_chroma()
    
    def get_chroma(self):
        embedding_function = SentenceTransformerEmbeddings(model_name="snunlp/KR-SBERT-V40K-klueNLI-augSTS")
        vector_store = Chroma(persist_directory="app/db/chromadb", embedding_function=embedding_function)
        self.chroma = vector_store

    def search_chroma(self, query):
        '''
        Search the chroma retriever
        '''
        results = self.chroma.similarity_search(query)
        most_similar_case = results[0]
        target_case_id = most_similar_case.metadata['case_id']
        target_crime_fact = most_similar_case.page_content
        defendant_opinion = most_similar_case.metadata['defendant_opinion']
        prosecutor_opinion = most_similar_case.metadata['prosecutor_opinion']
        search_result_dict = {
            "case_id" : target_case_id,
            "crime_fact" : target_crime_fact,
            "defendant_opinion" : defendant_opinion,
            "prosecutor_opinion" : prosecutor_opinion
        }
        logger.debug(f"Find a defendant opinion and prosecutor opinion from case_id {target_case_id}")
        return search_result_dict
    
    
if __name__ == "__main__":
    rag = ChromaSearcher()
    query = "피고인은 2018. 5. 16.경 불상지에서 D에게 위 게임 계정을 500만 원을 받고 양도하였고, D가 위 계정명을 'E'로 변경하여 사용하다가 2018. 9. 12. 경 다시 피해자 F에게 400만 원을 받고 양도하여 위 계정에 대한 접근권한이 없었음에도 불구하고, 2019. 2. 11.경 불상지에서 B 게임을 관리하는 주식회사 G 인터넷 홈페이지에 접속하여 본인인증 절차를 이용하여 위 계정에 대한 새로운 비밀번호를 부여받고 피해자가 기존에 사용하고 있던 계정의 비밀번호를 배제하는 방법으로 피해자의 접근을 차단시켰다."
    result = rag.search_chroma(query)
    logger.debug(f"Retriever Result : {result}")