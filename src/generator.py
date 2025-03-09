import os
import logging
from openai import OpenAI
from cohere import Client
from vector_db import PineconeClient
from utils import get_embedding

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/generator.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class Generator:
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY2"))
        self.cohere_client = Client(api_key=os.getenv("COHERE_API_KEY"))
        self.pc = PineconeClient()

    def rerank_results(self, user_question, email_texts):
        cohere_response = self.cohere_client.rerank(
            model='rerank-english-v2.0',
            documents=email_texts,
            query=user_question,
            top_n=5
        )
        return [email_texts[item.index] for item in cohere_response.results]

    def generate_answer(self, user_question):
        # Step 1: Generate embeddings and query Pinecone
        logger.debug("Generating embedding for question")
        question_embedding = get_embedding(user_question)

        # Query Pinecone for relevant emails
        logger.debug("Querying Pinecone for relevant emails")
        email_texts = self.pc.query_emails(user_question, top_k=3)
        logger.info(f"Retrieved {len(email_texts)} email chunks from vector store")
        for i, email in enumerate(email_texts):
            print(f"Email {i+1}: {email[:100]}")

        # Step 2: Re-rank results using Cohere for better relevance
        logger.info("Re-ranking results using Cohere")
        reranked_texts = self.rerank_results(user_question, email_texts)
        for i, email in enumerate(reranked_texts):
            print(f"Reranked Email {i+1}: {email[:100]}")
        email_text = "\n\n".join(reranked_texts)

        # Step 3: Generate response using OpenAI
        prompt = f"""
        You are an AI email assistant. Use the following chain of thought approach:

        1. **Understand the context**: Carefully read the emails provided.
        2. **Extract relevant information**: Identify the content most relevant to the user's query.
        3. **Answer the question concisely**: Use the extracted information to answer the user's question as clearly as possible.

        Here are some emails from my Gmail:
        {email_text}

        Now answer this question based on my emails: {user_question}
        """
        logger.debug("Sending prompt to OpenAI for final response")
        response = self.client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a helpful assistant using chain-of-thought reasoning."},
                {"role": "user", "content": prompt}
            ]
        )

        answer = response.choices[0].message.content
        logger.info("Successfully generated response")
        return answer
    
# if __name__ == "__main__":
#     generator = Generator()
#     print(generator.generate_answer("What is the latest rapido invoice amount?"))

