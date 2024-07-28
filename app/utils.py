from typing import Optional
from pydantic import BaseModel

from llama_index.core import QueryBundle
from llama_index.core.schema import NodeWithScore, TextNode
from llama_index.core.retrievers import BaseRetriever
from typing import List
from sqlalchemy.orm import Session
from sqlalchemy import text
import numpy as np


class CustomSQLRetriever(BaseRetriever):
    """Custom retriever that uses SQL database for embedding similarity search."""

    def __init__(self, db: Session, embed_model):
        """Initialize the retriever."""
        self.db = db
        self.embed_model = embed_model
        super().__init__()

    def _retrieve(self, query_bundle: QueryBundle) -> List[NodeWithScore]:
        """Retrieve nodes given query."""
        # Generate embedding for the query
        query_embedding = self.embed_model.embed(query_bundle.query_str)

        # Query the database
        results = self.query_embeddings(self.db, query_embedding)

        # Convert results to NodeWithScore objects
        nodes = []
        for result in results:
            # metadata = {}
            # if hasattr(result, 'user_id'):
            #     metadata['user_id'] = result.user_id

            # Ensure 'content' exists in the result
            content = result.content if hasattr(
                result, 'content') else str(result)

            node = TextNode(
                text=content,
                id_=str(result.id) if hasattr(result, 'id') else "-1",
                # metadata=metadata
            )
            # The similarity score is now directly included in the result
            score = result.similarity_score
            nodes.append(NodeWithScore(node=node, score=score))

        return nodes

    @staticmethod
    def query_embeddings(db: Session, embedding: list[float]):
        embedding_string = ','.join(map(str, embedding))
        sql = text(f"""
            SELECT id, content,
                1 - (embedding <=> ARRAY[{embedding_string}]::vector) AS similarity_score
            FROM entries
            ORDER BY embedding <=> ARRAY[{embedding_string}]::vector
            LIMIT 5
        """)
        return db.execute(sql).fetchall()


class MessagePayload(BaseModel):
    accountEmail: str
    content: str
    media_url: str
    is_outbound: bool
    status: str
    error_code: Optional[int]
    error_message: Optional[str]
    message_handle: str
    date_sent: str
    date_updated: str
    from_number: str
    number: str
    was_downgraded: Optional[bool]
    plan: str
