import os
import uuid
from typing import List, Dict, Any
from google.adk.memory import MemoryService
from pinecone import Pinecone, ServerlessSpec
from sentence_transformers import SentenceTransformer
from .utils import logger

class PineconeMemoryService(MemoryService):
    """
    Custom Memory Service using Pinecone for long-term vector storage.
    Uses 'all-MiniLM-L6-v2' for local embedding generation.
    """
    def __init__(self, api_key: str, index_name: str = "adk-memory", dimension: int = 384):
        self.api_key = api_key
        self.index_name = index_name
        self.dimension = dimension
        
        # Initialize Pinecone
        self.pc = Pinecone(api_key=self.api_key)
        
        # Create index if not exists
        if self.index_name not in self.pc.list_indexes().names():
            logger.info(f"🌲 Creating Pinecone index: {self.index_name}")
            self.pc.create_index(
                name=self.index_name,
                dimension=self.dimension,
                metric="cosine",
                spec=ServerlessSpec(cloud="aws", region="us-east-1") # Default free tier region
            )
            
        self.index = self.pc.Index(self.index_name)
        
        # Initialize Embedding Model
        logger.info("🧠 Loading embedding model: all-MiniLM-L6-v2...")
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        logger.info("✅ Pinecone Memory Service initialized")

    async def add_session_to_memory(self, session: Any):
        """
        Embeds the session history and saves it to Pinecone.
        """
        try:
            # 1. Convert session to text
            # Assuming session has a 'history' or we can iterate turns
            # We'll construct a simplified text representation
            text_content = ""
            for turn in session.turns:
                text_content += f"{turn.role}: {turn.content}\n"
            
            if not text_content.strip():
                return

            # 2. Generate Embedding
            vector = self.model.encode(text_content).tolist()
            
            # 3. Create Metadata
            metadata = {
                "session_id": session.session_id,
                "text": text_content[:1000], # Store snippet (limit size)
                "timestamp": str(session.created_at) if hasattr(session, 'created_at') else ""
            }
            
            # 4. Upsert to Pinecone
            # Use session_id as vector ID
            self.index.upsert(vectors=[(session.session_id, vector, metadata)])
            logger.info(f"💾 Saved session {session.session_id} to Pinecone")
            
        except Exception as e:
            logger.error(f"❌ Failed to save to Pinecone: {e}")

    async def search_memory(self, query: str, limit: int = 3) -> List[str]:
        """
        Searches Pinecone for relevant past sessions.
        """
        try:
            # 1. Embed Query
            query_vector = self.model.encode(query).tolist()
            
            # 2. Search Pinecone
            results = self.index.query(
                vector=query_vector,
                top_k=limit,
                include_metadata=True
            )
            
            # 3. Format Results
            memories = []
            for match in results['matches']:
                if match['score'] > 0.5: # Relevance threshold
                    memories.append(match['metadata']['text'])
            
            return memories
            
        except Exception as e:
            logger.error(f"❌ Failed to search Pinecone: {e}")
            return []
