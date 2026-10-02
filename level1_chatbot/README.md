# Chatbot using Rule-Based Logic (Level 1b)

## What it does
A terminal-based customer support chatbot that replies using predefined keyword rules.

## Features
- Detects keywords (hello, help, refund, hours, contact, bye, ...)
- Multiple conversation flows, including a multi-step order-tracking flow
- Memory: remembers your name and last topic
- Fallback replies for unknown inputs

## How to run
```
python chatbot.py
```

## Example
```
You: hello
SupportBot: Hello! How can I help you today?
You: my name is Vikas
SupportBot: Nice to meet you, Vikas! How can I help you?
You: track my order
SupportBot: Sure! Please enter your order number.
You: 12345
SupportBot: Order #12345 is packed and out for delivery. Expected arrival: within 2 days.
You: bye
SupportBot: Goodbye, Vikas! Have a great day.
```

## Concepts used
String handling, regular expressions, conditional logic, conversation design, classes.
