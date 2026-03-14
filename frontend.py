# ============================================================================
# FRONTEND MODULE - User Interfaces (Terminal and GUI)
# ============================================================================

"""
Frontend module for Portfolio Chatbot

Provides:
- Terminal mode (command-line chat)
- GUI mode (Gradio web interface)
"""

import gradio as gr
from backend import chat


# ============================================================================
# TERMINAL MODE
# ============================================================================

def run_terminal_mode():
    """
    Run chatbot in terminal mode
    User types questions directly, bot responds in real-time
    """
    print("\n" + "="*70)
    print("🤖 PORTFOLIO ASSISTANT - TERMINAL MODE")
    print("="*70)
    print("Welcome! I'm Prakhar Dwivedi's portfolio assistant.")
    print("Ask me about his experience, projects, education, or anything else!")
    print("\nType 'exit' or 'quit' to end the conversation.")
    print("="*70 + "\n")
    
    # Keep conversation history
    conversation_history = []
    
    # Main chat loop
    while True:
        try:
            # Get user input
            user_input = input("You: ").strip()
            
            # Check for exit commands
            if user_input.lower() in ['exit', 'quit', 'bye']:
                print("\n👋 Thank you for chatting! Goodbye!")
                break
            
            # Skip empty input
            if not user_input:
                print("⚠️  Please type something!\n")
                continue
            
            # Show thinking indicator
            print("\n⏳ Assistant is thinking...\n")
            
            # Get response from backend
            response = chat(user_input, conversation_history)
            
            # Display response
            print(f"Assistant: {response}\n")
            
            # Add to conversation history
            conversation_history.append({"role": "user", "content": user_input})
            conversation_history.append({"role": "assistant", "content": response})
            
        except KeyboardInterrupt:
            print("\n\n👋 Conversation ended. Goodbye!")
            break
        except Exception as e:
            print(f"\n❌ An error occurred: {str(e)}")
            print("Please try again.\n")


# ============================================================================
# GUI MODE (GRADIO)
# ============================================================================

def run_gui_mode():
    """
    Run chatbot in Gradio GUI mode
    Opens a beautiful web interface in your browser
    """
    # Chat interface with example questions
    gr.ChatInterface(
        fn=chat,
        type="messages",
        examples=[
            "Tell me about your projects",
            "What technologies do you work with?",
            "What is your work experience?",
            "What is your college and school name?"
        ]
    ).launch()
