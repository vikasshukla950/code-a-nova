#!/usr/bin/env python3
"""Rule-Based Customer Support Chatbot (Level 1b)

Features: keyword detection (whole-word regex), several conversation flows
(orders, refunds, hours, contact), memory (user's name + last topic),
fallback replies, and a small multi-step flow for tracking an order.
Run:  python chatbot.py
"""
import random
import re

BOT = "SupportBot"

# (name, keywords, replies) - first rule that matches wins, so order matters.
RULES = [
    ("greeting", ["hello", "hi", "hey", "good morning", "good evening"],
     ["Hello{name}! How can I help you today?", "Hi{name}! What can I do for you?"]),
    ("how_are_you", ["how are you", "how r u"],
     ["I'm just code, but running smoothly! How can I help you{name}?"]),
    ("help", ["help", "support", "assist", "problem", "issue"],
     ["I can help with: order tracking, refunds, store hours and contact details. "
      "Just type what you need!"]),
    ("track", ["track", "order status", "where is my order", "delivery"],
     None),  # handled by a multi-step flow
    ("refund", ["refund", "return", "money back", "cancel"],
     ["Refunds are processed within 5-7 working days once the item is received. "
      "Would you like to know about the return policy?"]),
    ("policy", ["policy", "return policy"],
     ["You can return any unused item within 30 days with the original receipt."]),
    ("hours", ["hours", "open", "timing", "timings", "close"],
     ["We're open Monday to Saturday, 9 AM - 8 PM. Closed on Sundays."]),
    ("contact", ["contact", "email", "phone", "call", "number"],
     ["Reach us at support@example.com or call 1800-123-456 (toll free)."]),
    ("thanks", ["thanks", "thank you", "thx"],
     ["You're welcome{name}! Anything else I can help with?"]),
    ("bye", ["bye", "goodbye", "exit", "quit", "see you"],
     ["Goodbye{name}! Have a great day."]),
]

FALLBACKS = [
    "Sorry, I didn't quite get that. Could you rephrase? (Type 'help' to see what I can do.)",
    "Hmm, I'm not sure about that yet. Try asking about orders, refunds, or store hours.",
    "I'm still learning! Type 'help' for the list of things I can answer.",
]


class Chatbot:
    def __init__(self):
        self.name = None
        self.state = None       # for multi-step flows
        self.last_topic = None
        self.running = True

    # -- helpers ---------------------------------------------------------
    @staticmethod
    def _has(text, keyword):
        return re.search(rf"\b{re.escape(keyword)}\b", text) is not None

    def _name_suffix(self):
        return f", {self.name}" if self.name else ""

    def _try_learn_name(self, text):
        m = re.search(r"\b(?:my name is|i am|i'm|call me)\s+([a-zA-Z]+)", text, re.I)
        if m and m.group(1).lower() not in {"fine", "good", "ok", "okay", "great", "here"}:
            self.name = m.group(1).capitalize()
            return f"Nice to meet you, {self.name}! How can I help you?"
        return None

    # -- main entry ------------------------------------------------------
    def respond(self, user_input):
        text = user_input.strip().lower()
        if not text:
            return "Please type something so I can help."

        # multi-step flow: waiting for an order id
        if self.state == "awaiting_order_id":
            self.state = None
            m = re.search(r"\d{4,}", text)
            if m:
                return (f"Order #{m.group()} is packed and out for delivery. "
                        "Expected arrival: within 2 days.")
            return "That doesn't look like a valid order number (needs 4+ digits). Type 'track' to retry."

        learned = self._try_learn_name(user_input)
        if learned:
            return learned

        if re.search(r"\bwhat(?:'s| is) my name\b|\bwho am i\b", text):
            return f"Your name is {self.name}." if self.name else "I don't know your name yet. Tell me with 'my name is ...'"

        if re.search(r"\bwhat did i (ask|say)\b|\blast topic\b", text):
            return (f"Your last topic was '{self.last_topic}'." if self.last_topic
                    else "We haven't discussed anything yet.")

        for topic, keywords, replies in RULES:
            if any(self._has(text, k) for k in keywords):
                self.last_topic = topic
                if topic == "bye":
                    self.running = False
                if topic == "track":
                    self.state = "awaiting_order_id"
                    return "Sure! Please enter your order number."
                return random.choice(replies).format(name=self._name_suffix())

        return random.choice(FALLBACKS)


_default_bot = Chatbot()


def get_response(user_input: str) -> str:
    """Standalone helper function to get a response from the default chatbot instance."""
    return _default_bot.respond(str(user_input))


def respond(user_input: str) -> str:
    """Standalone helper function to get a response from the default chatbot instance."""
    return _default_bot.respond(str(user_input))


def chatbot_response(user_input: str) -> str:
    """Standalone helper function to get a response from the default chatbot instance."""
    return _default_bot.respond(str(user_input))


def main():
    bot = Chatbot()
    print(f"{BOT}: Hi! I'm {BOT}. What's your name? (or just ask me something)")
    while bot.running:
        try:
            user = input("You: ")
            if not user.strip() and not sys.stdin.isatty():
                break
        except (EOFError, KeyboardInterrupt):
            print(f"\n{BOT}: Goodbye!")
            break
        print(f"{BOT}: {bot.respond(user)}")


if __name__ == "__main__":
    import sys
    main()

