from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from app.components.generator import ChromaSearcher
from app.components.llm import OpenAIModel
from app.utils import rag_converter
from app.logger import logger

class RagGenerator:
    def __init__(self):
        self.openai_model = OpenAIModel(model_type="gpt-4-turbo-generator")
        self.llm = self.openai_model.get_llm()
        
        self.chroma_search = ChromaSearcher()
        
    
    def execute_langchain(self, 
                          crime_fact, 
                          role,
                          main_claim="",
                          target_node=None,
                          history="", 
                          action_option=1): #action_option=1 (Initialize building claims) as default
        
        chroma_result = self.chroma_search.search_chroma(crime_fact)
        
        cf_template, query = self.openai_model.build_template_by_role(
            crime_fact=crime_fact,
            opinions = chroma_result, 
            role=role, 
            main_claim=main_claim, 
            target_node=target_node, 
            history=history, 
            action_option=action_option)
        
        try:
            logger.info(f"cf_template : {cf_template}")
            rag_chain = (
                    {"question": RunnablePassthrough()}
                    | cf_template
                    | self.llm
                    | StrOutputParser()
            )
            rag_result = rag_chain.invoke(query)
            logger.debug(f"RAG RESULT returned: {rag_result}")
            
            rag_result_formatted = rag_converter(
                output_str=rag_result, 
                action_option=action_option,
                role=role,
                target_node=target_node,
                main_claim=main_claim
                )
            logger.debug(f"RAG RESULT formatted in generator: {rag_result_formatted}")
            return rag_result_formatted
        
        except Exception as e:
            logger.error(f"Error in generator: {e}")
            return None
       
       
