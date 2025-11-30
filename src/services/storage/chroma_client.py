"""
ChromaDB Client for Nested Learning (Cold Memory)

Handles:
- Historical storage (L3)
- Domain knowledge (L4)
- Vector similarity search
"""

import os
from typing import Any, Dict, List, Optional

import chromadb
from chromadb.config import Settings
from src.utils.structured_logging import StructuredLogger

logger = StructuredLogger(__name__).logger


class ChromaClient:
    """
    ChromaDB client wrapper for Nested Learning persistence.
    
    Implements:
    - Collection management
    - Embedding storage
    - Similarity search
    """

    def __init__(self, persist_directory: str = "chroma_db"):
        """
        Initialize ChromaDB client.
        
        Args:
            persist_directory: Directory to store database
        """
        self.persist_directory = persist_directory
        self._client: Optional[chromadb.ClientAPI] = None
        
    def connect(self) -> bool:
        """
        Connect to ChromaDB (PersistentClient).
        
        Returns:
            True if connected
        """
        try:
            # Ensure directory exists
            os.makedirs(self.persist_directory, exist_ok=True)
            
            self._client = chromadb.PersistentClient(
                path=self.persist_directory,
                settings=Settings(allow_reset=True, anonymized_telemetry=False)
            )
            logger.info("Connected to ChromaDB", extra={"path": self.persist_directory})
            return True
        except Exception as e:
            logger.error("Failed to connect to ChromaDB", extra={"error": str(e)})
            self._client = None
            return False

    def get_or_create_collection(self, name: str) -> Optional[chromadb.Collection]:
        """
        Get or create a collection.
        
        Args:
            name: Collection name
            
        Returns:
            Collection object or None
        """
        if not self._client:
            if not self.connect():
                return None
                
        try:
            return self._client.get_or_create_collection(name=name)
        except Exception as e:
            logger.error("Failed to get/create collection", extra={"name": name, "error": str(e)})
            return None

    def add_documents(
        self,
        collection_name: str,
        documents: List[str],
        metadatas: List[Dict[str, Any]],
        ids: List[str],
        embeddings: Optional[List[List[float]]] = None
    ) -> bool:
        """
        Add documents to collection.
        
        Args:
            collection_name: Collection name
            documents: List of text documents
            metadatas: List of metadata dicts
            ids: List of unique IDs
            embeddings: Optional pre-computed embeddings
            
        Returns:
            True if successful
        """
        collection = self.get_or_create_collection(collection_name)
        if not collection:
            return False
            
        try:
            collection.add(
                documents=documents,
                metadatas=metadatas,
                ids=ids,
                embeddings=embeddings
            )
            return True
        except Exception as e:
            logger.error("Failed to add documents", extra={"collection": collection_name, "error": str(e)})
            return False

    def query(
        self,
        collection_name: str,
        query_texts: Optional[List[str]] = None,
        query_embeddings: Optional[List[List[float]]] = None,
        n_results: int = 5,
        where: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Query collection.
        
        Args:
            collection_name: Collection name
            query_texts: List of query texts
            query_embeddings: List of query embeddings
            n_results: Number of results
            where: Metadata filter
            
        Returns:
            Query results dict
        """
        collection = self.get_or_create_collection(collection_name)
        if not collection:
            return {}
            
        try:
            return collection.query(
                query_texts=query_texts,
                query_embeddings=query_embeddings,
                n_results=n_results,
                where=where
            )
        except Exception as e:
            logger.error("Failed to query collection", extra={"collection": collection_name, "error": str(e)})
            return {}

    def count(self, collection_name: str) -> int:
        """Get document count"""
        collection = self.get_or_create_collection(collection_name)
        if not collection:
            return 0
        return collection.count()
