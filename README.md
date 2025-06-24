# Bug Reporting Agent - ADK Implementation

A compassionate and professional bug reporting assistant built with Google's Agent Development Kit (ADK). This agent helps users report technical issues while providing emotional support and maintaining persistent storage of bug reports across sessions.

## Features

- **Empathetic Issue Handling**: Recognizes when users mention problems and provides emotional support
- **Structured Bug Reporting**: Collects only essential details that match the incidents table schema
- **Persistent Storage**: Uses SQLite database to store incidents in dedicated `incidents` table
- **Four Bug Categories**: Software, Platform, Account, and Other
- **Multi-turn Conversations**: Guides users through the bug reporting process step by step
- **Professional UI**: Color-coded terminal interface with clear state display
- **Tabular Display**: Always presents bug reports in clean, formatted tables with appropriate headers
- **Smart Date Parsing**: Uses `python-dateutil` library for robust date parsing - handles relative dates ("yesterday", "3 days ago", "last Monday") and various date formats
- **Focused Questions**: Only asks for information that's actually stored in the database

## Project Structure

```
bug-reporting-agent/
│
├── bug_reporting_agent/        # Agent package
│   ├── __init__.py            # Package initialization
│   └── agent.py               # Main agent implementation with tools
│
├── main.py                    # Application entry point
├── utils.py                   # Utility functions for UI and agent interaction
├── requirements.txt           # Python dependencies
├── bug_reports.db            # SQLite database (created on first run)
└── README.md                 # This documentation
```

## Key Components

### 1. Bug Reporting Agent (bug_reporting_agent/agent.py)

The main agent with specialized tools for bug reporting:

- **create_bug_report()**: Creates new bug reports with validation
- **view_bug_reports()**: Displays all user's bug reports
- **update_bug_status()**: Updates status of existing bug reports
- **update_user_info()**: Manages user contact information

### 2. Bug Categories

Users must choose from these four categories:

- **Software**: Application bugs, crashes, features not working, UI issues
- **Platform**: Infrastructure, server, performance issues, system outages
- **Account**: Login issues, permissions, user account related problems
- **Other**: Hardware issues, general questions, anything else

### 3. Persistent Storage

Uses ADK's `DatabaseSessionService` with SQLite to maintain:
- User contact information (name, email)
- Complete bug report history
- Session continuity across application restarts

## Installation & Setup

### Prerequisites

- Python 3.9+
- Google API Key for Gemini models
- SQLite (included with Python)

### Installation

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up environment variables**:
   Create a `.env` file with your Google API key:
   ```
   GOOGLE_API_KEY=your_google_api_key_here
   ```

### Running the Agent

```bash
python main.py
```

