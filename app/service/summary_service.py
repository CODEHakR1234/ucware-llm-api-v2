import os
from langchain.chains.summarize import load_summarize_chain
from langchain_openai import ChatOpenAI
from app.vectordb.vector_db import VectorDB
from app.cache.cache_db import get_cache_db  # ✅ Redis 기반 캐시
from app.cache.cache_db import RedisCacheDB  # ✅ 명시적으로 타입 지정
from langchain.prompts import PromptTemplate
#from langchain.llms import HuggingFaceHub

LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openai")
LLM_MODEL_NAME = os.getenv("LLM_MODEL_NAME")

def get_llm_instance(temperature: float = 0.5):
    if LLM_PROVIDER == "hf":
        #return HuggingFaceHub(repo_id=LLM_MODEL_NAME, model_kwargs={"temperature": temperature})
        return ChatOpenAI(model_name=LLM_MODEL_NAME, temperature=temperature,
                          max_tokens=1000, openai_api_base="http://localhost:12000/v1",)
    else:
        return ChatOpenAI(model_name=LLM_MODEL_NAME, temperature=temperature, max_tokens=1000)

class SummaryService:
    def __init__(self, vector: VectorDB, cache: RedisCacheDB = get_cache_db()):
        self.vector, self.cache = vector, cache
        self.llm = get_llm_instance()
        self.summary_prompt = PromptTemplate(
            template="다음 문서 내용:\n{text}\n\n질문: 내용을 요약해줘\n답변:",
            input_variables=["text"],
        )
        self.completeness_prompt = PromptTemplate(
            template="다음 요약 내용:\n{text}\n\n질문: 요약 내용의 완성도를 0에서 1 사이로 평가해줘.\n 최고의 요약 : {complete_sentence}\n답변:",
            input_variables=["text","complete_sentence"],
        )
        

    def generate(self, file_id: str) -> str:
        # ✅ Redis 캐시에서 먼저 요약 확인
        if (c := self.cache.get_pdf(file_id)):
            # completeness = self.check_sentence_completeness(c)
            return c
        
        # ✅ 벡터 DB에서 문서 가져오기
        docs = self.vector.get_docs(file_id)
        if not docs:
            return f"No documents found for file_id='{file_id}'."
        
        # ✅ LangChain map-reduce 요약 체인 사용
        # chain = load_summarize_chain(self.llm, chain_type="map_reduce")
        # summary = chain.run(docs)
        
        prompt = self.summary_prompt.format(text=docs)
        summary = self.llm.invoke(prompt)
        summary = summary.content.strip()
        #summary된 텍스트를 한국어로 번역
        # translated_summary = self.translate_summary(summary)
        
        # completeness = self.check_sentence_completeness(summary)
        
        # ✅ Redis에 캐시 저장
        self.cache.set_pdf(file_id, summary)
        return summary
    
    def check_sentence_completeness(self, sentence: str) -> str:
        complete_sentence = "이 논문은 2017년 Google에서 발표한 **Attention Is All You Need**입니다. 기존의 RNN이나 CNN 없이 오직 self-attention만으로 구성된 새로운 모델 Transformer를 제안합니다. Transformer는 병렬 처리가 가능하여 훈련 속도가 빠르고 성능이 우수합니다. 주요 구성은 Multi-Head Attention, Position-wise Feed-Forward Networks, Positional Encoding 등입니다. WMT 2014 번역 과제에서 기존 최고 BLEU 점수를 뛰어넘는 성과를 보였습니다. 번역"
        
        prompt = self.completeness_prompt.format(text=sentence, complete_sentence=complete_sentence)
        completeness = self.llm.invoke(prompt)
        completeness = completeness.content.strip()
        print(completeness)
        return completeness

