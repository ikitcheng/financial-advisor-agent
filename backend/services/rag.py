
"""
Hybrid RAG System with Semantic Search
Combines sentence-transformers embeddings with keyword matching for optimal retrieval
Indexes parsed markdown and extracted JSON documents.
"""
import numpy as np
from typing import List, Dict, Any
from sentence_transformers import SentenceTransformer
from services.llm_client import ask_zhipuai
from services.finance_logic import load_markdown_file, load_json_file

class HybridRAG:
    """Hybrid RAG system with semantic + keyword search, chunking, and document indexing"""
    def __init__(self):
        self.index = {}  # {task_id: {doc_id: {chunks: [], metadata: {}}}}
        self.embedding_model = None
        try:
            self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
            print("✅ Loaded embedding model: all-MiniLM-L6-v2")
        except Exception as e:
            print(f"⚠️ Failed to load embedding model: {e}")

    def _generate_embedding(self, text: str) -> List[float]:
        if not self.embedding_model:
            return []
        try:
            embedding = self.embedding_model.encode(text, convert_to_numpy=True)
            return embedding.tolist()
        except Exception as e:
            print(f"⚠️ Embedding generation failed: {e}")
            return []

    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        if not vec1 or not vec2:
            return 0.0
        try:
            vec1_np = np.array(vec1)
            vec2_np = np.array(vec2)
            dot_product = np.dot(vec1_np, vec2_np)
            norm1 = np.linalg.norm(vec1_np)
            norm2 = np.linalg.norm(vec2_np)
            if norm1 == 0 or norm2 == 0:
                return 0.0
            return float(dot_product / (norm1 * norm2))
        except Exception as e:
            print(f"⚠️ Similarity computation failed: {e}")
            return 0.0

    def _chunk_text(self, text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
        if not text:
            return []
        chunks = []
        start = 0
        while start < len(text):
            end = start + chunk_size
            chunk = text[start:end]
            # Try to break at sentence boundary
            if end < len(text):
                last_period = chunk.rfind('.')
                last_newline = chunk.rfind('\n')
                break_point = max(last_period, last_newline)
                if break_point > chunk_size * 0.5:
                    chunk = chunk[:break_point + 1]
                    end = start + break_point + 1
            chunks.append(chunk.strip())
            start = end - overlap
        return [c for c in chunks if c]

    def index_document(self, task_id: str, doc_id: str, markdown: str, extraction_json: dict, metadata: dict):
        if task_id not in self.index:
            self.index[task_id] = {}
        # Chunk the markdown
        chunks = self._chunk_text(markdown)
        chunk_data = []
        for idx, chunk in enumerate(chunks):
            embedding = self._generate_embedding(chunk)
            chunk_data.append({
                "text": chunk,
                "embedding": embedding,
                "chunk_index": idx
            })
        # Also embed structured extraction keys
        structured_chunks = []
        for key, value in extraction_json.items():
            if value:
                text = f"{key}: {value}"
                embedding = self._generate_embedding(text)
                structured_chunks.append({
                    "text": text,
                    "embedding": embedding,
                    "field": key,
                    "value": value
                })
        self.index[task_id][doc_id] = {
            "chunks": chunk_data,
            "structured": structured_chunks,
            "metadata": metadata
        }
        print(f"✅ Indexed {len(chunk_data)} chunks + {len(structured_chunks)} structured fields for doc {doc_id}")

    def search(self, task_id: str, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        if task_id not in self.index:
            return []
        query_embedding = self._generate_embedding(query)
        query_lower = query.lower()
        all_results = []
        for doc_id, doc_data in self.index[task_id].items():
            # Search markdown chunks
            for chunk_info in doc_data["chunks"]:
                semantic_score = 0.0
                if query_embedding and chunk_info.get("embedding"):
                    semantic_score = self._cosine_similarity(query_embedding, chunk_info["embedding"])
                chunk_lower = chunk_info["text"].lower()
                query_terms = set(query_lower.split())
                chunk_terms = set(chunk_lower.split())
                common_terms = query_terms.intersection(chunk_terms)
                keyword_score = len(common_terms) / max(len(query_terms), 1)
                if query_embedding:
                    final_score = (semantic_score * 0.7) + (keyword_score * 0.3)
                    score_type = "hybrid"
                else:
                    final_score = keyword_score
                    score_type = "keyword"
                all_results.append({
                    "doc_id": doc_id,
                    "text": chunk_info["text"],
                    "score": final_score,
                    "score_type": score_type,
                    "chunk_index": chunk_info["chunk_index"],
                    "filename": doc_data["metadata"].get("filename", "unknown"),
                    "semantic_score": semantic_score,
                    "keyword_score": keyword_score
                })
            # Search structured fields
            for struct_info in doc_data["structured"]:
                semantic_score = 0.0
                if query_embedding and struct_info.get("embedding"):
                    semantic_score = self._cosine_similarity(query_embedding, struct_info["embedding"])
                field_lower = struct_info["text"].lower()
                query_terms = set(query_lower.split())
                field_terms = set(field_lower.split())
                common_terms = query_terms.intersection(field_terms)
                keyword_score = len(common_terms) / max(len(query_terms), 1)
                if query_embedding:
                    final_score = (semantic_score * 0.7) + (keyword_score * 0.3)
                    score_type = "hybrid"
                else:
                    final_score = keyword_score
                    score_type = "keyword"
                all_results.append({
                    "doc_id": doc_id,
                    "text": struct_info["text"],
                    "score": final_score,
                    "score_type": score_type,
                    "chunk_index": struct_info.get("field", "structured"),
                    "filename": doc_data["metadata"].get("filename", "unknown"),
                    "semantic_score": semantic_score,
                    "keyword_score": keyword_score
                })
        all_results.sort(key=lambda x: x["score"], reverse=True)
        return all_results[:top_k]

    def get_rag_context(self, task_id: str, query: str, top_k: int = 5) -> Dict[str, Any]:
        results = self.search(task_id, query, top_k)
        if not results:
            return {"context": "", "sources": []}
        context_parts = []
        sources = []
        for idx, result in enumerate(results, 1):
            context_parts.append(f"[Source {idx}] {result['text']}")
            sources.append({
                "filename": result["filename"],
                "chunk_index": result["chunk_index"],
                "score": result["score"],
                "score_type": result["score_type"]
            })
        context = "\n\n".join(context_parts)
        return {
            "context": context,
            "sources": sources
        }

    def synthesize_answer(self, question: str, rag_context: Dict[str, Any]) -> str:
        """
        Synthesize a comprehensive answer using the LLM, including citations.
        """
        context_text = rag_context["context"]
        sources = rag_context["sources"]
        prompt = (
            f"Answer the following question using ONLY the provided context. "
            f"Cite sources in square brackets (e.g., [1], [2]) as you use them.\n\n"
            f"Context:\n{context_text}\n\n"
            f"Question: {question}\n\n"
            f"Comprehensive Answer:"
        )
        answer = ask_zhipuai([
            {"role": "system", "content": "You are a personal financial advisor that always cites sources."},
            {"role": "user", "content": prompt}
        ])
        return answer

    def answer_question(self, task_id: str, question: str, top_k: int = 5) -> Dict[str, Any]:
        rag_context = self.get_rag_context(task_id, question, top_k)
        answer = self.synthesize_answer(question, rag_context)
        return {
            "question": question,
            "answer": answer,
            "citations": rag_context["sources"],
            "context": rag_context["context"]
        }

# Global instance
_rag_instance = None
def get_instance():
    global _rag_instance
    if _rag_instance is None:
        _rag_instance = HybridRAG()
    return _rag_instance

# Module-level API
def index_document(task_id: str, doc_id: str, markdown: str, extraction_json: dict, metadata: dict):
    instance = get_instance()
    instance.index_document(task_id, doc_id, markdown, extraction_json, metadata)

def search(task_id: str, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
    instance = get_instance()
    return instance.search(task_id, query, top_k)

def get_rag_context(task_id: str, query: str, top_k: int = 5) -> Dict[str, Any]:
    instance = get_instance()
    return instance.get_rag_context(task_id, query, top_k)

def answer_question(task_id: str, question: str, top_k: int = 5) -> Dict[str, Any]:
    instance = get_instance()
    return instance.answer_question(task_id, question, top_k)

def format_answer(answer_dict:dict) -> str:
    # Format for chat interface (Markdown, wrapped, no horizontal scroll)
    answer = answer_dict["answer"].strip()
    # Ensure answer lines are wrapped at ~80 chars for readability
    import textwrap
    wrapped_answer = "\n".join(textwrap.wrap(answer, width=80))

    formatted = """**Comprehensive Answer**\n\n"""
    formatted += wrapped_answer + "\n\n"
    formatted += "**Citations:**\n"
    for i, src in enumerate(answer_dict["citations"], 1):
        # src is a dict with filename, chunk_index, score, etc.
        filename = src.get("filename", "unknown")
        chunk = src.get("chunk_index", "-")
        score = src.get("score", None)
        score_type = src.get("score_type", "")
        # Show only filename and chunk, optionally score (rounded)
        if score is not None:
            score_str = f" (score: {score:.2f}, {score_type})"
        else:
            score_str = ""
        formatted += f"- [Source {i}] `{filename}` (chunk: {chunk}){score_str}\n"
    return formatted.strip()

# Example usage
if __name__ == "__main__":
    # Example: index a document
    task_id = "demo_task"
    doc_id = "demo_doc"
    markdown = load_markdown_file("C:\\Users\\matth\\OneDrive\\Matthew\\Company\\eyesquare\\financial-advisor-agent\\backend\\output\\credit_card_statements\\0001_parsed.md")
    extraction_json = load_json_file("C:\\Users\\matth\\OneDrive\\Matthew\\Company\\eyesquare\\financial-advisor-agent\\backend\\output\\credit_card_statements\\0001_extracted.json")
    metadata = {"filename": "demo.md"}
    index_document(task_id, doc_id, markdown, extraction_json, metadata)
    # Ask a question
    user_question = input("Enter your question: ")
    result = answer_question(task_id, user_question)
    print(format_answer(result))
