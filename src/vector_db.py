from dotenv import load_dotenv
load_dotenv()

import os
from pinecone import Pinecone, ServerlessSpec
from tqdm import tqdm
import logging
from typing import List, Dict, Any
from utils import get_embedding, get_embeddings, my_hash
from mail import MailClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class PineconeClient:
    def __init__(self, api_key: str = None, index_name: str = "email-qa", namespace: str = ""):
        """
        Initialize PineconeClient with API credentials and index name.
        
        Args:
            api_key (str, optional): Pinecone API key. Defaults to environment variable.
            environment (str, optional): Pinecone environment. Defaults to environment variable.
            index_name (str, optional): Name of the Pinecone index. Defaults to "email-qa".
            namespace (str, optional): Namespace to use. Defaults to empty string.
        """
        self.api_key = api_key or os.getenv("PINECONE_APT_KEY")
        self.index_name = index_name
        self.namespace = namespace
        
        if not self.api_key:
            raise ValueError("Pinecone API key must be provided or set as environment variables")
        
        self.pc = Pinecone(api_key=self.api_key)
        self.create_index(self.index_name)
        self.index = self.pc.Index(self.index_name)

    def create_index(self, index_name: str = "email-qa") -> None:
        """
        Create a new Pinecone index.
        
        Args:
            index_name (str, optional): Name of the Pinecone index. Defaults to "email-qa".
        """
        try:
            logger.info(f"Creating new Pinecone index: {index_name}")
            if index_name in self.pc.list_indexes().names():
                logger.info(f"Index {index_name} already exists")
            else:
                self.pc.create_index(index_name, 
                                    dimension=1536,
                                    metric='cosine',
                                    spec = ServerlessSpec(
                                        cloud='aws',
                                        region='us-east-1'))
                logger.info(f"Successfully created index: {index_name}")
        except Exception as e:
            logger.error(f"Error creating index: {str(e)}")
            raise

    def upsert_emails(self, emails: List[Dict[str, Any]]) -> None:
        """
        Upsert email documents to Pinecone vector database.
        
        Args:
            emails (list): List of dictionaries containing email data with 'id' and 'text' keys
        """
        logger.info(f"Starting upsert operation for {len(emails)} emails")
        for email in tqdm(emails):
            try:
                embedding = get_embedding(email['text'])
                self.index.upsert([(email['id'], embedding, {"text": email['text']})])
            except Exception as e:
                logger.error(f"Error during email upsert: {str(e)}")
                continue
        logger.info("Successfully completed email upsert operation")

    def get_email_count(self) -> int:
        """
        Get the total count of email vectors in the database.
        
        Returns:
            int: Total number of vectors in the index
        """
        try:
            stats = self.index.describe_index_stats()
            count = stats['total_vector_count']
            logger.info(f"Current email count in database: {count}")
            return count
        except Exception as e:
            logger.error(f"Error fetching email count: {str(e)}")
            raise

    def delete_email(self, email_id: str) -> None:
        """
        Delete a specific email from the database by its ID.
        
        Args:
            email_id (str): The ID of the email to delete
        """
        try:
            logger.info(f"Deleting email with ID: {email_id}")
            self.index.delete(ids=[email_id])
            logger.info(f"Successfully deleted email {email_id}")
        except Exception as e:
            logger.error(f"Error deleting email {email_id}: {str(e)}")
            raise

    def delete_all_emails(self) -> None:
        """
        Delete all emails from the database.
        Warning: This is a destructive operation that cannot be undone.
        """
        try:
            logger.warning("Initiating deletion of ALL emails from the database")
            self.index.delete(delete_all=True)
            logger.info("Successfully deleted all emails from the database")
        except Exception as e:
            logger.error(f"Error deleting all emails: {str(e)}")
            raise

    def query_emails(self, query_text: str, top_k: int = 5) -> List[str]:
        """
        Query similar emails based on the input text.
        
        Args:
            query_text (str): The text to search for similar emails
            top_k (int): Number of similar emails to return (default: 5)
        
        Returns:
            list: List of similar email texts
        """
        try:
            logger.info(f"Querying emails with text: '{query_text[:50]}...' (top_k={top_k})")
            q_embedding = get_embedding(query_text)
            results = self.index.query(
                vector=q_embedding,
                top_k=top_k,
                include_metadata=True,
                namespace=self.namespace
            )
            logger.info(f"Found {len(results['matches'])} matching emails")
            return [result['metadata']['text'] for result in results['matches']]
        except Exception as e:
            logger.error(f"Error querying emails: {str(e)}")
            raise

# if __name__ == "__main__":
#     pc = PineconeClient()
#     mail_client = MailClient()
#     emails = mail_client.get_emails(query="category:primary")
#     pc.upsert_emails(emails)

#     print("Total emails in database:", pc.get_email_count())
    
#     # Check index statistics including namespaces
#     stats = pc.index.describe_index_stats()
#     print("\nIndex statistics:")
#     print(stats)
    
#     print("\nTrying to query all emails...")
#     print(pc.query_emails(query_text="data science", top_k=1))
#     pc.delete_email("1957a9a46d84f37e")
#     print(pc.get_email_count())
#     pc.delete_all_emails()
#     print(pc.get_email_count())
