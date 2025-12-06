# rag_engine.py

import os
import warnings
from typing import List
from dotenv import load_dotenv

# Suppress warnings
warnings.filterwarnings('ignore')

# Set environment variables before imports
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
os.environ["USER_AGENT"] = "PythonicAI/1.0 (+adinafraz01@gmail.com)"
os.environ["TOKENIZERS_PARALLELISM"] = "false"

# Load env variables
# Load .env for local development
load_dotenv()

import streamlit as st

# 1️⃣ Check Streamlit Cloud Secrets
openai_key = st.secrets.get("OPENAI_API_KEY")

# 2️⃣ Fallback to .env for local development
if not openai_key:
    openai_key = os.getenv("OPENAI_API_KEY")

# 3️⃣ If still missing, show error (but don't crash the app)
if not openai_key:
    st.error("OPENAI_API_KEY is missing. Add it in Streamlit Secrets or your .env file.")
else:
    os.environ["OPENAI_API_KEY"] = openai_key


from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.vectorstores import FAISS
from langchain_community.document_loaders import WebBaseLoader
from langchain_core.prompts import PromptTemplate
from langchain.schema import Document

# ------------------------------------------
# DOCUMENT LOADING (URL ONLY)
# ------------------------------------------

def load_user_document(url: str) -> List[Document]:
    """Load URL into LangChain documents."""
    try:
        if not url:
            raise ValueError("No URL provided")
        
        # Clean URL
        if not url.startswith(('http://', 'https://')):
            url = f'https://{url}'
            
        # Use WebBaseLoader with custom headers
        headers = {
            'User-Agent': os.environ.get("USER_AGENT", "PythonicAI/1.0")
        }
        
        loader = WebBaseLoader(
            web_paths=[url],
            requests_per_second=1,
            requests_kwargs={'headers': headers}
        )
        docs = loader.load()
        
        if not docs:
            raise ValueError("No content found in the URL")
            
        return docs
        
    except Exception as e:
        raise Exception(f"Error loading URL: {str(e)}")

# ------------------------------------------
# BUILD RETRIEVER FROM DOCUMENTS
# ------------------------------------------

def build_retriever_from_docs(docs: List[Document]):
    """Build FAISS vector store from documents."""
    if not docs:
        raise ValueError("No documents provided")
    
    # Use the same splitter settings as your example
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200
    )
    
    chunks = splitter.split_documents(docs)
    
    # Use the same embedding model as your example
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
    
    # Build vector store
    vector_store = FAISS.from_documents(chunks, embeddings)
    
    return vector_store.as_retriever(
        search_type="similarity",
        search_kwargs={"k": 6}
    )

# ------------------------------------------
# PYTHON DOMAIN CHECK
# ------------------------------------------

_llm = None

def get_llm():
    """Singleton pattern for LLM to avoid re-initialization."""
    global _llm
    if _llm is None:
        _llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.2,
            max_tokens=1000,
            request_timeout=60
        )
    return _llm

def is_python_related(question: str) -> bool:
    """Check if question is Python-related."""
    python_keywords = [
        'python', 'numpy', 'pandas', 'matplotlib', 'seaborn',
        'machine learning', 'deep learning', 'tensorflow', 'pytorch',
        'scikit-learn', 'sklearn', 'dataframe', 'array', 'plot',
        'import', 'def ', 'class ', 'function', 'method', 'library',
        'package', 'module', 'pip install', 'conda install', 'jupyter',
        'data', 'science', 'analysis', 'visualization', 'programming',
        'code', 'script', 'algorithm', 'model', 'training', 'prediction'
    ]
    
    # Quick keyword check first
    question_lower = question.lower()
    for keyword in python_keywords:
        if keyword in question_lower:
            return True
    
    return False

# ------------------------------------------
# ANSWER QUESTION
# ------------------------------------------

# Define the prompt template (same as your example)
prompt = PromptTemplate(
    template="""
    You are a helpful python assistant. 
    Answer ONLY from the provided text context.
    Display answer in a beautiful and user understandable format with proper formatting.
    Use bullet points, numbered lists, or code blocks when appropriate.
    If the context is insufficient, just say you don't know.

    Context: {context}
    Question: {question}
    """,
    input_variables=['context', 'question']
)

def answer_question(question: str, retriever):
    """Answer question using RAG pipeline."""
    # Validate topic
    if not is_python_related(question):
        return "I can only answer Python and data science related questions based on the provided documentation."
    
    try:
        # Retrieve relevant documents
        docs = retriever.invoke(question)
        
        if not docs:
            return "I couldn't find relevant information in the documentation to answer this question."
        
        # Combine context from retrieved documents
        context = "\n\n".join(doc.page_content for doc in docs)
        
        # Create final prompt
        final_prompt = prompt.invoke({
            "context": context,
            "question": question
        })
        
        # Get answer from LLM
        llm = get_llm()
        answer = llm.invoke(final_prompt)
        
        return answer.content
        
    except Exception as e:

        return f"Error generating answer: {str(e)}"
