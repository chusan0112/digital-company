#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Digital Company SQLite Database Initialization Script
Creates all tables and indexes for the company database
"""

import sqlite3
import os
from datetime import datetime

# Database file path
DB_PATH = os.path.join(os.path.dirname(__file__), 'company.db')


def create_tables(conn):
    """Create all database tables"""
    cursor = conn.cursor()
    
    # 1. users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'user',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    print("[OK] users table created")
    
    # 2. departments table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS departments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            parent_id INTEGER REFERENCES departments(id),
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    print("[OK] departments table created")
    
    # 3. employees table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS employees (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            role TEXT NOT NULL,
            department_id INTEGER REFERENCES departments(id),
            skills TEXT,
            status TEXT DEFAULT 'active',
            hire_date DATE,
            salary REAL,
            performance REAL
        )
    ''')
    print("[OK] employees table created")
    
    # 4. projects table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS projects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            status TEXT DEFAULT 'planning',
            priority TEXT DEFAULT 'medium',
            department_id INTEGER REFERENCES departments(id),
            start_date DATE,
            end_date DATE,
            budget REAL,
            progress REAL DEFAULT 0
        )
    ''')
    print("[OK] projects table created")
    
    # 5. tasks table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            project_id INTEGER REFERENCES projects(id),
            assignee_id INTEGER REFERENCES employees(id),
            status TEXT DEFAULT 'pending',
            priority TEXT DEFAULT 'medium',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            due_date DATE
        )
    ''')
    print("[OK] tasks table created")
    
    # 6. decisions table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS decisions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME,
            intent TEXT NOT NULL,
            policy TEXT,
            executive_panel TEXT,
            options TEXT,
            summary TEXT,
            status TEXT DEFAULT 'pending',
            execution_result TEXT
        )
    ''')
    print("[OK] decisions table created")
    
    # 7. approvals table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS approvals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            status TEXT DEFAULT 'pending',
            payload TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME,
            decided_at DATETIME,
            decision TEXT,
            comments TEXT
        )
    ''')
    print("[OK] approvals table created")
    
    # 8. audit_logs table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS audit_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_type TEXT NOT NULL,
            actor TEXT,
            target TEXT,
            details TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    print("[OK] audit_logs table created")
    
    # 9. meetings table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS meetings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            host_id INTEGER REFERENCES employees(id),
            start_time DATETIME NOT NULL,
            end_time DATETIME NOT NULL,
            status TEXT DEFAULT 'scheduled',
            notes TEXT,
            action_items TEXT
        )
    ''')
    print("[OK] meetings table created")
    
    # 10. meeting_rooms table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS meeting_rooms (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            capacity INTEGER NOT NULL,
            location TEXT,
            status TEXT DEFAULT 'available'
        )
    ''')
    print("[OK] meeting_rooms table created")
    
    conn.commit()


def create_indexes(conn):
    """Create indexes to improve query performance"""
    cursor = conn.cursor()
    
    indexes = [
        ("idx_users_username", "users", "username"),
        ("idx_employees_department", "employees", "department_id"),
        ("idx_projects_department", "projects", "department_id"),
        ("idx_projects_status", "projects", "status"),
        ("idx_tasks_project", "tasks", "project_id"),
        ("idx_tasks_assignee", "tasks", "assignee_id"),
        ("idx_tasks_status", "tasks", "status"),
        ("idx_decisions_status", "decisions", "status"),
        ("idx_approvals_status", "approvals", "status"),
        ("idx_audit_logs_event_type", "audit_logs", "event_type"),
        ("idx_audit_logs_created_at", "audit_logs", "created_at"),
        ("idx_meetings_host_id", "meetings", "host_id"),
        ("idx_meetings_start_time", "meetings", "start_time"),
    ]
    
    for idx_name, table, column in indexes:
        try:
            cursor.execute(f"CREATE INDEX IF NOT EXISTS {idx_name} ON {table}({column})")
            print(f"[OK] Index {idx_name} created")
        except sqlite3.Error as e:
            print(f"[FAIL] Index {idx_name} failed: {e}")
    
    conn.commit()


def insert_sample_data(conn):
    """Insert sample data"""
    cursor = conn.cursor()
    
    # Insert default admin user
    cursor.execute('''
        INSERT OR IGNORE INTO users (username, password_hash, role)
        VALUES ('admin', 'admin123', 'admin')
    ''')
    
    # Insert sample departments
    cursor.execute('''
        INSERT OR IGNORE INTO departments (id, name, description, parent_id)
        VALUES 
        (1, 'Headquarters', 'Company headquarters', NULL),
        (2, 'Technology', 'Tech R&D department', 1),
        (3, 'Marketing', 'Marketing department', 1)
    ''')
    
    # Insert sample employees
    cursor.execute('''
        INSERT OR IGNORE INTO employees (id, name, role, department_id, skills, status, hire_date, salary, performance)
        VALUES 
        (1, 'Zhang San', 'CTO', 2, '["Python", "SQL", "System Design"]', 'active', '2023-01-15', 50000, 95),
        (2, 'Li Si', 'Marketing Director', 3, '["Marketing", "Sales"]', 'active', '2022-06-01', 45000, 88),
        (3, 'Wang Wu', 'Senior Engineer', 2, '["Java", "React", "DevOps"]', 'active', '2023-03-20', 35000, 90)
    ''')
    
    # Insert sample meeting rooms
    cursor.execute('''
        INSERT OR IGNORE INTO meeting_rooms (id, name, capacity, location, status)
        VALUES 
        (1, 'Room A', 10, '3F 301', 'available'),
        (2, 'Room B', 6, '3F 302', 'available'),
        (3, 'VIP Room', 15, '5F 501', 'available')
    ''')
    
    conn.commit()
    print("[OK] Sample data inserted")


def main():
    """Main function"""
    print("=" * 50)
    print("Digital Company SQLite Database Initialization")
    print("=" * 50)
    print(f"\nDatabase path: {DB_PATH}")
    print(f"Init time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("-" * 50)
    
    # Delete existing database file if exists
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
        print(f"[OK] Old database file removed: {DB_PATH}")
    
    # Create database connection
    conn = sqlite3.connect(DB_PATH)
    print(f"[OK] Database connection established")
    
    try:
        # Create tables
        create_tables(conn)
        
        # Create indexes
        create_indexes(conn)
        
        # Insert sample data
        insert_sample_data(conn)
        
        print("-" * 50)
        print("[OK] Database initialization completed!")
        
        # Verify tables
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        tables = cursor.fetchall()
        print(f"\nTables created ({len(tables)}):")
        for table in tables:
            print(f"  - {table[0]}")
        
    except sqlite3.Error as e:
        print(f"[FAIL] Database initialization failed: {e}")
        conn.rollback()
    finally:
        conn.close()
    
    print("=" * 50)
    return DB_PATH


if __name__ == "__main__":
    db_path = main()
