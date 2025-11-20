"""
Base Repository
Generic repository implementing common CRUD operations (DRY principle)
"""

from typing import TypeVar, Generic, Optional, List, Dict, Any
from abc import ABC, abstractmethod
from motor.motor_asyncio import AsyncIOMotorCollection
from bson import ObjectId
import logging

logger = logging.getLogger(__name__)

T = TypeVar('T')


class BaseRepository(ABC, Generic[T]):
    """
    Base repository with common database operations
    Implements DRY principle and Repository pattern
    """
    
    def __init__(self, collection: AsyncIOMotorCollection):
        """
        Initialize repository with a MongoDB collection
        
        Args:
            collection: Motor AsyncIOMotorCollection instance
        """
        self.collection = collection
    
    async def find_by_id(self, id: str) -> Optional[Dict[str, Any]]:
        """
        Find document by ID
        
        Args:
            id: Document ID (string or ObjectId)
            
        Returns:
            Document dict or None
        """
        try:
            # Try as ObjectId first
            try:
                object_id = ObjectId(id)
                doc = await self.collection.find_one({"_id": object_id})
                if doc:
                    return doc
            except:
                pass
            
            # Try as string ID
            return await self.collection.find_one({"id": id})
            
        except Exception as e:
            logger.error(f"Error finding document by ID {id}: {e}")
            return None
    
    async def find_one(self, query: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Find one document matching query
        
        Args:
            query: MongoDB query dict
            
        Returns:
            Document dict or None
        """
        try:
            return await self.collection.find_one(query)
        except Exception as e:
            logger.error(f"Error in find_one: {e}")
            return None
    
    async def find_many(
        self, 
        query: Dict[str, Any],
        limit: int = 100,
        sort: Optional[List[tuple]] = None
    ) -> List[Dict[str, Any]]:
        """
        Find multiple documents matching query
        
        Args:
            query: MongoDB query dict
            limit: Maximum number of documents
            sort: Sort specification (e.g., [("created_at", -1)])
            
        Returns:
            List of documents
        """
        try:
            cursor = self.collection.find(query)
            
            if sort:
                cursor = cursor.sort(sort)
            
            return await cursor.to_list(length=limit)
            
        except Exception as e:
            logger.error(f"Error in find_many: {e}")
            return []
    
    async def insert_one(self, document: Dict[str, Any]) -> Optional[str]:
        """
        Insert single document
        
        Args:
            document: Document to insert
            
        Returns:
            Inserted document ID or None
        """
        try:
            result = await self.collection.insert_one(document)
            return str(result.inserted_id)
        except Exception as e:
            logger.error(f"Error inserting document: {e}")
            return None
    
    async def update_one(
        self, 
        query: Dict[str, Any], 
        update: Dict[str, Any]
    ) -> bool:
        """
        Update single document
        
        Args:
            query: Query to find document
            update: Update operations
            
        Returns:
            True if updated, False otherwise
        """
        try:
            result = await self.collection.update_one(query, update)
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Error updating document: {e}")
            return False
    
    async def delete_one(self, query: Dict[str, Any]) -> bool:
        """
        Delete single document
        
        Args:
            query: Query to find document
            
        Returns:
            True if deleted, False otherwise
        """
        try:
            result = await self.collection.delete_one(query)
            return result.deleted_count > 0
        except Exception as e:
            logger.error(f"Error deleting document: {e}")
            return False
    
    async def count(self, query: Dict[str, Any] = {}) -> int:
        """
        Count documents matching query
        
        Args:
            query: MongoDB query dict (empty for all)
            
        Returns:
            Number of documents
        """
        try:
            return await self.collection.count_documents(query)
        except Exception as e:
            logger.error(f"Error counting documents: {e}")
            return 0
