# -- 知识问答 --
import json
from numbers import Number
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from models.schema import QueryRequest, QueryResponse, RetrievalHit
from services.embedding_service import generate_embedding
from services.milvus_service import search_chunks
from services.llm_service import generate_answer, stream_answer


router = APIRouter(prefix="/api", tags=["query"])
# -- 辅助函数 调用两个重排函数 提检索的命中-- 
async def rerank_chunks(question: str, chunks: list[dict], model_provider: str = "openai") -> list[dict]:
    from services.llm_service import call_llm  

    contents = [c["content"] for c in chunks]
    numbered = "\n".join([f"[{i}] {c}" for i, c in enumerate(contents)]) # -- 文本拼接

    prompt = (
        "请对以下文本段落与问题的相关性进行打分（0-10分），返回 JSON 格式。\n"
        "格式: {\"scores\": [分数1, 分数2, ...]}\n"
        "只返回 JSON，不要其他内容。\n\n"
        f"问题：{question}\n\n"
        f"段落：\n{numbered}"
    )

    try:
        response = await call_llm(
            messages=[{"role": "user", "content": prompt}],
            model_provider=model_provider,
            temperature=0,
        )
        data = json.load(response)
        scores = data.get("scores", [])
        if len(scores) == len(chunks):
            for i, chunk in enumerate(chunks):
                chunk["rerank_score"] = scores[i]
            chunks.sort(key=lambda x: x.get("rerank_score", 0), reverse=True)
    except Exception:
       pass
    return chunks


@router.post("/query",response_model=QueryResponse)
async def query(req: QueryRequest):
    query_vector = await generate_embedding(req.question, model_provider=req.model_provider) # 问题向量化
    hits = search_chunks(query_vector, model_provider=req.model_provider, top_k=req.top_k)  #  Milvus 相似度检索

    if not hits:
        return QueryResponse(answer="未找到相关文档内容，请先上传文档。", contexts=[])