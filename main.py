import openai
import numpy as np
from langchain.embeddings import OpenAIEmbeddings
import json
import os
from qdrant_client import QdrantClient, models
from sentence_transformers import SentenceTransformer

# Set variables
current_adventure = "Bardic tales/"
folder_for_databases = "/Users/yanbarta/Documents/gmGPT/"

# Default variables
vault_adress = "/Users/yanbarta/Library/Mobile Documents/iCloud~md~obsidian/Documents/The Foundation/TTRPG/"
skippable_elements = ["", " ", "  ", "\n"]
skippable_elements2 = ["Narrator:", "Player:"]

# Set up sentence transformer
encoder = SentenceTransformer('all-MiniLM-L6-v2')

# Set up qdrant client
summary_db = QdrantClient(path=folder_for_databases + "summary_db")

summary_db.recreate_collection(
    collection_name="summary_db",
    vectors_config= models.VectorParams(
        size=encoder.get_sentence_embedding_dimension(),
        distance= models.Distance.COSINE,
    )
)

# Set up persistent dictionaries
if not os.path.exists('summary_dic.json'):
    # Create an empty dictionary and write it to the file
    summary_dic = {}
    with open('summary_dic.json', 'w') as file:
        json.dump(summary_dic, file)
with open('summary_dic.json', 'r') as file:
    summary_dic = json.load(file)


# Fetch API token from file
with open("/Users/yanbarta/openai_api_token.txt", "r") as api_token:
    token = api_token.read()

# export token to environment variable
openai.api_key = token

def get_OpenAI_embedding(text, model="text-embedding-ada-002"):
   text = text.replace("\n", " ")
   return openai.Embedding.create(input = [text], model=model)['data'][0]['embedding']

def get_paragraphs(file_name, source):
    list_of_paragraphs = []
    with open(file_name, "r") as file:
        text = file.read()
        for paragraph in text.split("\n"):
            # Skip empty lines
            if paragraph in skippable_elements:
                continue
            # Skip Narrator and Player lines
            elif "Narrator:" in paragraph or "Player:" in paragraph:
                continue
            else:
                list_of_paragraphs.append({"source": source, "text": paragraph})
    return list_of_paragraphs

def save_embeddings(db_entity,db_name,paragraphs):
    db_entity.upload_records(
        collection_name=db_name,
        records=[
            models.Record(
                id=idx,
                vector=encoder.encode(paragraph["text"]).tolist(),
                payload=paragraph
            ) for idx, paragraph in enumerate(paragraphs)
        ]
    )

def search_embeddings(db_entity, db_name, query, limit):
    return db_entity.search(
        collection_name=db_name,
        query_vector = encoder.encode(query).tolist(),
        limit = limit
    )

paragraphs = get_paragraphs(vault_adress + current_adventure + "Full summary.md", "summary")


save_embeddings(summary_db, "summary_db", paragraphs)

hits = search_embeddings(summary_db, "summary_db", "Elara negotiating about cooking supplies", 2)

for hit in hits:
   print(hit.payload)

#print(summary_dicg)