import os
import sys
import re
import json
import requests
import random
import tempfile

from agents.agent import Agent
from agents.question_answerer import QuestionAnswerer
from langchain_community.document_loaders import PyPDFLoader
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import CharacterTextSplitter
from langchain_community.vectorstores import Chroma

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import config

class SearchAgent(Agent):
    def __init__(self) -> None:
        super().__init__()
        self.cache = {}
        self.question_answerer = QuestionAnswerer()
        
        # MODIFICATION: Replaced OpenAIEmbeddings with HuggingFaceEmbeddings.
        # Now we embed locally, change embedder in config.py
        print("[Investigator]: Loading local embedding model into memory (one-time)...")
        self.embeddings = HuggingFaceEmbeddings(model_name=config.embedding_model)

    def clean_conversational_question(self, question):
        # MODIFICATION: custom cleaning function for the agent's prompts.
        # We dont need those phrases...
        cleaned = question
        cleaned = re.sub(r'^(Investigator:\s*)', '', cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r'^(Search the web to understand\s*)', '', cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r'^(Search the paper to understand\s*)', '', cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r'^(Search the web to find\s*)', '', cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r'^(Search the paper to find\s*)', '', cleaned, flags=re.IGNORECASE)
        
        if not cleaned.endswith("?"):
            cleaned += "?"
            
        if cleaned:
            cleaned = cleaned[0].upper() + cleaned[1:]
            
        return cleaned

    def transform_query_for_vector_db(self, original_query):
        # MODIFICATION: Added a query transformation step.
        # The more precise the description, the better the output.
        prompt = f"""
        Transform the following search topic or question into a single, dense, factual scientific paragraph (like a paper's abstract) extracting the core scientific concepts.
        CRITICAL RULES:
        - It MUST be a single, dense, factual paragraph.
        - Use precise, objective scientific language.
        - NEVER include conversational filler.
        - It should read exactly like a dense section of a computer science or machine learning paper's abstract.
        
        Original search topic/question: "{original_query}"
        Dense scientific paragraph:
        """
        
        try:
            messages = [{"role": "user", "content": prompt}]
            transformed = self.send_message(messages).strip()
            transformed = transformed.replace('"', '').replace('`', '').strip()
            print(f"\n[Investigator]: Optimizing search query for vector database:")
            print(f">>> Original: '{original_query}'")
            print(f">>> Optimized:    '{transformed}'\n")
            return transformed
        except Exception as e:
            return original_query

    def handle_individual_result(self, search_result, is_pdf=0):
        if is_pdf == 1:
            link = search_result.get("link", "").strip('\"\' ')
            if not link:
                return ""
                
            print(f"[Investigator]: Loading the Paper for a detailed analysis...")
            
            evidence = ""
            try:
                if link.startswith("http"):
                    response = requests.get(link, timeout=30)
                    response.raise_for_status()
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                        tmp.write(response.content)
                        tmp_path = tmp.name
                    
                    loader = PyPDFLoader(tmp_path)
                    pages = loader.load()
                    os.remove(tmp_path)
                else:
                    loader = PyPDFLoader(link)
                    pages = loader.load()
                    
                evidence = "\n".join([page.page_content for page in pages])
            except Exception as e:
                print(f"[Investigator PDF Error]: Could not load paper: {e}")
                return ""

            if not evidence.strip():
                print("[Investigator]: The PDF does not contain readable text.")
                return ""

            # Chunking & Vector Database
            embeddings = self.embeddings
            text_splitter = CharacterTextSplitter(separator="\n", chunk_size=2000, chunk_overlap=200, length_function=len)
            
            try:
                chunks = text_splitter.create_documents([evidence])
            except Exception as e:
                print(f"[Investigator Chunking Error]: {e}")
                return ""

            if not chunks:
                return ""

            vectorstore = Chroma.from_documents(chunks, embeddings)
            retriever = vectorstore.as_retriever(search_kwargs={"k": 5})

            docs = retriever.invoke(search_result["search_string"])
            context_text = "\n\n".join([doc.page_content for doc in docs])
            vectorstore.delete_collection()
            
        else:
            context_text = search_result.get("evidence", "")

        if not context_text.strip():
            return ""

        prompt = f"Answer the question based on the context below. IF the question cannot be answered based on the context, return exactly 'I don't know' . . \n\n{context_text}\n\nQuestion: {search_result['search_string']}\nAnswer:"
        
        messages = [{"role": "user", "content": prompt}]
        result = self.send_message(messages)

        lower_res = result.lower()
        if "i don't know" in lower_res or "does not provide" in lower_res or "i'm sorry" in lower_res or "i do not know" in lower_res or "not clear" in lower_res:
            return ""

        return result

    def get_paper_results(self, search_string, paper_url):
        source = "the paper"
        search_result = {"search_string": search_string, "link": paper_url}
        source_doc = self.handle_individual_result(search_result, is_pdf=1)

        if source_doc != "":
            storage_key = paper_url + " " + search_string
            if storage_key in self.cache:
                return [self.cache[storage_key]]
            else:
                self.cache[storage_key] = {"answer": source_doc, "source": source}
                return [self.cache[storage_key]]
        else:
            return []

    def get_custom_api_results(self, search_string):
        # MODIFICATION: Replaced the original `__google_search__` with this custom API fetcher.
        # Using a dedicated domain-specific database (Ideenatlas) yields higher quality, scientifically relevant context for the reviewer agent.
        # My databse = no api costs, full control, only scientific details.
        clean_question = self.clean_conversational_question(search_string)
        dense_query = self.transform_query_for_vector_db(clean_question)
        
        url = "https://ideenatlas.eu/api/search?format=md"
        payload = {"query": dense_query}
        headers = {"Content-Type": "application/json"}
        
        print(f"[Investigator]: Searching private vector database...")
        
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            response.raise_for_status()
            md_data = response.text
        except Exception as e:
            print(f"[Investigator API Error]: {e}")
            return []

        # Parse and clean the returned markdown data
        # The returned markdown has a task instruction for agents, we dont want that here
        lines = md_data.split("\n")
        cleaned_lines = []
        skip = False
        for line in lines:
            if "**Your Task:**" in line:
                skip = True
                continue
            if skip and line.strip().startswith(">"):
                continue
            else:
                skip = False
            cleaned_lines.append(line)
        cleaned_md = "\n".join(cleaned_lines)

        prompt = f"""
        Answer the following question based on the Ideenatlas research data provided below.
        
        Question: {clean_question}
        
        Ideenatlas Research Data (Context):
        {cleaned_md}
        
        Answer:
        """
        
        messages = [{"role": "user", "content": prompt}]
        answer = self.send_message(messages).strip()

        lower_res = answer.lower()
        if "i don't know" in lower_res or "does not provide" in lower_res or "i'm sorry" in lower_res or "i do not know" in lower_res or "not clear" in lower_res:
            print("[Investigator]: No sufficient data found in the vector database.")
            return []

        print(f"[Investigator]: Answer successfully generated from Ideenatlas!")
        
        return [{
            "answer": answer,
            "source": "https://ideenatlas.eu"
        }]

    def answer_question(self, question, paper_url, from_paper):
        stored_answers = []
        if from_paper:
            search_results = self.get_paper_results(question, paper_url)
        else:
            # MODIFICATION: Pointed web search to the custom API instead of Google Search
            search_results = self.get_custom_api_results(question)
        
        for s in search_results:
            answer_text = s["answer"]
            source = s["source"]

            answer = self.question_answerer.get_answer_from_evidence(question, answer_text, source)
            if answer["answer"] == "unavailable":
                continue

            stored_answers.append(answer)
            if len(stored_answers) > 0:
                break

        if len(stored_answers) == 0:
            return {
                "actor": "Investigator",
                "answers": [],
                "description": "I could not find any answers.",
                "action": "answer the question \""+question+"\""
            }

        resolution = {
            "actor": "Investigator",
            "answers": stored_answers,
            "description": "I found the following answers:\n" + "\n".join([" * According to " + a["source"] + ", \""+ a["backing"] + "\"" for a in stored_answers]),
            "action": "answer the question \""+question+"\"",
            "question": question
        }
        print(resolution["description"])
        return resolution

    def get_actions(self):
        return [
            "Actor: Investigator | Action: Answer question using the paper | Parameters: question | Description: Answer the provided question from the provided paper. It is important that the query that is searched is a question ending in '?'.",
            "Actor: Investigator | Action: Answer question using Google | Parameters: question | Description: Use web search to try to answer the provided question. It is important that the query that is searched is a question ending in '?'.",
        ]
    
    def interpret(self, action):
        params = action.get("parameters", {})
        if not isinstance(params, dict):
            params = {}
            
        question = params.get("question") or params.get("query") or params.get("search_string")
        if not question and params:
            question = list(params.values())[0]
        if not question:
            try:
                question = action["plan"].get_next_step().describe()
            except:
                question = "Please summarize this section."

        cleaned_question = self.clean_conversational_question(question)

        if action["action"] == "Answer question using the paper":
            return self.answer_question(cleaned_question, action["paper_url"], from_paper=1)
        elif action["action"] == "Answer question using Google":
            return self.answer_question(cleaned_question, action["paper_url"], from_paper=0)
        else:
            return {
                "actor": "Investigator",
                "description": "This action is not in my set of possible instructions.",
                "action": action["action"]
            }