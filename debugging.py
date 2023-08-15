import streamlit as st
import os
import re
from langchain.embeddings import HuggingFaceEmbeddings, OpenAIEmbeddings
from qdrant_client import QdrantClient
from langchain.vectorstores import Qdrant
from qdrant_client.models import Distance, VectorParams
from langchain.chat_models.openai import ChatOpenAI
from langchain.prompts.chat import HumanMessagePromptTemplate, SystemMessagePromptTemplate
from langchain.prompts import ChatPromptTemplate

# Set variables
vault_address = "/Users/yanbarta/Library/Mobile Documents/iCloud~md~obsidian/Documents/The Foundation/TTRPG/"
current_adventure = "Bardic tales/"
db_path = "/Users/yanbarta/Documents/gmGPT/"
last_x_summary_senteces = 5

characer_path = os.path.join(vault_address, current_adventure, "Character.md")
setting_path = os.path.join(vault_address, current_adventure, "Setting.md")
summary_path = os.path.join(vault_address, current_adventure, "Summary.md")
prevously_path = os.path.join(vault_address, current_adventure, "Previously.md")
current_situation_path = os.path.join(vault_address, current_adventure, "Current situation.md")
game_path = os.path.join(vault_address, current_adventure, "Game.md")
instructions_path = os.path.join(vault_address, current_adventure, "Instructions.md")

# When doing a vector search using current sitution, how many sentences from the summary should be pulled
k_summary_sentences_from_situation = 7
k_full_text_from_game = 4

# Small 512 encoder
embedding = HuggingFaceEmbeddings(model_name='all-MiniLM-L6-v2')


# Fetch API token from file
with open("/Users/yanbarta/openai_api_token.txt", "r") as api_token:
    openai_token = api_token.read()


# Large 1536 encoder
openai_embedding = OpenAIEmbeddings(openai_api_key=openai_token)

# Model for summarisation
summary_model = ChatOpenAI(openai_api_key=openai_token,
                       model="gpt-3.5-turbo",
                       temperature=0.5,
                       )

summary_prompt = ChatPromptTemplate.from_messages([
    SystemMessagePromptTemplate.from_template("You are a summarisation tool. Your task is to use simple, self-contained sentences that summarise user input."),
    HumanMessagePromptTemplate.from_template("{text}")])


# QDrant varaibles
full_text_db_name = "full_conversation"
summary_db_name = "summaries"
summary_db_path = os.path.join(db_path, "Summaries.json")
with open("/Users/yanbarta/qdrant_api_key.txt", "r") as api_token:
    qdrant_token = api_token.read()
qdrant_address = "https://fdd4a708-5232-433e-a5f0-830c4eb7e177.eu-central-1-0.aws.cloud.qdrant.io:6333"

qdrant_client = QdrantClient(url=qdrant_address, api_key=qdrant_token)

summary_vectorstore = Qdrant(
    client=qdrant_client,
    collection_name=summary_db_name,
    embeddings=embedding,
)

full_text_vectorstore = Qdrant(
    client=qdrant_client,
    collection_name=full_text_db_name,
    embeddings=openai_embedding,
)

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

def search_vectorstore(query, vectorstore, k):
    if isinstance(query, list):
        matches = set()
        for item in query:
            search_result = vectorstore.similarity_search(item, k=k)
            for match in search_result:
                matches.add(match.page_content)
        return list(matches)
    
    elif isinstance(query, str):
        matches = vectorstore.similarity_search(query, k=k)
        return [match.page_content for match in matches]
    
    else:
        raise TypeError("Query must be either string or list of strings")


def continue_adventure():
    last_x_sentences = split_to_setences(read_file(summary_path))
    # Get only last x sentences of the summary
    if len(last_x_sentences) > last_x_summary_senteces:
        last_x_sentences = last_x_sentences[last_x_summary_senteces:]
    last_x_sentences_text = '.\n \n'.join(last_x_sentences)
    current_situation = read_file(current_situation_path)
    summary_search_result = search_vectorstore(current_situation, summary_vectorstore, k_summary_sentences_from_situation)
    summary_search_result_for_print = ('\n \n'.join(summary_search_result))
    character_info = read_file(characer_path)
    setting_info = read_file(setting_path)
    instructions = read_file(instructions_path)
    latest_conversation = read_file(game_path)
    game_paragraphs = split_to_paragraphs(latest_conversation)
    best_game_results = search_vectorstore(game_paragraphs, full_text_vectorstore, k_full_text_from_game)
    best_game_results_for_print = ('\n'.join(best_game_results))

    query = f"""
# Instructions

{instructions}

# Setting

{setting_info}

# Character

{character_info}

# Previously
## Summary

{summary_search_result_for_print}
{last_x_sentences_text}

## Conversation log

{best_game_results_for_print}

# Currently
## Scene

{current_situation}

## Conversation

Narrator:
    """

    print(query)
    return query


def on_text_update(key, path):
    if st.session_state[key]:
        updated_text = st.session_state[key]
        write_file(path, updated_text)

def transfer_to_memory():
    # get game file and add it to full text database
    game_text = read_file(game_path)
    game_paragraphs = split_to_paragraphs(game_text)
    full_text_vectorstore.add_texts(game_paragraphs)

    # create a summary

    # add summary to summary file and and database

    # wipe game file and append content to full text file
    write_file(game_path, "")
    write_file(current_situation_path, "")
    return True

def rebuild_memory():
    # Wipe full text database
    # uses larger encoder - openai
    qdrant_client.recreate_collection(collection_name=full_text_db_name, vectors_config=VectorParams(size=1536, distance=Distance.COSINE))
    # Get all paragraphs from Previously
    full_text_paragraphs = split_to_paragraphs(read_file(prevously_path))
    # Add them to the database
    full_text_vectorstore.add_texts(full_text_paragraphs)

    # Wipe summary database
    # It is using smaller encoder because it is just single sentences
    qdrant_client.recreate_collection(collection_name=summary_db_name, vectors_config=VectorParams(size=384, distance=Distance.COSINE))
    # Get all of summary
    summary_sentences = split_to_setences(read_file(summary_path))
    # Add it to the database
    summary_vectorstore.add_texts(summary_sentences)




text_for_summary = read_file(game_path)
print(summary_model(summary_prompt.format_prompt(text=text_for_summary).to_messages()).content)