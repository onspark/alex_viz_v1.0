import json
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings.sentence_transformer import (
    SentenceTransformerEmbeddings,
)
from langchain.docstore.document import Document
from app.logger import logger
from app.utils import save_json_db

#FIXME: Change retriever method 
#FIXME: Load sentence transformer model only once
class ChromaSearcher:
    def __init__(self):
        # self.chroma_data_path = "/home/hmc/Desktop/work/alex_viz/backend/app/data/no_duplicates_computer_fraud.json"
        # self.chroma_data_path = "app/data/no_duplicates_computer_fraud.json"
        self.chroma_data_path = "app/data/0315_train_171.json"
        self.docs = []
        self.data_lst = []
        self.opinion_lst = []
        self.case_id_lst = []
        self.total_data = []
        self._retriever = None 
        # self.build_chroma()
        self.get_chroma()
    
    def prepare_chroma_data(self):
        with open(self.chroma_data_path, 'r', encoding='utf-8-sig') as case:
            datas = json.load(case)
            meta_data = []
            for i in datas:
                # prosecutor_lst = i['count_args']
                # prosecutor_opinion_lst = []
                # for element in prosecutor_lst:
                #     prosecutor_opinion_lst.append(element['text'])
                #     prosecutor_opinion_lst.append(element['reason'])
                # prosecutor_str = "\n".join(prosecutor_opinion_lst)
                
                self.data_lst.append(i['crime_fact'])

                row = {
                    "case_id" : i['case_id'],
                    "judgment" : i['judgment'],
                    "defendant_opinion" : i['opinion_result'][1],
                    "prosecutor_opinion" : i['opinion_result'][-1]
                }
                meta_data.append(row)
        
        
        print(f"meta_data : {len(meta_data)}")
        print(f"self.data : {len(list(set(self.data_lst)))}")

        for i in range(len(list(set(self.data_lst)))):
            self.docs.append(Document(page_content=self.data_lst[i], metadata=meta_data[i]))
        print(f"docs : {len(self.docs)}")

    def build_chroma(self):
        '''
        Use if you want to build the chroma retriever from other documents
        '''
        
        self.prepare_chroma_data()

        embedding_function = SentenceTransformerEmbeddings(model_name="snunlp/KR-SBERT-V40K-klueNLI-augSTS")
        vector_store = Chroma.from_documents(persist_directory="app/db/chromadb", embedding=embedding_function, documents=self.docs)
        self.chroma = vector_store
    
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
        defendant_opinion = most_similar_case.metadata['defendant_opinion']
        prosecutor_opinion = most_similar_case.metadata['prosecutor_opinion']
        search_result_dict = {
            "case_id" : target_case_id,
            "defendant_opinion" : defendant_opinion,
            "prosecutor_opinion" : prosecutor_opinion
        }
        save_json_db(search_result_dict)
        logger.debug(f"Find a defendant opinion and prosecutor opinion from case_id {target_case_id}")
        return search_result_dict

    # @property
    # def retriever(self):
    #     return self._retriever
    
    
