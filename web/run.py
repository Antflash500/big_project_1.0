from flask import Flask, render_template, redirect, request, session, flash, jsonify
import sqlite3
import os

app = Flask(__name__)
app.secret_key = 'nexus_community_dashboard_secret_2024'

# ========== CONFIG ==========
USERNAME = 'admin'
PASSWORD = 'nexus123'
DATABASE_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'bot.db')

# ========== HELPERS ==========
def db_connect():
    """Connect to database"""
    try:
        os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)
        conn = sqlite3.connect(DATABASE_PATH)
        conn.row_factory = sqlite3.Row
        return conn
    except Exception as e:
        print(f"Database error: {e}")
        return None

def login_needed(f):
    """Decorator untuk require login"""
    def wrapper(*args, **kwargs):
        if 'user' not in session:
            return redirect('/login')
        return f(*args, **kwargs)
    wrapper.__name__ = f.__name__
    return wrapper

# ========== ROUTES ==========

@app.route('/')
def home_route():
    if 'user' in session:
        return redirect('/dashboard')
    return redirect('/login')

@app.route('/login', methods=['GET', 'POST'])
def login_route():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if username == USERNAME and password == PASSWORD:
            session['user'] = username
            flash('Login successful!', 'success')
            return redirect('/dashboard')
        else:
            flash('Invalid username or password', 'error')
    
    return render_template('login.html')

@app.route('/logout')
def logout_route():
    session.clear()
    flash('Logged out successfully', 'success')
    return redirect('/login')

@app.route('/dashboard')
@login_needed
def dashboard_route():
    """Dashboard utama"""
    conn = db_connect()
    stats = {'users': 0, 'messages': 0, 'commands': 0, 'filters': 0}
    
    if conn:
        try:
            result = conn.execute("SELECT COUNT(*) FROM users").fetchone()
            stats['users'] = result[0] if result else 0
            
            result = conn.execute("SELECT SUM(messages) FROM users").fetchone()
            stats['messages'] = result[0] if result and result[0] else 0
            
            result = conn.execute("SELECT COUNT(*) FROM custom_commands").fetchone()
            stats['commands'] = result[0] if result else 0
            
            result = conn.execute("SELECT COUNT(*) FROM filtered_words").fetchone()
            stats['filters'] = result[0] if result else 0
            
            conn.close()
        except Exception as e:
            print(f"Stats error: {e}")
    
    return render_template('dashboard.html', stats=stats)

@app.route('/commands')
@login_needed
def commands_route():
    """Page custom commands"""
    conn = db_connect()
    command_list = []
    
    if conn:
        try:
            command_list = conn.execute(
                "SELECT cmd_name, response FROM custom_commands ORDER BY cmd_name"
            ).fetchall()
            conn.close()
        except:
            pass
    
    return render_template('commands.html', commands=command_list)

@app.route('/api/command', methods=['POST'])
@login_needed
def add_command_api():
    """API: Add custom command"""
    data = request.json
    name = data.get('name', '').strip().lower()
    response = data.get('response', '').strip()
    
    if not name or not response:
        return jsonify({'error': 'Name and response required'}), 400
    
    conn = db_connect()
    if conn:
        try:
            conn.execute(
                "INSERT OR REPLACE INTO custom_commands (cmd_name, response) VALUES (?, ?)",
                (name, response)
            )
            conn.commit()
            conn.close()
            return jsonify({'success': True})
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    return jsonify({'error': 'Database error'}), 500

@app.route('/api/command/<name>', methods=['DELETE'])
@login_needed
def delete_command_api(name):
    """API: Delete custom command"""
    conn = db_connect()
    if conn:
        try:
            conn.execute("DELETE FROM custom_commands WHERE cmd_name = ?", (name,))
            conn.commit()
            conn.close()
            return jsonify({'success': True})
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    return jsonify({'error': 'Database error'}), 500

@app.route('/filter')
@login_needed
def filter_route():
    """Page word filter"""
    conn = db_connect()
    word_list = []
    
    if conn:
        try:
            word_list = conn.execute(
                "SELECT word FROM filtered_words ORDER BY word"
            ).fetchall()
            conn.close()
        except:
            pass
    
    return render_template('filter.html', words=word_list)

@app.route('/api/filter', methods=['POST'])
@login_needed
def add_filter_api():
    """API: Add filtered word"""
    data = request.json
    word = data.get('word', '').strip().lower()
    
    if not word:
        return jsonify({'error': 'Word required'}), 400
    
    conn = db_connect()
    if conn:
        try:
            conn.execute(
                "INSERT OR IGNORE INTO filtered_words (word) VALUES (?)",
                (word,)
            )
            conn.commit()
            conn.close()
            return jsonify({'success': True})
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    return jsonify({'error': 'Database error'}), 500

@app.route('/api/filter/<word>', methods=['DELETE'])
@login_needed
def delete_filter_api(word):
    """API: Delete filtered word"""
    conn = db_connect()
    if conn:
        try:
            conn.execute("DELETE FROM filtered_words WHERE word = ?", (word,))
            conn.commit()
            conn.close()
            return jsonify({'success': True})
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    return jsonify({'error': 'Database error'}), 500

@app.route('/api/filter', methods=['GET'])
@login_needed
def get_filters_api():
    """API: Get all filtered words"""
    conn = db_connect()
    if conn:
        try:
            words = conn.execute("SELECT word FROM filtered_words").fetchall()
            conn.close()
            return jsonify([dict(w) for w in words])
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    return jsonify({'error': 'Database error'}), 500

@app.route('/api/status')
def status_api():
    """API: Check bot status"""
    return jsonify({'online': True, 'status': 'Nexus Community Bot Dashboard running'})

# ========== RUN APP ==========

if __name__ == '__main__':
    print("=" * 50)
    print("🚀 NEXUS COMMUNITY DASHBOARD")
    print("=" * 50)
    print(f"📁 Database: {DATABASE_PATH}")
    print(f"✅ Database exists: {os.path.exists(DATABASE_PATH)}")
    print(f"🔑 Login: {USERNAME} / {PASSWORD}")
    print(f"🌐 URL: http://localhost:5000")
    print("=" * 50)
    
    app.run(debug=True, host='0.0.0.0', port=5000)