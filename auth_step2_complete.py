#!/usr/bin/env python3
"""Step 2: Complete Gmail OAuth with redirect URL."""

import sys
from urllib.parse import urlparse, parse_qs
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

print()
print("="*70)
print("STEP 2: Complete Authorization")
print("="*70)
print()
print("Paste the full redirect URL from your browser:")
print("(It should start with 'http://localhost')")
print()

redirect_url = input("Redirect URL: ").strip()

if not redirect_url:
    print("\n❌ Error: No URL provided")
    sys.exit(1)

try:
    # Parse the authorization code from the URL
    parsed = urlparse(redirect_url)
    params = parse_qs(parsed.query)
    code = params.get('code', [None])[0]

    if not code:
        print("\n❌ Error: Could not find authorization code in URL")
        print("   Make sure you copied the complete URL")
        sys.exit(1)

    print("\n🔄 Exchanging code for credentials...")

    # Create flow and exchange code for credentials
    flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
    flow.redirect_uri = 'http://localhost'
    flow.fetch_token(code=code)
    creds = flow.credentials

    # Save credentials
    with open('token.json', 'w') as token_file:
        token_file.write(creds.to_json())

    print("\n✅ Authentication successful!")
    print("\n   Credentials saved to: token.json")
    print()
    print("="*70)
    print("\n🎉 Setup complete! You can now run:")
    print("   source venv/bin/activate")
    print("   python src/main.py fetch --days 7")
    print()

except Exception as e:
    print(f"\n❌ Error: {e}")
    print("\n💡 Tip: Make sure you:")
    print("   1. Copied the ENTIRE URL (including http://localhost)")
    print("   2. The URL contains '?code=' in it")
    sys.exit(1)
