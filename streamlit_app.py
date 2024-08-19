import streamlit as st
import requests
import pandas as pd
import pymysql
import time
import plotly.express as px

# Database Configuration
DB_HOST = "tellmoredb.cd24ogmcy170.us-east-1.rds.amazonaws.com"
DB_USER = "admin"
DB_PASS = "2yYKKH8lUzaBvc92JUxW"
DB_PORT = "3306"
DB_NAME = "claires_data"
CONVO_DB_NAME = "store_questions"

# Declaring Colors
CLAIRE_DEEP_PURPLE = '#553D94'
CLAIRE_MAUVE = '#D2BBFF'

# Initialize session state variables
if 'history' not in st.session_state:
    st.session_state['history'] = []

if 'display_df_and_nlr' not in st.session_state:
    st.session_state['display_df_and_nlr'] = False

if 'user_input' not in st.session_state:
    st.session_state['user_input'] = ""

st.set_page_config(layout='wide', initial_sidebar_state='collapsed')

def connect_to_db(db_name):
    return pymysql.connect(
        host=DB_HOST,
        port=int(DB_PORT),
        user=DB_USER,
        password=DB_PASS,
        db=db_name
    )

def send_message_to_api(message):
    api_url = "http://127.0.0.1:5000/response"
    payload = {"database": DB_NAME, "query": message}
    response = requests.post(api_url, json=payload)
    if response.status_code == 200:
        try:
            return response.json()
        except ValueError:
            st.error("Error decoding JSON")
            return None
    else:
        st.error(f"Error: HTTP {response.status_code} - {response.text}")
        return None

def execute_query(query, connection):
    try:
        with connection.cursor() as cursor:
            cursor.execute(query)
            getResult = cursor.fetchall()
            columns = [column[0] for column in cursor.description]
        return pd.DataFrame(getResult, columns=columns)
    finally:
        connection.close()

def store_question_in_db(question, sql_query):
    connection = connect_to_db(CONVO_DB_NAME)
    query = "INSERT INTO pinned_questions (question, sql_query) VALUES (%s, %s)"
    try:
        with connection.cursor() as cursor:
            cursor.execute(query, (question, sql_query))
        connection.commit()
    finally:
        connection.close()

def get_queries_from_db():
    connection = connect_to_db(CONVO_DB_NAME)
    query = "SELECT question, sql_query FROM pinned_questions;"
    df = execute_query(query, connection)
    questions = {"Select a query": None}
    questions.update(dict(zip(df['question'], df['sql_query'])))
    return questions

# Set custom CSS for the application
def set_custom_css():
    custom_css = """
    <style>
        .st-emotion-cache-9aoz2h.e1vs0wn30 {
            display: flex;
            justify-content: center;
        }
        .st-emotion-cache-9aoz2h.e1vs0wn30 table {
            margin: 0 auto;
        }
    </style>
    """
    st.markdown(custom_css, unsafe_allow_html=True)

