
"""
auth.py - Secure Authentication
Features:
 - Register / Login / Exit
 - bcrypt password hashing
 - Username/password validation
 - Auto-create users.txt
 - Falls back from getpass() when running in non-TTY environments (e.g. PyCharm Run)
"""

import os
import re
import sys
from getpass import getpass, GetPassWarning
import bcrypt

USER_DATA_FILE = "users.txt"

def _ensure_user_file():
    if not os.path.exists(USER_DATA_FILE):
        open(USER_DATA_FILE, "w", encoding="utf-8").close()


def _read_users():
    """Return dict username -> hashed_password"""
    users = {}
    if not os.path.exists(USER_DATA_FILE):
        return users
    with open(USER_DATA_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            # stored as username,hashed
            parts = line.split(",", 1)
            if len(parts) == 2:
                users[parts[0]] = parts[1]
    return users


def _append_user(username, hashed):
    _ensure_user_file()
    with open(USER_DATA_FILE, "a", encoding="utf-8") as f:
        f.write(f"{username},{hashed}\n")



def hash_password(plain_password: str) -> str:
    if plain_password is None:
        raise ValueError("Password cannot be None")
    hashed = bcrypt.hashpw(plain_password.encode("utf-8"), bcrypt.gensalt())
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(plain_password.encode("utf-8"), hashed.encode("utf-8"))
    except Exception:
        return False



def validate_username(u: str):
    if not u or u.strip() == "":
        return False, "Username cannot be empty."
    if not re.fullmatch(r"[A-Za-z0-9]{3,20}", u):
        return False, "Username must be 3-20 characters, letters and digits only."
    return True, ""


def validate_password(p: str):
    if p is None or p == "":
        return False, "Password cannot be empty."
    if len(p) < 6 or len(p) > 50:
        return False, "Password must be 6-50 characters."
    if not re.search(r"[A-Z]", p):
        return False, "Password must include at least one uppercase letter."
    if not re.search(r"[a-z]", p):
        return False, "Password must include at least one lowercase letter."
    if not re.search(r"\d", p):
        return False, "Password must include at least one digit."
    return True, ""


def safe_get_password(prompt: str = "Password: ") -> str:
    """
    Use getpass() when stdin is a TTY. If not (e.g. PyCharm Run console), fall back to input()
    so the program doesn't hang.
    """
    try:
        # If running in a proper terminal, getpass will work and not echo
        if sys.stdin.isatty():
            return getpass(prompt)
        else:
            # non-tty (IDE run window), fallback to visible input
            print("(Note: running in non-interactive console — password will be visible)")
            return input(prompt)
    except (GetPassWarning, Exception):
        # any getpass issues -> fallback
        print("(Note: getpass unavailable, using visible input)")
        return input(prompt)



def register_flow():
    print("\n--- USER REGISTRATION ---")
    username = input("Enter a username: ").strip()
    ok, msg = validate_username(username)
    if not ok:
        print(f"Error: {msg}")
        return

    users = _read_users()
    if username in users:
        print("Error: Username already exists.")
        return

    password = safe_get_password("Enter a password: ").strip()
    ok, msg = validate_password(password)
    if not ok:
        print(f"Error: {msg}")
        return

    password_confirm = safe_get_password("Confirm password: ").strip()
    if password != password_confirm:
        print("Error: Passwords do not match.")
        return

    hashed = hash_password(password)
    _append_user(username, hashed)
    print(f"Success: User '{username}' registered successfully!")


def login_flow():
    print("\n--- USER LOGIN ---")
    username = input("Enter your username: ").strip()
    users = _read_users()
    if username not in users:
        print("Error: Username not found.")
        return

    password = safe_get_password("Enter your password: ").strip()
    if verify_password(password, users[username]):
        print(f"Success: Welcome, {username}!")
    else:
        print("Error: Invalid password.")



def print_menu():
    print("\n" + "-" * 48)
    print("[1] Register a new user")
    print("[2] Login")
    print("[3] Exit")
    print("-" * 48)


def main():
    print("Welcome to the Secure Authentication Program")
    _ensure_user_file()
    while True:
        print_menu()
        choice = input("Please select an option (1-3): ").strip()
        if choice == "1":
            register_flow()
        elif choice == "2":
            login_flow()
        elif choice == "3":
            print("Exiting... Goodbye.")
            break
        else:
            print("Invalid option. Please select 1, 2 or 3.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nInterrupted. Exiting.")
        sys.exit(0)