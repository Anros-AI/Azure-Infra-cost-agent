content = open("agent/rag_retriever.py", "w")
content.write("""import os
import json
import hashlib
import boto3
import chromadb
from pathlib import Path
from agent.config import DEMO_MODE, AWS_REGION

DOCS_DIR = Path(__file__).parent.parent / 'runbooks'
CHROMA_PATH = Path(__file__).parent.parent / 'data' / 'chroma_db'
COLLECTION_NAME = 'azure_cost_kb'
CHUNK_SIZE = 500
CHUNK_OVERLAP = 100
""")
content.close()
print("done")
