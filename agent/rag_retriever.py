"""
RAG Retriever — converts runbook docs to vectors using
Amazon Titan Embeddings and stores in ChromaDB for retrieval.
"""

import os
import json
import hashlib
import boto3
import chromadb
from pathlib import Path

DOCS_DIR        = Path(__file__).parent.parent / "runbooks"
CHROMA_PATH     = Path(__file__).parent.parent / "data" / "chroma_db"
COLLECTION_NAME = "azure_cost_kb"
CHUNK_SIZE      = 500
CHUNK_OVERLAP   = 100
REGION          = os.environ.get("AWS_DEFAULT_REGION", "us-east-1")


class TitanEmbeddingFunction(chromadb.EmbeddingFunction):
    """Uses Amazon Titan Embeddings V2 via Bedrock."""

    def __init__(self):
        self.client = boto3.client(
            "bedrock-runtime",
            region_name=REGION
        )

    def __call__(self, input: list[str]) -> list[list[float]]:
        embeddings = []
        for text in input:
            body = json.dumps({"inputText": text})
            response = self.client.invoke_model(
                modelId="amazon.titan-embed-text-v2:0",
                body=body,
                contentType="application/json",
                accept="application/json",
            )
            result = json.loads(response["body"].read())
            embeddings.append(result["embedding"])
        return embeddings


class RAGRetriever:

    def __init__(self):
        self._embed_fn = TitanEmbeddingFunction()
        CHROMA_PATH.mkdir(parents=True, exist_ok=True)

        client = chromadb.PersistentClient(path=str(CHROMA_PATH))
        self._col = client.get_or_create_collection(
            name=COLLECTION_NAME,
            embedding_function=self._embed_fn,
            metadata={"hnsw:space": "cosine"},
        )

        if self._col.count() == 0:
            print("Indexing Azure cost knowledge base...")
            self._index()
        else:
            print(f"KB loaded — {self._col.count()} chunks ready")

    def _index(self):
        docs, ids, metas = [], [], []
        for f in DOCS_DIR.glob("*.md"):
            text   = f.read_text(encoding="utf-8")
            chunks = self._chunk(text)
            for i, chunk in enumerate(chunks):
                cid = hashlib.md5(f"{f.name}_{i}".encode()).hexdigest()
                docs.append(chunk)
                ids.append(cid)
                metas.append({"source": f.name, "chunk": i})

        batch = 5
        for s in range(0, len(docs), batch):
            self._col.add(
                documents=docs[s:s+batch],
                ids=ids[s:s+batch],
                metadatas=metas[s:s+batch],
            )
        print(f"Indexed {len(docs)} chunks from {len(list(DOCS_DIR.glob('*.md')))} docs")

    def _chunk(self, text: str) -> list[str]:
        chunks, start = [], 0
        while start < len(text):
            chunks.append(text[start:start+CHUNK_SIZE].strip())
            start += CHUNK_SIZE - CHUNK_OVERLAP
        return [c for c in chunks if len(c) > 50]

    def retrieve(self, query: str, top_k: int = 3) -> list[dict]:
        query_embedding = self._embed_fn([query])[0]

        res = self._col.query(
            query_embeddings=[query_embedding],
            n_results=min(top_k, self._col.count()),
        )
        chunks = []
        for text, meta, dist in zip(
            res["documents"][0],
            res["metadatas"][0],
            res["distances"][0],
        ):
            chunks.append({
                "text":       text,
                "source":     meta["source"],
                "similarity": round(1 - dist, 4),
            })
        return chunks
