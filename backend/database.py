import sqlite3
import os
import json
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), 'history.db')

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initializes the database schema if it doesn't already exist."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS comparisons (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_a_name TEXT NOT NULL,
            file_b_name TEXT NOT NULL,
            comparison_date TEXT NOT NULL,
            summary TEXT NOT NULL,       -- JSON string of summary stats
            results_json TEXT NOT NULL   -- JSON string of detailed comparison data
        )
    ''')
    conn.commit()
    conn.close()

def save_comparison(file_a_name, file_b_name, summary, results):
    """
    Saves a comparison run into the database.
    
    :param file_a_name: Name of the original file
    :param file_b_name: Name of the compared file
    :param summary: Dictionary of summary statistics & overview
    :param results: Dictionary of detailed comparison results
    :return: The ID of the inserted record
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    comparison_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    cursor.execute(
        '''
        INSERT INTO comparisons (file_a_name, file_b_name, comparison_date, summary, results_json)
        VALUES (?, ?, ?, ?, ?)
        ''',
        (
            file_a_name,
            file_b_name,
            comparison_date,
            json.dumps(summary),
            json.dumps(results)
        )
    )
    conn.commit()
    inserted_id = cursor.lastrowid
    conn.close()
    return inserted_id

def get_history(limit=50):
    """Retrieves list of past comparisons ordered by date descending."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        '''
        SELECT id, file_a_name, file_b_name, comparison_date, summary
        FROM comparisons
        ORDER BY id DESC
        LIMIT ?
        ''',
        (limit,)
    )
    rows = cursor.fetchall()
    conn.close()
    
    history = []
    for row in rows:
        history.append({
            'id': row['id'],
            'file_a_name': row['file_a_name'],
            'file_b_name': row['file_b_name'],
            'comparison_date': row['comparison_date'],
            'summary': json.loads(row['summary'])
        })
    return history

def get_comparison(comp_id):
    """Retrieves a single comparison record with detailed results."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        '''
        SELECT id, file_a_name, file_b_name, comparison_date, summary, results_json
        FROM comparisons
        WHERE id = ?
        ''',
        (comp_id,)
    )
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return {
            'id': row['id'],
            'file_a_name': row['file_a_name'],
            'file_b_name': row['file_b_name'],
            'comparison_date': row['comparison_date'],
            'summary': json.loads(row['summary']),
            'results': json.loads(row['results_json'])
        }
    return None

def delete_comparison(comp_id):
    """Deletes a comparison record by ID."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM comparisons WHERE id = ?', (comp_id,))
    conn.commit()
    conn.close()
    return True

# Initialize database schema immediately when module is imported
init_db()
