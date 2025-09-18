from database import init_db
from user import register_user, get_user
from history import view_history
from training import record_training, start_today_session

def get_valid_email():
    """Prompt user for a valid email."""
    while True:
        email = input("\nEnter your email: ")
        try:
            user = get_user(email)
            return email, user
        except ValueError as e:
            print(e)
            print("Please try again.")

def get_valid_menu_choice():
    """Prompt user for a valid menu choice."""
    while True:
        print("\n===== MAIN MENU =====")
        print("1. Record training")
        print("2. View history")
        print("3. Get started with today’s session")
        print("4. Exit")
        choice = input("Enter choice: ").strip()
        if choice in ["1", "2", "3", "4"]:
            return choice
        print("Invalid choice! Please enter 1, 2, 3, or 4.")

def get_valid_name():
    """Prompt user for a valid name."""
    while True:
        name = input("Enter name: ")
        if name.strip():
            return name
        print("Name cannot be empty. Please try again.")

def get_valid_phone():
    """Prompt user for a valid phone number (10 digits)."""
    while True:
        phone = input("Enter phone: ")
        if phone.isdigit() and len(phone) == 10:
            return phone
        print("Invalid phone number! Please enter a 10-digit number.")

def main():
    try:
        init_db()
    except Exception as e:
        print(f"Error: Failed to initialize database: {e}")
        return

    print("\nWELCOME TO VYOMA")
    print("Your AI-powered training companion with secure session tracking")

    email, user = get_valid_email()

    if not user:
        print("No user found. Let's create your profile!")
        name = get_valid_name()
        phone = get_valid_phone()
        try:
            register_user(name, phone, email)
            user = get_user(email)
            print("\nLETS GET STARTED WITH VYOMA!")
        except ValueError as e:
            print(e)
            return  # Exit if email is invalid

    user_id = user[0]

    while True:
        choice = get_valid_menu_choice()

        if choice == "1":
            record_training(user_id)
        elif choice == "2":
            view_history(user_id)
        elif choice == "3":
            start_today_session(user_id)
        elif choice == "4":
            print("Goodbye!")
            break

if __name__ == "__main__":
    main()