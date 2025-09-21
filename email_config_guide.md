# Email Setup Guide for Apple Stock Monitor

## Option 1: Gmail (Recommended)

### Step 1: Enable 2-Factor Authentication
1. Go to your Google Account settings: https://myaccount.google.com/
2. Click on "Security"
3. Enable "2-Step Verification" if not already enabled

### Step 2: Generate App Password
1. Go to: https://myaccount.google.com/apppasswords
2. Select "Mail" from the dropdown
3. Select "Other" for device and name it "Apple Monitor"
4. Click "Generate"
5. Copy the 16-character password (spaces don't matter)

### Step 3: Configure the Monitor
Create or edit the `.env` file in the project directory:

```bash
# Gmail configuration
EMAIL_FROM=your_email@gmail.com
EMAIL_PASSWORD=xxxx xxxx xxxx xxxx  # Your 16-character app password
EMAIL_TO=fruitcc@gmail.com
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
```

## Option 2: Outlook/Hotmail

```bash
# Outlook configuration
EMAIL_FROM=your_email@outlook.com
EMAIL_PASSWORD=your_regular_password
EMAIL_TO=fruitcc@gmail.com
SMTP_SERVER=smtp-mail.outlook.com
SMTP_PORT=587
```

## Option 3: Yahoo Mail

```bash
# Yahoo configuration
EMAIL_FROM=your_email@yahoo.com
EMAIL_PASSWORD=your_app_password  # Generate from Yahoo security settings
EMAIL_TO=fruitcc@gmail.com
SMTP_SERVER=smtp.mail.yahoo.com
SMTP_PORT=587
```

## Option 4: iCloud Mail

```bash
# iCloud configuration
EMAIL_FROM=your_email@icloud.com
EMAIL_PASSWORD=your_app_specific_password  # Generate from Apple ID settings
EMAIL_TO=fruitcc@gmail.com
SMTP_SERVER=smtp.mail.me.com
SMTP_PORT=587
```

## Testing Email Configuration

Run this test script to verify your email setup:

```python
python test_email.py
```

## Common Issues

### Gmail: "Less secure app access"
- This is deprecated. You MUST use App Passwords now.

### "Authentication failed"
- Double-check your app password (not your regular password)
- Ensure 2FA is enabled for Gmail
- Check that you're using the correct SMTP server

### "Connection refused"
- Check your firewall settings
- Try port 465 with SSL if 587 doesn't work
- Some networks block SMTP ports

### Rate Limiting
- Gmail limits: 500 emails/day for regular accounts
- The monitor has a 5-minute cooldown between notifications to prevent spam

## Security Notes

⚠️ **NEVER** commit your `.env` file to Git!
- Add `.env` to `.gitignore`
- Use `.env.example` for sharing configuration templates
- Keep your app passwords secure and rotate them periodically