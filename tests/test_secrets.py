from dotenv import load_dotenv
import os

def test_secrets():
    # Load environment variables from .env file
    load_dotenv()
    
    # Test getting environment variables
    openai_key = os.getenv('OPENAI_API_KEY2')
    pinecone_key = os.getenv('PINE_CONE_APT_KEY')
    
    # Print masked versions of the keys for verification
    print(f"OpenAI API Key exists: {'Yes' if openai_key else 'No'}")
    print(f"Pinecone API Key exists: {'Yes' if pinecone_key else 'No'}")
    
    # Print first and last 4 characters of each key if they exist
    if openai_key:
        print(f"OpenAI Key: {openai_key[:4]}...{openai_key[-4:]}")
    if pinecone_key:
        print(f"Pinecone Key: {pinecone_key[:4]}...{pinecone_key[-4:]}")

if __name__ == "__main__":
    test_secrets() 