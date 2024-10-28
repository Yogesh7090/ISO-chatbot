from langchain_community.document_loaders import PyMuPDFLoader
from langchain_openai import ChatOpenAI
from langchain.embeddings import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate
from langchain.chains import create_retrieval_chain
import streamlit as st
import os
from logo import add_logo
import openai
from dotenv import load_dotenv, find_dotenv

# Load .env file if exists
_ = load_dotenv(find_dotenv())

index_save_path = "faiss_index.bin"
index_metadata_path = "faiss_index.pkl"

# Function to create and save FAISS index
def create_and_save_faiss_index(documents, embeddings, index_save_path):
    vector_store = FAISS.from_documents(documents, embeddings)
    vector_store.save_local(index_save_path)
    print(f"FAISS index saved to {index_save_path}")
    return vector_store

# Function to load the FAISS index from disk
def load_faiss_index(index_save_path, embeddings):
    vector_store = FAISS.load_local(index_save_path, embeddings, allow_dangerous_deserialization=True)
    print(f"FAISS index loaded from {index_save_path}")
    return vector_store

st.markdown("<p style='font-size:32px; font-weight:bold;'>ISO Chatbot</p>", unsafe_allow_html=True)
st.write("<p style='font-size:32px; font-weight:bold;'>Document Intelligence</p>", unsafe_allow_html=True)

# API key input
api_key_input = st.text_input("Enter your OpenAI API key", type="password")
if api_key_input:
    openai.api_key = api_key_input

pdf_file = st.file_uploader("Upload PDF file", type="pdf")
add_logo()

if api_key_input and pdf_file:
    st.success(f"Your {pdf_file.name} is uploaded")
    if "file" not in st.session_state:
        st.session_state.file = pdf_file

    loader = PyMuPDFLoader(pdf_file.name)
    docs = loader.load()

    text_splitter = RecursiveCharacterTextSplitter()
    documents = text_splitter.split_documents(docs)

    embeddings = OpenAIEmbeddings(api_key=api_key_input)

    if not os.path.exists(index_save_path):
        vector_store = create_and_save_faiss_index(documents, embeddings, index_save_path)
    else:
        vector_store = load_faiss_index(index_save_path, embeddings)

    input = st.chat_input("Enter Your Queries...")

    if "messages" not in st.session_state:
        st.session_state.messages = [{"role": "ai", "content": "Hello. Ask me a question related to the PDF document"}]

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            if message["role"] == 'assistant':
                st.write(message["content"][0])
                st.write(f"<i>Source: {message['content'][1]}, Page No: {message['content'][2]}</i>", unsafe_allow_html=True)
            else:
                st.write(message["content"])

    if input:
        with st.chat_message("user"):
            st.write(input)
        st.session_state.messages.append({"role": "user", "content": input})

        llm = ChatOpenAI(model='gpt-4', temperature=0.2, api_key=api_key_input)
        prompt = ChatPromptTemplate.from_template("""Answer the following question based only on the provided context:

            <context>
            {context}
            </context>

            Question: {input}""")
        
        retriever = vector_store.as_retriever(search_kwargs={"k": 1})

        document_chain = create_stuff_documents_chain(llm, prompt)
        retrieval_chain = create_retrieval_chain(retriever, document_chain)

        response = retrieval_chain.invoke({"input": input})

        with st.chat_message("assistant"):
            st.write(response['answer'])
            st.write(f"<i>Source: {response['context'][0].metadata['source']}, Page No: {response['context'][0].metadata['page']}</i>", unsafe_allow_html=True)

        st.session_state.messages.append({"role": "assistant", "content": [response['answer'], response['context'][0].metadata['source'], response['context'][0].metadata['page']]})
else:
    st.warning("Please enter your OpenAI API key and upload a PDF document to proceed.")
