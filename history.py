from database import get_connection
from user import validate_user_id
from web3 import Web3
import os
import hashlib
from dotenv import load_dotenv

load_dotenv()

# Blockchain config
INFURA_URL = os.getenv('SEPOLIA_RPC_URL')
SECURITY_CONTRACT_ADDRESS = os.getenv('SECURITY_CONTRACT_ADDRESS')
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

def verify_session_hash(session_id, user_id, sport, reward, status, accuracy):
    """Verify local session data against blockchain hash."""
    if not w3.is_connected():
        return False, "Blockchain offline"
    try:
        session_data = f"user_id:{user_id},sport:{sport},accuracy:{accuracy},reward:{reward},status:{status}"
        local_hash = hashlib.sha256(session_data.encode()).hexdigest()
        onchain_hash, _ = security_contract.functions.getSession(session_id).call()
        return local_hash == w3.to_hex(onchain_hash), "Verified" if local_hash == w3.to_hex(onchain_hash) else "Tampered"
    except Exception as e:
        return False, f"Error verifying: {e}"

def view_history(user_id):
    try:
        if not validate_user_id(user_id):
            print(f"Error: Invalid user ID {user_id}. Please register a valid user.")
            return

        conn = get_connection()
        c = conn.cursor()
        c.execute("SELECT id, sport, reward_points, status, accuracy, tx_hash, injury_risk FROM sessions WHERE user_id=?", (user_id,))
        sessions = c.fetchall()
        conn.close()

        print(f"\n===== SESSION HISTORY for User ID {user_id} =====")
        if not sessions:
            print("No sessions found. Try recording a session (Main Menu option 1) or starting today’s session (option 3).")
            return

        completed_sessions = [s for s in sessions if s[3] == "Completed"]
        failed_sessions = [s for s in sessions if s[3] == "Failed"]
        injury_sessions = [s for s in sessions if s[6] == 1]  # injury_risk

        print(f"\nTotal Sessions: {len(sessions)} (Completed: {len(completed_sessions)}, Failed: {len(failed_sessions)}, Injury Flagged: {len(injury_sessions)})")
        total_rewards = 0
        for s in sessions:
            session_id, sport, reward, status, accuracy, tx_hash, injury_risk = s
            accuracy_display = f"{accuracy:.2f}%" if accuracy is not None else "N/A"
            verified, status_msg = verify_session_hash(session_id, user_id, sport, reward, status, accuracy) if tx_hash else (False, "No blockchain record")
            injury_flag = "Yes" if injury_risk else "No"
            print(f"Session ID: {session_id} | Sport: {sport} | Reward: {reward} | Status: {status} | Accuracy: {accuracy_display} | Injury Risk: {injury_flag} | Tx Hash: {tx_hash or 'N/A'} | Verified: {status_msg}")
            total_rewards += reward

        print(f"\nTotal Rewards Earned: {total_rewards}")
    except sqlite3.Error as e:
        print(f"Error retrieving session history: {e}")