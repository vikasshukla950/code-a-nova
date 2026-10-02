# Simple Banking System – Console App (Level 2a)

## What it does
A banking simulation built with object-oriented programming.

## Features
- Create accounts, deposit, withdraw, check balance
- Transfer between accounts and view transaction history
- PIN authentication (salted PBKDF2 hash); account locks after 3 wrong attempts
- Multiple accounts saved to `bank_data.json` (data persistence)
- Uses `Decimal` for accurate money handling

## How to run
```
python banking_system.py
```

## Structure
- `Transaction` – one record in the history
- `Account` – balance, PIN check, deposit/withdraw
- `Bank` – manages accounts, login, transfers, saving/loading

## Concepts used
Classes and methods, custom exceptions, hashing, JSON persistence, input validation.
