import streamlit as st
import os
import re
from langchain.embeddings import OpenAIEmbeddings
from qdrant_client import QdrantClient
import openai
from langchain.vectorstores import Qdrant
from qdrant_client.models import Distance, VectorParams
from langchain.embeddings import OpenAIEmbeddings

# Set variables
vault_address = "."
current_adventure = "Template/"
last_x_summary_senteces = 3

characer_path = os.path.join(vault_address, current_adventure, "Character.md")
setting_path = os.path.join(vault_address, current_adventure, "Setting.md")
summary_path = os.path.join(vault_address, current_adventure, "Summary.md")
prevously_path = os.path.join(vault_address, current_adventure, "Previously.md")
current_situation_path = os.path.join(vault_address, current_adventure, "Current situation.md")
game_path = os.path.join(vault_address, current_adventure, "Game.md")
instructions_path = os.path.join(vault_address, current_adventure, "Instructions.md")
summary_instruction_path = os.path.join(vault_address, current_adventure, "Summary instructions.md")

azure_openai_path = os.path.join(vault_address, "/azure_openai_api_token.txt")

qdrant_endpoint_path = os.path.join(vault_address, "/qdrant_endpoint.txt")
qdrant_api_key_path = os.path.join(vault_address, "/qdrant_api_token.txt")

# When doing a vector search using current sitution, how many sentences from the summary should be pulled
k_summary_sentences_from_situation = 3
k_full_text_from_game = 3

# Set up variable that keeps track of token usage
if 'usage' not in st.session_state:
        st.session_state.usage = 0


def read_file(path):
    with open(path, "r") as f:
        content = f.read()
    return content



# Azure definition

azure_version = "2023-07-01-preview"
azure_base = "https://dsopenaidev.openai.azure.com/"

openai.api_type = "azure"
os.environ["OPENAI_API_TYPE"] = "azure"
openai.api_base = azure_base
os.environ["OPENAI_API_BASE"] = azure_base
openai.api_version = azure_version
os.environ["OPENAI_API_VERSION"] = azure_version
azure_openai_key = read_file(azure_openai_path)
openai.api_key = azure_openai_key
os.environ["OPENAI_API_KEY"] = azure_openai_key

azure_embedding = OpenAIEmbeddings(deployment="embeddings", openai_api_version=azure_version, 
                                   openai_api_base=azure_base, openai_api_key=azure_openai_key)

prompt_cost_gpt4 = 0.03
completion_cost_gpt4 = 0.06

prompt_cost_gpt35 = 0.003
completion_cost_gpt35 = 0.004

# QDrant varaibles
full_text_db_name = "full_conversation"
summary_db_name = "summaries"
qdrant_address = read_file(qdrant_endpoint_path)
qdrant_api_key= read_file(qdrant_api_key_path)


qdrant_client = QdrantClient(url=qdrant_address, api_key=qdrant_api_key)

full_text_vectorstore = Qdrant(
    client=qdrant_client,
    collection_name=full_text_db_name,
    embeddings=azure_embedding,
)

summary_vectorstore = Qdrant(
    client=qdrant_client,
    collection_name=summary_db_name,
    embeddings=azure_embedding,
)

def write_file(path, content):
    with open(path, "w") as f:
        f.write(content)

def append_to_file(path, text):
    with open(path, "a") as f:
        f.write(text)

def split_to_setences(content):
    content = content.replace("\n", " ")
    return content.split(".")

def split_to_paragraphs(content):
    pattern = r"(Narrator:|Player:)"
    paragraphs = re.split(pattern, content)[1:]
    paragraphs = [paragraphs[i] + paragraphs[i+1] for i in range(0, len(paragraphs), 2)]
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

def get_llm_response(query, model, temperature, max_tokens, stopwords):
    response = openai.ChatCompletion.create(
            engine=model,
            messages = query,
            temperature=temperature,
            max_tokens=max_tokens,
            top_p=0.95,
            frequency_penalty=0,
            presence_penalty=0,
            stop=stopwords)
    return response

def chunkify_and_add_to_db(vectorstore, paragraphs):
    # split list of paragraphs into chunks of 16
    chunks = [paragraphs[i:i+16] for i in range(0, len(paragraphs), 16)]
    for chunk in chunks:
        vectorstore.add_texts(chunk)

def calculate_cost(response):
    if response["model"] == "gpt-4-0613":
        prompt_cost = response.usage.prompt_tokens * prompt_cost_gpt4
        completion_cost = response.usage.completion_tokens * completion_cost_gpt4
    else:
        prompt_cost = response.usage.prompt_tokens * prompt_cost_gpt35
        completion_cost = response.usage.completion_tokens * completion_cost_gpt35
    print(f"Prompt tokens: {response.usage.prompt_tokens}")
    print(f"Completion tokens: {response.usage.completion_tokens}")
    return round((prompt_cost + completion_cost)/1000, 3)

