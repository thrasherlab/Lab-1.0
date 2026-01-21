"""Gmail API client for fetching PE newsletter emails."""

import os
import base64
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from email.utils import parsedate_to_datetime

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

import html2text


# Gmail API scopes
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

# Common PE newsletter sender patterns
PE_NEWSLETTER_SENDERS = [
    'pitchbook.com',
    'axios.com',
    'pehub.com',
    'privateequityinfo.com',
    'preqin.com',
    'dealbook',
    'bloomberg.com',
    'wsj.com',
    'ft.com'
]


class GmailClient:
    """Client for interacting with Gmail API."""

    def __init__(self, credentials_path: str = 'credentials.json', token_path: str = 'token.json'):
        """Initialize Gmail client.

        Args:
            credentials_path: Path to OAuth2 credentials file
            token_path: Path to store/load access token
        """
        self.credentials_path = credentials_path
        self.token_path = token_path
        self.service = None
        self.html_converter = html2text.HTML2Text()
        self.html_converter.ignore_links = False
        self.html_converter.ignore_images = True

    def authenticate(self):
        """Authenticate with Gmail API."""
        creds = None

        # Load existing token
        if os.path.exists(self.token_path):
            creds = Credentials.from_authorized_user_file(self.token_path, SCOPES)

        # If no valid credentials, initiate OAuth flow
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not os.path.exists(self.credentials_path):
                    raise FileNotFoundError(
                        f"Credentials file not found at {self.credentials_path}. "
                        "Please download OAuth2 credentials from Google Cloud Console."
                    )

                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_path, SCOPES
                )

                # Manual authorization flow
                auth_url, _ = flow.authorization_url(prompt='consent')

                print("\n" + "="*60)
                print("Gmail Authentication Required")
                print("="*60)
                print("\n1. Visit this URL in your browser:")
                print(f"\n{auth_url}\n")
                print("2. Sign in and authorize the app")
                print("3. You'll be redirected to a URL starting with 'http://localhost'")
                print("4. Copy the ENTIRE URL from your browser address bar")
                print("5. Paste it below:")
                print("="*60)

                code_url = input("\nPaste the full redirect URL here: ").strip()

                # Extract the code from the URL
                if code_url.startswith(('http://', 'https://')):
                    # Parse the code from URL parameters
                    from urllib.parse import urlparse, parse_qs
                    parsed = urlparse(code_url)
                    params = parse_qs(parsed.query)
                    code = params.get('code', [None])[0]

                    if not code:
                        raise ValueError("Could not extract authorization code from URL. Please ensure the URL contains a 'code' parameter.")

                    flow.fetch_token(code=code)
                    creds = flow.credentials
                else:
                    # Assume they pasted just the code
                    flow.fetch_token(code=code_url)
                    creds = flow.credentials

                print("\n✓ Authentication successful!")
                print("="*60 + "\n")

            # Save credentials
            with open(self.token_path, 'w') as token:
                token.write(creds.to_json())

        self.service = build('gmail', 'v1', credentials=creds)
        print("Successfully authenticated with Gmail API")

    def build_query(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        sender_domains: Optional[List[str]] = None,
        label: Optional[str] = None
    ) -> str:
        """Build Gmail search query.

        Args:
            start_date: Filter emails after this date
            end_date: Filter emails before this date
            sender_domains: List of sender domains to filter
            label: Gmail label to filter

        Returns:
            Gmail search query string
        """
        query_parts = []

        if start_date:
            query_parts.append(f"after:{start_date.strftime('%Y/%m/%d')}")

        if end_date:
            query_parts.append(f"before:{end_date.strftime('%Y/%m/%d')}")

        if sender_domains:
            sender_query = ' OR '.join([f"from:@{domain}" for domain in sender_domains])
            query_parts.append(f"({sender_query})")

        if label:
            query_parts.append(f"label:{label}")

        return ' '.join(query_parts) if query_parts else ''

    def fetch_emails(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        sender_domains: Optional[List[str]] = None,
        label: Optional[str] = None,
        max_results: int = 500
    ) -> List[Dict]:
        """Fetch emails matching criteria.

        Args:
            start_date: Filter emails after this date
            end_date: Filter emails before this date
            sender_domains: List of sender domains (defaults to PE newsletters)
            label: Gmail label to filter
            max_results: Maximum number of emails to fetch

        Returns:
            List of email dictionaries with parsed content
        """
        if not self.service:
            raise RuntimeError("Not authenticated. Call authenticate() first.")

        # Use default PE newsletter senders if none specified
        if sender_domains is None:
            sender_domains = PE_NEWSLETTER_SENDERS

        query = self.build_query(start_date, end_date, sender_domains, label)
        print(f"Gmail query: {query}")

        emails = []

        try:
            # Get list of message IDs
            results = self.service.users().messages().list(
                userId='me',
                q=query,
                maxResults=max_results
            ).execute()

            messages = results.get('messages', [])
            print(f"Found {len(messages)} emails matching criteria")

            # Fetch full message details
            for i, msg in enumerate(messages, 1):
                try:
                    message = self.service.users().messages().get(
                        userId='me',
                        id=msg['id'],
                        format='full'
                    ).execute()

                    email_data = self._parse_email(message)
                    emails.append(email_data)

                    if i % 10 == 0:
                        print(f"Fetched {i}/{len(messages)} emails...")

                except HttpError as e:
                    print(f"Error fetching email {msg['id']}: {e}")
                    continue

        except HttpError as e:
            print(f"Error fetching emails: {e}")
            raise

        print(f"Successfully fetched {len(emails)} emails")
        return emails

    def _parse_email(self, message: Dict) -> Dict:
        """Parse Gmail message into structured format.

        Args:
            message: Gmail API message object

        Returns:
            Dictionary with email data
        """
        headers = {h['name']: h['value'] for h in message['payload']['headers']}

        # Extract body
        body = self._get_email_body(message['payload'])

        # Parse date
        email_date = None
        if 'Date' in headers:
            try:
                email_date = parsedate_to_datetime(headers['Date']).isoformat()
            except Exception:
                email_date = headers['Date']

        return {
            'id': message['id'],
            'subject': headers.get('Subject', ''),
            'from': headers.get('From', ''),
            'to': headers.get('To', ''),
            'date': email_date,
            'body': body,
            'snippet': message.get('snippet', '')
        }

    def _get_email_body(self, payload: Dict) -> str:
        """Extract email body from message payload.

        Args:
            payload: Gmail message payload

        Returns:
            Email body as text
        """
        body = ""

        if 'parts' in payload:
            for part in payload['parts']:
                if part['mimeType'] == 'text/plain':
                    if 'data' in part['body']:
                        body = base64.urlsafe_b64decode(
                            part['body']['data']
                        ).decode('utf-8')
                        break
                elif part['mimeType'] == 'text/html':
                    if 'data' in part['body']:
                        html_body = base64.urlsafe_b64decode(
                            part['body']['data']
                        ).decode('utf-8')
                        body = self.html_converter.handle(html_body)
                elif 'parts' in part:
                    # Recursive for nested parts
                    body = self._get_email_body(part)
                    if body:
                        break
        else:
            if 'data' in payload.get('body', {}):
                data = payload['body']['data']
                decoded = base64.urlsafe_b64decode(data).decode('utf-8')

                if payload.get('mimeType') == 'text/html':
                    body = self.html_converter.handle(decoded)
                else:
                    body = decoded

        return body.strip()
