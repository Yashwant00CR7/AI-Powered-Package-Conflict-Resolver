import os
import uuid
from typing import List, Dict, Any, Optional
from google.adk.memory.base_memory_service import BaseMemoryService, SearchMemoryResponse
from google.adk.memory.memory_entry import MemoryEntry
from google.genai import types as genai_types
from pinecone import Pinecone, ServerlessSpec
from sentence_transformers import SentenceTransformer
from .utils import logger

class PineconeMemoryService(BaseMemoryService):
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
        logger.info("🧠 Loading embedding model: all-MiniLM-L6-v2... (This may take a while if downloading)")
        try:
            self.model = SentenceTransformer('all-MiniLM-L6-v2')
            logger.info("✅ SentenceTransformer loaded.")
        except Exception as e:
            logger.error(f"❌ Failed to load SentenceTransformer: {e}")
            self.model = None
        
        logger.info("✅ Pinecone Memory Service initialized")

    async def add_session_to_memory(self, session: Any):
        """
        Embeds the session history and saves it to Pinecone.
        """
        if not self.model:
            logger.warning("⚠️ Embedding model not loaded. Skipping memory save.")
            return

        try:
            # Get session ID safely
            session_id = getattr(session, 'id', getattr(session, 'session_id', 'UNKNOWN'))
            
            logger.info(f"💾 Attempting to save session to Pinecone. Session ID: {session_id}")

            # 1. Convert session to text
            text_content = ""
            
            if hasattr(session, 'turns'):
                turns = session.turns
                for turn in turns:
                    text_content += f"{turn.role}: {turn.content}\n"
            elif hasattr(session, 'events'):
                events = session.events
                for event in events:
                    author = getattr(event, 'author', 'unknown')
                    content = getattr(event, 'content', getattr(event, 'text', ''))
                    text_content += f"{author}: {content}\n"
            
            if not text_content.strip():
                logger.warning("⚠️ Session content is empty. Skipping Pinecone save.")
                return

            # 2. Generate Embedding
            vector = self.model.encode(text_content).tolist()
            
            # 3. Create Metadata
            metadata = {
                "session_id": session_id,
                "text": text_content[:1000], # Store snippet (limit size)
                "timestamp": str(session.created_at) if hasattr(session, 'created_at') else ""
            }
            
            # 4. Upsert to Pinecone
            self.index.upsert(vectors=[(session_id, vector, metadata)])
            logger.info(f"💾 Saved session {session_id} to Pinecone")
            
        except Exception as e:
            logger.error(f"❌ Failed to save to Pinecone: {e}")

    async def search_memory(
        self,
        *,
        app_name: str,
        user_id: str,
        query: str,
    ) -> SearchMemoryResponse:
        """
        Searches Pinecone for relevant past sessions.
        """
        if not self.model:
            return SearchMemoryResponse(memories=[])

        try:
            # 1. Embed Query
            query_vector = self.model.encode(query).tolist()
            
            # 2. Search Pinecone
            results = self.index.query(
                vector=query_vector,
                top_k=3, # Default limit
                include_metadata=True
            )
            
            # 3. Format Results
            memories = []
            for match in results['matches']:
                if match['score'] > 0.5: # Relevance threshold
                    text = match['metadata'].get('text', '')
                    session_id = match['metadata'].get('session_id', '')
                    
                    # Create MemoryEntry
                    memory_entry = MemoryEntry(
                        content=genai_types.Content(
                            parts=[genai_types.Part.from_text(text=text)]
                        ),
                        custom_metadata={"score": match['score'], "session_id": session_id},
                        id=match['id']
                    )
                    memories.append(memory_entry)
            
            return SearchMemoryResponse(memories=memories)
            
        except Exception as e:
            logger.error(f"❌ Failed to search Pinecone: {e}")
            return SearchMemoryResponse(memories=[])
