import os
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.chains import RetrievalQA
from langchain.vectorstores import Chroma
from langchain.schema import Document
from langchain.prompts import PromptTemplate
from typing import Dict, List, Any, Tuple
from utils import create_citation, highlight_text_in_pdf
import json

class EnhancedQASystem:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-1.5-flash",
            google_api_key=api_key,
            temperature=0.7,
            convert_system_message_to_human=True
        )
        self.vectorstore = None
        self.qa_chain = None
        self.document_metadata = {}
        
    def initialize_vectorstore(self, documents: List[Document], metadata: Dict):
        """Initialize vector store with documents"""
        try:
            from langchain_google_genai import GoogleGenerativeAIEmbeddings
            
            embeddings = GoogleGenerativeAIEmbeddings(
                model="models/embedding-001",
                google_api_key=self.api_key
            )
            
            self.vectorstore = Chroma.from_documents(
                documents=documents,
                embedding=embeddings,
                persist_directory="./chroma_db"
            )
            
            self.document_metadata = metadata
            self._setup_qa_chain()
            return True
            
        except Exception as e:
            print(f"Error initializing vectorstore: {e}")
            return False
    
    def _setup_qa_chain(self):
        """Setup the QA chain with custom prompt"""
        
        custom_prompt = PromptTemplate(
            template="""You are a helpful assistant that answers questions based on the provided document context. 
            Always provide specific, accurate answers and mention which document(s) you're referencing when possible.
            
            Context: {context}
            
            Question: {question}
            
            Answer with specific details and cite the source document(s) when relevant:""",
            input_variables=["context", "question"]
        )
        
        self.qa_chain = RetrievalQA.from_chain_type(
            llm=self.llm,
            chain_type="stuff",
            retriever=self.vectorstore.as_retriever(search_kwargs={"k": 5}),
            return_source_documents=True,
            chain_type_kwargs={"prompt": custom_prompt}
        )
    
    def get_enhanced_response(self, question: str) -> Dict[str, Any]:
        """Get enhanced response with citations and source information"""
        try:
            # Get response from QA chain
            response = self.qa_chain({"query": question})
            answer = response["result"]
            source_docs = response["source_documents"]
            
            # Create citations
            citations = create_citation(source_docs)
            
            # Get source information with page numbers
            sources_info = self._extract_source_info(source_docs)
            
            # Generate key phrases for highlighting
            key_phrases = self._extract_key_phrases_from_answer(answer)
            
            return {
                'answer': answer,
                'citations': citations,
                'sources_info': sources_info,
                'source_documents': source_docs,
                'key_phrases': key_phrases,
                'confidence': self._calculate_confidence(source_docs)
            }
            
        except Exception as e:
            return {
                'answer': f"Error generating response: {str(e)}",
                'citations': "",
                'sources_info': [],
                'source_documents': [],
                'key_phrases': [],
                'confidence': 0
            }
    
    def _extract_source_info(self, source_docs: List[Any]) -> List[Dict]:
        """Extract detailed source information"""
        sources_info = []
        seen_sources = set()
        
        for doc in source_docs:
            metadata = doc.metadata
            source_key = f"{metadata.get('source', 'Unknown')}_{metadata.get('page_number', 1)}"
            
            if source_key not in seen_sources:
                sources_info.append({
                    'filename': metadata.get('source', 'Unknown'),
                    'page_number': metadata.get('page_number', 1),
                    'chunk_id': metadata.get('chunk_id', 0),
                    'file_type': metadata.get('file_type', 'unknown'),
                    'content_preview': doc.page_content[:200] + "..." if len(doc.page_content) > 200 else doc.page_content
                })
                seen_sources.add(source_key)
        
        return sources_info
    
    def _extract_key_phrases_from_answer(self, answer: str) -> List[str]:
        """Extract key phrases from the answer for highlighting"""
        # Simple extraction - get important sentences
        sentences = answer.split('.')
        key_phrases = []
        
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) > 20 and len(sentence) < 150:
                # Look for sentences with important keywords
                important_words = ['important', 'key', 'significant', 'main', 'primary', 'essential']
                if any(word in sentence.lower() for word in important_words):
                    key_phrases.append(sentence)
        
        return key_phrases[:3]  # Return top 3
    
    def _calculate_confidence(self, source_docs: List[Any]) -> float:
        """Calculate confidence score based on source documents"""
        if not source_docs:
            return 0.0
        
        # Simple confidence calculation based on number of sources and content similarity
        num_sources = len(source_docs)
        avg_content_length = sum(len(doc.page_content) for doc in source_docs) / num_sources
        
        # Normalize confidence score
        confidence = min(1.0, (num_sources * 0.2) + (avg_content_length / 1000 * 0.3))
        return round(confidence, 2)
    
    def generate_executive_summary(self) -> str:
        """Generate executive summary of all loaded documents"""
        try:
            summaries = []
            for file_id, metadata in self.document_metadata.items():
                summaries.append(f"**{metadata['filename']}**: {metadata['summary']}")
            
            if len(summaries) > 1:
                # Create a combined summary
                combined_text = " ".join([meta['summary'] for meta in self.document_metadata.values()])
                
                prompt = f"""Create a comprehensive executive summary combining the following individual document summaries:

{chr(10).join(summaries)}

Provide a unified executive summary highlighting key themes and insights across all documents:"""
                
                response = self.llm.invoke(prompt)
                return response.content
            elif len(summaries) == 1:
                return summaries[0]
            else:
                return "No documents loaded for summary generation."
                
        except Exception as e:
            return f"Error generating executive summary: {str(e)}"
    
    def get_document_insights(self) -> Dict[str, Any]:
        """Get insights about loaded documents"""
        total_docs = len(self.document_metadata)
        total_chunks = sum(meta.get('total_chunks', 0) for meta in self.document_metadata.values())
        
        file_types = {}
        for meta in self.document_metadata.values():
            file_type = meta.get('file_type', 'unknown')
            file_types[file_type] = file_types.get(file_type, 0) + 1
        
        return {
            'total_documents': total_docs,
            'total_chunks': total_chunks,
            'file_types': file_types,
            'document_list': [meta['filename'] for meta in self.document_metadata.values()]
        }