# Bug Reporting System with A2A Protocol Integration

A sophisticated bug reporting system with intelligent duplicate detection, status management, and A2A protocol compliance for seamless agent-to-agent communication.

## 🚀 **Quick Start Guide**

### **Prerequisites**

- **Python 3.11+** (Recommended: Python 3.13)
- **Git** for cloning the repository
- **Google AI API Key** for LLM functionality
- **Email Account** (optional, for notifications)

---

## 📥 **Step 1: Clone and Setup**

### **1.1 Clone the Repository**

```bash
# Clone the entire examples repository
git clone <repository-url>
cd bug_reporting_system

# Or if you only want this specific system
# Navigate to the bug_reporting_system folder
```

**⚠️ Important:** Make sure you're in the `bug_reporting_system` directory before proceeding. Your terminal should show:
```
your-path/examples/bug_reporting_system>
```

### **1.2 Create Virtual Environment**

#### **On Windows (PowerShell):**
```powershell
# Create virtual environment
python -m venv .venv

# Activate virtual environment  
.\.venv\Scripts\activate

# Verify activation (should show (.venv) in prompt)
```

#### **On macOS/Linux:**
```bash
# Create virtual environment
python -m venv .venv

# Activate virtual environment
source .venv/bin/activate

# Verify activation (should show (.venv) in prompt)
```

### **1.3 Install Dependencies**

```bash
# Upgrade pip first
pip install --upgrade pip

# Install all required packages
pip install -r requirements.txt
```

---

## ⚙️ **Step 2: Configuration Setup**

### **2.1 Create Environment File**

#### **On Windows (PowerShell):**
```powershell
# Copy the example configuration
copy env_config.example .env

# Or use the interactive setup
python setup_env.py
```

#### **On macOS/Linux:**
```bash
# Copy the example configuration
cp env_config.example .env

# Or use the interactive setup
python setup_env.py
```

### **2.2 Required Configuration**

Edit your `.env` file with the following **required** settings:

```bash
# REQUIRED: Google AI API Key
GOOGLE_API_KEY=your_actual_google_api_key_here

# REQUIRED: User Information  
USER_ID=user001
USER_NAME=Your Name
USER_EMAIL=your.email@example.com

# OPTIONAL: Email Notifications (leave disabled if not needed)
EMAIL_ENABLED=false
EMAIL_USER=your-notifications@example.com
EMAIL_PASSWORD=your_secure_app_password
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SUPPORT_EMAIL=support@example.com

# OPTIONAL: A2A Protocol Settings
A2A_PORT=10001
A2A_HOST=localhost
```

### **2.3 Get Google AI API Key**

