# app/infrastructure/summarizer.py
from typing import List
from langchain.docstore.document import Document
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from app.utils.llm_factory import get_llm_instance
from app.domain.interfaces import LlmChainIF, TextChunk

SUMMARY_PROMPT = PromptTemplate(
    template=(
        "다음 글 조각들을 참고하여 **질문에 한국어로 답하세요**.\n"
        "### 질문: {question}\n"
        "### 글\n{docs}\n"
        "### 답변:"
    ),
    input_variables=["docs", "question"],
)

class StuffSummarizer(LlmChainIF):
    def __init__(self):
        llm = get_llm_instance(temperature=0.3)
        self.chain = LLMChain(llm=llm, prompt=SUMMARY_PROMPT)

    async def summarize(self, docs: List[TextChunk], query: str) -> str:
        joined = "\n\n".join(docs)                     # 이미 RAG로 추린 청크 합치기
        result = await self.chain.apredict(docs=joined, question=query)
        return result.strip()

