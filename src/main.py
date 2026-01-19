"""Main orchestration script for PE Deal Tracker."""

import os
from datetime import datetime, timedelta
from typing import Optional

import click
from dotenv import load_dotenv

from database import DealDatabase
from gmail_client import GmailClient
from deal_extractor import DealExtractor


# Load environment variables
load_dotenv()


@click.group()
def cli():
    """PE Deal Tracker - Extract and track private equity deals from newsletters."""
    pass


@cli.command()
@click.option('--days', default=30, help='Number of days to look back (default: 30)')
@click.option('--start-date', help='Start date (YYYY-MM-DD)')
@click.option('--end-date', help='End date (YYYY-MM-DD)')
@click.option('--label', help='Gmail label to filter emails')
@click.option('--max-emails', default=100, help='Maximum number of emails to process (default: 100)')
def fetch(days: int, start_date: Optional[str], end_date: Optional[str], label: Optional[str], max_emails: int):
    """Fetch emails and extract PE deals."""

    click.echo("=" * 60)
    click.echo("PE Deal Tracker - Fetch Mode")
    click.echo("=" * 60)

    # Parse dates
    if start_date and end_date:
        start_dt = datetime.fromisoformat(start_date)
        end_dt = datetime.fromisoformat(end_date)
    else:
        end_dt = datetime.now()
        start_dt = end_dt - timedelta(days=days)

    click.echo(f"\nDate range: {start_dt.date()} to {end_dt.date()}")

    # Initialize components
    gmail_client = GmailClient()
    db = DealDatabase()

    # Get API key
    anthropic_api_key = os.getenv('ANTHROPIC_API_KEY')
    if not anthropic_api_key:
        click.echo("\n❌ Error: ANTHROPIC_API_KEY not found in environment variables")
        click.echo("Please set it in .env file or export it as an environment variable")
        return

    extractor = DealExtractor(api_key=anthropic_api_key)

    # Authenticate with Gmail
    click.echo("\n📧 Authenticating with Gmail...")
    try:
        gmail_client.authenticate()
    except Exception as e:
        click.echo(f"\n❌ Gmail authentication failed: {e}")
        return

    # Fetch emails
    click.echo(f"\n📥 Fetching emails (max: {max_emails})...")
    try:
        emails = gmail_client.fetch_emails(
            start_date=start_dt,
            end_date=end_dt,
            label=label,
            max_results=max_emails
        )
    except Exception as e:
        click.echo(f"\n❌ Error fetching emails: {e}")
        return

    if not emails:
        click.echo("\n⚠️  No emails found matching criteria")
        return

    # Extract deals
    click.echo(f"\n🤖 Extracting deals using Claude API...")
    deals = extractor.extract_deals_batch(emails)

    if not deals:
        click.echo("\n⚠️  No deals found in emails")
        return

    # Save to database
    click.echo(f"\n💾 Saving {len(deals)} deals to database...")
    new_deals = 0
    duplicate_deals = 0

    for deal in deals:
        deal_id = db.insert_deal(deal)
        if deal_id:
            new_deals += 1
        else:
            duplicate_deals += 1

    click.echo(f"   ✓ {new_deals} new deals saved")
    if duplicate_deals > 0:
        click.echo(f"   ℹ {duplicate_deals} duplicate deals skipped")

    # Show statistics
    stats = db.get_statistics()
    click.echo("\n📊 Database Statistics:")
    click.echo(f"   Total deals: {stats['total_deals']}")
    click.echo(f"   Date range: {stats['date_range']['earliest']} to {stats['date_range']['latest']}")

    if stats['by_outlet']:
        click.echo("\n   Deals by outlet:")
        for outlet in stats['by_outlet']:
            click.echo(f"      • {outlet['news_outlet']}: {outlet['count']}")

    db.close()
    click.echo("\n✓ Done!")


@cli.command()
@click.option('--output', default='exports/deals.csv', help='Output CSV file path')
@click.option('--start-date', help='Filter: Start date (YYYY-MM-DD)')
@click.option('--end-date', help='Filter: End date (YYYY-MM-DD)')
@click.option('--outlet', help='Filter: News outlet name')
def export(output: str, start_date: Optional[str], end_date: Optional[str], outlet: Optional[str]):
    """Export deals to CSV file."""

    click.echo("=" * 60)
    click.echo("PE Deal Tracker - Export Mode")
    click.echo("=" * 60)

    db = DealDatabase()

    # Apply filters
    filters = []
    if start_date:
        filters.append(f"start_date={start_date}")
    if end_date:
        filters.append(f"end_date={end_date}")
    if outlet:
        filters.append(f"outlet={outlet}")

    if filters:
        click.echo(f"\nFilters: {', '.join(filters)}")
    else:
        click.echo("\nExporting all deals")

    # Export
    click.echo(f"\n📤 Exporting to {output}...")

    # Ensure export directory exists
    os.makedirs(os.path.dirname(output) if os.path.dirname(output) else 'exports', exist_ok=True)

    db.export_to_csv(output, start_date, end_date, outlet)
    db.close()

    click.echo("\n✓ Done!")


@cli.command()
def stats():
    """Show database statistics."""

    click.echo("=" * 60)
    click.echo("PE Deal Tracker - Statistics")
    click.echo("=" * 60)

    db = DealDatabase()
    stats = db.get_statistics()

    click.echo(f"\n📊 Total deals: {stats['total_deals']}")

    if stats['date_range']['earliest']:
        click.echo(f"\n📅 Date range:")
        click.echo(f"   Earliest: {stats['date_range']['earliest']}")
        click.echo(f"   Latest: {stats['date_range']['latest']}")

    if stats['by_outlet']:
        click.echo(f"\n📰 Deals by news outlet:")
        for outlet in stats['by_outlet']:
            click.echo(f"   • {outlet['news_outlet']}: {outlet['count']} deals")

    db.close()


@cli.command()
@click.option('--start-date', help='Filter: Start date (YYYY-MM-DD)')
@click.option('--end-date', help='Filter: End date (YYYY-MM-DD)')
@click.option('--outlet', help='Filter: News outlet name')
@click.option('--limit', default=20, help='Number of deals to show (default: 20)')
def list_deals(start_date: Optional[str], end_date: Optional[str], outlet: Optional[str], limit: int):
    """List deals from database."""

    click.echo("=" * 60)
    click.echo("PE Deal Tracker - List Deals")
    click.echo("=" * 60)

    db = DealDatabase()
    deals = db.get_deals(start_date, end_date, outlet)

    if not deals:
        click.echo("\n⚠️  No deals found")
        db.close()
        return

    click.echo(f"\nFound {len(deals)} deal(s). Showing first {limit}:\n")

    for i, deal in enumerate(deals[:limit], 1):
        click.echo(f"{i}. {deal['deal_name']}")
        click.echo(f"   Date: {deal['date_announced']}")
        click.echo(f"   Target: {deal['target_company']}")
        click.echo(f"   Acquirer: {deal['acquiring_company']}")
        if deal['acquiring_pe_firm']:
            click.echo(f"   PE Firm (Buy-side): {deal['acquiring_pe_firm']}")
        if deal['selling_pe_firm']:
            click.echo(f"   PE Firm (Sell-side): {deal['selling_pe_firm']}")
        if deal['deal_value']:
            click.echo(f"   Value: {deal['deal_value']}")
        click.echo(f"   Source: {deal['news_outlet']}")
        click.echo()

    if len(deals) > limit:
        click.echo(f"... and {len(deals) - limit} more. Use --limit to see more.")

    db.close()


if __name__ == '__main__':
    cli()
