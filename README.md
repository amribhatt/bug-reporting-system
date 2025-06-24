# Enhanced Bug Reporting System with Guard Agent

An intelligent bug reporting system built with the Google Agent Development Kit (ADK), featuring an independent Guard Agent for input classification and A2A protocol integration.

## 🚀 New Features

### Guard Agent
- **Independent Guard Agent** that classifies user inputs into 5 severity levels
- **Real-time classification** with confidence scoring and reasoning
- **Escalation pattern detection** for identifying concerning trends
- **A2A protocol integration** for agent-to-agent communication

### Enhanced Database
- **Level tracking** - All bug reports now include severity levels (1-5)
- **Backward compatibility** - Existing functionality maintained
- **Automatic level assignment** from Guard Agent classifications

### A2A Protocol Support
- **Basic A2A implementation** via callbacks and event bus
- **Cross-agent communication** between Guard Agent and Bug Reporting Agent
- **Event tracking** and metrics collection
- **Escalation alerts** for high-priority issues

## 📊 Classification Levels

The Guard Agent classifies user inputs into these 5 levels:

| Level | Description | Examples |
|-------|-------------|----------|
| **Level 1** | Simple FAQ questions (how-to, information requests) | "How do I reset my password?" |
| **Level 2** | Common technical/account issues (crashes, login problems) | "App keeps crashing on login" |
| **Level 3** | Unstructured but solvable problems (save corruption, gameplay issues) | "Game save file corrupted" |
| **Level 4** | Security/fraud issues (hacking, stolen items) | "Account compromised" |
| **Level 5** | Critical emergencies (doxxing, legal issues, server outages) | "Server completely down" |

## 🏗️ Architecture

```
┌─────────────────┐    A2A Protocol    ┌─────────────────────┐
│   Guard Agent   │◄──────────────────►│ Bug Reporting Agent │
│                 │                    │                     │
│ - Classification│                    │ - Bug Reports       │
│ - Escalation    │                    │ - User Management   │
│ - A2A Events    │                    │ - Database Storage  │
└─────────────────┘                    └─────────────────────┘
         │                                        │
         ▼                                        ▼
┌─────────────────┐                    ┌─────────────────────┐
│ A2A Event Bus   │                    │ Enhanced Database   │
│                 │                    │                     │
│ - Event History │                    │ - Level Column      │
│ - Subscriptions │                    │ - Backward Compat   │
│ - Metrics       │                    │ - SQLite Storage    │
└─────────────────┘                    └─────────────────────┘
```

## 🛠️ Components

### Guard Agent (`guard_agent/`)
- **`agent.py`** - Main Guard Agent with classification tools
- **`__init__.py`** - Module initialization

### Bug Reporting Agent (`bug_reporting_agent/`)
- **`agent.py`** - Enhanced to integrate with Guard Agent levels
- **Unchanged functionality** - All existing features preserved

### Database (`database.py`)
- **Enhanced schema** with `level` column
- **Automatic migration** for existing databases
- **Level parameter** in `create_incident()` method

### A2A Integration (`a2a_integration.py`)
- **Event bus** for agent communication
- **Callback system** for real-time notifications
- **Metrics tracking** for monitoring
- **Agent registry** for protocol management

### Configuration (`config.py`)
- **Level definitions** and descriptions
- **Guard Agent settings**
- **A2A protocol configuration**

## 🔧 Usage

### Running the Enhanced System

```bash
# Start the main application (existing functionality)
python main.py

# The Guard Agent will automatically classify user inputs
# Bug reports will include severity levels from Guard Agent
```

### Guard Agent Classification

The Guard Agent automatically:
1. **Analyzes** user input using keyword and pattern matching
2. **Assigns** appropriate severity level (1-5)
3. **Provides** confidence score and reasoning
4. **Monitors** for escalation patterns
5. **Communicates** with Bug Reporting Agent via A2A protocol

### A2A Protocol Events

The system generates these A2A events:
- **`classification_complete`** - When Guard Agent classifies input
- **`bug_report_created`** - When Bug Reporting Agent creates report
- **`escalation_detected`** - When escalation pattern identified
- **`metrics_update`** - Periodic metrics updates

## 📁 Enhanced Database Schema

```sql
CREATE TABLE incidents (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    user_name TEXT,
    user_email TEXT,
    category TEXT NOT NULL,
    description TEXT NOT NULL,
    date_observed TEXT NOT NULL,
    date_created TEXT NOT NULL,
    status TEXT DEFAULT 'Open',
    level INTEGER DEFAULT 2,  -- NEW: Severity level 1-5
    last_updated TEXT,
    FOREIGN KEY (user_id) REFERENCES sessions(user_id)
);
```

## 🔄 Integration Workflow

1. **User Input** → Guard Agent receives and analyzes
2. **Classification** → Guard Agent assigns level and confidence
3. **A2A Event** → Classification result sent via A2A protocol
4. **Bug Report** → Bug Reporting Agent creates report with level
5. **Confirmation** → Bug Reporting Agent confirms via A2A protocol
6. **Monitoring** → Guard Agent tracks patterns for escalation

## 🎯 Key Features Maintained

- ✅ **Bug Reporting Agent unchanged** - All existing functionality preserved
- ✅ **Database compatibility** - Existing data unaffected
- ✅ **User experience** - Same interface and workflows
- ✅ **Configuration** - Existing settings maintained

## 🎯 Key Features Added

- ✅ **Independent Guard Agent** - Separate classification service
- ✅ **5-level classification** - Intelligent input categorization
- ✅ **Enhanced database** - Level tracking in incidents table
- ✅ **A2A protocol** - Basic agent-to-agent communication
- ✅ **Escalation detection** - Pattern recognition for urgent issues
- ✅ **Real-time communication** - Event-driven architecture

## 📝 Requirements

```
google-adk>=1.0.0
python-dotenv>=1.0.0
python-dateutil>=2.8.2
```

## 🚀 Future Enhancements

- **Advanced A2A protocol** - Full compliance with Agent2Agent specification
- **Machine learning classification** - Improve accuracy over time
- **Human-in-the-loop** - Manual review for high-level issues
- **Integration APIs** - REST endpoints for external systems
- **Dashboard** - Real-time monitoring and analytics

---

*Built with Google Agent Development Kit (ADK) and enhanced with independent Guard Agent for intelligent input classification and A2A protocol integration.* 