The agent will:
1. Connect to the SQLite database (or create it if it doesn't exist)
2. Check for previous sessions for the user
3. Start an interactive conversation
4. Save all interactions and bug reports to the database

## Usage Examples

### First Time User

```
🐛 Welcome to Bug Reporting Agent! 🐛
You: Hi, I'm having issues with the login page

Agent: I'm sorry to hear you're experiencing issues with the login page. That must be frustrating! 
Let me help you create a proper bug report so our team can address this.

First, could you please tell me your name and email address so I can properly track this issue?

You: My name is John Smith and my email is john@example.com

Agent: Thank you, John! I've updated your contact information. Now, let's gather some details about the login issue.

Which category best describes this issue?
1. Software (application bugs, crashes, features not working)  
2. Platform (infrastructure, server, performance issues)
3. Account (login, permissions, user account related)
4. Other (anything that doesn't fit the above categories)

You: Account

Agent: Perfect! Could you please provide a detailed description of the login issue you're experiencing?

You: I can't log in to my account. It says invalid credentials even though I'm sure my password is correct.

Agent: Thank you for the details. When did you first notice this issue?

You: Yesterday morning around 9 AM

Agent: Bug report BUG-0001 has been created successfully! I've recorded your account issue and will ensure it gets proper attention.
```

### Returning User

```
You: What bug reports do I have?

Agent: Here are your current bug reports, John:

🐛 Bug Reports:
1. [BUG-0001] 🔴 Account: Can't log in - invalid credentials error
   - Reported: 2024-01-15
   - Status: Open

You: Can you update the status of BUG-0001 to In Progress?

Agent: Updated bug report BUG-0001 status from 'Open' to 'In Progress'
```

## Smart Date Handling

The agent uses the robust `python-dateutil` library for intelligent date parsing and asks for clarification when needed:

### ✅ Automatically Accepted Formats

- **Relative dates**: "yesterday", "today", "3 days ago", "2 weeks ago", "last week"
- **Specific dates**: "2024-01-15", "01/15/2024", "15-01-2024", "Jan 15, 2024"
- **Weekday references**: "last Monday", "last Friday"
- **Natural language**: "Dec 16", "January 1st", "15th of December"

### ❓ Requires Clarification

- **Vague expressions**: "last month", "recently", "a while ago", "long time ago"
- **Agent response**: "Could you give me a specific date when you first noticed this issue?"

### 🔧 Key Features

- **Accurate calculations**: "last week" correctly returns last Monday (e.g., if today is Dec 23, "last week" = Dec 16)
- **International formats**: Handles various date formats automatically
- **Error prevention**: Prevents future date parsing errors
- **Library-powered**: Uses `python-dateutil` instead of custom parsing logic

### Example Date Interactions

```
User: "I've been having this issue since yesterday"
Agent: ✅ Automatically converts to: 2024-01-23

User: "This started last month"  
Agent: ❓ "You mentioned 'last month' - could you give me a specific date 
         when you first noticed this issue?"

User: "It happened 5 days ago"
Agent: ✅ Automatically converts to: 2024-01-19
```

## Agent Personality & Approach

The agent is designed to be:

- **Empathetic**: Always acknowledges user frustration and provides emotional support
- **Professional**: Maintains a helpful, solution-focused approach
- **Patient**: Guides users through the process without overwhelming them
- **Reassuring**: Confirms that issues will be properly tracked and addressed

### Sample Empathetic Responses

- "I'm sorry to hear you're experiencing this issue. That must be frustrating!"
- "I understand how annoying technical problems can be. Don't worry - I'll make sure your issue gets the attention it deserves."
- "Thank you for bringing this to my attention. Let's get this documented properly so we can get it resolved for you."

## Technical Implementation

### ADK Best Practices Implemented

1. **Persistent Storage**: Uses `DatabaseSessionService` for long-term memory
2. **State Management**: Proper session handling with state persistence
3. **Tool Context**: Uses `ToolContext` for accessing and updating session state
4. **Error Handling**: Validates inputs and provides helpful error messages
5. **User Experience**: Color-coded terminal UI with clear state display

### Database Schema

The agent automatically creates the necessary database tables. Bug reports are stored with:

```json
{
  "id": "BUG-0001",
  "category": "Software",
  "description": "Button not responding on checkout page",
  "date_observed": "2024-01-15",
  "date_created": "2024-01-15T10:30:00",
  "status": "Open",
  "last_updated": "2024-01-15T10:30:00"
}
```

## Extending the Agent

### Adding New Bug Categories

Modify the `valid_categories` list in `create_bug_report()` function:

```python
valid_categories = ["Software", "Platform", "Account", "Other", "New Category"]
```

### Adding New Bug Statuses

Update the `valid_statuses` list in `update_bug_status()` function:

```python
valid_statuses = ["Open", "In Progress", "Resolved", "Closed", "New Status"]
```

### Production Deployment

For production use:

1. **Database**: Replace SQLite with PostgreSQL or MySQL
2. **Security**: Implement proper authentication and authorization
3. **Monitoring**: Add logging and monitoring capabilities
4. **Scaling**: Use ADK's production deployment features

## Troubleshooting

### Common Issues

1. **Database Connection Error**: Ensure SQLite permissions are correct
2. **API Key Issues**: Verify your Google API key is set correctly in `.env`
3. **Import Errors**: Make sure all dependencies are installed with `pip install -r requirements.txt`

### Debug Mode

To enable debug output, modify the `process_agent_response()` function in `utils.py` to show more detailed event information.

## Contributing

This implementation follows ADK best practices and can be extended for more complex bug tracking workflows. Feel free to customize the agent's personality, add new tools, or integrate with external bug tracking systems.

## References

- [Google ADK Documentation](https://google.github.io/adk-docs/)
- [ADK Persistent Storage Example](https://github.com/amribhatt/agent-development-kit-crash-course/tree/main/6-persistent-storage)
- [ADK Sessions and State Management](https://google.github.io/adk-docs/sessions/state/) 