#python -m app.components.generator.rag_generator 
if __name__ == '__main__':
    fact = """
    범죄사실\n「2020고단1312」\n성명불상의 보이스피싱 조직은 불특정 다수의 피해자들에게 카카오톡으로 가족을 사칭하여 신용카드와 신분증 등 개인정보를 넘겨받고 원격제어 어플리케이션을 휴대폰에 설치하도록 유도하여 피해자들 명의의 신용카드로 결제하거나 개인정보를 이용하여 계좌를 개설한 후 대출을 받는 등의 방법으로 금원을 편취하는 조적이며, 모든 범행을 계획하고 지시하는 '총책', 피해금을 입금 받을 계좌 및 이와 연결된 체크카드를 수집하는 '모집책', 위 체크카드를 전달받아 입금된 돈을 인출하여 보이스피싱 조직원에게 전달하는 '수거책 및 인출책' 등으로 구성되어있다.\n피고인은 2020. 7. 초순경 성명불상자(일명 F')로부터 '대출을 해주겠다, 체크카드를 보내주면 이자를 인출하는 용도로 사용한다'는 제안을 받고 피고인의 체크카드를 성명불상자에게 넘겨주었으나 곧 보이스피싱 사기범행에 이용되어 위 체크카드와 연결된은행 계좌가 정지되자 체크카드가 범죄에 사용되었음을 인지하였음에도 위 성명불상자로부터 '택배로 체크카드를 받아 체크카드에 입금된 돈을 인출해주면 인출액의 3%를주겠다'는 제안을 수락하여 '수거책 및 인출책' 역할을 하기로 하였다.\n1. 전자금융거래법위반\n누구든지 접근매체를 사용 및 관리함에 있어서 다른 법률에 특별한 규정이 없는 한 대가를 수수·요구 또는 약속하거나 범죄에 이용될 것을 알면서 접근매체를 보관·전달·유통하는 행위를 하여서는 아니 된다.\n피고인은 성명불상자의 지시에 따라 2020. 7. 9.경 부산 연제구 G에 있는 H편의점에서 I 명의의 J 체크카드(K)를 택배로 전달받아 보관한 것을 비롯하여 그 때부터 2020. 8. 18. 경까지 별지 범죄일람표 기재와 같이 총 5장의 체크카드를 전달받아 보관하였다. 이로써 피고인은 대가를 수수하고 범죄에 이용될 것을 알면서 접근매체를 보관·전달하는 행위를 하였다.\n2. 컴퓨터등사용사기방조\n성명불상의 보이스피싱 조직원은 2020. 7. 9.경 카카오톡으로 피해자 E에게 그의 딸을 사칭하며 '엄마 나 휴대폰 고장났는데 문화상품권 구매해야 되니 주민등록증, L 신용카드와 계좌번호, 비밀번호를 알려달라'고 거짓말하여 이에 속은 피해자로부터 위 정보를 넘겨받고 피해자로 하여금 휴대전화에 원격제어 어플리케이션을 설치하게 한 후,성명불상의 보이스피싱 조직원은 원격제어 어플리케이션을 이용하여 피해자의 개인정보를 이용하여 같은 날 피해자의 L 신용카드를 이용하여 인터넷에서 1,386,000원 상당의 물품을 구매하고 피해자 명의로 M계좌를 개설하여 634만원을 대출받은 뒤 I 명의의 J 계좌(N)로 이체함으로써 컴퓨터등 정보처리장치에 권한 없이 정보를 입력·변경하여 정보처리를 함으로써 재산상 이익을 취득하였다.\n피고인은 성명불상자의 지시를 받아 2020. 7. 9.경 부산 연제구 0은행 연산지점에서 제1항과 같이 전달받은 1 명의의 J 체크카드를 이용하여 200만원을 인출한 후 자신의수수료를 제외한 나머지 돈을 성명불상자가 지시하는 계좌로 무통장 송금하였다.\n이로써 피고인은 성명불상의 보이스피싱 조직원의 사기범행을 용이하게 하여 방조하였다.\n「2020고단1554」\n성명불상의 보이스피싱 조직은 불특정 다수의 피해자들에게 \"저금리 대출을 해주겠으니 기존 대출금을 직원에게 상환하라\"는 취지로 거짓말하는 방법으로 금원을 편취하는 조직이며, 모든 범행을 계획하고 지시하는 '총책', 피해금을 입금받을 계좌 및 이와연결된 체크카드를 수집하는 '모집책', 위 체크카드를 전달받아 입금된 돈을 인출하여 보이스피싱 조직원에게 전달하는 '수거책 및 인출책' 등으로 구성되어있다.\n피고인은 2020. 7. 초순경 성명불상자로부터 \"대출을 해주겠다, 체크카드를 보내주면 이자를 인출하는 용도로 사용한다\"는 제안을 받고 피고인의 체크카드를 성명불상자에게 넘겨주었으나 곧 보이스피싱 사기 범행에 이용되어 위 체크카드와 연결된 은행 계좌가 정지되자 체크카드가 범죄에 사용되었음을 인지하였음에도 위 성명불상자로부터 \"택배로 체크카드를 받아 체크카드에 입금된 돈을 인출해주면 인출액의 3%를 주겠다\"는 제안을 수락하여 '수거책 및 인출책' 역할을 하기로 하였다.\n1. 피해자 B에 대한 사기\n성명불상의 보이스피싱 조직원은 2020. 7. 15.경 피해자 B에게 은행직원을 사칭하며 \"저금리 정부지원자금 대출이 가능하다, P을 통해 보증서를 발급받아야하니 보증료1,000만 원을 입금하라\"는 취지로 거짓말하여 이에 속은 피해자로 하여금 같은 달 17.경 Q 명의의 L은행 계좌(R)로 1,000만원을 송금하게 하여 이를 편취하였다.\n피고인은 위 성명불상자와의 공모에 따라 2020. 7. 17.경 부산시 연제구 S에 있는 L은행 T지점에서 위 성명불상자로부터 미리 택배로 전달받은 위 Q 명의의 계좌와 연결된 체크카드를 이용하여 600만원을 인출하고, 다음 날 같은 구 U에 있는 L은행 연산동지점에서 같은 방법으로 400만원을 인출한 후 자신의 수수료를 제외한 나머지 돈을위 성명불상자가 지시하는 계좌로 무통장 송금하였다.\n이로써 피고인은 성명불상의 보이스피싱 조직원과 공모하여 피해자를 기망하여 이에 속은 피해자로부터 1,000만원을 송금받아 편취하였다.\n2. 피해자 C에 대한 사기\n성명불상의 보이스피싱 조직원은 2020. 7. 16.경 피해자 C에게 은행직원을 사칭하며 \"V은행인데 2,000만원 대출이 가능하다, W 미납금을 우선 상환해야된다. 지정하는 계좌로 돈을 입금하라\"는 취지로 거짓말하여 이에 속은 피해자로 하여금 다음 날X명의의 기업은행 계좌(Y)로 994,600원을 송금하게 하여 이를 편취하였다.\n피고인은 위 성명불상자와의 공모에 따라 2020. 7. 17.경 부산시 연제구 Z에 있는 L은행 연산역지점에서 위 성명불상자로부터 미리 택배로 전달받은 위 X 명의의 계좌와 연결된 체크카드를 이용하여 99만원을 인출한 후 자신의 수수료를 제외한 나머지 돈을성명불상자가 지시하는 계좌로 무통장 송금하였다.\n이로써 피고인은 성명불상의 보이스피싱 조직원과 공모하여 피해자를 기망하여 이에 속은 피해자로부터 994,600원을 송금받아 편취하였다.\n3. 피해자 D에 대한 사기\n성명불상의 보이스피싱 조직원은 2020. 7. 22. 경 피해자 D에게 은행직원을 사칭하며 \"AA이다, 저금리 대환대출 상품이 있는데 기존의 대출금이 있다면 우리가 보내는 수금직원에게 상환하여 주면 6,000만원의 저금리 대출을 해주겠다\"는 취지로 거짓말하여 이에 속은 피해자로 하여금 같은 달 24.경 김해시 AB에 있는 AC 편의점 앞 노상에서 현금을 가지고 기다리도록 하였다.\n피고인은 위 성명불상자와의 공모에 따라 2020. 7. 24. 17:30경 위 성명불상자가 알려준 주소인 위 장소에서 피해자에게 \"AD 대리이고 사원번호 AE번이다\"라는 취지로 자신을 소개하고 피해자로부터 875만원을 교부받았다.\n이로써 피고인은 성명불상의 보이스피싱 조직원과 공모하여 피해자를 기망하여 이에 속은 피해자로부터 875만원을 교부받아 편취하였다.\n「2020고단1783」\n성명불상의 보이스피싱 조직은 불특정 다수의 피해자들에게 \"저금리 대출을 해주겠으니 기존 대출금을 직원에게 상환하라\"는 취지로 거짓말하는 방법으로 금원을 편취하는 조직이며, 모든 범행을 계획하고 지시하는 '총책', 피해금을 입금받을 계좌 및 이와연결된 체크카드를 수집하는 '모집책', 위 체크카드를 전달받아 입금된 돈을 인출하여 보이스피싱 조직원에서 전달하는 '수거책 및 인출책' 등으로 구성되어 있다.\n피고인은 2020. 7. 2.경 성명불상자로부터 \"대출을 해주겠다, 체크카드를 보내주면 이자를 인출하는 용도로 사용한다\"는 제안을 받고 피고인의 체크카드를 성명불상자에게 넘겨주었으나 곧 보이스피싱 사기 범행에 이용되어 위 체크카드와 연결된 은행 계좌가 정지되자 체크카드가 범죄에 사용되었음을 인지하였음에도 위 성명불상자로부터 \"택배로 체크카드를 받아 체크카드에 입금된 돈을 인출해주면 인출액의 3%를 주겠다\"는 제안을 수락하여 '수거책 및 인출책' 역할을 하기로 하였다.\n성명불상의 보이스피싱 조직원은 2020. 7. 21.경 피해자 AF에게 은행직원을 사칭하며 '저금리로 대출을 해주겠다, 기존에 대출받은 1,000만원을 갚아야 되니 우리가 보내는 수금직원에게 상환하라'는 취지로 거짓말하여 이에 속은 피해자로 하여금 같은 달 24.경 울산 남구 AG 앞에서 현금을 가지고 기다리도록 하였다.\n피고인은 성명불상자와의 공모에 따라 2020. 7. 24. 16:26경 성명불상자가 알려준 주소인 위 장소에서 피해자로부터 1,000만원을 교부받았다.\n이로써 피고인은 성명불상의 보이스피싱 조직원과 공모하여 피해자를 기망하여 이에 속은 피해자로부터 1,000만원을 교부받았다."""
    rr = RagGenerator()
    retriever_result = rr.execute_langchain(
        crime_fact=fact, 
        role="defense", 
        main_claim="피고인은 피해자 C에게 전화한 사실은 인정하지만, 그 전화는 피해자를 도와주기 위한 선의에서 이루어진 것이며, 불법 자금 세탁에 관련된 의도나 목적이 전혀 없었다. 따라서 피고인에게 사기의 고의가 없었음을 주장한다.",
        target_node={"text":"피고인은 피해자 C에게 '선생님 명의의 SC제일은행 계좌가 불법 자금 세탁에 이용되었습니다.'라고 알리고, 피해자로 등록하려면 안내하는 사이트에 들어가서 선생님이 사용하였다고 말했다. 이는 피해자가 자신의 계좌를 확인하고 문제가 있을 경우 대응할 수 있도록 하는 의도에서 비롯된 것이다.", "node_type":"datum"},
        history="",
        action_option=1)
    # print(retriever_result)
    # retriever_result = rr.execute_langchain(
    #     crime_fact=fact, 
    #     role="prosecution", 
    #     main_claim="피고인은 고도의 계획 하에 피해자 C에게 접근, 거짓된 신분을 이용해 피해자를 기망하였으며, 이는 명백한 사기 행위로서 피해자에게 경제적 손실을 입혔습니다.",
    #     target_node={"text":"피고인은 피해자 C에게 '선생님 명의의 SC제일은행 계좌가 불법 자금 세탁에 이용되었습니다.'라고 알리고, 피해자로 등록하려면 안내하는 사이트에 들어가서 선생님이 사용하였다고 말했다. 이는 피해자가 자신의 계좌를 확인하고 문제가 있을 경우 대응할 수 있도록 하는 의도에서 비롯된 것이다.", "node_type":"datum"},
    #     history="",
    #     action_option=2)