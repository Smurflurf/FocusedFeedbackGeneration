This is a cloned and slightly rewritten and modernized version of https://github.com/ericchamoun/FocusedFeedbackGeneration.
Please take look at the original repo.
This code is purely educational and for nothing else.


To use and install everything, follow those steps:
(1. is only for the first use, afterwards, you only have to execute "source .venv/bin/activate" to run run.py)

1. create a venv and install all dependencies:
1.1: python3 -m venv .venv
1.2: source .venv/bin/activate
1.3: pip install --upgrade pip
1.4: pip install -r requirements.txt

2. ADD YOUR API KEYS!
2.1: Go to config.py
2.2: Change the LLM if you want (optional)
2.3: Change the embedder if you want (highly optional)
2.4: Add your gemini api keys to gemini_api_keys. There are instructions in config.py!

3. run it. 
3.1: pyhton3 run.py
3.2: You are asked for a paragraph. Make sure to paste it without any \n (line breaks), as the terminal probably won't understand that. 
3.3: You are asked for the link of the paper. You can paste the local link (on your file system) or an online link (like arxiv).
3.4: Wait and enjoy

4. run it again: 
4.1 comment the commets in run.py in to use the downloaded files.
4.2 source .venv/bin/activate (Activates the venv)
