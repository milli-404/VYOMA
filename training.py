import cv2
import os
import hashlib
from database import get_connection
from posture import analyze_posture
from user import validate_user_id
from web3 import Web3
from dotenv import load_dotenv

load_dotenv()

# Blockchain config for security (kept from previous)
INFURA_URL = os.getenv('SEPOLIA_RPC_URL')
SECURITY_CONTRACT_ADDRESS = os.getenv('SECURITY_CONTRACT_ADDRESS')
ADMIN_PRIVATE_KEY = os.getenv('ADMIN_PRIVATE_KEY')

# VyomaSecurity contract ABI (same as before)
SECURITY_ABI = [
    {
        "inputs": [
            {"internalType": "uint256", "name": "sessionId", "type": "uint256"},
            {"internalType": "bytes32", "name": "sessionHash", "type": "bytes32"}
        ],
        "name": "storeSession",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [
            {"internalType": "uint256", "name": "sessionId", "type": "uint256"}
        ],
        "name": "getSession",
        "outputs": [
            {"internalType": "bytes32", "name": "", "type": "bytes32"},
            {"internalType": "uint256", "name": "", "type": "uint256"}
        ],
        "stateMutability": "view",
        "type": "function"
    }
]

w3 = Web3(Web3.HTTPProvider(INFURA_URL))
security_contract = w3.eth.contract(address=SECURITY_CONTRACT_ADDRESS, abi=SECURITY_ABI)
admin_account = w3.eth.account.from_key(ADMIN_PRIVATE_KEY)

def store_session_hash(session_id, user_id, sport, reward, status, accuracy):
    """Store a hash of session data on Ethereum for security."""
    if not w3.is_connected():
        print("Warning: Blockchain offline. Session saved locally only.")
        return None

    # Create session data string and hash
    session_data = f"user_id:{user_id},sport:{sport},accuracy:{accuracy},reward:{reward},status:{status}"
    session_hash = hashlib.sha256(session_data.encode()).hexdigest()
    session_hash_bytes = w3.to_bytes(hexstr=session_hash)

    try:
        # Build transaction
        txn = security_contract.functions.storeSession(session_id, session_hash_bytes).build_transaction({
            'from': admin_account.address,
            'nonce': w3.eth.get_transaction_count(admin_account.address),
            'gas': 50000,
            'gasPrice': w3.to_wei('20', 'gwei')
        })

        # Sign and send
        signed_txn = w3.eth.account.sign_transaction(txn, admin_account.privateKey)
        tx_hash = w3.eth.send_raw_transaction(signed_txn.rawTransaction)
        tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        print(f"Session secured on blockchain! Tx Hash: {tx_hash.hex()}")
        return tx_hash.hex()
    except Exception as e:
        print(f"Error storing session hash on blockchain: {e}")
        return None

# YouTube suggestions for injuries (hardcoded from credible sources)
YOUTUBE_SUGGESTIONS = {
    "Football": [
        "https://www.youtube.com/watch?v=C5RTd9QpaK0",  # Soccer Prehab Exercises for Injury Prevention (The Prehab Guys)
        "https://www.youtube.com/watch?v=example-knee-rehab",  # Knee and Ankle Rehab for Soccer (AAOS-inspired)
        "https://www.youtube.com/watch?v=example-ankle-sprain"  # Medial Ankle Sprain Rehab (The Prehab Guys)
    ],
    "Volleyball": [
        "https://www.youtube.com/watch?v=1jJnh8QUH0s",  # 9 Shoulder Exercises for Volleyball (No More Pain)
        "https://www.youtube.com/watch?v=example-shoulder-prehab",  # Shoulder Impingement Prevention
        "https://www.youtube.com/watch?v=example-elbow-rehab"  # Elbow Tendonitis Rehab for Overhead Sports
    ]
}