def continue_adventure():
    last_x_sentences = split_to_setences(read_file(summary_path))
    # Get only last x sentences of the summary
    if len(last_x_sentences) > last_x_summary_senteces:
        last_x_sentences = last_x_sentences[-last_x_summary_senteces:]
    last_x_sentences_text = '.\n \n'.join(last_x_sentences)
    current_situation = read_file(current_situation_path)
    summary_search_result = search_vectorstore(current_situation, summary_vectorstore, k_summary_sentences_from_situation)
    summary_search_result_for_print = ('\n \n'.join(summary_search_result))
    character_info = read_file(characer_path)
    setting_info = read_file(setting_path)
    instructions = read_file(instructions_path)
    latest_conversation = read_file(game_path)
    if latest_conversation:
        game_paragraphs = split_to_paragraphs(latest_conversation)
    else:
        game_paragraphs = [current_situation]
    game_paragraphs = split_to_paragraphs(latest_conversation)
    best_game_results = search_vectorstore(game_paragraphs, full_text_vectorstore, k_full_text_from_game)
    best_game_results_for_print = ('\n'.join(best_game_results))
    query = f"""
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

## Latest conversation
{latest_conversation}

Narrator:
    """

    call = [{"role": "system", "content": instructions}, {"role":"user", "content": query}]
    llm_response = get_llm_response(call, "gpt-4-0613", 0.8, 600, "Player:")
    content = llm_response.choices[0].message["content"]

    append_to_file(game_path, "\n\nNarrator:\n" + content)

    usage = calculate_cost(llm_response)
    st.session_state.usage = usage
    
    


def on_text_update(key, path):
    if key in st.session_state:
        updated_text = st.session_state[key]
        write_file(path, updated_text)
        

def transfer_to_memory():
    # Get current situation 
    current_situation = read_file(current_situation_path)

    # get game file and add it to full text database
    game_text = read_file(game_path)
    game_paragraphs = split_to_paragraphs(game_text)
    chunkify_and_add_to_db(full_text_vectorstore, game_paragraphs)

    # Append to full text
    append_to_file(prevously_path, game_text)

    # Combine current situtation and game text for summary
    for_summary = f" Scene setting: {current_situation} \n \n {game_text}"

    # create a summary
    summary_instructions = read_file(summary_instruction_path)
    
    messages = [{"role":"system", "content": summary_instructions}, {"role":"user", "content": "Text to be summarised:\n" + for_summary}]
    summary = get_llm_response(messages, "gpt-35-turbo-16k", 0.7, 600, None)
    summary_content = summary.choices[0].message["content"]
    print(summary_content)
    summary_usage = calculate_cost(summary)
    st.session_state.usage = summary_usage
    # add summary to summary file and and database

    chunkify_and_add_to_db(summary_vectorstore, split_to_setences(summary_content))
    append_to_file(summary_path, "\n\n" + summary_content)
    # wipe game file and append content to full text file
    write_file(game_path, "")
    write_file(current_situation_path, "")

def rebuild_memory():
    # Reset full text database
    qdrant_client.recreate_collection(collection_name=full_text_db_name, vectors_config=VectorParams(size=1536, distance=Distance.COSINE))
    # because Azure is a crybaby which can't make more than 16 embeddings at once
    chunkify_and_add_to_db(full_text_vectorstore, split_to_paragraphs(read_file(prevously_path)))

    # Wipe summary database
    # It is using smaller encoder because it is just single sentences
    qdrant_client.recreate_collection(collection_name=summary_db_name, vectors_config=VectorParams(size=1536, distance=Distance.COSINE))
    # Add summary
    chunkify_and_add_to_db(summary_vectorstore, split_to_paragraphs(read_file(summary_path)))

def main():
    st.header("gmGPT")
    st.subheader("Your personal ttrpg Game Master.")
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
                  on_click = transfer_to_memory)
    
    with col3:
        st.button("Rebuild memory", 
                  key="rebuild_button", 
                  help="Wipes current database and rebuilds it from Summary and Previously.",
                  on_click = rebuild_memory)
    st.write(f"Last call cost ${st.session_state.usage}")
    st.text_area(label="Game", key="game_space_input", value=read_file(game_path), height= 600, on_change=lambda: on_text_update("game_space_input", game_path))
    
    with st.sidebar:
        st.subheader("Supporting information")
        st.text_area(label="Who is your character?", height= 100, value=read_file(characer_path), key="character_input", on_change=lambda: on_text_update("character_input", characer_path))
        st.text_area(label="Setting",height= 100, value=read_file(setting_path), key="setting_input", on_change=lambda: on_text_update("setting_input", setting_path))
        st.text_area(label="Summary",height= 300,value=read_file(summary_path), key="summary_input", on_change=lambda: on_text_update("summary_input", summary_path))
        st.text_area(label="Previously",height= 300, value=read_file(prevously_path), key="previously_input", on_change=lambda: on_text_update("previously_input", prevously_path))

if __name__ == '__main__':
    main()