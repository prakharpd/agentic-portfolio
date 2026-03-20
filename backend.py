# ============================================================================
# BACKEND MODULE - All AI Logic and Processing
# ============================================================================

"""
Backend module for Portfolio Chatbot

Handles:
- RAG system (document loading & semantic search)
- AI agent creation and chat processing
- Notification system
"""

import os
import asyncio
import nest_asyncio
import requests
from dotenv import load_dotenv
from pypdf import PdfReader
import numpy as np
from sentence_transformers import SentenceTransformer
import warnings
import logging
import sys

# Suppress all warnings
warnings.filterwarnings("ignore")

# Suppress logging from libraries
logging.getLogger("anthropic").setLevel(logging.CRITICAL)
logging.getLogger("openai").setLevel(logging.CRITICAL)
logging.getLogger("urllib3").setLevel(logging.CRITICAL)
logging.basicConfig(level=logging.CRITICAL)

# Suppress stderr output PERMANENTLY (kill all those annoying tracing messages)
class SuppressOutput:
    def write(self, x):
        pass
    def flush(self):
        pass

# Redirect stderr PERMANENTLY - don't restore it
sys.stderr = SuppressOutput()

# Apply nest_asyncio for compatibility
nest_asyncio.apply()

# Load environment variables
load_dotenv()

# ============================================================================
# CONFIGURATION - DISABLE TRACING AND WARNINGS
# ============================================================================

# Disable all tracing
os.environ["AGENTS_DISABLE_TRACING"] = "true"
os.environ["ANTHROPIC_DISABLE_TRACING"] = "true"
os.environ["OTEL_SDK_DISABLED"] = "true"

# Use local Ollama
os.environ["OPENAI_BASE_URL"] = "http://localhost:11434/v1"
os.environ["OPENAI_API_KEY"] = "sk-proj-ollama-local"  # Proper dummy key format

notification_user_id = os.getenv("PUSHOVER_USER")
notification_api_token = os.getenv("PUSHOVER_TOKEN")
notification_api_url = "Put your own PUSHOVER API URL"

# Get the directory where this script is located
script_dir = os.path.dirname(os.path.abspath(__file__))

# Set file paths relative to script location
resume_pdf_path = os.path.join(script_dir, "resume", "linkedin.pdf")
summary_file_path = os.path.join(script_dir, "resume", "summary.txt")

# ============================================================================
# NOTIFICATION SYSTEM
# ============================================================================

def send_notification(message_text):
    """Send push notification"""
    try:
        payload = {
            "user": notification_user_id,
            "token": notification_api_token,
            "message": message_text
        }
        requests.post(notification_api_url, data=payload, timeout=5)
    except:
        pass


# ============================================================================
# AGENT TOOLS - Imported only when needed
# ============================================================================

def get_agent_tools():
    """Import and create agent tools (delayed import)"""
    from agents import function_tool
    
    @function_tool
    def save_user_contact(email: str, phone_number: str = 'Not provided', name: str = "Not provided", notes: str = "No notes"):
        """Save user contact information"""
        message = f"New contact: {name}, Email: {email}, Phone: {phone_number}, Notes: {notes}"
        send_notification(message)
        return {"status": "Contact saved successfully!"}

    @function_tool
    def save_unanswered_question(question_text: str):
        """Save questions the chatbot couldn't answer"""
        message = f"Unanswered question: {question_text}"
        send_notification(message)
        return {"status": "Question saved for later"}
    
    return save_user_contact, save_unanswered_question


# ============================================================================
# RAG SYSTEM - Document Loading and Search
# ============================================================================

