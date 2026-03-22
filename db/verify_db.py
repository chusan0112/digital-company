#!/usr/bin/env python3
import sqlite3
conn = sqlite3.connect('company.db')
cursor = conn.cursor()

# 查询所有表
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
tables = cursor.fetchall()
print('=== 数据库表 ===')
for t in tables:
    print(f'  - {t[0]}')

# 查询各表数据量
print('\n=== 各表数据量 ===')
for table in ['users', 'departments', 'employees', 'projects', 'tasks', 'decisions', 'approvals', 'meetings', 'meeting_rooms', 'audit_logs']:
    cursor.execute(f'SELECT COUNT(*) FROM {table}')
    count = cursor.fetchone()[0]
    print(f'  {table}: {count} 条')

# 查询示例数据
print('\n=== 部门示例 ===')
cursor.execute('SELECT * FROM departments')
for row in cursor.fetchall():
    print(f'  {row}')

print('\n=== 员工示例 ===')
cursor.execute('SELECT id, name, role, department_id, skills, status FROM employees')
for row in cursor.fetchall():
    print(f'  {row}')

print('\n=== 会议室示例 ===')
cursor.execute('SELECT * FROM meeting_rooms')
for row in cursor.fetchall():
    print(f'  {row}')

conn.close()
