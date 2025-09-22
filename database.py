#!/usr/bin/env python3

import sqlite3
import json
from datetime import datetime
from typing import List, Dict, Optional
import os

class StockDatabase:
    def __init__(self, db_path="stock_history.db"):
        """Initialize database connection and create tables if needed"""
        self.db_path = db_path
        self.init_database()

    def init_database(self):
        """Create database tables if they don't exist"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Create products table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_name TEXT NOT NULL,
                product_url TEXT NOT NULL,
                part_numbers TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(product_url)
            )
        """)

        # Create stores table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS stores (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                store_name TEXT NOT NULL UNIQUE,
                store_code TEXT,
                location TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Create availability history table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS availability_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id INTEGER NOT NULL,
                store_id INTEGER NOT NULL,
                is_available BOOLEAN NOT NULL,
                status_message TEXT,
                checked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (product_id) REFERENCES products (id),
                FOREIGN KEY (store_id) REFERENCES stores (id)
            )
        """)

        # Create availability changes table (only records when status changes)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS availability_changes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id INTEGER NOT NULL,
                store_id INTEGER NOT NULL,
                previous_status BOOLEAN,
                new_status BOOLEAN NOT NULL,
                status_message TEXT,
                changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (product_id) REFERENCES products (id),
                FOREIGN KEY (store_id) REFERENCES stores (id)
            )
        """)

        # Create indices for better query performance
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_availability_history_time
            ON availability_history(checked_at DESC)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_availability_changes_time
            ON availability_changes(changed_at DESC)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_availability_product_store
            ON availability_history(product_id, store_id, checked_at DESC)
        """)

        conn.commit()
        conn.close()

    def add_product(self, product_name: str, product_url: str, part_numbers: List[str] = None) -> int:
        """Add a product to the database or get existing product ID"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Check if product exists
        cursor.execute("SELECT id FROM products WHERE product_url = ?", (product_url,))
        result = cursor.fetchone()

        if result:
            product_id = result[0]
            # Update product info if needed
            cursor.execute("""
                UPDATE products
                SET product_name = ?, part_numbers = ?
                WHERE id = ?
            """, (product_name, json.dumps(part_numbers) if part_numbers else None, product_id))
        else:
            cursor.execute("""
                INSERT INTO products (product_name, product_url, part_numbers)
                VALUES (?, ?, ?)
            """, (product_name, product_url, json.dumps(part_numbers) if part_numbers else None))
            product_id = cursor.lastrowid

        conn.commit()
        conn.close()
        return product_id

    def add_store(self, store_name: str, store_code: str = None, location: str = None) -> int:
        """Add a store to the database or get existing store ID"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT id FROM stores WHERE store_name = ?", (store_name,))
        result = cursor.fetchone()

        if result:
            store_id = result[0]
        else:
            cursor.execute("""
                INSERT INTO stores (store_name, store_code, location)
                VALUES (?, ?, ?)
            """, (store_name, store_code, location))
            store_id = cursor.lastrowid

        conn.commit()
        conn.close()
        return store_id

    def record_availability(self, product_id: int, store_id: int, is_available: bool, status_message: str = None):
        """Record an availability check result"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Record in history
        cursor.execute("""
            INSERT INTO availability_history (product_id, store_id, is_available, status_message)
            VALUES (?, ?, ?, ?)
        """, (product_id, store_id, is_available, status_message))

        # Check if status changed
        cursor.execute("""
            SELECT is_available FROM availability_history
            WHERE product_id = ? AND store_id = ?
            ORDER BY checked_at DESC
            LIMIT 2
        """, (product_id, store_id))

        results = cursor.fetchall()

        # If we have at least 2 records and status changed
        if len(results) == 2 and results[0][0] != results[1][0]:
            cursor.execute("""
                INSERT INTO availability_changes (product_id, store_id, previous_status, new_status, status_message)
                VALUES (?, ?, ?, ?, ?)
            """, (product_id, store_id, results[1][0], is_available, status_message))

        conn.commit()
        conn.close()

    def get_availability_timeline(self, product_id: int = None, store_id: int = None, hours: int = 24) -> List[Dict]:
        """Get availability timeline for a product/store"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        query = """
            SELECT
                h.*,
                p.product_name,
                p.product_url,
                s.store_name
            FROM availability_history h
            JOIN products p ON h.product_id = p.id
            JOIN stores s ON h.store_id = s.id
            WHERE h.checked_at > datetime('now', '-{} hours')
        """.format(hours)

        params = []
        if product_id:
            query += " AND h.product_id = ?"
            params.append(product_id)
        if store_id:
            query += " AND h.store_id = ?"
            params.append(store_id)

        query += " ORDER BY h.checked_at DESC"

        cursor.execute(query, params)
        results = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return results

    def get_availability_changes(self, product_id: int = None, store_id: int = None, days: int = 7) -> List[Dict]:
        """Get status changes (when items became available/unavailable)"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        query = """
            SELECT
                c.*,
                p.product_name,
                p.product_url,
                s.store_name
            FROM availability_changes c
            JOIN products p ON c.product_id = p.id
            JOIN stores s ON c.store_id = s.id
            WHERE c.changed_at > datetime('now', '-{} days')
        """.format(days)

        params = []
        if product_id:
            query += " AND c.product_id = ?"
            params.append(product_id)
        if store_id:
            query += " AND c.store_id = ?"
            params.append(store_id)

        query += " ORDER BY c.changed_at DESC"

        cursor.execute(query, params)
        results = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return results

    def get_current_status(self) -> List[Dict]:
        """Get current availability status for all products and stores"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                p.id as product_id,
                p.product_name,
                s.id as store_id,
                s.store_name,
                h.is_available,
                h.status_message,
                h.checked_at,
                last_avail.last_available_at
            FROM products p
            CROSS JOIN stores s
            LEFT JOIN (
                SELECT product_id, store_id, is_available, status_message, checked_at,
                       ROW_NUMBER() OVER (PARTITION BY product_id, store_id ORDER BY checked_at DESC) as rn
                FROM availability_history
            ) h ON h.product_id = p.id AND h.store_id = s.id AND h.rn = 1
            LEFT JOIN (
                SELECT product_id, store_id, MAX(checked_at) as last_available_at
                FROM availability_history
                WHERE is_available = 1
                GROUP BY product_id, store_id
            ) last_avail ON last_avail.product_id = p.id AND last_avail.store_id = s.id
            ORDER BY p.product_name, s.store_name
        """)

        results = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return results

    def get_availability_stats(self, product_id: int, store_id: int, days: int = 7) -> Dict:
        """Get availability statistics for a product/store combination"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Total checks
        cursor.execute("""
            SELECT COUNT(*) FROM availability_history
            WHERE product_id = ? AND store_id = ?
            AND checked_at > datetime('now', '-{} days')
        """.format(days), (product_id, store_id))
        total_checks = cursor.fetchone()[0]

        # Available count
        cursor.execute("""
            SELECT COUNT(*) FROM availability_history
            WHERE product_id = ? AND store_id = ? AND is_available = 1
            AND checked_at > datetime('now', '-{} days')
        """.format(days), (product_id, store_id))
        available_count = cursor.fetchone()[0]

        # Times became available
        cursor.execute("""
            SELECT COUNT(*) FROM availability_changes
            WHERE product_id = ? AND store_id = ? AND new_status = 1
            AND changed_at > datetime('now', '-{} days')
        """.format(days), (product_id, store_id))
        times_became_available = cursor.fetchone()[0]

        conn.close()

        return {
            'total_checks': total_checks,
            'available_count': available_count,
            'availability_rate': (available_count / total_checks * 100) if total_checks > 0 else 0,
            'times_became_available': times_became_available
        }

    def get_all_products(self) -> List[Dict]:
        """Get all products from the database"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM products ORDER BY created_at DESC")
        results = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return results

    def get_all_stores(self) -> List[Dict]:
        """Get all stores from the database"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM stores ORDER BY store_name")
        results = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return results