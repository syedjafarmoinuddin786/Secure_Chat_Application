# app/admin_cli.py
import argparse
import json
import os
import csv
import re
from app.config import CONFIG

USER_FILE = CONFIG.USER_FILE


def load_users():
    if os.path.exists(USER_FILE):
        with open(USER_FILE, "r") as f:
            return json.load(f)
    return {}


def save_users(users):
    with open(USER_FILE, "w") as f:
        json.dump(users, f, indent=4)


users_db = load_users()


def is_valid_username(username):
    return bool(re.match(r"^[a-zA-Z0-9_]+$", username))


def is_valid_role(role):
    return role.lower() in ["admin", "user"]


def create_user(username, role):
    if not is_valid_username(username):
        print("Error: Invalid username. Use only letters, numbers, and underscores.")
        return
    if not is_valid_role(role):
        print("Error: Role must be 'admin' or 'user'.")
        return
    if username in users_db:
        print(f"Error: User '{username}' already exists!")
    else:
        users_db[username] = role.lower()
        save_users(users_db)
        print(f"User '{username}' created with role '{role}'.")


def delete_user(username):
    if username in users_db:
        del users_db[username]
        save_users(users_db)
        print(f"User '{username}' deleted successfully.")
    else:
        print(f"Error: User '{username}' does not exist!")


def list_users():
    if users_db:
        print("Current users:")
        for username, role in users_db.items():
            print(f" - {username} ({role})")
    else:
        print("No users found.")


def update_user(username, new_role):
    if username not in users_db:
        print(f"Error: User '{username}' does not exist!")
        return
    if not is_valid_role(new_role):
        print("Error: Role must be 'admin' or 'user'.")
        return
    users_db[username] = new_role.lower()
    save_users(users_db)
    print(f"User '{username}' updated with new role '{new_role}'.")


def search_user(query):
    query_lower = query.lower()
    matches = [(u, r) for u, r in users_db.items()
               if query_lower in u.lower() or query_lower == r.lower()]
    if matches:
        print("Matching users:")
        for username, role in matches:
            print(f" - {username} ({role})")
    else:
        print(f"No users found matching '{query}'.")


def export_users(file_path):
    if not users_db:
        print("No users to export.")
        return
    with open(file_path, "w", newline="") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["Username", "Role"])
        for u, r in users_db.items():
            writer.writerow([u, r])
    print(f"Users exported successfully to '{file_path}'.")


def main():
    parser = argparse.ArgumentParser(description="Admin CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    p = subparsers.add_parser("create-user", help="Create a new user")
    p.add_argument("--username", required=True)
    p.add_argument("--role", required=True)

    p = subparsers.add_parser("delete-user", help="Delete an existing user")
    p.add_argument("--username", required=True)

    subparsers.add_parser("list-users", help="List all users")

    p = subparsers.add_parser("update-user", help="Update an existing user's role")
    p.add_argument("--username", required=True)
    p.add_argument("--role", required=True)

    p = subparsers.add_parser("search-user", help="Search users by username or role")
    p.add_argument("--query", required=True)

    p = subparsers.add_parser("export-users", help="Export users to CSV file")
    p.add_argument("--file", required=True)

    args = parser.parse_args()

    if args.command == "create-user":
        create_user(args.username, args.role)
    elif args.command == "delete-user":
        delete_user(args.username)
    elif args.command == "list-users":
        list_users()
    elif args.command == "update-user":
        update_user(args.username, args.role)
    elif args.command == "search-user":
        search_user(args.query)
    elif args.command == "export-users":
        export_users(args.file)


if __name__ == "__main__":
    main()
