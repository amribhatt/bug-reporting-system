import asyncio

from dotenv import load_dotenv
from google.adk.runners import Runner
from google.adk.sessions import DatabaseSessionService
from bug_reporting_agent.agent import bug_reporting_agent
from utils import call_agent_async
from config import get_database_name, get_default_user_id, AGENT_CONFIG

load_dotenv()

# ===== PART 1: Initialize Persistent Session Service =====
# Using SQLite database for persistent storage
db_url = f"sqlite:///./{get_database_name()}"
session_service = DatabaseSessionService(db_url=db_url)


# ===== PART 2: Define Initial State =====
# This will only be used when creating a new session
initial_state = {
    "user_name": "",
    "user_email": "",
    "bug_reports": [],
    "_user_id": "",  # Will be set during session creation
}


async def main_async():
    # Setup constants from config
    APP_NAME = "Bug Reporting Agent"
    USER_ID = get_default_user_id()

    # ===== PART 3: Session Management - Find or Create =====
    # Check for existing sessions for this user
    existing_sessions = await session_service.list_sessions(
        app_name=APP_NAME,
        user_id=USER_ID,
    )

    # If there's an existing session, use it, otherwise create a new one
    if existing_sessions and len(existing_sessions.sessions) > 0:
        # Use the most recent session
        SESSION_ID = existing_sessions.sessions[0].id
        print(f"Continuing existing session: {SESSION_ID}")
    else:
        # Create a new session with initial state
        initial_state["_user_id"] = USER_ID  # Store user_id in state
        new_session = await session_service.create_session(
            app_name=APP_NAME,
            user_id=USER_ID,
            state=initial_state,
        )
        SESSION_ID = new_session.id
        print(f"Created new session: {SESSION_ID}")
    
    # Ensure user_id is stored in existing session state as well
    if existing_sessions and len(existing_sessions.sessions) > 0:
        session = await session_service.get_session(
            app_name=APP_NAME, user_id=USER_ID, session_id=SESSION_ID
        )
        if session and "_user_id" not in session.state:
            session.state["_user_id"] = USER_ID
            # Session state will be automatically updated during conversation

    # ===== PART 4: Agent Runner Setup =====
    # Create a runner with the bug reporting agent
    runner = Runner(
        agent=bug_reporting_agent,
        app_name=APP_NAME,
        session_service=session_service,
    )

    # ===== PART 5: Interactive Conversation Loop =====
    print("\n🐛 Welcome to Bug Reporting Agent! 🐛")
    print("I'm here to help you report any technical issues you're experiencing.")
    print("Just tell me about any problems you're having, and I'll help create a proper bug report.")
    print("Type 'exit' or 'quit' to end the conversation.\n")

    while True:
        # Get user input
        user_input = input("You: ")

        # Check if user wants to exit
        if user_input.lower() in ["exit", "quit"]:
            print("Thank you for using Bug Reporting Agent! Your reports have been saved.")
            print("Feel free to come back anytime if you encounter more issues.")
            break

        # Process the user query through the agent
        await call_agent_async(runner, USER_ID, SESSION_ID, user_input)


if __name__ == "__main__":
    asyncio.run(main_async()) 