if __name__ == "__main__":
    rag = ChromaSearcher()
    rag.build_chroma()
    # query = "범죄사실\n「2020고단1312」\n성명불상의 보이스피싱 조직은 불특정 다수의 피해자들에게 카카오톡으로 가족을 사칭하여 신용카드와 신분증 등 개인정보를 넘겨받고 원격제어 어플리케이션을 휴대폰에 설치하도록 유도하여 피해자들 명의의 신용카드로 결제하거나 개인정보를 이용하여 계좌를 개설한 후 대출을 받는 등의 방법으로 금원을 편취하는 조적이며, 모든 범행을 계획하고 지시하는 '총책', 피해금을 입금 받을 계좌 및 이와 연결된 체크카드를 수집하는 '모집책', 위 체크카드를 전달받아 입금된 돈을 인출하여 보이스피싱 조직원에게 전달하는 '수거책 및 인출책' 등으로 구성되어있다.\n피고인은 2020. 7. 초순경 성명불상자(일명 F')로부터 '대출을 해주겠다, 체크카드를 보내주면 이자를 인출하는 용도로 사용한다'는 제안을 받고 피고인의 체크카드를 성명불상자에게 넘겨주었으나 곧 보이스피싱 사기범행에 이용되어 위 체크카드와 연결된은행 계좌가 정지되자 체크카드가 범죄에 사용되었음을 인지하였음에도 위 성명불상자로부터 '택배로 체크카드를 받아 체크카드에 입금된 돈을 인출해주면 인출액의 3%를주겠다'는 제안을 수락하여 '수거책 및 인출책' 역할을 하기로 하였다.\n1. 전자금융거래법위반\n누구든지 접근매체를 사용 및 관리함에 있어서 다른 법률에 특별한 규정이 없는 한 대가를 수수·요구 또는 약속하거나 범죄에 이용될 것을 알면서 접근매체를 보관·전달·유통하는 행위를 하여서는 아니 된다.\n피고인은 성명불상자의 지시에 따라 2020. 7. 9.경 부산 연제구 G에 있는 H편의점에서 I 명의의 J 체크카드(K)를 택배로 전달받아 보관한 것을 비롯하여 그 때부터 2020. 8. 18. 경까지 별지 범죄일람표 기재와 같이 총 5장의 체크카드를 전달받아 보관하였다. 이로써 피고인은 대가를 수수하고 범죄에 이용될 것을 알면서 접근매체를 보관·전달하는 행위를 하였다.\n2. 컴퓨터등사용사기방조\n성명불상의 보이스피싱 조직원은 2020. 7. 9.경 카카오톡으로 피해자 E에게 그의 딸을 사칭하며 '엄마 나 휴대폰 고장났는데 문화상품권 구매해야 되니 주민등록증, L 신용카드와 계좌번호, 비밀번호를 알려달라'고 거짓말하여 이에 속은 피해자로부터 위 정보를 넘겨받고 피해자로 하여금 휴대전화에 원격제어 어플리케이션을 설치하게 한 후,성명불상의 보이스피싱 조직원은 원격제어 어플리케이션을 이용하여 피해자의 개인정보를 이용하여 같은 날 피해자의 L 신용카드를 이용하여 인터넷에서 1,386,000원 상당의 물품을 구매하고 피해자 명의로 M계좌를 개설하여 634만원을 대출받은 뒤 I 명의의 J 계좌(N)로 이체함으로써 컴퓨터등 정보처리장치에 권한 없이 정보를 입력·변경하여 정보처리를 함으로써 재산상 이익을 취득하였다.\n피고인은 성명불상자의 지시를 받아 2020. 7. 9.경 부산 연제구 0은행 연산지점에서 제1항과 같이 전달받은 1 명의의 J 체크카드를 이용하여 200만원을 인출한 후 자신의수수료를 제외한 나머지 돈을 성명불상자가 지시하는 계좌로 무통장 송금하였다.\n이로써 피고인은 성명불상의 보이스피싱 조직원의 사기범행을 용이하게 하여 방조하였다.\n「2020고단1554」\n성명불상의 보이스피싱 조직은 불특정 다수의 피해자들에게 \"저금리 대출을 해주겠으니 기존 대출금을 직원에게 상환하라\"는 취지로 거짓말하는 방법으로 금원을 편취하는 조직이며, 모든 범행을 계획하고 지시하는 '총책', 피해금을 입금받을 계좌 및 이와연결된 체크카드를 수집하는 '모집책', 위 체크카드를 전달받아 입금된 돈을 인출하여 보이스피싱 조직원에게 전달하는 '수거책 및 인출책' 등으로 구성되어있다.\n피고인은 2020. 7. 초순경 성명불상자로부터 \"대출을 해주겠다, 체크카드를 보내주면 이자를 인출하는 용도로 사용한다\"는 제안을 받고 피고인의 체크카드를 성명불상자에게 넘겨주었으나 곧 보이스피싱 사기 범행에 이용되어 위 체크카드와 연결된 은행 계좌가 정지되자 체크카드가 범죄에 사용되었음을 인지하였음에도 위 성명불상자로부터 \"택배로 체크카드를 받아 체크카드에 입금된 돈을 인출해주면 인출액의 3%를 주겠다\"는 제안을 수락하여 '수거책 및 인출책' 역할을 하기로 하였다.\n1. 피해자 B에 대한 사기\n성명불상의 보이스피싱 조직원은 2020. 7. 15.경 피해자 B에게 은행직원을 사칭하며 \"저금리 정부지원자금 대출이 가능하다, P을 통해 보증서를 발급받아야하니 보증료1,000만 원을 입금하라\"는 취지로 거짓말하여 이에 속은 피해자로 하여금 같은 달 17.경 Q 명의의 L은행 계좌(R)로 1,000만원을 송금하게 하여 이를 편취하였다.\n피고인은 위 성명불상자와의 공모에 따라 2020. 7. 17.경 부산시 연제구 S에 있는 L은행 T지점에서 위 성명불상자로부터 미리 택배로 전달받은 위 Q 명의의 계좌와 연결된 체크카드를 이용하여 600만원을 인출하고, 다음 날 같은 구 U에 있는 L은행 연산동지점에서 같은 방법으로 400만원을 인출한 후 자신의 수수료를 제외한 나머지 돈을위 성명불상자가 지시하는 계좌로 무통장 송금하였다.\n이로써 피고인은 성명불상의 보이스피싱 조직원과 공모하여 피해자를 기망하여 이에 속은 피해자로부터 1,000만원을 송금받아 편취하였다.\n2. 피해자 C에 대한 사기\n성명불상의 보이스피싱 조직원은 2020. 7. 16.경 피해자 C에게 은행직원을 사칭하며 \"V은행인데 2,000만원 대출이 가능하다, W 미납금을 우선 상환해야된다. 지정하는 계좌로 돈을 입금하라\"는 취지로 거짓말하여 이에 속은 피해자로 하여금 다음 날X명의의 기업은행 계좌(Y)로 994,600원을 송금하게 하여 이를 편취하였다.\n피고인은 위 성명불상자와의 공모에 따라 2020. 7. 17.경 부산시 연제구 Z에 있는 L은행 연산역지점에서 위 성명불상자로부터 미리 택배로 전달받은 위 X 명의의 계좌와 연결된 체크카드를 이용하여 99만원을 인출한 후 자신의 수수료를 제외한 나머지 돈을성명불상자가 지시하는 계좌로 무통장 송금하였다.\n이로써 피고인은 성명불상의 보이스피싱 조직원과 공모하여 피해자를 기망하여 이에 속은 피해자로부터 994,600원을 송금받아 편취하였다.\n3. 피해자 D에 대한 사기\n성명불상의 보이스피싱 조직원은 2020. 7. 22. 경 피해자 D에게 은행직원을 사칭하며 \"AA이다, 저금리 대환대출 상품이 있는데 기존의 대출금이 있다면 우리가 보내는 수금직원에게 상환하여 주면 6,000만원의 저금리 대출을 해주겠다\"는 취지로 거짓말하여 이에 속은 피해자로 하여금 같은 달 24.경 김해시 AB에 있는 AC 편의점 앞 노상에서 현금을 가지고 기다리도록 하였다.\n피고인은 위 성명불상자와의 공모에 따라 2020. 7. 24. 17:30경 위 성명불상자가 알려준 주소인 위 장소에서 피해자에게 \"AD 대리이고 사원번호 AE번이다\"라는 취지로 자신을 소개하고 피해자로부터 875만원을 교부받았다.\n이로써 피고인은 성명불상의 보이스피싱 조직원과 공모하여 피해자를 기망하여 이에 속은 피해자로부터 875만원을 교부받아 편취하였다.\n「2020고단1783」\n성명불상의 보이스피싱 조직은 불특정 다수의 피해자들에게 \"저금리 대출을 해주겠으니 기존 대출금을 직원에게 상환하라\"는 취지로 거짓말하는 방법으로 금원을 편취하는 조직이며, 모든 범행을 계획하고 지시하는 '총책', 피해금을 입금받을 계좌 및 이와연결된 체크카드를 수집하는 '모집책', 위 체크카드를 전달받아 입금된 돈을 인출하여 보이스피싱 조직원에서 전달하는 '수거책 및 인출책' 등으로 구성되어 있다.\n피고인은 2020. 7. 2.경 성명불상자로부터 \"대출을 해주겠다, 체크카드를 보내주면 이자를 인출하는 용도로 사용한다\"는 제안을 받고 피고인의 체크카드를 성명불상자에게 넘겨주었으나 곧 보이스피싱 사기 범행에 이용되어 위 체크카드와 연결된 은행 계좌가 정지되자 체크카드가 범죄에 사용되었음을 인지하였음에도 위 성명불상자로부터 \"택배로 체크카드를 받아 체크카드에 입금된 돈을 인출해주면 인출액의 3%를 주겠다\"는 제안을 수락하여 '수거책 및 인출책' 역할을 하기로 하였다.\n성명불상의 보이스피싱 조직원은 2020. 7. 21.경 피해자 AF에게 은행직원을 사칭하며 '저금리로 대출을 해주겠다, 기존에 대출받은 1,000만원을 갚아야 되니 우리가 보내는 수금직원에게 상환하라'는 취지로 거짓말하여 이에 속은 피해자로 하여금 같은 달 24.경 울산 남구 AG 앞에서 현금을 가지고 기다리도록 하였다.\n피고인은 성명불상자와의 공모에 따라 2020. 7. 24. 16:26경 성명불상자가 알려준 주소인 위 장소에서 피해자로부터 1,000만원을 교부받았다.\n이로써 피고인은 성명불상의 보이스피싱 조직원과 공모하여 피해자를 기망하여 이에 속은 피해자로부터 1,000만원을 교부받았다."

    # print(f"answer : CASE000313202102042020077001312 ")
    # result_dic = rag.search_chroma(query=query)
    # print(f"result_dic : {result_dic}")