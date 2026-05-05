# ============================================================================
# MAIN - Entry Point (Run This File!)
# ============================================================================

"""
Main file to run the Portfolio Chatbot

Choose between Terminal or GUI mode when you run this file
"""

from frontend import run_terminal_mode, run_gui_mode


def show_menu():
    """Display the mode selection menu"""
    print("\n" + "="*70)
    print("🎯 PORTFOLIO CHATBOT - MODE SELECTION")
    print("="*70)
    print("\nChoose how you want to use the chatbot:\n")
    print("  [1] 📱 TERMINAL MODE")
    print("      - Chat directly in your terminal")
    print("      - Perfect for quick questions. Limited experience\n")
    print("  [2] 🌐 GUI MODE (Gradio)")
    print("      - Best experience with beautiful web interface")
    print("      - Opens in your browser\n")
    print("="*70)
    
    # Get user choice
    while True:
        choice = input("\nEnter your choice (1 or 2): ").strip()
        
        if choice in ['1', '2']:
            return choice
        else:
            print("❌ Invalid choice! Please enter 1 or 2.")


def main():
    """Main entry point"""
    # Show menu and get choice
    user_choice = show_menu()
    
    # Run selected mode
    if user_choice == '1':
        print("\n✅ Starting Terminal Mode...\n")
        run_terminal_mode()
    else:
        print("\n✅ Starting GUI Mode...")
        print("🌐 Gradio interface will open in your browser!\n")
        run_gui_mode()


if __name__ == "__main__":
    main()
