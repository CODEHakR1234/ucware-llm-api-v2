# app/infrastructure/summarizer.py
from typing import List
from app.domain.interfaces import LlmChainIF, TextChunk
from app.utils.llm_factory import get_llm_instance
from langchain.chains.summarize import load_summarize_chain
from langchain.docstore.document import Document


class MapReduceSummarizer(LlmChainIF):
    def __init__(self):
        self.llm = get_llm_instance()
        self.chain = load_summarize_chain(self.llm, chain_type="map_reduce")

    async def summarize(self, docs: List[TextChunk], query: str) -> str:
        prompt = (
            "다음 문서 조각들을 참고하여 사용자의 질문에 답하십시오.\n"
            f"## 질문: {query}\n\n"
            "{text}"
        )
        lc_docs = [Document(page_content=t) for t in docs]
        return self.chain.invoke({"input_documents": lc_docs, "question": query})