1. Go to [Google AI Studio](https://aistudio.google.com/app/apikey)
2. Click **"Create API Key"**
3. Copy the generated key
4. Add it to your `.env` file as `GOOGLE_API_KEY=your_key_here`

---

## 🚀 **Step 3: Running the System**

### **3.1 Quick Test Run**

```bash
# Test if everything is configured correctly
python run.py
```

### **3.2 Production Run**

```bash
# Start the bug reporting system
python main.py

# Or use the production wrapper (recommended)
python run.py
```

### **3.3 Expected Output**

You should see output like:
```
✅ Bug Reporting Agent callbacks configured
🚀 A2A Protocol server starting on http://localhost:10001
📋 Bug Reporting System ready for connections
💬 Chat interface available
```

---

## 💬 **Step 4: Using the System**

### **4.1 Reporting a Bug**

Simply start describing your issue:

```
"My login keeps failing"
"The app crashes when I click save" 
"I cannot reset my password"
```

### **4.2 Managing Bug Reports**

```
# View your reports
"show my bug reports"
"list my bugs"

# Update status
"resolve BUG-00001"
"mark BUG-00002 as closed"
"update status of BUG-00003 to in progress"
```

### **4.3 Available Categories**

- **UI:** Interface problems, layout issues, visual bugs
- **Performance:** Slow loading, crashes, freezing
- **Functionality:** Features not working as expected
- **Security:** Login issues, permissions, unauthorized access
- **Account:** Profile problems, settings, user data
- **Data:** Information missing, incorrect, or corrupted
- **Other:** General issues that don't fit other categories

### **4.4 Status Options**

- **Open:** New issues (default)
- **In Progress:** Being actively worked on
- **Resolved:** Fixed or addressed
- **Closed:** Resolved and verified/no longer relevant

---

## 🔧 **Advanced Configuration**

### **Email Notifications Setup**

If you want email alerts for repeated issues:

1. **Enable email in `.env`:**
   ```bash
   EMAIL_ENABLED=true
   EMAIL_USER=your-notifications@gmail.com
   EMAIL_PASSWORD=your_app_password  # Use App Password, not regular password
   SUPPORT_EMAIL=your-support@company.com
   ```

2. **For Gmail users:**
   - Enable 2-Factor Authentication
   - Generate an App Password
   - Use the App Password in `EMAIL_PASSWORD`

3. **See [EMAIL_SETUP_GUIDE.md](EMAIL_SETUP_GUIDE.md) for detailed instructions**

### **A2A Protocol Integration**

The system supports A2A (Agent-to-Agent) protocol for integration with other AI agents:

- **Default endpoint:** `http://localhost:10001`
- **Agent card:** `http://localhost:10001/.well-known/agent.json`
- **Change port:** Set `A2A_PORT=8080` in `.env`

---

## 🧪 **Testing the System**

### **Test Basic Functionality**

```bash
# Test duplicate detection
User: "I cannot login to my account"
System: [Creates new bug report]

User: "I am unable to login"  
System: [Detects 85% similarity, offers options]

# Test status updates
User: "resolve BUG-00001"
System: [Updates status with confirmation]

# Test viewing reports
User: "show my reports"
System: [Lists all your bug reports]
```

### **Expected Behavior**

✅ **Smart Duplicate Detection:** Similar issues get flagged  
✅ **Status Management:** Easy status updates with validation  
✅ **User Isolation:** You only see your own reports  
✅ **Professional Responses:** Clear, helpful messaging  
✅ **Bypass Logic:** Status updates skip duplicate checks  

---

## 📁 **Project Structure**

```
bug_reporting_system/
├── main.py                     # Main application entry point
├── run.py                      # Production wrapper with error handling
├── config.py                   # Centralized configuration management
├── database.py                 # SQLite database operations
├── utils.py                    # Utility functions and helpers
├── a2a_integration.py          # A2A protocol implementation
├── bug_reporting_agent/        # Main agent logic
│   ├── __init__.py
│   └── agent.py               # Core bug reporting functionality
├── guard_agent/               # Security and validation layer
│   ├── __init__.py
│   ├── agent.py              # Guard agent coordination
│   └── tools/                # Specialized analysis tools
│       ├── __init__.py
│       ├── duplicate_detection_tool.py
│       ├── level_assignment_tool.py
│       ├── analysis_tools.py
│       └── support_email_tool.py
├── requirements.txt           # Python dependencies
├── env_config.example        # Configuration template
├── .env                      # Your configuration (not in git)
├── bug_reports.db           # SQLite database (auto-created)
└── README.md               # This file
```

---

## 🛡️ **Security Features**

- **Input Validation:** All user inputs are sanitized and validated
- **SQL Injection Protection:** Parameterized queries throughout
- **Rate Limiting:** Prevents email spam (3 emails/user/hour)
- **User Isolation:** Users can only access their own data
- **Secure Configuration:** No hardcoded credentials
- **Error Handling:** No sensitive information in error messages

---

## 🐛 **Troubleshooting**

### **Common Issues**

**Issue:** `ModuleNotFoundError: No module named 'google'`  
**Solution:** Install dependencies: `pip install -r requirements.txt`

**Issue:** `FileNotFoundError: .env file not found`  
**Solution:** Copy configuration: `cp env_config.example .env`

**Issue:** `API key not configured`  
**Solution:** Add `GOOGLE_API_KEY=your_key` to `.env file

**Issue:** `Permission denied on database`  
**Solution:** Check write permissions in the project directory

**Issue:** `Email authentication failed`  
**Solution:** Use App Password instead of regular password for Gmail

### **Getting Help**

1. **Check your `.env` file** - Ensure all required fields are set
2. **Verify API key** - Test it at Google AI Studio
3. **Check Python version** - Requires Python 3.11+
4. **Review logs** - Error messages will guide you to the issue
5. **Test step by step** - Start with basic functionality first

### **Debug Mode**

Enable debug logging by setting:
```bash
DEBUG=true
```

---

## 🚀 **Quick Commands Reference**

#### **Windows PowerShell:**
```powershell
# Setup commands
copy env_config.example .env         # Copy configuration
python setup_env.py                 # Interactive setup
pip install -r requirements.txt     # Install dependencies

# Run commands  
python run.py                       # Production run (recommended)
python main.py                      # Direct run

# Test commands
python -c "import google.adk; print('✅ Dependencies OK')"  # Test imports
```

#### **macOS/Linux:**
   ```bash
# Setup commands
cp env_config.example .env          # Copy configuration
python setup_env.py                 # Interactive setup
pip install -r requirements.txt     # Install dependencies

# Run commands  
python run.py                       # Production run (recommended)
python main.py                      # Direct run

# Test commands
python -c "import google.adk; print('✅ Dependencies OK')"  # Test imports
```

---

## 📋 **Features Summary**

✅ **Intelligent Bug Reporting** - Natural language issue reporting  
✅ **Smart Duplicate Detection** - Semantic similarity with 50% threshold  
✅ **Status Management** - Complete lifecycle tracking  
✅ **A2A Protocol Support** - Agent-to-agent communication  
✅ **Email Notifications** - Automatic support alerts  
✅ **User Isolation** - Secure multi-user support  
✅ **Professional UI** - Clean, informative responses  
✅ **Security Hardened** - Input validation and secure configuration  
✅ **Database Persistence** - SQLite with proper indexing  
✅ **Rate Limiting** - Anti-spam protection  

---

**🎉 You're all set! The Bug Reporting System is ready to help manage and track issues efficiently.**

For additional configuration options, see the example configuration file and inline documentation. 