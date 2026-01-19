#!/usr/bin/env python3
"""Step 1: Generate Gmail OAuth URL."""

from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
auth_url, _ = flow.authorization_url(prompt='consent', access_type='offline')

print()
print("="*70)
print("STEP 1: Get Authorization URL")
print("="*70)
print("\n📋 Copy this URL and open it in your browser:\n")
print(auth_url)
print()
print("="*70)
print("\n📌 After you authorize:")
print("   1. You'll be redirected to a URL starting with 'http://localhost'")
print("   2. The page will show an error (that's OK!)")
print("   3. Copy the ENTIRE URL from your browser address bar")
print("   4. Save it somewhere - you'll need it for Step 2")
print()
print("="*70)
print("\n✓ Once you have the redirect URL, run:")
print("   python auth_step2_complete.py")
print()
