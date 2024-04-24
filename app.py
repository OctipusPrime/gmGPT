import streamlit as st
import argparse
import os
import re
from langchain.embeddings import HuggingFaceEmbeddings, OpenAIEmbeddings
from qdrant_client import QdrantClient
from langchain.vectorstores import Qdrant
from qdrant_client.models import Distance, VectorParams
from langchain.chat_models.openai import ChatOpenAI
from langchain.prompts.chat import (
    HumanMessagePromptTemplate,
    SystemMessagePromptTemplate,
)
from langchain.prompts import ChatPromptTemplate

# Set variables
vault_address = "/Users/yanbarta/Library/Mobile Documents/iCloud~md~obsidian/Documents/The Foundation/TTRPG/"
current_adventure = "Bardic tales/"
db_path = "/Users/yanbarta/Documents/gmGPT/"
last_x_summary_sentences = 3

character_path = os.path.join(vault_address, current_adventure, "Character.md")
setting_path = os.path.join(vault_address, current_adventure, "Setting.md")
summary_path = os.path.join(vault_address, current_adventure, "Summary.md")
previously_path = os.path.join(vault_address, current_adventure, "Previously.md")
current_situation_path = os.path.join(
    vault_address, current_adventure, "Current situation.md"
)
game_path = os.path.join(vault_address, current_adventure, "Game.md")
instructions_path = os.path.join(vault_address, current_adventure, "Instructions.md")

# When doing a vector search using current sitution, how many sentences from the summary should be pulled
k_summary_sentences_from_situation = 3
k_full_text_from_game = 3

# Small 512 encoder
embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")


# Fetch API token from file
with open("/Users/yanbarta/openai_api_token.txt", "r") as api_token:
    openai_token = api_token.read()

# Large 1536 encoder
openai_embeddings = OpenAIEmbeddings(openai_api_key=openai_token)

# Model for summarisation
summary_model = ChatOpenAI(
    openai_api_key=openai_token, model="gpt-3.5-turbo", temperature=0.5
)

story_model = ChatOpenAI(
    openai_api_key=openai_token,
    model="gpt-4",
)

prompt = ChatPromptTemplate.from_messages(
    [
        SystemMessagePromptTemplate.from_template("{instructions}"),
        HumanMessagePromptTemplate.from_template("{text}"),
    ]
)

os.environ["TOKENIZERS_PARALLELISM"] = "true"

# QDrant varaibles
full_text_db_name = "full_conversation"
summary_db_name = "summaries"
summary_db_path = os.path.join(db_path, "Summaries.json")
with open("/Users/yanbarta/qdrant_api_key.txt", "r") as api_token:
    qdrant_token = api_token.read()
qdrant_address = "https://fdd4a708-5232-433e-a5f0-830c4eb7e177.eu-central-1-0.aws.cloud.qdrant.io:6333"

qdrant_client = QdrantClient(url=qdrant_address, api_key=qdrant_token)

full_text_vectorstore = Qdrant(
    client=qdrant_client,
    collection_name=full_text_db_name,
    embeddings=openai_embeddings,
)

summary_vectorstore = Qdrant(
    client=qdrant_client,
    collection_name=summary_db_name,
    embeddings=embeddings,
)


def read_file(path):
    with open(path, "r") as f:
        content = f.read()
    return content


def write_file(path, content):
    with open(path, "w") as f:
        f.write(content)


def append_to_file(path, text):
    with open(path, "a") as f:
        f.write(text)


def split_to_sentences(content):
    content = content.replace("\n", " ")
    return content.split(".")


def split_to_paragraphs(content):
    pattern = r"(Narrator:|Player:)"
    paragraphs = re.split(pattern, content)[1:]
    paragraphs = [
        paragraphs[i] + paragraphs[i + 1] for i in range(0, len(paragraphs), 2)
    ]
    paragraphs = [p.strip() for p in paragraphs if p.strip()]
    return paragraphs


def search_vectorstore(query, vectorstore, number_of_results):
    if isinstance(query, list):
        matches = set()
        for item in query:
            search_result = vectorstore.similarity_search(item, k=number_of_results)
            for match in search_result:
                matches.add(match.page_content)
        return list(matches)

    elif isinstance(query, str):
        matches = vectorstore.similarity_search(query, k=number_of_results)
        return [match.page_content for match in matches]

    else:
        raise TypeError("Query must be either string or list of strings")


