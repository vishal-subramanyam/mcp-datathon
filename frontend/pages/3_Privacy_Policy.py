"""
Privacy Policy page for Canvas MPC.
"""
import streamlit as st

st.set_page_config(
    page_title="Privacy Policy - Canvas MPC",
    page_icon="🔒",
    layout="wide"
)

st.title("🔒 Privacy Policy")
st.markdown("**Last Updated**: January 2025")

st.markdown("""
## Introduction

Canvas MPC ("we", "our", or "us") is committed to protecting your privacy. This Privacy Policy explains how we collect, use, and safeguard your information when you use our service.

## Information We Collect

### Account Information
- **User ID**: A unique identifier you provide (e.g., email address)
- **Google Account**: When you connect your Google account, we store OAuth tokens to access:
  - Gmail (to read and send emails)
  - Google Calendar (to view and create calendar events)

### Canvas LMS Data
- **Canvas API Credentials**: Stored securely if you provide them
- **Course Information**: Accessed through Canvas API when you use the service
- **Assignment Data**: Retrieved from Canvas when requested

### Usage Data
- **Conversation History**: Stored locally in your browser session
- **Flashcard Data**: Stored locally or in cloud storage (if configured)

## How We Use Your Information

We use your information to:
- **Provide Services**: Access your Gmail, Calendar, and Canvas data to fulfill your requests
- **Store Credentials**: Securely store your API credentials in Supabase database
- **Improve Service**: Analyze usage patterns to improve the service (anonymized data only)

## Data Storage

### Credentials Storage
- Your Google OAuth tokens are stored in **Supabase** database
- Credentials are encrypted and secured with Row Level Security (RLS)
- Only you can access your own credentials

### Session Data
- Conversation history is stored in your browser session
- Data is cleared when you close your browser (unless saved locally)

## Data Security

We implement security measures to protect your data:
- **Encryption**: All data transmitted over HTTPS
- **Access Control**: Row Level Security (RLS) in Supabase
- **Secure Storage**: Credentials stored in secure database
- **No Sharing**: We do not share your data with third parties

## Third-Party Services

We use the following third-party services:
- **Supabase**: Database and authentication (privacy policy: https://supabase.com/privacy)
- **Google APIs**: Gmail and Calendar integration (privacy policy: https://policies.google.com/privacy)
- **OpenRouter**: AI chat functionality (privacy policy: https://openrouter.ai/privacy)
- **Render**: Backend hosting (privacy policy: https://render.com/privacy)
- **Streamlit Cloud**: Frontend hosting (privacy policy: https://streamlit.io/privacy)

## Your Rights

You have the right to:
- **Access**: Request access to your stored data
- **Delete**: Delete your credentials and data at any time
- **Modify**: Update your credentials through the Settings page
- **Disconnect**: Unlink your Google account at any time

## Data Retention

- **Credentials**: Stored until you delete them
- **Session Data**: Cleared when you close your browser
- **Flashcard Data**: Stored until you delete it

## Children's Privacy

Our service is not intended for users under 13 years of age. We do not knowingly collect information from children.

## Changes to This Policy

We may update this Privacy Policy from time to time. We will notify you of any changes by posting the new Privacy Policy on this page.

## Contact Us

If you have questions about this Privacy Policy, please contact us at:
- **Email**: [Your support email]
- **GitHub**: [Your repository URL]

## Consent

By using our service, you consent to this Privacy Policy and agree to its terms.

---

**Note**: This is a template privacy policy. Please review and customize it according to your specific needs and legal requirements.
""")

