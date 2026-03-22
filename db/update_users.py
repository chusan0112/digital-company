# Update users table to add salt column
import sqlite3
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

db_path = os.path.join(os.path.dirname(__file__), 'company.db')
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Check if salt column exists
cursor.execute('PRAGMA table_info(users)')
columns = [col[1] for col in cursor.fetchall()]
print('Current columns:', columns)

if 'salt' not in columns:
    cursor.execute('ALTER TABLE users ADD COLUMN salt TEXT')
    print('Added salt column')
    conn.commit()
else:
    print('Salt column already exists')

# Re-hash the default admin password with salt
cursor.execute("SELECT id, password_hash FROM users WHERE username = 'admin'")
row = cursor.fetchone()
if row:
    from auth.jwt_auth import hash_password
    user_id = row[0]
    old_hash = row[1]
    
    # Check if already hashed (has salt)
    cursor.execute("SELECT salt FROM users WHERE id = ?", (user_id,))
    salt_row = cursor.fetchone()
    
    if salt_row[0] is None:
        # Re-hash the password with proper salt
        new_hash, salt = hash_password("admin123")
        cursor.execute("UPDATE users SET password_hash = ?, salt = ? WHERE id = ?", 
                      (new_hash, salt, user_id))
        conn.commit()
        print(f"Updated admin password hash with salt")
    else:
        print("Admin password already properly hashed")

conn.close()
print("Done!")
