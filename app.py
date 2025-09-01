import streamlit as st
import os
from dotenv import load_dotenv
import google.generativeai as genai
from datetime import datetime

# Import your modules
from document_processor import DocumentProcessor
from qa_system import EnhancedQASystem
from summary_generator import SummaryGenerator

# Load environment
load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# Page config
st.set_page_config(page_title="Document QA", page_icon="📚", layout="wide")

# Initialize session state
@st.cache_resource
def init_systems():
    return {
        'processor': DocumentProcessor(os.getenv("GEMINI_API_KEY")),
        'qa_system': EnhancedQASystem(os.getenv("GEMINI_API_KEY")),
        'summarizer': SummaryGenerator()
    }

def init_session_state():
    defaults = {
        'messages': [],
        'conversation_history': [],
        'document_metadata': {},
        'executive_summary': ""
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

def sidebar():
    """Handle all sidebar functionality"""
    with st.sidebar:
        st.header("📤 Upload Documents")
        
        # File uploader
        uploaded_files = st.file_uploader(
            "Choose files", 
            type=['pdf', 'txt'], 
            accept_multiple_files=True
        )
        
        # Process documents
        if uploaded_files and st.button(" Process Documents", type="primary"):
            systems = init_systems()
            
            with st.spinner("Processing..."):
                success, message, result = systems['processor'].process_multiple_documents(uploaded_files)
                
                if success:
                    systems['qa_system'].initialize_vectorstore(result['documents'], result['metadata'])
                    st.session_state.document_metadata = result['metadata']
                    st.session_state.executive_summary = systems['qa_system'].generate_executive_summary()
                    st.success("Documents processed!")
                    st.rerun()
                else:
                    st.error(message)
        
        # Conversation history (last 3 conversations)
        if st.session_state.conversation_history:
            st.subheader(" Recent Conversations")
            recent_conversations = st.session_state.conversation_history[-3:]
            
            for chat in reversed(recent_conversations):
                with st.expander(f"Q: {chat['question'][:25]}...", expanded=False):
                    st.write(f"**Q:** {chat['question']}")
                    st.write(f"**A:** {chat['answer'][:100]}...")
                    st.write(f"**Time:** {chat['timestamp']}")
                    if 'citations' in chat and chat['citations']:
                        st.write(f"**Sources:** {chat['citations']}")
        
        st.divider()
        
        # Status
        if st.session_state.document_metadata:
            st.success(f" {len(st.session_state.document_metadata)} document(s) loaded")
            
            # Download buttons
            st.subheader("Downloads")
            
            # Executive summary (always available if documents loaded)
            if st.session_state.executive_summary:
                summary_text = f"""EXECUTIVE SUMMARY
==================
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

{st.session_state.executive_summary}
"""
                st.download_button(
                    " Download Summary",
                    summary_text,
                    f"summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                    "text/plain"
                )
            
            # Full reports (only if conversation exists)
            if st.session_state.conversation_history:
                systems = init_systems()
                
                col1, col2 = st.columns(2)
                
                with col1:
                    # PDF download
                    pdf_buffer = systems['summarizer'].generate_downloadable_summary(
                        st.session_state.conversation_history,
                        st.session_state.document_metadata,
                        st.session_state.executive_summary
                    )
                    st.download_button(
                        " PDF Report",
                        pdf_buffer.getvalue(),
                        f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                        "application/pdf"
                    )
                
                with col2:
                    # Markdown download
                    markdown_content = systems['summarizer'].create_markdown_summary(
                        st.session_state.conversation_history,
                        st.session_state.document_metadata,
                        st.session_state.executive_summary
                    )
                    st.download_button(
                        " MD Report",
                        markdown_content,
                        f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
                        "text/markdown"
                    )
        
        # Clear options
        if st.session_state.conversation_history or st.session_state.document_metadata:
            st.subheader(" Clear Data")
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("Clear Chat", type="secondary"):
                    st.session_state.messages = []
                    st.session_state.conversation_history = []
                    st.rerun()
            
            with col2:
                if st.button("Clear All", type="secondary"):
                    st.cache_resource.clear()  # Clear Streamlit's resource cache
                    st.session_state.messages = []
                    st.session_state.conversation_history = []
                    st.session_state.document_metadata = {}
                    st.session_state.executive_summary = ""
                    st.rerun()

def main_content():
    """Handle main content area"""
    st.title(" Document Insights Generator")
    
    # Executive summary
    if st.session_state.executive_summary:
        with st.expander(" Executive Summary", expanded=True):
            st.write(st.session_state.executive_summary)
        st.divider()
    
    # Chat interface
    st.header(" Ask Questions")
    
    # Display messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Chat input
    if prompt := st.chat_input("Ask about your documents..."):
        if not st.session_state.document_metadata:
            st.error("Please upload documents first!")
            return
        
        # Add user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Generate response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                systems = init_systems()
                response_data = systems['qa_system'].get_enhanced_response(prompt)
                answer = response_data['answer']
                
                st.markdown(answer)
                
                # Add to history
                st.session_state.messages.append({"role": "assistant", "content": answer})
                st.session_state.conversation_history.append({
                    'question': prompt,
                    'answer': answer,
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                })

def main():
    init_session_state()
    sidebar()
    main_content()

if __name__ == "__main__":
    main()