from flask import Flask, request, jsonify ,g
import os
from llama_index.core import (
    SimpleDirectoryReader, VectorStoreIndex, StorageContext,
    load_index_from_storage
)
# from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.core.node_parser import SentenceWindowNodeParser, SentenceSplitter
from llama_index.core.postprocessor import MetadataReplacementPostProcessor
from LLM import LLM
from llama_index.core import Settings
from flask_cors import CORS
from CustomEmbedding import CustomAPIEmbeddings
from threading import Lock
import re

app = Flask(__name__)
CORS(app, origins=["http://localhost:8080","https://ve4al631sy.dsone.3ds.com:444/", "https://vdevpril922dsy.dsone.3ds.com:444","https://ve4al631sy.dsone.3ds.com:444","https://dsext001-eu1-215dsi0708-ifwe.3dexperience.3ds.com"]) 

# Global variables for indices
sentence_index = None
base_index = None


def extract_queries(text):
    # Regex pattern to match numbered list items
    pattern = r'\d+\.\s+([^\n]+)'
    queries = re.findall(pattern, text)
    return queries


def initialize_index():
    global sentence_index , base_index

    if os.path.exists("vector_store/sentence_index") and os.path.exists("vector_store/base_index"):
        storage_context_sentence = StorageContext.from_defaults(persist_dir="vector_store/sentence_index")
        sentence_index = load_index_from_storage(storage_context_sentence)
        
        storage_context_base = StorageContext.from_defaults(persist_dir="vector_store/base_index")
        base_index = load_index_from_storage(storage_context_base)
    else:
        reader = SimpleDirectoryReader(input_dir="documentation", recursive=True)
        documents = reader.load_data()
        
        node_parser = SentenceWindowNodeParser.from_defaults(
            window_size=3,
            window_metadata_key="window",
            original_text_metadata_key="original_text"
        )
        nodes = node_parser.get_nodes_from_documents(documents)
        sentence_index = VectorStoreIndex(nodes)
        sentence_index.storage_context.persist(persist_dir="vector_store/sentence_index")
        
        text_splitter = SentenceSplitter()
        base_nodes = text_splitter.get_nodes_from_documents(documents)
        base_index = VectorStoreIndex(base_nodes)
        base_index.storage_context.persist(persist_dir="vector_store/base_index")
    return sentence_index, base_index
 
@app.route('/ds_doc', methods=['POST'])
def home():
    global sentence_index , base_index
   
   
    data = request.json
    query_text = data.get('query', '')
    print("query_text", query_text)
    if not query_text:
            return jsonify({"error": "No query provided"}), 400
    try:
        Settings.llm = LLM()
        embed_model = CustomAPIEmbeddings(embed_batch_size=2)
        Settings.embed_model = embed_model


        prompt = f"""Reformulate and Transform the following query into clear, concise natural language sub-queries. simply list the distinct questions.
            Respond ONLY with list of Queries .
            The Original query: {query_text}"""
        llm = LLM()
        processed_query = llm.complete(prompt).text
        print(f"Query After: {query_text}")
        print("------------------")
        print(f"Query Before: {processed_query}")
        extracted_queries = extract_queries(processed_query)
        print(f"Processed Cleaned Query : {extracted_queries}")

        if sentence_index is None or base_index is None:
            initialize_index()

        query_engine = sentence_index.as_query_engine(
            similarity_top_k=5,
            node_postprocessors=[MetadataReplacementPostProcessor(target_metadata_key="window")]
        )
        responses = []
        for query in extracted_queries:
            response = query_engine.query(query)
            print(f"\nQUESTION : {query} :\n RESPONSE {response}")
            # window = response.source_nodes[0].node.metadata["window"]
            # sentence = response.source_nodes[0].node.metadata["original_text"]
            # print(f"Window: {window}")
            # print("------------------")
            # print(f"Original Sentence: {sentence}")
            responses.append(f"QUERY: {query}  :\n RESPONSE: {response}")
        final_responses = "\n".join(responses)


        print(f"_____________________________________")


        resume_prompt=f"""Reformulate and provide a well-structured response based on the information given. Conclude with a concise summary of the main points.{final_responses}"""

        final_response= llm.complete(resume_prompt).text
        cleaned_response = re.sub(r"^Here is.*?\n", "", final_response, flags=re.DOTALL)

        print(f"_____________________________________")
        print("CHATBOT RESPONSE",cleaned_response)
        return str(cleaned_response), 200
    
    except Exception as e:
        print(e) 
        return jsonify({"error": "Error processing your query"}), 500
    

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001)
