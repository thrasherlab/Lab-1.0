#!/usr/bin/env python3
"""Standalone authentication script for Gmail API."""

import sys
sys.path.insert(0, 'src')

from gmail_client import GmailClient

def main():
    """Run Gmail authentication."""
    print("="*60)
    print("Gmail API Authentication Setup")
    print("="*60)
    print("\nThis will authenticate your Gmail account for PE Deal Tracker.")
    print()

    client = GmailClient()

    try:
        client.authenticate()
        print("\n✅ Authentication complete!")
        print("\nYou can now run: python src/main.py fetch")
        print()

    except Exception as e:
        print(f"\n❌ Authentication failed: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
