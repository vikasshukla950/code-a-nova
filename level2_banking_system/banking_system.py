#!/usr/bin/env python3
"""Simple Banking System - Console App (Level 2a)

OOP design:  Transaction, Account, Bank (+ custom exceptions)
Features: create account, PIN authentication (salted PBKDF2 hash, lock after
3 wrong attempts), deposit, withdraw, balance, transfer, transaction history,
multiple accounts persisted in a JSON file.
Run:  python banking_system.py
"""
import getpass
import hashlib
import json
import os
import secrets
from datetime import datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path

DATA_FILE = Path(__file__).with_name("bank_data.json")
MAX_ATTEMPTS = 3
MIN_BALANCE = Decimal("0")


class BankError(Exception):
    """Base class for all banking errors."""


class InsufficientFunds(BankError):
    pass


class AuthError(BankError):
    pass


def hash_pin(pin: str, salt: bytes) -> str:
    return hashlib.pbkdf2_hmac("sha256", pin.encode(), salt, 100_000).hex()


def parse_amount(text) -> Decimal:
    try:
        amount = Decimal(str(text)).quantize(Decimal("0.01"))
    except InvalidOperation:
        raise BankError("Invalid amount.")
    if amount <= 0:
        raise BankError("Amount must be greater than zero.")
    return amount


class Transaction:
    def __init__(self, kind, amount, balance_after, note="", timestamp=None):
        self.kind, self.amount, self.balance_after, self.note = kind, Decimal(amount), Decimal(balance_after), note
        self.timestamp = timestamp or datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def to_dict(self):
        return {"kind": self.kind, "amount": str(self.amount), "balance_after": str(self.balance_after),
                "note": self.note, "timestamp": self.timestamp}

    @classmethod
    def from_dict(cls, d):
        return cls(d["kind"], d["amount"], d["balance_after"], d.get("note", ""), d["timestamp"])

    def __str__(self):
        return (f"{self.timestamp} | {self.kind:<12} | {self.amount:>10} | "
                f"bal {self.balance_after:>10} | {self.note}")


class Account:
    def __init__(self, acc_no, holder, salt, pin_hash, balance=Decimal("0"),
                 history=None, failed_attempts=0):
        self.acc_no, self.holder = acc_no, holder
        self._salt, self._pin_hash = salt, pin_hash
        self._balance = Decimal(balance)
        self.history = history or []
        self.failed_attempts = failed_attempts

    @classmethod
    def create(cls, acc_no, holder, pin, opening=Decimal("0")):
        salt = os.urandom(16)
        acc = cls(acc_no, holder, salt, hash_pin(pin, salt))
        if opening > 0:
            acc.deposit(opening, "Opening deposit")
        return acc

    @property
    def balance(self):
        return self._balance

    @property
    def locked(self):
        return self.failed_attempts >= MAX_ATTEMPTS

    def verify_pin(self, pin):
        if self.locked:
            raise AuthError("Account locked after too many wrong PINs. Contact the bank.")
        if secrets.compare_digest(hash_pin(pin, self._salt), self._pin_hash):
            self.failed_attempts = 0
            return True
        self.failed_attempts += 1
        left = MAX_ATTEMPTS - self.failed_attempts
        raise AuthError("Incorrect PIN." + (f" {left} attempt(s) left." if left else " Account locked."))

    def deposit(self, amount, note="Deposit"):
        self._balance += amount
        self.history.append(Transaction("DEPOSIT", amount, self._balance, note))

    def withdraw(self, amount, note="Withdrawal"):
        if self._balance - amount < MIN_BALANCE:
            raise InsufficientFunds(f"Insufficient funds. Balance: {self._balance}")
        self._balance -= amount
        self.history.append(Transaction("WITHDRAW", amount, self._balance, note))

    def to_dict(self):
        return {"acc_no": self.acc_no, "holder": self.holder, "salt": self._salt.hex(),
                "pin_hash": self._pin_hash, "balance": str(self._balance),
                "failed_attempts": self.failed_attempts,
                "history": [t.to_dict() for t in self.history]}

    @classmethod
    def from_dict(cls, d):
        return cls(d["acc_no"], d["holder"], bytes.fromhex(d["salt"]), d["pin_hash"], Decimal(d["balance"]),
                   [Transaction.from_dict(t) for t in d["history"]], d.get("failed_attempts", 0))


