"""Deal extraction using Claude API."""

import json
import re
from typing import Dict, List, Optional
from datetime import datetime

from anthropic import Anthropic


EXTRACTION_PROMPT = """You are analyzing a private equity industry newsletter email to extract deal announcements.

Please extract ALL deal announcements mentioned in this email and return them as a JSON array. For each deal, extract:

1. **deal_name**: A concise name for the deal (e.g., "Vista Equity acquires Finastra")
2. **date_announced**: The date the deal was announced (ISO format YYYY-MM-DD if possible, otherwise as written)
3. **target_company**: The company being acquired/sold
4. **selling_pe_firm**: The private equity firm selling (if applicable, null if not a sponsor exit)
5. **acquiring_company**: The company or entity acquiring the target
6. **acquiring_pe_firm**: The PE firm behind the acquirer (if the acquirer is PE-backed or is a PE firm, null otherwise)
7. **deal_type**: Type of deal (e.g., "buyout", "growth equity", "exit", "merger", "add-on acquisition")
8. **deal_value**: Deal value if mentioned (e.g., "$1.5B", "undisclosed")
9. **confidence**: Your confidence in this extraction (high/medium/low)
10. **notes**: Any additional relevant context

Important distinctions:
- If a PE firm is directly acquiring a company, put the PE firm name in BOTH acquiring_company and acquiring_pe_firm
- If a portfolio company of a PE firm is acquiring another company, put the portfolio company in acquiring_company and the PE firm in acquiring_pe_firm
- If no PE involvement on sell-side, selling_pe_firm should be null
- If target is not PE-backed, selling_pe_firm should be null

Return ONLY a valid JSON array, no other text. If no deals are found, return an empty array [].

Example format:
[
  {
    "deal_name": "Vista Equity Partners acquires Finastra",
    "date_announced": "2024-01-15",
    "target_company": "Finastra",
    "selling_pe_firm": null,
    "acquiring_company": "Vista Equity Partners",
    "acquiring_pe_firm": "Vista Equity Partners",
    "deal_type": "buyout",
    "deal_value": "$2.1B",
    "confidence": "high",
    "notes": "One of the largest fintech buyouts of the year"
  },
  {
    "deal_name": "Thoma Bravo's Proofpoint acquires Tessian",
    "date_announced": "2024-01-16",
    "target_company": "Tessian",
    "selling_pe_firm": null,
    "acquiring_company": "Proofpoint",
    "acquiring_pe_firm": "Thoma Bravo",
    "deal_type": "add-on acquisition",
    "deal_value": "undisclosed",
    "confidence": "high",
    "notes": "Proofpoint is a Thoma Bravo portfolio company"
  }
]

Email to analyze:
---
Subject: {subject}
From: {sender}
Date: {date}

{body}
---

Extract all deals as JSON array:"""


class DealExtractor:
    """Extracts PE deal information from emails using Claude API."""

    def __init__(self, api_key: str, model: str = "claude-3-5-sonnet-20241022"):
        """Initialize deal extractor.

        Args:
            api_key: Anthropic API key
            model: Claude model to use
        """
        self.client = Anthropic(api_key=api_key)
        self.model = model

    def extract_deals(self, email_data: Dict) -> List[Dict]:
        """Extract deal information from an email.

        Args:
            email_data: Email dictionary from GmailClient

        Returns:
            List of extracted deals
        """
        # Prepare prompt
        prompt = EXTRACTION_PROMPT.format(
            subject=email_data.get('subject', ''),
            sender=email_data.get('from', ''),
            date=email_data.get('date', ''),
            body=email_data.get('body', '')[:15000]  # Limit body length
        )

        try:
            # Call Claude API
            response = self.client.messages.create(
                model=self.model,
                max_tokens=4096,
                temperature=0,
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )

            # Extract JSON from response
            response_text = response.content[0].text
            deals = self._parse_response(response_text)

            # Add metadata to each deal
            news_outlet = self._extract_news_outlet(email_data.get('from', ''))

            for deal in deals:
                deal['news_outlet'] = news_outlet
                deal['source_email_id'] = email_data.get('id')
                deal['email_subject'] = email_data.get('subject')
                deal['email_date'] = email_data.get('date')
                deal['extraction_date'] = datetime.now().isoformat()
                deal['confidence_score'] = deal.pop('confidence', 'unknown')
                deal['raw_content'] = email_data.get('body', '')[:2000]  # Store snippet

                # Rename notes to preserve it
                if 'notes' in deal:
                    deal['deal_notes'] = deal.pop('notes')

            return deals

        except Exception as e:
            print(f"Error extracting deals from email {email_data.get('id')}: {e}")
            return []

    def _parse_response(self, response_text: str) -> List[Dict]:
        """Parse Claude response to extract JSON.

        Args:
            response_text: Claude API response text

        Returns:
            List of deal dictionaries
        """
        # Try to find JSON array in response
        json_match = re.search(r'\[[\s\S]*\]', response_text)

        if json_match:
            try:
                deals = json.loads(json_match.group())
                if isinstance(deals, list):
                    return deals
            except json.JSONDecodeError as e:
                print(f"JSON parse error: {e}")
                print(f"Response text: {response_text[:500]}")

        return []

    def _extract_news_outlet(self, sender: str) -> str:
        """Extract news outlet name from sender email.

        Args:
            sender: Email sender string

        Returns:
            News outlet name
        """
        sender_lower = sender.lower()

        if 'pitchbook' in sender_lower:
            return 'PitchBook'
        elif 'axios' in sender_lower:
            return 'Axios Pro Rata'
        elif 'pehub' in sender_lower:
            return 'PE Hub'
        elif 'dealbook' in sender_lower:
            return 'DealBook'
        elif 'bloomberg' in sender_lower:
            return 'Bloomberg'
        elif 'wsj' in sender_lower or 'wall street journal' in sender_lower:
            return 'WSJ Pro PE'
        elif 'ft.com' in sender_lower or 'financial times' in sender_lower:
            return 'Financial Times'
        elif 'preqin' in sender_lower:
            return 'Preqin'
        else:
            # Extract domain
            email_match = re.search(r'@([\w\.-]+)', sender)
            if email_match:
                domain = email_match.group(1)
                return domain.split('.')[0].title()
            return 'Unknown'

    def extract_deals_batch(
        self,
        emails: List[Dict],
        show_progress: bool = True
    ) -> List[Dict]:
        """Extract deals from multiple emails.

        Args:
            emails: List of email dictionaries
            show_progress: Whether to show progress

        Returns:
            List of all extracted deals
        """
        all_deals = []

        for i, email in enumerate(emails, 1):
            if show_progress:
                print(f"Processing email {i}/{len(emails)}: {email.get('subject', 'No subject')[:60]}...")

            deals = self.extract_deals(email)

            if deals:
                print(f"  → Found {len(deals)} deal(s)")
                all_deals.extend(deals)
            else:
                print(f"  → No deals found")

        return all_deals
