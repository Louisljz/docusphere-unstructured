import sys
import time
import tempfile
import streamlit as st

import langchain
from langchain_core.messages import AIMessage, HumanMessage
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import UnstructuredFileLoader
from unstructured.cleaners.core import clean_extra_whitespace

sys.path.append('..')
from langchain_qna import QNAAgent
from langchain_pinecone import PineconeVectorStore
from langchain_openai import OpenAIEmbeddings


langchain.debug = True

@st.cache_resource
def init_connection():
    embeddings = OpenAIEmbeddings(model='text-embedding-3-small')
    vector_store = PineconeVectorStore(index_name="docusphere", embedding=embeddings)
    retriever = vector_store.as_retriever(search_kwargs={"namespace": st.session_state.user['id']})
    qna_agent = QNAAgent(retriever)

    return vector_store, qna_agent


vector_store, qna_agent = init_connection()

st.title('Docusphere 📃🌐')
st.subheader(f'Hello {st.session_state["user"]["name"]}, welcome back!')
st.write('Our web app allows you to upload your personal documents, stored in our secure database, and you may ask your inquiries about them.')

tabs = st.tabs(['Ingest', 'Ask'])
with tabs[0]:
    with st.form(key='upload_form', clear_on_submit=True):
        temp_paths = []
        files = st.file_uploader('Upload your documents', accept_multiple_files=True)
        if st.form_submit_button('Confirm'):
            if files:
                for f in files:
                    temp_file = tempfile.NamedTemporaryFile(delete=False)
                    temp_file.write(f.read())
                    temp_file.close()
                    temp_paths.append(temp_file.name)

                loader = UnstructuredFileLoader(
                    temp_paths,
                    post_processors=[clean_extra_whitespace],
                )
                docs = loader.load()
                
                text_splitter = RecursiveCharacterTextSplitter(chunk_size=500)
                texts = text_splitter.split_text(docs[0].page_content)

                vector_store.add_texts(texts, namespace=st.session_state.user["id"])
                info = st.info('Documents uploaded successfully!')
                time.sleep(3)
                info.empty()


with tabs[1]:
    if "messages" not in st.session_state:
        st.session_state.messages = []

    for message in st.session_state.messages:
        if type(message) is AIMessage:
            role = 'ai'
        else:
            role = 'human'
        
        with st.chat_message(role):
            st.write(message.content)

    query_holder = st.empty()
    response_holder = st.empty()

    if query := st.chat_input("Ask me anything! 🤔"):
        st.session_state.messages.append(HumanMessage(content=query))
        with query_holder.chat_message("user"):
            st.write(query)
        
        with response_holder.chat_message("assistant"):
            stream = qna_agent.execute_rag_chain({"question": query, 
                                                        "chat_history": st.session_state.messages})
            response = st.write_stream(stream)
            st.session_state.messages.append(AIMessage(content=response))
