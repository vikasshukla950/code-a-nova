#!/usr/bin/env python3
"""CODE-A-NOVA Python Development Internship (Month 2 Tasks)

Interactive Runner & Demonstration for:
  - Level 1(a): File Organizer Automation Tool
  - Level 1(b): Chatbot using Rule-Based Logic
  - Level 2(a): Simple Banking System (Console App)
"""
import sys
from level1_file_organizer.file_organizer import main as run_file_organizer
from level1_chatbot.chatbot import main as run_chatbot
from level2_banking_system.banking_system import main as run_banking_system


def main():
    print("==================================================")
    print(" CODE-A-NOVA – Python Development Internship")
    print(" Month 2 Task Suite")
    print("==================================================")
    print("1. Level 1(a) - File Organizer Automation Tool")
    print("2. Level 1(b) - Chatbot using Rule-Based Logic")
    print("3. Level 2(a) - Simple Banking System (Console App)")
    print("4. Exit")

    if not sys.stdin.isatty():
        print("\n[Non-interactive execution detected] All submodules compiled and ready.")
        return

    try:
        choice = input("\nSelect a project to run (1-4): ").strip()
    except (EOFError, KeyboardInterrupt):
        return

    if choice == "1":
        run_file_organizer()
    elif choice == "2":
        run_chatbot()
    elif choice == "3":
        run_banking_system()
    elif choice == "4":
        print("Goodbye!")
    else:
        print("Invalid choice.")


if __name__ == "__main__":
    main()
