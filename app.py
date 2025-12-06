# app.py
# force redeploy

import streamlit as st
from rag_engine import (
    load_user_document,
    build_retriever_from_docs,
    answer_question
)
import os

# Set environment variables
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
os.environ["USER_AGENT"] = "PythonicAI/1.0 (+adinafraz01@gmail.com)"

st.set_page_config(
    page_title="AI Documentation Assistant",
    layout="wide",
    initial_sidebar_state="expanded"
)

# -------------------- SESSION STATE --------------------
if "retriever" not in st.session_state:
    st.session_state.retriever = None

if "docs_loaded" not in st.session_state:
    st.session_state.docs_loaded = False

if "current_url" not in st.session_state:
    st.session_state.current_url = None

if "processing" not in st.session_state:
    st.session_state.processing = False

# -------------------- CUSTOM CSS --------------------
st.markdown("""
<style>
body {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    min-height: 100vh;
}

.main-container {
    max-width: 1000px;
    margin: 0 auto;
}

.header-card {
    background: rgba(255,255,255,0.95);
    border-radius: 20px;
    padding: 30px;
    margin-bottom: 30px;
    box-shadow: 0 10px 40px rgba(0,0,0,0.1);
    backdrop-filter: blur(10px);
    border: 1px solid rgba(255,255,255,0.2);
}

.input-card {
    background: rgba(255,255,255,0.95);
    border-radius: 15px;
    padding: 25px;
    margin-bottom: 25px;
    box-shadow: 0 8px 32px rgba(0,0,0,0.1);
    border: 1px solid rgba(255,255,255,0.2);
}

.answer-card {
    background: white;
    border-radius: 15px;
    padding: 30px;
    margin-top: 25px;
    box-shadow: 0 10px 40px rgba(0,0,0,0.08);
    animation: fadeIn 0.5s ease;
    border-left: 5px solid #667eea;
}

.url-display {
    background: #f0f4ff;
    border-radius: 10px;
    padding: 15px;
    margin: 15px 0;
    border-left: 4px solid #4f46e5;
    word-break: break-all;
}

.stButton button {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    font-weight: 600;
    border: none;
    border-radius: 12px;
    padding: 14px 28px;
    width: 100%;
    transition: all 0.3s;
    font-size: 16px;
}

.stButton button:hover {
    transform: translateY(-3px);
    box-shadow: 0 7px 20px rgba(0,0,0,0.2);
}

.primary-btn {
    background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%) !important;
}

.secondary-btn {
    background: linear-gradient(135deg, #10b981 0%, #059669 100%) !important;
}

.question-box {
    background: #f8fafc;
    border-radius: 12px;
    padding: 20px;
    border: 2px solid #e2e8f0;
    font-size: 16px;
    min-height: 120px;
}

.info-box {
    background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
    color: white;
    padding: 20px;
    border-radius: 15px;
    margin: 15px 0;
}

.example-chip {
    display: inline-block;
    background: #e0e7ff;
    color: #4f46e5;
    padding: 8px 16px;
    margin: 5px;
    border-radius: 20px;
    cursor: pointer;
    font-size: 14px;
    transition: all 0.2s;
    border: 1px solid #c7d2fe;
}

.example-chip:hover {
    background: #c7d2fe;
    transform: translateY(-2px);
}

@keyframes fadeIn {
    from { opacity:0; transform:translateY(10px); }
    to { opacity:1; transform:translateY(0); }
}

/* Scrollbar styling */
::-webkit-scrollbar {
    width: 8px;
}

::-webkit-scrollbar-track {
    background: #f1f1f1;
    border-radius: 10px;
}

::-webkit-scrollbar-thumb {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    border-radius: 10px;
}

::-webkit-scrollbar-thumb:hover {
    background: linear-gradient(135deg, #5a67d8 0%, #6d28d9 100%);
}
</style>
""", unsafe_allow_html=True)

