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
 

_ = load_dotenv(find_dotenv())  # read local .env file
openai.api_key = os.environ['OPENAI_API_KEY']

st.markdown("<p style='font-size:32px; font-weight:bold;'>ISO QUEST</p>", unsafe_allow_html=True)
st.write("<p style='font-size:32px; font-weight:bold;'>Insights from standard tables in ISO 14224 PDF</p>", unsafe_allow_html=True)
# st.subheader("AI-Powered Document Query Assistant")
 
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
    
    # Define some basic responses for generic chat inputs
    generic_responses = {
        "hi": "Hello! How can I assist you today?",
        "hello": "Hi there! What can I help you with?",
        "thankyou": "You're very welcome! Let me know if you need anything else.",
        "thank you": "You're very welcome! Let me know if you need anything else.",
        "thanks": "You're very welcome! Let me know if you need anything else.",
        "bye": "Goodbye! Have a great day!"
    }
    
    # Check if input matches any generic response pattern
    input_lower = input.lower()
    for key, response in generic_responses.items():
        if key in input_lower:
            return response
    
    # If input is not a generic chat, proceed with the custom template formation
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
   
    | Failure Code | Description                    | Example                   |
    |--------------|--------------------------------| --------------------------|
    | FTS          | Failure to start on demand     | Doesn't start on demand   |
    | STP          | Failure to stop on demand      | Doesn't stop on demand    |
    | ...          | ...                            | ...                       |
   
    Ensure all output is consistent in this tabular format throughout the entire response.
 
    If no relevant data is found based on the query, respond with a table indicating "No data available".
   
    Example:
 
    | Failure Code | Description      | Example           |
    |--------------|------------------|-------------------|          
    | No data      | No data available| No data available |
    |
 
    Available Failure Codes:
    {', '.join([f'{code} : {desc}' for code, desc in failure_dict.items()])}
    """
   
    return _DEFAULT_TEMPLATE + PROMPT_SUFFIX
 
def maintenance_template(df, input):
    # Check if input matches any generic response pattern
    input_lower = input.lower()
    generic_responses = {
        "hi": "Hello! How can I assist you today?",
        "hello": "Hi there! What can I help you with?",
        "thankyou": "You're very welcome! Let me know if you need anything else.",
        "thank you": "You're very welcome! Let me know if you need anything else.",
        "thanks": "You're very welcome! Let me know if you need anything else.",
        "bye": "Goodbye! Have a great day!"
    }
    
    for key, response in generic_responses.items():
        if key in input_lower:
            return response
    
    # If input is not a generic chat, proceed with the custom template formation
    PROMPT_SUFFIX = f"""Use only the following dataframe to process the query:
    {df}
   
    The dataframe contains maintenance activity codes and their descriptions.
   
    Return the answer as a pandas dataframe with appropriate column names for easy readability.
     
    Question: {input}"""
 
    _DEFAULT_TEMPLATE = f"""Given an input question, analyze the dataframe and provide an answer based on the relevant information found in it.
   
    Return the response in a tabular format or as a pandas dataframe with clear column names.
    """
 
    return _DEFAULT_TEMPLATE + PROMPT_SUFFIX


def transform_value(x):
    if pd.isna(x):  # Check if value is NaN
        return 0
    elif x == 'X':  # Check if value is 'X'
        return 1
    else:
        return x  # Keep the original value for other cases
 
def response_generator(df, prompt, api_key):
    memory = ConversationBufferMemory()
    llm = ChatOpenAI(model='gpt-4', temperature=0.2, api_key=api_key)
    prompt_template = template_formation(df, prompt)
    agent = create_pandas_dataframe_agent(llm, df, prefix=prompt_template, allow_dangerous_code=True, verbose=True)
    response = agent.invoke({"input": prompt, "history": memory.buffer}, handle_parsing_errors=True)
 
    return response['output']
 
def main():
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
    "Table B.7": {
        "pages": [193, 194],
        "description": "Overview of system failure rates for B.7"
    },
    "Table B.8": {
        "pages": [195, 196],
        "description": "System configuration and performance for B.8"
    },
    "Table B.9": {
        "pages": [197, 198, 199],
        "description": "Analysis of component reliability for B.9"
    },
    "Table B.10": {
        "pages": [200, 201],
        "description": "System breakdown and diagnostics for B.10"
    },
    "Table B.11": {
        "pages": [202, 203],
        "description": "Detailed fault codes and errors for B.11"
    },
    "Table B.12": {
        "pages": [204, 205],
        "description": "System output and efficiency data for B.12"
    },
    "Table B.13": {
        "pages": [206],
        "description": "Failure prediction and maintenance for B.13"
    },
    "Table B.14": {
        "pages": [207],
        "description": "Maintenance records and schedules for B.14"
    },
    "Table B.15 Failure Mode_Codes": {
        "pages": [208, 209],
        "description": "Failure mode and error codes for Table B.15"
    }
        }

    st.write("<p style='font-size:28px;'><b>Tables available for user interaction</b></p>", unsafe_allow_html=True)

    df = sheet_names = pd.read_excel('Table_Description.xlsx')
    html = df.to_html(index=False)
    html = html.replace('<th>', '<th style="font-weight: bold; text-align:center">')

    st.markdown(html, unsafe_allow_html=True)
    # st.table(df)
    
    # if "file" in st.session_state.keys():
        # pdf_file = st.session_state.file
    sheet_names = pd.ExcelFile('Annex B Failure modes matrix ISO 14224.xlsx').sheet_names
    if sheet_names:
        st.markdown("<p style='font-size:28px'><b>Choose the table for insights</b></p>", unsafe_allow_html=True)
        selected_sheet = st.selectbox("", options=sheet_names, placeholder='choose table',index=None, label_visibility="hidden")
       
        if selected_sheet:
            # print('selected sheet',selected_sheet)
            dfs = pd.read_excel("Annex B Failure modes matrix ISO 14224.xlsx", sheet_name = selected_sheet)
            # print('df',dfs)
        
            # df = dfs[selected_sheet]

                # Apply a transformation function to every cell in the DataFrame
            df = dfs.applymap(transform_value)
        # Initialize state for table displays
        if "active_section" not in st.session_state:
            st.session_state.active_section = 'iso'  # None, 'iso', 'maintenance'
 
        if "iso_table_messages" not in st.session_state:
            st.session_state.iso_table_messages = [{"role": "assistant", "content": "Hello. Ask me a question related to ISO failure codes."}]
 
        # Add message before ISO Failure Codes button
        if selected_sheet:

        # Handle ISO Failure Codes Section
            if st.session_state.active_section == 'iso':
                st.dataframe(df)  # Display ISO table
                for table_name in tables:
                    if selected_sheet in table_name:
                        table_info = tables[table_name]  # This gives you the dictionary with 'pages' and 'description'
                        numbers = table_info['pages']
                        st.write(f"**Page No**: {', '.join(map(str, numbers))}")

                # Show ISO chat history
                for message in st.session_state.iso_table_messages:
                    with st.chat_message(message["role"]):
                        st.markdown(message["content"])
    
            # Single chat input for both sections
            if st.session_state.active_section:
                # Show the chat input box
                
                keywords = st.chat_input(f"**Enter query to get your answer for {'ISO Failure Codes' if st.session_state.active_section == 'iso' else 'Maintenance Activity Codes'}.**")
    
                if keywords:
                    # Display user query and store it
                    with st.chat_message("user"):
                        st.markdown(keywords)
    
                    # Append user query to the respective section's messages
                    if st.session_state.active_section == 'iso':
                        st.session_state.iso_table_messages.append({"role": "user", "content": keywords})
    
                        # Generate and display response from ISO Failure Codes
                        response = response_generator(df, keywords, api_key)
                        print(f'ISO response {response=}')  # Debug ISO response
    
                        with st.chat_message("assistant"):
                            st.markdown(response)
                        st.session_state.iso_table_messages.append({"role": "assistant", "content": response})
    
    # else:
    #     st.warning("Please upload a PDF document in Document Intelligence page", icon="⚠️")
 
if __name__ == "__main__":
    main()


# Q: Give me examples of VIB and PDE failure modes
# A: Abnormal vibration, monitored parameter exceeding limits, e.g. high/
# low alarm
# Q: which equipment types that can be expected to have ELP Failure mode?
# A: Compressors, Gas Turbines, Pumps, Steam Turbines, Turbo-expanders
# Q: if an equipment had a failure to connect as failure mode, what will the Failure code be? and what type of 
# equipment it can be?
# A: FCO, Turrets, Swivels
# Q: What are the Failure modes that are not related to Heat exchangers
# A: BRD, FCO, FLP ,FRO ,FTD ,FTI ,FTS ,IHT ,LBP ,LOA ,LOB ,LOO ,MOF ,NOI ,OHE ,PTF, SBU ,SLP ,SPO ,STP ,VIB
# Q: What is the least expected occurring Failure mode to happen in rotation equipment class?
# A: ELF
# Q: What is the Failure mode that happens to all rotating Equipment Classes?
# A: AIR
# Q: What is the rotating equipment class that can the most failure modes to occur?
# A: Combustion Engines, Compressor, steam Turbines
