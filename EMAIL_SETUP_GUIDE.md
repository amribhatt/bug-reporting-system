# Email Setup Guide - Real Email Sending

This guide shows you how to configure the Bug Reporting System to send **real emails** using Gmail or other email providers.

## 🚨 Why You Didn't Receive Emails

The system was previously in **simulation mode** - it logged email content but didn't actually send emails. This has now been updated to send real emails when properly configured.

## 📧 Gmail Setup (Recommended)

### Step 1: Enable 2-Factor Authentication
1. Go to [Google Account Security](https://myaccount.google.com/security)
2. Enable **2-Step Verification** if not already enabled

### Step 2: Create App Password
1. Go to [Google Account Security](https://myaccount.google.com/security)
2. Click **2-Step Verification**
3. Scroll down to **App passwords**
4. Click **Select app** → Choose **Mail**
5. Click **Select device** → Choose **Other (custom name)**
6. Enter "Bug Reporting System" as the name
7. Click **Generate**
8. **Copy the 16-character password** (e.g., `abcd efgh ijkl mnop`)

### Step 3: Configure Environment Variables
Edit your `.env` file:

```bash
# Gmail Configuration
SUPPORT_EMAIL=your-support-team@gmail.com
EMAIL_USER=your-gmail-address@gmail.com
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
EMAIL_PASSWORD=abcd efgh ijkl mnop  # Your app password (no spaces)
EMAIL_ENABLED=true
```

## 🔧 Other Email Providers

### Outlook/Hotmail
```bash
SMTP_SERVER=smtp-mail.outlook.com
SMTP_PORT=587
EMAIL_USER=your-email@outlook.com
EMAIL_PASSWORD=your-app-password
```

### Yahoo Mail
```bash
SMTP_SERVER=smtp.mail.yahoo.com
SMTP_PORT=587
EMAIL_USER=your-email@yahoo.com
EMAIL_PASSWORD=your-app-password
```

### Custom SMTP Server
```bash
SMTP_SERVER=mail.yourcompany.com
SMTP_PORT=587
EMAIL_USER=noreply@yourcompany.com
EMAIL_PASSWORD=your-password
```

## 🧪 Testing Email Functionality

### Test 1: Check Configuration
```bash
python -c "from config import get_email_config, is_email_enabled; print('Email enabled:', is_email_enabled()); print('Config:', get_email_config())"
```

### Test 2: Manual Email Test
Create a test script `test_email.py`:

```python
import smtplib
from email.mime.text import MIMEText
from config import get_email_config

config = get_email_config()

try:
    msg = MIMEText("Test email from Bug Reporting System")
    msg['Subject'] = "Test Email"
    msg['From'] = config['sender_email']
    msg['To'] = config['support_email']
    
    with smtplib.SMTP(config['smtp_server'], config['smtp_port']) as server:
        server.starttls()
        server.login(config['sender_email'], config['email_password'])
        server.send_message(msg)
    
    print("✅ Test email sent successfully!")
except Exception as e:
    print(f"❌ Email test failed: {e}")
```

Run: `python test_email.py`

## 🔍 Troubleshooting

### Common Issues

1. **"Authentication failed"**
   - Make sure you're using an App Password, not your regular password
   - Check that 2FA is enabled on your Google account

2. **"SMTP connection failed"**
   - Verify SMTP server and port settings
   - Check your internet connection

3. **"Email enabled: False"**
   - Set `EMAIL_ENABLED=true` in your `.env` file

4. **"App passwords not available"**
   - Enable 2-Step Verification first
   - Wait a few minutes after enabling 2FA

### Email Sending Conditions

Emails are sent when:
- A user reports the **same issue** after the original was marked as **Resolved**
- Email notifications are **enabled** (`EMAIL_ENABLED=true`)
- All email configuration is **properly set**

### Security Best Practices

1. **Never commit passwords** to version control
2. **Use App Passwords** instead of regular passwords
3. **Restrict email permissions** to sending only
4. **Monitor email logs** for suspicious activity
5. **Rotate passwords** regularly

## 📝 Example Complete Configuration

Your `.env` file should look like this:

```bash
# Required API Key
GOOGLE_API_KEY=your_google_api_key_here

# Email Configuration (Gmail example)
SUPPORT_EMAIL=support@yourcompany.com
EMAIL_USER=bug-reports@gmail.com
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
EMAIL_PASSWORD=your_16_char_app_password
EMAIL_ENABLED=true

# Other settings
DEBUG=false
LOG_LEVEL=INFO
```

## ✅ Verification Checklist

- [ ] 2-Factor Authentication enabled on email account
- [ ] App Password generated and copied
- [ ] `.env` file updated with correct settings
- [ ] `EMAIL_ENABLED=true` set
- [ ] Test email script runs successfully
- [ ] Bug Reporting System shows "Email enabled: True"

Once configured correctly, you'll receive real email alerts when users report repeated issues! 📬 