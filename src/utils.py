import os
import hashlib
from openai import OpenAI
from dotenv import load_dotenv
load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY2")
client = OpenAI(api_key=OPENAI_API_KEY)
ENGINE = 'text-embedding-3-small'

# Function to get embeddings for a list of texts using the OpenAI API
def get_embeddings(texts, engine=ENGINE):
    # Create embeddings for the input texts using the specified engine
    response = client.embeddings.create(
        input=texts,
        model=engine
    )

    # Extract and return the list of embeddings from the response
    return [d.embedding for d in list(response.data)]

# Function to get embedding for a single text using the OpenAI API
def get_embedding(text, engine=ENGINE):
    # Use the get_embeddings function to get the embedding for a single text
    return get_embeddings([text], engine)[0]

def my_hash(s):
    # Return the MD5 hash of the input string as a hexadecimal string
    return hashlib.md5(s.encode()).hexdigest()

# if __name__ == "__main__":
#     print(get_embedding("Hello, world!"))
#     print(get_embeddings(["Hello, world!", "Hello, world!"]))
#     print(len(get_embeddings(["Hello, world!", "Hello, world!"])))