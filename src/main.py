"""
RAG-based Email Chatbot

This script implements a chatbot that can answer questions about your emails using RAG
(Retrieval Augmented Generation) approach. It fetches emails from Gmail, stores them in
a vector database (Pinecone), and uses OpenAI to generate relevant responses.
"""

from dotenv import load_dotenv
load_dotenv()  # Load environment variables from .env file

import logging
import argparse
from mail import MailClient
from vector_db import PineconeClient
from generator import Generator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        logging.FileHandler('logs/main.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def ingest_emails():
    """Fetch emails from Gmail and store them in the vector database."""
    try:
        # Initialize Gmail client and fetch emails
        logger.info("Initializing Gmail client...")
        mail_client = MailClient()
        logger.info("Fetching emails from Gmail...")
        emails = mail_client.get_emails(query="category:primary")
        logger.info(f"Successfully retrieved {len(emails)} emails")

        # Initialize Pinecone client and store emails
        logger.info("Initializing Pinecone client...")
        pinecone_client = PineconeClient()
        logger.info("Upserting emails to Pinecone vector database...")
        pinecone_client.upsert_emails(emails)
        logger.info("Successfully stored emails in vector database")
        print("\n Emails have been successfully loaded into the database!")

    except Exception as e:
        logger.error(f"An error occurred during ingestion: {str(e)}", exc_info=True)
        print("\n Sorry, an error occurred while loading emails.")

def chat_loop():
    """Interactive loop for querying the email database."""
    try:
        # Initialize Pinecone client for querying
        generator = Generator()
        print("\nWelcome to Email Chatbot! Type 'exit' to quit.")
        while True:
            # Get user's question about their emails
            user_query = input("\nAsk something about your emails (like: Show my Amazon orders): ")
            
            if user_query.lower() in ['exit', 'quit']:
                print("Goodbye! ")
                break

            logger.info(f"Received user query: {user_query}")

            # Generate response using OpenAI
            logger.info("Generating response using OpenAI...")
            response = generator.generate_answer(user_query)
            logger.info("Successfully generated response")

            # Display the response to the user
            print("\n Answer from OpenAI:")
            print(response)

    except Exception as e:
        logger.error(f"An error occurred during chat: {str(e)}", exc_info=True)
        print("\n Sorry, an error occurred while processing your request.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Email Chatbot with RAG")
    parser.add_argument('--ingest', action='store_true', help='Fetch and store emails in the vector database')
    args = parser.parse_args()

    if args.ingest:
        ingest_emails()
    else:
        chat_loop()