class Bank:
    def __init__(self, path=DATA_FILE):
        self.path = Path(path)
        self.accounts = {}
        self.load()

    def load(self):
        if self.path.exists():
            try:
                data = json.loads(self.path.read_text())
                self.accounts = {d["acc_no"]: Account.from_dict(d) for d in data}
            except (json.JSONDecodeError, KeyError, ValueError):
                raise BankError("Data file is corrupted.")

    def save(self):
        self.path.write_text(json.dumps([a.to_dict() for a in self.accounts.values()], indent=2))

    def open_account(self, holder, pin, opening=Decimal("0")):
        if not holder.strip():
            raise BankError("Name cannot be empty.")
        if not (pin.isdigit() and len(pin) == 4):
            raise BankError("PIN must be exactly 4 digits.")
        acc_no = str(1000001 + len(self.accounts))
        self.accounts[acc_no] = Account.create(acc_no, holder.strip(), pin, opening)
        self.save()
        return acc_no

    def login(self, acc_no, pin):
        acc = self.accounts.get(acc_no)
        if not acc:
            raise AuthError("Account not found.")
        try:
            acc.verify_pin(pin)
        finally:
            self.save()  # persist attempt counter
        return acc

    def transfer(self, source, to_acc_no, amount):
        target = self.accounts.get(to_acc_no)
        if not target or target is source:
            raise BankError("Invalid destination account.")
        source.withdraw(amount, f"Transfer to {to_acc_no}")
        source.history[-1].kind = "TRANSFER_OUT"
        target.deposit(amount, f"Transfer from {source.acc_no}")
        target.history[-1].kind = "TRANSFER_IN"
        self.save()


# ---------------- console UI ----------------
def ask_pin(prompt="PIN: "):
    try:
        return getpass.getpass(prompt)
    except Exception:
        return input(prompt)


def account_menu(bank, acc):
    print(f"\nWelcome, {acc.holder}!")
    while True:
        print("\n1.Balance  2.Deposit  3.Withdraw  4.Transfer  5.History  6.Logout")
        choice = input("Choose: ").strip()
        try:
            if choice == "1":
                print(f"Balance: {acc.balance}")
            elif choice == "2":
                acc.deposit(parse_amount(input("Amount: "))); bank.save(); print(f"Deposited. Balance: {acc.balance}")
            elif choice == "3":
                acc.withdraw(parse_amount(input("Amount: "))); bank.save(); print(f"Withdrawn. Balance: {acc.balance}")
            elif choice == "4":
                bank.transfer(acc, input("To account no: ").strip(), parse_amount(input("Amount: ")))
                print(f"Transferred. Balance: {acc.balance}")
            elif choice == "5":
                print("\n".join(str(t) for t in acc.history[-15:]) or "No transactions yet.")
            elif choice == "6":
                return
            else:
                print("Invalid choice.")
        except BankError as exc:
            print(f"Error: {exc}")


def main():
    try:
        bank = Bank()
    except BankError as exc:
        raise SystemExit(exc)
    while True:
        print("\n=== SIMPLE BANK ===\n1.Create account  2.Login  3.Exit")
        choice = input("Choose: ").strip()
        try:
            if choice == "1":
                name = input("Full name: ")
                pin = ask_pin("Set 4-digit PIN: ")
                raw = input("Opening deposit (0 for none): ").strip() or "0"
                opening = Decimal(raw).quantize(Decimal("0.01"))
                if opening < 0:
                    raise BankError("Opening deposit cannot be negative.")
                print(f"Account created! Your account number is {bank.open_account(name, pin, opening)}")
            elif choice == "2":
                acc = bank.login(input("Account no: ").strip(), ask_pin())
                account_menu(bank, acc)
            elif choice == "3":
                print("Thank you for banking with us.")
                break
            else:
                print("Invalid choice.")
        except (BankError, InvalidOperation) as exc:
            print(f"Error: {exc}")


if __name__ == "__main__":
    main()