# -------------------- SIDEBAR --------------------
with st.sidebar:
    st.markdown("""
    <div style="text-align:center; padding:18px 0;">
        <h2 style="color:black; margin-bottom:2px; font-size:20px;">📚 AI Doc Assistant</h2>
        <p style="color:black; font-size:20px;">Python Documentation Q&A</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    if st.session_state.docs_loaded:
        st.markdown("### ✅ Document Status")
        st.success("Document Loaded Successfully")
        
        if st.session_state.current_url:
            st.markdown("**Current URL:**")
            st.code(st.session_state.current_url[:80] + "..." if len(st.session_state.current_url) > 80 else st.session_state.current_url, language="text")
        
        if st.button("🗑️ Clear Document", use_container_width=True):
            st.session_state.docs_loaded = False
            st.session_state.retriever = None
            st.session_state.current_url = None
            st.rerun()
    else:
        st.markdown("### ⚠️ Status")
        st.info("No document loaded")
    
    st.markdown("---")
    st.markdown("### 📖 How to Use")
    st.markdown("""
    1. **Enter a URL** pointing to Python documentation
    2. Click **Load Document** to process
    3. Ask **Python-related questions** about the content
    4. Get instant, context-aware answers
    """)
    
    st.markdown("---")
    st.markdown("### 💡 Example URLs")
    urls = [
        "https://numpy.org/doc/2.3/user/absolute_beginners.html",
        "https://pandas.pydata.org/docs/",
        "https://matplotlib.org/stable/users/index.html",
        "https://scikit-learn.org/stable/user_guide.html"
    ]
    
    for url in urls:
        if st.button(f"📄 {url.split('/')[2]}", key=f"url_{url}"):
            st.session_state.url_input = url
            st.rerun()
    
    st.markdown("---")
    st.markdown("""
    <div style="text-align:center; color:black; font-size:12px; padding:10px;">
        Powered by OpenAI • LangChain • FAISS
    </div>
    """, unsafe_allow_html=True)

# -------------------- MAIN CONTENT --------------------
st.markdown('<div class="main-container">', unsafe_allow_html=True)

# Header
st.markdown("""
<div class="header-card">
    <h1 style="text-align:center; font-size:42px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin-bottom:10px;">
        🤖 AI Documentation Assistant
    </h1>
    <p style="text-align:center; font-size:18px; color:#4b5563; margin-bottom:20px;">
        Ask questions about any Python documentation from a URL
    </p>
</div>
""", unsafe_allow_html=True)

# URL Input Section
st.markdown('<div class="input-card">', unsafe_allow_html=True)
st.markdown("### 🌐 Enter Documentation URL")

# Initialize session state for URL if not exists
if "url_input" not in st.session_state:
    st.session_state.url_input = "https://numpy.org/doc/2.3/user/absolute_beginners.html"

url = st.text_input(
    "Enter the URL of Python documentation:",
    value=st.session_state.url_input,
    placeholder="https://example.com/python-docs",
    label_visibility="collapsed",
    key="url_input_field"
)

col1, col2 = st.columns([1, 1])

with col1:
    load_clicked = st.button(
        "📥 Load Document",
        use_container_width=True,
        type="primary",
        disabled=not url.strip()
    )

with col2:
    if st.session_state.docs_loaded:
        if st.button("🔄 Reload", use_container_width=True):
            load_clicked = True

st.markdown('</div>', unsafe_allow_html=True)

# Handle document loading
if load_clicked:
    if not url.strip():
        st.error("❌ Please enter a valid URL")
    else:
        try:
            with st.spinner("🔍 Loading and processing documentation..."):
                # Store current URL
                st.session_state.current_url = url
                
                # Show progress
                progress_text = st.empty()
                progress_bar = st.progress(0)
                
                progress_text.text("Downloading document...")
                docs = load_user_document(url)
                progress_bar.progress(30)
                
                progress_text.text("Processing content...")
                st.session_state.retriever = build_retriever_from_docs(docs)
                progress_bar.progress(70)
                
                progress_text.text("Finalizing...")
                st.session_state.docs_loaded = True
                progress_bar.progress(100)
                
                progress_text.text("✅ Ready!")
            
            st.success(f"✅ Successfully loaded documentation from: {url}")
           
            
            # Show document info
            st.markdown(f"""
            <div class="url-display">
                <strong>📄 Loaded Document:</strong> {url}<br>
                <strong>📊 Pages Processed:</strong> {len(docs)}<br>
                <strong>✅ Status:</strong> Ready for questions
            </div>
            """, unsafe_allow_html=True)
            
        except Exception as e:
            st.error(f"❌ Error loading document: {str(e)}")

# Question Input Section (only show if document is loaded)
if st.session_state.docs_loaded:
    st.markdown('<div class="input-card">', unsafe_allow_html=True)
    
    st.markdown("### 💭 Ask a Question")
    
    # Example questions
    st.markdown("**💡 Try asking:**")
    col1, col2, col3, col4 = st.columns(4)
    
    example_questions = [
        "What is this library about?",
        "How to get started?",
        "What are the main functions?",
        "Give me a code example"
    ]
    
    for i, question in enumerate(example_questions):
        col = [col1, col2, col3, col4][i]
        with col:
            if st.button(question, use_container_width=True):
                st.session_state.question_input = question
                st.rerun()
    
    # Question input
    question = st.text_area(
        "Enter your Python-related question:",
        value=st.session_state.get("question_input", ""),
        placeholder="Example: What is NumPy? How to create arrays? What are the main functions?",
        height=120,
        key="question_input_area"
    )
    
    # Answer button
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col2:
        if st.button("🚀 Get Answer", type="primary", use_container_width=True):
            if not question.strip():
                st.warning("Please enter a question")
            else:
                st.session_state.processing = True
                st.session_state.current_question = question
    
    with col3:
        if st.button("🗑️ Clear", use_container_width=True):
            st.session_state.question_input = ""
            st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Process and display answer
    if st.session_state.get("processing") and st.session_state.get("current_question"):
        with st.spinner("🤔 Analyzing document and generating answer..."):
            try:
                answer = answer_question(
                    st.session_state.current_question, 
                    st.session_state.retriever
                )
                
                st.markdown("### 📝 Answer")
                st.markdown(f'<div class="answer-card">{answer}</div>', unsafe_allow_html=True)
                
                # Reset processing state
                st.session_state.processing = False
                
            except Exception as e:
                st.error(f"❌ Error generating answer: {str(e)}")
                st.session_state.processing = False
    
    # Quick actions
    st.markdown("""
    <div style="text-align:center; margin-top:30px;">
        <hr style="border:none; height:1px; background:linear-gradient(90deg, transparent, #667eea, transparent); margin:20px 0;">
        <p style="color:#6b7280; font-size:14px;">
            💡 Tip: Ask specific questions for better answers. Try asking about functions, usage examples, or concepts.
        </p>
    </div>
    """, unsafe_allow_html=True)

else:
    # Welcome message when no document is loaded
    st.markdown("""
    <div class="info-box">
        <h3>👋 Welcome to AI Documentation Assistant!</h3>
        <p>Get started by entering a URL to Python documentation above.</p>
        <p><strong>Try the default URL</strong> or enter your own documentation link.</p>
    </div>
    
    <div style="background:white; border-radius:15px; padding:30px; margin-top:20px;">
        <h3 style="color:#4f46e5;">✨ Features:</h3>
        <ul style="font-size:16px; line-height:1.8;">
            <li><strong>📚 URL-based</strong> - Just paste a documentation URL</li>
            <li><strong>🤖 AI-powered</strong> - Get intelligent answers from docs</li>
            <li><strong>⚡ Fast processing</strong> - Quick document analysis</li>
            <li><strong>💬 Interactive</strong> - Ask follow-up questions</li>
            <li><strong>🎯 Python-focused</strong> - Optimized for Python documentation</li>
        </ul>
        
        <h3 style="color:#4f46e5; margin-top:30px;">🚀 Quick Start:</h3>
        <ol style="font-size:16px; line-height:1.8;">
            <li>Enter a Python documentation URL (or use the default)</li>
            <li>Click <strong>"Load Document"</strong></li>
            <li>Wait a few seconds for processing</li>
            <li>Ask any Python-related question about the documentation</li>
        </ol>
    </div>
    """, unsafe_allow_html=True)


st.markdown('</div>', unsafe_allow_html=True)
