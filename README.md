# gmGPT
A LangChain application that acts as a Game Master for a setting and character of your choice. 

## How to use it:

### GUI
Once you set up your environment (guide under Installation), you can run the app using `streamlit run app.py` (make sure you are running this command in the same folder where the app.py is located and in an environment that has streamlit installed). The following page should appear in your default browser:
![image](https://github.com/OctipusPrime/gmGPT/assets/77053094/8a20321b-08e9-4ab9-acc6-70ac5277f7ff)

To start using the app you must
1. Fill out the setting (DnD or other well known fandom works)
2. Fill out your character
3. Press "Rebuild memory" to test vectorstores
4. Fill out the "Current situation" where you describe the current scene

After that simply press "Start/Continue adventure" and enjoy. 
Once a certain scene is finihsed, press "Transfer to memory" which
- creates a summary of the current scene
- add summary and full record to vector store
- reduces the cost per answer (full current convesation is added to the prompt, which can raise the costs)
- Allows the GM to remember beyond the context limit

### CLI
There is a branch "CLI" that you can switch to. This version has commands `continue`, `transfer` and `rebuild` which work the same way as the buttons in the GUI version. You will need to have a separate software of your choice for displaying the markdown files. 

## Installation
1. Use requirement.txt to create a virtual environment with all the dependencies.
2. Change paths (first few lines in app.py) to where you want to be storing your .md files. Template folder is provided in the repository.
3. Add openai api key, qdrant api key, qdrant endpoint htttp either as files or paste them directly into the code.

## How it works
TODO
