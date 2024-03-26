import json
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings.sentence_transformer import (
    SentenceTransformerEmbeddings,
)
from langchain.docstore.document import Document

class ChromaBuilder:
    def __init__(self):
        self.chroma_data_path = "test/db_data/alex_en_db_126.json"
        self.docs = []
        self.data_lst = []
        self.opinion_lst = []
        self.case_id_lst = []
        self.total_data = []
        self.build_chroma()
    
    def prepare_chroma_data(self):
        with open(self.chroma_data_path, 'r', encoding='utf-8-sig') as case:
            datas = json.load(case)
            meta_data = []
            for i in datas:
                self.data_lst.append(i['EN_crime_fact'])
                row = {
                    "case_id" : i['case_id'],
                    "judgment" : i['EN_judgment'],
                    "defendant_opinion" : i['EN_opinions']['defense'],
                    "prosecutor_opinion" : i['EN_opinions']['prosecution']
                }
                meta_data.append(row)

        for i in range(len(list(set(self.data_lst)))):
            self.docs.append(Document(page_content=self.data_lst[i], metadata=meta_data[i]))

    def build_chroma(self):
        '''
        Use if you want to build the chroma retriever from other documents
        '''
        self.prepare_chroma_data()
        embedding_function = SentenceTransformerEmbeddings(model_name="snunlp/KR-SBERT-V40K-klueNLI-augSTS")
        vector_store = Chroma.from_documents(persist_directory="backend/app/db/chromadb", embedding=embedding_function, documents=self.docs)
        self.chroma = vector_store
    
    
if __name__ == "__main__":
    rag = ChromaBuilder()