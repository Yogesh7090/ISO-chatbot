import streamlit as st
from logo import add_logo

add_logo()

st.markdown("<p style='font-size:32px; font-weight:bold;'>ISO Chatbot</p>", unsafe_allow_html=True)
st.markdown("""
<style>
    body {
        font-family: 'Arial', sans-serif;
        font-size: 16px;
    }
</style>
<body>        
<b>Overview</b>:<br>  
The ISO Chatbot is a web-based application designed to streamline communication and information retrieval from ISO-related documents.
Built using Generative AI, the chatbot enables users to interact with ISO standards and documents more efficiently. 
It allows for document uploads, parsing, and structured data extraction, even handling complex tasks like converting horizontal tables into vertical formats for better processing. 
<br>        
<br>       
<b>Core Features</b>:
<br>          
📥 Document Uploading<br>
Users can upload multiple ISO-related documents (primarily PDFs) through an intuitive interface.
<br><br>
📊 Table Selection<br>
Users can specify and focus on particular tables within the uploaded documents to narrow down the scope of their queries.
<br><br>         
💬 Conversational Chat Interface<br>
Engage in real-time conversations with the chatbot, asking questions related to the content of the uploaded ISO documents.
<br><br>          
🔍 Contextual Responses<br>
The chatbot provides responses based on the content of the entire document or specific tables as selected by the user.
<br><br>  
🔄 Persistent Storage<br>
Uploaded documents and their embeddings are stored persistently using FAISS, ensuring data is retained across sessions.
<br><br>
            
<b>Intuitive User Interface</b>:  
Professionally designed interface facilitating straightforward navigation and operation.
Streamlined User Interface: A single, professionally designed page facilitates both querying
and summarizing, optimizing user workflow which integrates all essential functionalities into a unified and intuitive interface.
</body>
""", unsafe_allow_html=True)