def continue_adventure():
    last_x_sentences = split_to_sentences(read_file(summary_path))
    # Get only last x sentences of the summary
    if len(last_x_sentences) > last_x_summary_sentences:
        last_x_sentences = last_x_sentences[-last_x_summary_sentences:]
    last_x_sentences_text = ".\n \n".join(last_x_sentences)
    current_situation = read_file(current_situation_path)
    summary_search_result = search_vectorstore(
        current_situation, summary_vectorstore, k_summary_sentences_from_situation
    )
    summary_search_result_for_print = "\n \n".join(summary_search_result)
    character_info = read_file(character_path)
    setting_info = read_file(setting_path)
    instructions = read_file(instructions_path)
    latest_conversation = read_file(game_path)
    if latest_conversation:
        game_paragraphs = split_to_paragraphs(latest_conversation)
    else:
        game_paragraphs = [current_situation]
    game_paragraphs = split_to_paragraphs(latest_conversation)
    best_game_results = search_vectorstore(
        game_paragraphs, full_text_vectorstore, k_full_text_from_game
    )
    best_game_results_for_print = "\n".join(best_game_results)
    query_system = instructions
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
{latest_conversation}
Narrator:
    """
    print(query)
    response = story_model(
        prompt.format_prompt(instructions=query_system, text=query).to_messages(),
        stop=["Player:"],
    ).content
    append_to_file(game_path, "\nNarrator:\n" + response)


def on_text_update(key, path):
    if st.session_state[key]:
        updated_text = st.session_state[key]
        write_file(path, updated_text)


def transfer_to_memory():
    # get game file and add it to full text database
    game_text = read_file(game_path)
    game_paragraphs = split_to_paragraphs(game_text)
    full_text_vectorstore.add_texts(game_paragraphs)

    # Append to full text
    append_to_file(previously_path, game_text)

    # create a summary
    # summary = summary_model(prompt.format_prompt(instructions= "You are a summarisation tool. Your task is to use simple, self-contained sentences that summarise user input.",text=game_text).to_messages()).content

    summary_instructions = f"""You are a summarisation tool. Your task is to use simple sentences that summarise the user input. 
    Each sentence must be self-contained and not rely on any other sentence to make sense."""
    summary = summary_model(
        prompt.format_prompt(
            instructions=summary_instructions, text=game_text
        ).to_messages()
    ).content
    # add summary to summary file and and database
    summary_vectorstore.add_texts(split_to_sentences(summary))
    append_to_file(summary_path, summary)
    # wipe game file and append content to full text file
    write_file(game_path, "")
    write_file(current_situation_path, "")
    return True


def rebuild_memory():
    # Reset full text database
    qdrant_client.recreate_collection(
        collection_name=full_text_db_name,
        vectors_config=VectorParams(size=1536, distance=Distance.COSINE),
    )
    # Get all paragraphs from Previously
    full_text_paragraphs = split_to_paragraphs(read_file(previously_path))
    # Add them to the database
    full_text_vectorstore.add_texts(full_text_paragraphs)

    # Wipe summary database
    # It is using smaller encoder because it is just single sentences
    qdrant_client.recreate_collection(
        collection_name=summary_db_name,
        vectors_config=VectorParams(size=384, distance=Distance.COSINE),
    )
    # Get all of summary
    summary_sentences = split_to_sentences(read_file(summary_path))
    # Add it to the database
    summary_vectorstore.add_texts(summary_sentences)


def main():
    # main
    st.set_page_config(page_title="gmGPT", page_icon="::robot::")
    st.header("gmGPT")
    st.subheader("Your personal ttrpg Game Master.")
    st.text_area(
        label="Current situation",
        key="current_situation_input",
        height=100,
        value=read_file(current_situation_path),
        on_change=lambda: on_text_update(
            "current_situation_input", current_situation_path
        ),
    )
    col1, col2, col3 = st.columns(3)
    with col1:
        st.button(
            "Start/Continue adventure",
            key="start_button",
            help="Takes context + current situation + past conversation and generates Narrator response",
            on_click=continue_adventure,
        )
    with col2:
        st.button(
            "Transfer into memory",
            key="transfer_button",
            help="Transfer current conversation into memory to reduce context size (= cost per response)",
            on_click=transfer_to_memory,
        )
    with col3:
        st.button(
            "Rebuild memory",
            key="rebuild_button",
            help="Wipes current database and rebuilds it from Summary and Previously.",
            on_click=rebuild_memory,
        )
    st.text_area(
        label="Game",
        key="game_space_input",
        value=read_file(game_path),
        height=1000,
        on_change=lambda: on_text_update("game_space_input", game_path),
    )
    # sidebar
    with st.sidebar:
        st.subheader("Supporting information")
        st.text_area(
            label="Who is your character?",
            height=200,
            value=read_file(character_path),
            key="character_input",
            on_change=lambda: on_text_update("character_input", character_path),
        )
        st.text_area(
            label="Setting",
            height=200,
            value=read_file(setting_path),
            key="setting_input",
            on_change=lambda: on_text_update("setting_input", setting_path),
        )
        st.text_area(
            label="Summary",
            height=400,
            value=read_file(summary_path),
            key="summary_input",
            on_change=lambda: on_text_update("summary_input", summary_path),
        )
        st.text_area(
            label="Previously",
            height=500,
            value=read_file(previously_path),
            key="previously_input",
            on_change=lambda: on_text_update("previously_input", previously_path),
        )


if __name__ == "__main__":
    main()