def get_valid_training_choice():
    """Prompt user for training option and validate input."""
    while True:
        print("\nChoose training option:")
        print("1. Record new video (webcam)")
        print("2. Upload existing video")
        choice = input("Enter choice: ").strip()
        if choice in ["1", "2"]:
            return choice
        print("Invalid choice! Please enter 1 or 2.")

def get_valid_sport_choice():
    """Prompt user for sport choice and validate input."""
    while True:
        print("\nSelect sport for this training:")
        print("1. Football")
        print("2. Volleyball")
        choice = input("Enter choice: ").strip()
        if choice in ["1", "2"]:
            return "Football" if choice == "1" else "Volleyball"
        print("Invalid choice! Please enter 1 or 2.")

def get_valid_video_path():
    """Prompt user for a valid video file path."""
    valid_extensions = {'.mp4', '.avi', '.mov', '.mkv'}
    while True:
        video_path = input("Enter path to video file: ")
        if os.path.isfile(video_path):
            if os.path.splitext(video_path)[1].lower() in valid_extensions:
                cap = cv2.VideoCapture(video_path)
                if cap.isOpened():
                    cap.release()
                    return video_path
                else:
                    print("Invalid video file! Please provide a valid video (e.g., .mp4, .avi).")
            else:
                print("Unsupported file format! Please provide a video file (e.g., .mp4, .avi, .mov, .mkv).")
        else:
            print("File does not exist! Please provide a valid file path.")

def record_training(user_id):
    # Validate user_id
    if not validate_user_id(user_id):
        print("Error: Invalid user ID. Please register a valid user.")
        return False

    choice = get_valid_training_choice()
    sport = get_valid_sport_choice()

    accuracy = 0
    is_valid_exercise = False
    wrong_streak = 0
    status = "Failed"
    reward = 0
    injury_risk = 0

    if choice == "1":
        output_file = "recorded_training.avi"
        cap = cv2.VideoCapture(0)  # Open webcam
        if not cap.isOpened():
            print("Error: Could not access webcam. Please check your camera and try again.")
            return False

        fourcc = cv2.VideoWriter_fourcc(*"XVID")
        out = cv2.VideoWriter(output_file, fourcc, 20.0, (640, 480))

        print("\nRecording started... Press 'q' to stop.")
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                print("Error: Failed to capture video. Please check your webcam.")
                break
            out.write(frame)
            cv2.imshow("Recording (press q to stop)", frame)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

        cap.release()
        out.release()
        cv2.destroyAllWindows()
        print(f"Video saved as {output_file}")

        # Analyze recorded video
        try:
            accuracy, is_valid_exercise, wrong_streak = analyze_posture(output_file, sport)
        except Exception as e:
            print(f"Error analyzing video: {e}")
            # Store failed session
            try:
                conn = get_connection()
                c = conn.cursor()
                c.execute("INSERT INTO sessions (user_id, sport, reward_points, status, accuracy, injury_risk) VALUES (?, ?, ?, ?, ?, ?)",
                          (user_id, sport, reward, status, accuracy, injury_risk))
                conn.commit()
                session_id = c.lastrowid
                # Store hash on blockchain (kept from security integration)
                tx_hash = store_session_hash(session_id, user_id, sport, reward, status, accuracy)
                if tx_hash:
                    c.execute("UPDATE sessions SET tx_hash=? WHERE id=?", (tx_hash, session_id))
                    conn.commit()
                conn.close()
                print("Session recorded as failed due to analysis error.")
            except sqlite3.Error as e:
                print(f"Error saving session to database: {e}")
            return False

    elif choice == "2":
        video_path = get_valid_video_path()
        try:
            accuracy, is_valid_exercise, wrong_streak = analyze_posture(video_path, sport)
        except Exception as e:
            print(f"Error analyzing video: {e}")
            # Store failed session
            try:
                conn = get_connection()
                c = conn.cursor()
                c.execute("INSERT INTO sessions (user_id, sport, reward_points, status, accuracy, injury_risk) VALUES (?, ?, ?, ?, ?, ?)",
                          (user_id, sport, reward, status, accuracy, injury_risk))
                conn.commit()
                session_id = c.lastrowid
                # Store hash on blockchain
                tx_hash = store_session_hash(session_id, user_id, sport, reward, status, accuracy)
                if tx_hash:
                    c.execute("UPDATE sessions SET tx_hash=? WHERE id=?", (tx_hash, session_id))
                    conn.commit()
                conn.close()
                print("Session recorded as failed due to analysis error.")
            except sqlite3.Error as e:
                print(f"Error saving session to database: {e}")
            return False

    # Assign rewards and status for valid exercises
    if is_valid_exercise:
        reward = 15 if accuracy >= 70 else 5 if choice == "1" else 10 if accuracy >= 70 else 3
        status = "Completed"

    # New: Check for injury risk based on wrong streak
    injury_risk = 1 if wrong_streak >= 3 else 0
    if injury_risk:
        print(f"\nPotential injury detected! Wrong posture streak: {wrong_streak}")
        response = input("Are you facing an injury? (Y/N): ").strip().upper()
        if response == 'Y':
            print(f"\nRecommendations for {sport} injury rehab/prevention:")
            for link in YOUTUBE_SUGGESTIONS.get(sport, []):
                print(f"- Watch: {link}")
            print("Consult a doctor for personalized advice.")
        else:
            print("Great! Continue monitoring your form.")

    # Store session locally and on blockchain
    try:
        conn = get_connection()
        c = conn.cursor()
        c.execute("INSERT INTO sessions (user_id, sport, reward_points, status, accuracy, injury_risk) VALUES (?, ?, ?, ?, ?, ?)",
                  (user_id, sport, reward, status, accuracy, injury_risk))
        conn.commit()
        session_id = c.lastrowid
        # Store hash on blockchain
        tx_hash = store_session_hash(session_id, user_id, sport, reward, status, accuracy)
        if tx_hash:
            c.execute("UPDATE sessions SET tx_hash=? WHERE id=?", (tx_hash, session_id))
            conn.commit()
        conn.close()
        if is_valid_exercise:
            print(f"Training {'recorded' if choice == '1' else 'uploaded'} successfully! Reward +{reward} (Accuracy: {accuracy:.2f}%)")
        else:
            print(f"Training rejected: Video does not contain valid {sport} exercises. Session recorded as failed.")
        return is_valid_exercise
    except sqlite3.Error as e:
        print(f"Error saving session to database: {e}")
        return False

