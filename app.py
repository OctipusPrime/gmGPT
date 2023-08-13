import streamlit as st
import os

# Set variables
vault_address = "/Users/yanbarta/Library/Mobile Documents/iCloud~md~obsidian/Documents/The Foundation/TTRPG/"
current_adventure = "Bardic tales/"
last_x_summary_senteces = 10

characer_path = os.path.join(vault_address, current_adventure, "Character.md")
setting_path = os.path.join(vault_address, current_adventure, "Setting.md")
summary_path = os.path.join(vault_address, current_adventure, "Summary.md")
prevously_path = os.path.join(vault_address, current_adventure, "Previously.md")
current_situation_path = os.path.join(vault_address, current_adventure, "Current situation.md")
game_path = os.path.join(vault_address, current_adventure, "Game.md")
instructions_path = os.path.join(vault_address, current_adventure, "Instructions.md")

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
        st.button("Transfer into memory", key="transfer_button", help="Transfer current conversation into memory to reduce context size (= cost per response)")
    
    st.text_area(label="Game", key="game_space_input", value=read_file(game_path), height= 1000, on_change=lambda: on_text_update("game_space_input", game_path))
    
    with st.sidebar:
        st.subheader("Supporting information")
        st.text_area(label="Who is your character?", height= 200, value=read_file(characer_path), key="character_input", on_change=lambda: on_text_update("character_input", characer_path))
        st.text_area(label="Setting",height= 200, value=read_file(setting_path), key="setting_input", on_change=lambda: on_text_update("setting_input", setting_path))
        st.text_area(label="Summary",height= 400,value=read_file(summary_path), key="summary_input", on_change=lambda: on_text_update("summary_input", summary_path))
        st.text_area(label="Previously",height= 500, value=read_file(prevously_path), key="previously_input", on_change=lambda: on_text_update("previously_input", prevously_path))

if __name__ == '__main__':
    main()