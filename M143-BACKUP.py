from flask import Flask, render_template, request, redirect
import sqlite3
from datetime import datetime

app = Flask(__name__)
DB_NAME = "entries.db"

# Initialize database
def init_db():
    conn = sqlite3.connect(DB_NAME)
    conn.execute('CREATE TABLE IF NOT EXISTS entries (id INTEGER PRIMARY KEY, content TEXT, timestamp TEXT)')
    conn.commit()
    conn.close()

@app.route('/')
def index():
    conn = sqlite3.connect(DB_NAME)
    entries = conn.execute('SELECT * FROM entries ORDER BY id DESC').fetchall()
    conn.close()
    return render_template('index.html', entries=entries)

@app.route('/add', methods=['POST'])
def add():
    content = request.form.get('content')
    if content:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        conn = sqlite3.connect(DB_NAME)
        conn.execute('INSERT INTO entries (content, timestamp) VALUES (?, ?)', (content, timestamp))
        conn.commit()
        conn.close()
    return redirect('/')

@app.route('/delete/<int:id>')
def delete(id):
    conn = sqlite3.connect(DB_NAME)
    conn.execute('DELETE FROM entries WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    return redirect('/')

if __name__ == '__main__':
    init_db()
    app.run(debug=True)