def load_and_chunk_documents():
    """Load resume PDF and summary, break into chunks"""
    sections = []
    
    # Check if PDF exists
    if not os.path.exists(resume_pdf_path):
        print(f"⚠️  Warning: {resume_pdf_path} not found!")
        print(f"   Expected path: {os.path.abspath(resume_pdf_path)}\n")
        print("   Create the folder structure like this:")
        print("   📁 Your Project Folder/")
        print("   ├── resume/")
        print("   │   ├── linkedin.pdf")
        print("   │   └── summary.txt")
        print("   ├── backend.py")
        print("   ├── frontend.py")
        print("   └── main.py\n")
        
        # Add placeholder content so chatbot still works
        placeholder = """PLACEHOLDER RESUME

This is a placeholder. Please add your actual resume files:
- Place your LinkedIn PDF at: resume/linkedin.pdf
- Place your summary at: resume/summary.txt

For now, the chatbot will use this placeholder text."""
        sections.append(placeholder)
        return sections
    
    # Load PDF
    print("📄 Loading resume PDF...")
    try:
        pdf = PdfReader(resume_pdf_path)
        all_text = ""
        
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                all_text += text
        
        # Smart chunking by section headers
        current_chunk = ""
        section_headers = ['Education', 'Experience', 'Projects', 'Skills', 'Awards & Accomplishments', 'Competitive Conqueror', 'Counselxperts', 'Sawari']
        
        for line in all_text.split('\n'):
            if line.strip() in section_headers:
                if current_chunk:
                    sections.append(current_chunk.strip())
                current_chunk = line + "\n"
            else:
                current_chunk += line + "\n"
        
        if current_chunk:
            sections.append(current_chunk.strip())
        
        # Add full text as one chunk
        sections.append(all_text)
        
    except Exception as e:
        print(f"❌ Error reading PDF: {str(e)}")
        sections.append("Error reading PDF file. Using placeholder content.")
    
    # Load summary
    print("📝 Loading summary file...")
    if os.path.exists(summary_file_path):
        try:
            with open(summary_file_path, "r", encoding="utf-8") as f:
                summary = f.read().strip()
                sections.append(summary)
        except Exception as e:
            print(f"⚠️  Could not load summary: {str(e)}")
    else:
        print(f"⚠️  Summary file not found at: {summary_file_path}")
    
    print(f"✓ Created {len(sections)} text chunks\n")
    return sections


# Initialize RAG system
print("🚀 Starting RAG system...")
embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
all_document_chunks = load_and_chunk_documents()
all_chunk_embeddings = embedding_model.encode(all_document_chunks)
print("✓ RAG system ready!\n")


def find_matching_sections(user_question, top_k=5):
    """Search resume chunks and return matching sections"""
    question_embedding = embedding_model.encode([user_question])[0]
    
    similarity_scores = np.dot(all_chunk_embeddings, question_embedding) / (
        np.linalg.norm(all_chunk_embeddings, axis=1) * np.linalg.norm(question_embedding)
    )
    
    top_indices = np.argsort(similarity_scores)[-top_k:][::-1]
    matching_chunks = [all_document_chunks[i] for i in top_indices]
    
    return "\n\n---\n\n".join(matching_chunks)


# ============================================================================
# AI AGENT SETUP
# ============================================================================

system_prompt = """You are Prakhar Dwivedi's portfolio assistant.

RULES:
1. Answer ONLY from the CONTEXT provided below
2. If the answer is in CONTEXT, give it accurately and professionally
3. If the answer is NOT in CONTEXT, call save_unanswered_question
4. If user provides contact info, call save_user_contact
5. Be concise and professional in your responses
6. You can respond to basic greetings like Hi, Hello, Bye, etc

Use these emojis to be friendly: 🙂🚀👍

---
CONTEXT (Resume information):
{context}
---
"""

# Will be initialized when chat is called
portfolio_assistant = None


def initialize_agent():
    """Initialize the agent (delayed import)"""
    global portfolio_assistant
    if portfolio_assistant is None:
        from agents import Agent
        save_user_contact, save_unanswered_question = get_agent_tools()
        
        portfolio_assistant = Agent(
            name="Portfolio Assistant",
            instructions="",
            model="gpt-oss:120b-cloud",
            tools=[save_user_contact, save_unanswered_question]
        )
    return portfolio_assistant


# ============================================================================
# CHAT FUNCTION
# ============================================================================

async def chat_async(user_message, conversation_history):
    """Async chat function"""
    from agents import Runner
    
    # Initialize agent if needed
    agent = initialize_agent()
    
    # Get relevant resume sections
    relevant_context = find_matching_sections(user_message)
    
    # Update agent instructions with context
    agent.instructions = system_prompt.format(context=relevant_context)
    
    # Add user message to history
    full_messages = conversation_history + [{"role": "user", "content": user_message}]
    
    # Run agent
    result = await Runner.run(agent, input=full_messages)
    
    return result.final_output


def chat(user_message, conversation_history):
    """Sync wrapper for chat function"""
    return asyncio.run(chat_async(user_message, conversation_history))
