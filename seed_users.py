"""Seed users into the database. Run this to add users who can access the system."""

from api.auth import seed_user

# Add your users here
USERS = [
    {"email": "admin@koinx.com", "password": "admin123", "name": "Admin"},
    {"email": "shreya@koinx.com", "password": "shreya123", "name": "Shreya"},
]

if __name__ == "__main__":
    for u in USERS:
        seed_user(u["email"], u["password"], u["name"])
        print(f"Seeded user: {u['email']}")
    print("Done!")