# Merge App Functionality
def store_ops_app():
    #Load the logo 
    with open(r'Claires_logo.svg', 'r') as image:
        image_data = image.read()
    st.logo(image=image_data)

    # Claire Purple top bar on Top.
    # st.markdown(f"""
    # <div style="position: fixed; top: 0; left: 0; width: 100%; height: 100px; background-color: {CLAIRE_DEEP_PURPLE}; z-index: 1000;">
    # </div>
    # """, unsafe_allow_html=True)

    # st.markdown(f"""
    # <h4 style="background-color: {CLAIRE_DEEP_PURPLE}; color: white; padding: 10px;">
    #     Store Ops App
    # </h4>
    # """, unsafe_allow_html=True)

    st.markdown(f"""
    <div style="position: fixed; top: 0; left: 0; width: 100%; height: 100px; background-color: {CLAIRE_DEEP_PURPLE}; z-index: 1000; display: flex; align-items: center; justify-content: center;">
    <h4 style="color: white; margin: 0;">
        STORE OPS APP
    </h4>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)

    for chat in st.session_state.history:
        st.write(f"**User:** {chat['question']}")
        st.write(f"**Natural Language Response:** {chat['nlr']}")

    st.session_state['user_input'] = st.text_input("You: ", st.session_state['user_input'])

    if st.button("SAVE"):
        if st.session_state.history:
            last_chat = st.session_state.history[-1]
            store_question_in_db(last_chat['question'], last_chat['sql'])
            st.success("Last conversation stored.")
            st.session_state['user_input'] = ""
            st.session_state['display_df_and_nlr'] = False
            st.session_state['last_result'] = None
            st.session_state['last_nlr'] = None
        else:
            st.warning("No conversation to store.")

    if st.session_state['user_input']:
        st.session_state.history.append({
            "question": st.session_state['user_input'],
            "nlr": """
The data table returned provides information on the sales performance of different stores for this year and the previous year. The table includes columns such as STORE_ID, STORE_NAME, SALES_TY (sales for this year), and SALES_LY (sales for the previous year).\n\n
Looking at the data, we can observe that the sales for most stores vary between this year and the previous year. Some stores have seen an increase in sales, while others have experienced a decrease.\n\n
For example, stores like BRISTOL SUPERSTORE, CWMBRAN, and CARDIFF have seen an increase in sales this year compared to the previous year. On the other hand, stores like NEWPORT, CRIBBS CAUSEWAY, and SWANSEA have shown a decrease in sales.\n\n
It is also interesting to note that some stores have had significant changes in sales performance. For instance, stores like West End New, Budapest Arena Plaza, and Arkad Budapest have experienced a significant increase in sales this year compared to the previous year. Conversely, stores like Budapest Vaci Utca and Gyor Arkad have seen a significant decrease in sales.\n\n
Overall, the data table provides a comparison of sales performance across all stores for this year against the previous year, highlighting the varying trends in sales for different stores.
""",
            "sql": "SELECT DISTINCT STORE_ID, STORE_NAME, SALES_TY, SALES_LY FROM claires_data.store_total;"
        })
        conn = connect_to_db(DB_NAME)
        result = execute_query("SELECT DISTINCT STORE_ID, STORE_NAME, SALES_TY, SALES_LY FROM claires_data.store_total;", conn)
        st.session_state['display_df_and_nlr'] = True
        st.session_state['last_result'] = result
        st.session_state['last_nlr'] = st.session_state.history[-1]["nlr"]

    if st.session_state['display_df_and_nlr']:
        st.dataframe(st.session_state['last_result'], height=200)
        time.sleep(1)
        st.write(st.session_state['last_nlr'])

def store_manager_app():
    #Load the logo 
    with open(r'Claires_logo.svg', 'r') as image:
        image_data = image.read()
    st.logo(image=image_data)

    st.markdown(f"""
    <div style="position: fixed; top: 0; left: 0; width: 100%; height: 100px; background-color: {CLAIRE_DEEP_PURPLE}; z-index: 1000;">
    </div>
    """, unsafe_allow_html=True)

    queries = get_queries_from_db()
    result = None

    st.markdown(f"""
    <h4 style="background-color: {CLAIRE_DEEP_PURPLE}; color: white; padding: 10px;">
        North Riverside Park Mall, Store001
    </h4>
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <h4 style="background-color: {CLAIRE_MAUVE}; color: black; padding: 10px;">
        Store Management App
    </h4>
    """, unsafe_allow_html=True)

    selected_query = st.selectbox("Select a query", list(queries.keys()))
    if selected_query and selected_query != "Select a query":
        query_sql = queries[selected_query]
        conn = connect_to_db(DB_NAME)
        result = execute_query(query_sql, conn)
        st.markdown("""
The data table returned provides information on the sales performance of different stores for this year and the previous year. The table includes columns such as STORE_ID, STORE_NAME, SALES_TY (sales for this year), and SALES_LY (sales for the previous year).\n\n
Looking at the data, we can observe that the sales for most stores vary between this year and the previous year. Some stores have seen an increase in sales, while others have experienced a decrease.\n\n
For example, stores like BRISTOL SUPERSTORE, CWMBRAN, and CARDIFF have seen an increase in sales this year compared to the previous year. On the other hand, stores like NEWPORT, CRIBBS CAUSEWAY, and SWANSEA have shown a decrease in sales.\n\n
It is also interesting to note that some stores have had significant changes in sales performance. For instance, stores like West End New, Budapest Arena Plaza, and Arkad Budapest have experienced a significant increase in sales this year compared to the previous year. Conversely, stores like Budapest Vaci Utca and Gyor Arkad have seen a significant decrease in sales.\n\n
Overall, the data table provides a comparison of sales performance across all stores for this year against the previous year, highlighting the varying trends in sales for different stores.        
""")
        st.dataframe(result, height=300)

# Main Application
set_custom_css()

# Sidebar for toggling between personas
persona = st.sidebar.radio("Choose Persona:", ("Store Ops", "Store Manager"))

# Load the corresponding persona app
if persona == "Store Ops":
    store_ops_app()
else:
    store_manager_app()
