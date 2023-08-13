import streamlit as st
import os
import re
import json
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams
from qdrant_client.http import models


# Set variables
vault_address = "/Users/yanbarta/Library/Mobile Documents/iCloud~md~obsidian/Documents/The Foundation/TTRPG/"
current_adventure = "Bardic tales/"
db_path = "/Users/yanbarta/Documents/gmGPT/"
last_x_summary_senteces = 10

characer_path = os.path.join(vault_address, current_adventure, "Character.md")
setting_path = os.path.join(vault_address, current_adventure, "Setting.md")
summary_path = os.path.join(vault_address, current_adventure, "Summary.md")
prevously_path = os.path.join(vault_address, current_adventure, "Previously.md")
current_situation_path = os.path.join(vault_address, current_adventure, "Current situation.md")
game_path = os.path.join(vault_address, current_adventure, "Game.md")
instructions_path = os.path.join(vault_address, current_adventure, "Instructions.md")

# QDrant varaibles
full_text_db_name = "full_conversation"
summary_db_name = "summaries"
summary_db_path = os.path.join(db_path, "Summaries.json")
with open("/Users/yanbarta/qdrant_api_key.txt", "r") as api_token:
    qdrant_token = api_token.read()
qdrant_address = "https://fdd4a708-5232-433e-a5f0-830c4eb7e177.eu-central-1-0.aws.cloud.qdrant.io:6333"

qdrant_client = QdrantClient(url=qdrant_address, api_key=qdrant_token)

# Small 512 encoder
encoder = SentenceTransformer('all-MiniLM-L6-v2')


# Fetch API token from file
with open("/Users/yanbarta/openai_api_token.txt", "r") as api_token:
    openai_token = api_token.read()


def read_file(path):
    with open(path, "r") as f:
        content = f.read()
    return content

def write_file(path, content):
    with open(path, "w") as f:
        f.write(content)

def split_to_setences(content):
    content = content.replace("\n", " ")
    return content.split(".")

def split_to_paragraphs(content):
    pattern = r"(Narrator:|Player:)"
    paragraphs = re.split(pattern, content)[1:]
    paragraphs = [paragraphs[i] + paragraphs[i+1] for i in range(0, len(paragraphs), 2)]
    paragraphs = [p.strip() for p in paragraphs if p.strip()]
    return paragraphs


def continue_adventure():
    last_x_sentences = split_to_setences(read_file(summary_path))
    # Get only last x sentences of the summary
    if len(last_x_sentences) > last_x_summary_senteces:
        last_x_sentences = last_x_sentences[last_x_summary_senteces:]
    last_x_sentences_text = '.'.join(last_x_sentences)
    current_situation = read_file(current_situation_path)
    latest_conversation = read_file(game_path)
    character_info = read_file(characer_path)
    setting_info = read_file(setting_path)
    instructions = read_file(instructions_path)
    previously = read_file(prevously_path)

    query = f"""
# Instructions
{instructions}
# Setting
{setting_info}
# Character
{character_info}
# Previously
## Summary
{last_x_sentences_text}
## Conversation log
{previously}
# Currently
## Scene
{current_situation}

## Conversation
{latest_conversation}
Narrator:
    """

    print(query)
    return query


def on_text_update(key, path):
    if st.session_state[key]:
        updated_text = st.session_state[key]
        write_file(path, updated_text)

def rebuild_memory():
    summary_local_db = {}
    summary_counter = 1
    summary_sentences = split_to_setences(read_file(summary_path))
    for summary_text in summary_sentences:
        summary_encoding = encoder.encode(summary_text)
        # Add it to local db
        summary_local_db[summary_counter] = summary_text
        qdrant_client.upsert(
            collection_name=summary_db_name,
            points=[models.PointStruct(
                id = summary_counter,
                vector= summary_encoding,
            )])
        summary_counter += 1
    write_file(summary_db_path, json.dumps(summary_local_db))
    return True

def main():
    st.set_page_config(page_title="gmGPT", page_icon="::robot::")
    
    st.header("gmGPT")
    st.subheader("Your personal Game Master for a DnD game.")
    st.text_area(label="Current situation", key="current_situation_input",height=100, value=read_file(current_situation_path), on_change=lambda: on_text_update("current_situation_input", current_situation_path))
    col1, col2, col3 = st.columns(3)
    with col1:
        st.button("Start/Continue adventure", 
                  key="start_button", 
                  help="Takes context + current situation + past conversation and generates Narrator response",
                  on_click=continue_adventure)
    with col2:
        st.button("Transfer into memory", 
                  key="transfer_button", 
                  help="Transfer current conversation into memory to reduce context size (= cost per response)",
                  on_click = rebuild_memory)
    
    with col3:
        st.button("Rebuild memory", key="rebuild_button", help="Wipes current database and rebuilds it from Summary and Previously.")
    st.text_area(label="Game", key="game_space_input", value=read_file(game_path), height= 1000, on_change=lambda: on_text_update("game_space_input", game_path))
    
    with st.sidebar:
        st.subheader("Supporting information")
        st.text_area(label="Who is your character?", height= 200, value=read_file(characer_path), key="character_input", on_change=lambda: on_text_update("character_input", characer_path))
        st.text_area(label="Setting",height= 200, value=read_file(setting_path), key="setting_input", on_change=lambda: on_text_update("setting_input", setting_path))
        st.text_area(label="Summary",height= 400,value=read_file(summary_path), key="summary_input", on_change=lambda: on_text_update("summary_input", summary_path))
        st.text_area(label="Previously",height= 500, value=read_file(prevously_path), key="previously_input", on_change=lambda: on_text_update("previously_input", prevously_path))

if __name__ == '__main__':
    main()