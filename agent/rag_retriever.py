import os
import json
import hashlib
import boto3
import chromadb
from pathlib import Path
from agent.config import DEMO_MODE, AWS_REGION

DOCS_DIR        = Path(__file__).parent.parent / "runbooks"
CHROMA_PATH     = Path(__file__).parent.parent / "data" / "chroma_db"
COLLECTION_NAME = "azure_cost_kb"
CHUNK_SIZE      = 500
CHUNK_OVERLAP   = 100


class TitanEmbeddingFunction(chromadb.EmbeddingFunction):

    def __init__(self):
        self.use_mock = DEMO_MODE
        self.client   = None
        if not DEMO_MODE:
            try:
                self.client = boto3.client("bedrock-runtime", region_name=AWS_REGION)
                print("Using Amazon Titan Embeddings")
            except Exception:
                self.use_mock = True
                print("Falling back to mock embeddings")
        else:
            print("Demo mode - using mock embeddings")

    def _mock_embedding(self, text):
        import random
        seed = int(hashlib.md5(text.encode()).hexdigest(), 16) % (2**32)
        rng  = random.Random(seed)
        vec  = [rng.gauss(0, 1) for _ in range(256)]
        mag  = sum(x**2 for x in vec) ** 0.5
        return [x / mag for x in vec]

    def __call__(self, input):
        if self.use_mock:
            return [self._mock_embedding(t) for t in input]
        embeddings = []
        for text in input:
            response = self.client.invoke_model(
                modelId="amazon.titan-embed-text-v2:0",
                body=json.dumps({"inputText": text}),
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
        client    = chromadb.PersistentClient(path=str(CHROMA_PATH))
        self._col = client.get_or_create_collection(
            name=COLLECTION_NAME,
            embedding_function=self._embed_fn,
            metadata={"hnsw:space": "cosine"},
        )
        if self._col.count() == 0:
            print("Indexing Azure cost knowledge base...")
            self._index()
        else:
            print(f"KB loaded with {self._col.count()} chunks ready")

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

    def _chunk(self, text):
        chunks, start = [], 0
        while start < len(text):
            chunks.append(text[start:start+CHUNK_SIZE].strip())
            start += CHUNK_SIZE - CHUNK_OVERLAP
        return [c for c in chunks if len(c) > 50]

    def retrieve(self, query, top_k=3):
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