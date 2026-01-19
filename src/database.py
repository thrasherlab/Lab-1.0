"""Database module for PE deal tracking."""

import sqlite3
from datetime import datetime
from typing import List, Dict, Optional
import pandas as pd


class DealDatabase:
    """Manages SQLite database for PE deals."""

    def __init__(self, db_path: str = "pe_deals.db"):
        """Initialize database connection.

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self._create_tables()

    def _create_tables(self):
        """Create database tables if they don't exist."""
        cursor = self.conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS deals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                news_outlet TEXT,
                deal_name TEXT,
                date_announced TEXT,
                target_company TEXT,
                selling_pe_firm TEXT,
                acquiring_company TEXT,
                acquiring_pe_firm TEXT,
                deal_type TEXT,
                deal_value TEXT,
                source_email_id TEXT UNIQUE,
                email_subject TEXT,
                email_date TEXT,
                extraction_date TEXT,
                raw_content TEXT,
                confidence_score TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_date_announced
            ON deals(date_announced)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_target_company
            ON deals(target_company)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_news_outlet
            ON deals(news_outlet)
        """)

        self.conn.commit()

    def insert_deal(self, deal_data: Dict) -> Optional[int]:
        """Insert a new deal into the database.

        Args:
            deal_data: Dictionary containing deal information

        Returns:
            The ID of the inserted deal, or None if duplicate
        """
        cursor = self.conn.cursor()

        try:
            cursor.execute("""
                INSERT INTO deals (
                    news_outlet, deal_name, date_announced, target_company,
                    selling_pe_firm, acquiring_company, acquiring_pe_firm,
                    deal_type, deal_value, source_email_id, email_subject,
                    email_date, extraction_date, raw_content, confidence_score
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                deal_data.get('news_outlet'),
                deal_data.get('deal_name'),
                deal_data.get('date_announced'),
                deal_data.get('target_company'),
                deal_data.get('selling_pe_firm'),
                deal_data.get('acquiring_company'),
                deal_data.get('acquiring_pe_firm'),
                deal_data.get('deal_type'),
                deal_data.get('deal_value'),
                deal_data.get('source_email_id'),
                deal_data.get('email_subject'),
                deal_data.get('email_date'),
                deal_data.get('extraction_date', datetime.now().isoformat()),
                deal_data.get('raw_content'),
                deal_data.get('confidence_score')
            ))

            self.conn.commit()
            return cursor.lastrowid

        except sqlite3.IntegrityError:
            # Duplicate email_id
            return None

    def get_deals(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        news_outlet: Optional[str] = None
    ) -> List[Dict]:
        """Retrieve deals with optional filters.

        Args:
            start_date: Filter deals announced on or after this date (ISO format)
            end_date: Filter deals announced on or before this date (ISO format)
            news_outlet: Filter by news outlet

        Returns:
            List of deal dictionaries
        """
        cursor = self.conn.cursor()

        query = "SELECT * FROM deals WHERE 1=1"
        params = []

        if start_date:
            query += " AND date_announced >= ?"
            params.append(start_date)

        if end_date:
            query += " AND date_announced <= ?"
            params.append(end_date)

        if news_outlet:
            query += " AND news_outlet LIKE ?"
            params.append(f"%{news_outlet}%")

        query += " ORDER BY date_announced DESC"

        cursor.execute(query, params)
        rows = cursor.fetchall()

        return [dict(row) for row in rows]

    def export_to_csv(
        self,
        output_path: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        news_outlet: Optional[str] = None
    ):
        """Export deals to CSV file.

        Args:
            output_path: Path for output CSV file
            start_date: Filter deals announced on or after this date
            end_date: Filter deals announced on or before this date
            news_outlet: Filter by news outlet
        """
        deals = self.get_deals(start_date, end_date, news_outlet)

        if not deals:
            print("No deals found matching the criteria.")
            return

        # Convert to DataFrame and export
        df = pd.DataFrame(deals)

        # Select and reorder columns for export
        export_columns = [
            'date_announced', 'news_outlet', 'deal_name', 'target_company',
            'acquiring_company', 'acquiring_pe_firm', 'selling_pe_firm',
            'deal_type', 'deal_value', 'email_subject', 'email_date'
        ]

        # Only include columns that exist
        export_columns = [col for col in export_columns if col in df.columns]
        df = df[export_columns]

        df.to_csv(output_path, index=False)
        print(f"Exported {len(deals)} deals to {output_path}")

    def get_statistics(self) -> Dict:
        """Get database statistics.

        Returns:
            Dictionary with statistics
        """
        cursor = self.conn.cursor()

        cursor.execute("SELECT COUNT(*) as total FROM deals")
        total = cursor.fetchone()['total']

        cursor.execute("""
            SELECT news_outlet, COUNT(*) as count
            FROM deals
            GROUP BY news_outlet
            ORDER BY count DESC
        """)
        by_outlet = [dict(row) for row in cursor.fetchall()]

        cursor.execute("""
            SELECT MIN(date_announced) as earliest, MAX(date_announced) as latest
            FROM deals
        """)
        date_range = dict(cursor.fetchone())

        return {
            'total_deals': total,
            'by_outlet': by_outlet,
            'date_range': date_range
        }

    def close(self):
        """Close database connection."""
        self.conn.close()
