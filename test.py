import openai
import numpy as np
from langchain.embeddings import OpenAIEmbeddings
from annoy import AnnoyIndex
import tensorflow as tf
import tensorflow_hub as hub

from qdrant_client import QdrantClient, models


# Set variables
current_adventure = "Bardic tales/"
folder_for_databases = "/Users/yanbarta/Documents/gmGPT/"

# Default variables
vault_adress = "/Users/yanbarta/Library/Mobile Documents/iCloud~md~obsidian/Documents/The Foundation/TTRPG/"
skippable_elements = ["", " ", "  ", "\n"]
skippable_elements2 = ["Narrator:", "Player:"]

# Load embeddings model
module_url = "https://tfhub.dev/google/universal-sentence-encoder/4"
model = hub.load(module_url)

# Set up qdrant client
summary_db = QdrantClient(path=folder_for_databases + "summary_db")


