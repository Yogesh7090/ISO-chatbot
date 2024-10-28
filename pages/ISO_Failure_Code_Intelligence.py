import streamlit as st
import pandas as pd
import fitz
from langchain_experimental.agents import create_pandas_dataframe_agent
from langchain_openai import ChatOpenAI
from langchain.memory import ConversationBufferMemory
from logo import add_logo
import openai
import os
from dotenv import load_dotenv, find_dotenv

add_logo()

st.markdown("<p style='font-size:32px; font-weight:bold;'>ISO Chatbot</p>", unsafe_allow_html=True)
st.write("<p style='font-size:32px; font-weight:bold;'>Insights from standard tables in ISO 14224 PDF</p>", unsafe_allow_html=True)

def transform_value(x):
    if pd.isna(x):
        return 0
    elif x == 'X':
        return 1
    else:
        return x

def clean_df(df):
    df1 = df.drop(columns=['Examples','Type c'])
    df1.replace('', None, inplace=True)
    df_final = df1.T
    df_final.columns = df_final.iloc[-1]
    df_final = df_final.iloc[:-1]
    df_sorted = df_final[sorted(df_final.columns)]
    df_sorted.columns.name = None
    df_transformed = df_sorted.applymap(transform_value)
    return df_transformed

def pdf_to_df(file, page_nums):
    doc = fitz.open(file)
    df_list = []
    for i, page_num in enumerate(page_nums):
        page = doc[page_num]
        page.set_rotation(90)
        tabs = page.find_tables()
        tab = tabs[0]
        empty_header = [True for element in tab.header.names if not element]
        empty_first_cell = [True for element in tab.rows[0].cells if not element]
        empty_last_cell = [True for element in tab.rows[-1].cells if not element]
        df_name = tab.to_pandas()
        if True in empty_header and True in empty_first_cell and True in empty_last_cell:
            df_name.columns = df_name.iloc[1]
            df_name = df_name.iloc[2:-1].reset_index(drop=True)
        elif True in empty_header and True in empty_first_cell:
            df_name.columns = df_name.iloc[1]
            df_name = df_name.iloc[2:].reset_index(drop=True)
        df_list.append(df_name)
    df = pd.concat(df_list, ignore_index=True)
    formatted_df = clean_df(df)
    return formatted_df

def template_formation(df, input):
    failure_dict = {
        'FTS': 'Failure to start on demand',
        'STP': 'Failure to stop on demand',
        'UST': 'Spurious stop',
        'BRD': 'Breakdown',
        'HIO': 'High output',
        'LOO': 'Low output',
        'ERO': 'Erratic output',
        'ELF': 'External leakage fuel',
        'ELP': 'External leakage process medium',
        'ELU': 'External leakage utility medium',
        'INL': 'Internal leakage',
        'VIB': 'Vibration',
        'NOI': 'Noise',
        'OHE': 'Overheating',
        'PLU': 'Plugged/choked',
        'PDE': 'Parameter deviation',
        'AIR': 'Abnormal instrument reading',
        'STD': 'Structural deficiency',
        'SER': 'Minor in-service problems',
        'OTH': 'Other',
        'UNK': 'Unknown'
    }

    PROMPT_SUFFIX = f"""Use only the following dataframe to process the query:
    {df}

    The dataframe contains the failure codes and their descriptions.
    In the dataframe, 1 represents a failure for a specific code, and 0 represents a non-failure code.
    
    Question: {input}"""

    _DEFAULT_TEMPLATE = f"""Given an input question, first create a syntactically correct query to run on the dataframe, then
    analyze the results of the query, and return the answer in a summarized tabular format.
   
    Make sure the query is compatible with the dataframe and returns relevant columns for the given question.
    The response should consistently be displayed as a well-formatted table, using both the failure code abbreviation and full description.
   
    **Response Format:**
   
    | Failure Code | Description                    |
    |--------------|--------------------------------|
    | FTS          | Failure to start on demand     |
    | STP          | Failure to stop on demand      |
    | ...          | ...                            |
   
    Ensure all output is consistent in this tabular format throughout the entire response.

    If no relevant data is found based on the query, respond with a table indicating "No data available".
   
    Example:

    | Failure Code | Description      |
    |--------------|------------------|
    | No data      | No data available|

    Available Failure Codes:
    {', '.join([f'{code} : {desc}' for code, desc in failure_dict.items()])}
    """
   
    return _DEFAULT_TEMPLATE + PROMPT_SUFFIX

def response_generator(df, prompt, api_key):
    memory = ConversationBufferMemory()
    llm = ChatOpenAI(model='gpt-4', temperature=0.2, api_key=api_key)
    prompt_template = template_formation(df, prompt)
    agent = create_pandas_dataframe_agent(llm, df, prefix=prompt_template, allow_dangerous_code=True, verbose=True)
    response = agent.invoke({"input": prompt, "history": memory.buffer}, handle_parsing_errors=True)
 
    return response['output']

def main():
    # Input field for API key
    api_key = st.text_input("Enter your OpenAI API key", type="password")
    
    if not api_key:
        st.warning("Please enter your OpenAI API key to proceed.")
        return

    tables = {
        "Table A.4 and EquipSubD": {
            "pages": [57, 58, 59, 60, 61, 62, 63, 64, 65],
            "description": "Equipment Subdivision and related data"
        },
        "Table B.6": {
            "pages": [192],
            "description": "Performance metrics for system B.6"
        },
        # Other tables as defined previously
    }

    st.write("<p style='font-size:28px;'><b>Tables available for user interaction</b></p>", unsafe_allow_html=True)

    df = pd.read_excel('Table_Description.xlsx')
    st.table(df)
    
    sheet_names = pd.ExcelFile('Annex B Failure modes matrix ISO 14224.xlsx').sheet_names
    if sheet_names:
        st.markdown("<p style='font-size:28px'><b>Choose the table for insights</b></p>", unsafe_allow_html=True)
        selected_sheet = st.selectbox("", options=sheet_names, placeholder='choose table',index=None, label_visibility="hidden")
        
        if selected_sheet:
            dfs = pd.read_excel("Annex B Failure modes matrix ISO 14224.xlsx", sheet_name=selected_sheet)
            df = dfs.applymap(transform_value)
        
        if "active_section" not in st.session_state:
            st.session_state.active_section = 'iso'

        if "iso_table_messages" not in st.session_state:
            st.session_state.iso_table_messages = [{"role": "assistant", "content": "Hello. Ask me a question related to ISO failure codes."}]
        
        if selected_sheet:
            if st.session_state.active_section == 'iso':
                st.dataframe(df)
                for table_name in tables:
                    if selected_sheet in table_name:
                        table_info = tables[table_name]
                        numbers = table_info['pages']
                        st.write(f"**Page No**: {', '.join(map(str, numbers))}")

                for message in st.session_state.iso_table_messages:
                    with st.chat_message(message["role"]):
                        st.markdown(message["content"])

                keywords = st.chat_input(f"**Enter query to get your answer for {'ISO Failure Codes' if st.session_state.active_section == 'iso' else 'Maintenance Activity Codes'}.**")

                if keywords:
                    with st.chat_message("user"):
                        st.markdown(keywords)
                    
                    if st.session_state.active_section == 'iso':
                        st.session_state.iso_table_messages.append({"role": "user", "content": keywords})
                        response = response_generator(df, keywords, api_key)
                        with st.chat_message("assistant"):
                            st.markdown(response)
                        st.session_state.iso_table_messages.append({"role": "assistant", "content": response})

if __name__ == "__main__":
    main()