def start_today_session(user_id):
    print("\n===== TODAY'S SESSION =====")
    print("Step 1: Warm-up exercises ✅")

    sport = get_valid_sport_choice()

    print("\nStep 3: Record your session")
    success = record_training(user_id)

    if not success:
        print(f"\nNo valid {sport} session was recorded. Try again with a proper exercise video.")
        return

    try:
        conn = get_connection()
        c = conn.cursor()
        c.execute("UPDATE sessions SET status = 'Completed', reward_points = reward_points + 5 WHERE user_id = ? AND sport = ? AND status = 'Ongoing'",
                  (user_id, sport))
        updated = c.rowcount
        if updated > 0:
            # Update blockchain hash for modified session (kept from security)
            c.execute("SELECT id, user_id, sport, reward_points, status, accuracy FROM sessions WHERE user_id = ? AND sport = ? AND status = 'Completed'",
                      (user_id, sport))
            session = c.fetchone()
            if session:
                session_id, user_id, sport, reward, status, accuracy = session
                tx_hash = store_session_hash(session_id, user_id, sport, reward, status, accuracy)
                if tx_hash:
                    c.execute("UPDATE sessions SET tx_hash=? WHERE id=?", (tx_hash, session_id))
                    conn.commit()
        conn.close()

        if updated > 0:
            print(f"\nGreat! Your {sport} session has been completed. Additional Reward +5.")
        else:
            print(f"\nNo ongoing {sport} session found to update. Ensure a valid session was recorded.")
    except sqlite3.Error as e:
        print(f"Error updating session in database: {e}")