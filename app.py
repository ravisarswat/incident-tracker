
from flask import Flask, render_template, request, redirect, url_for
import sqlite3
import os

app = Flask(__name__)

DB_FILE = 'database/incidents.db'

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS incidents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            incident_number TEXT,
            month TEXT,
            opened_date TEXT,
            final_impact_classification TEXT,
            accountability TEXT,
            product_line TEXT,
            product TEXT,
            seal_id TEXT,
            seal_name TEXT,
            issue_description TEXT,
            impact TEXT,
            timeline_summary TEXT,
            root_cause TEXT,
            code_review TEXT,
            testing TEXT,
            follow_up TEXT,
            reviewed TEXT,
            reviewed_date TEXT
        )
    ''')
    conn.commit()
    conn.close()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/submit', methods=['POST'])
def submit():
    data = (
        request.form['incident_number'],
        request.form['month'],
        request.form['opened_date'],
        request.form['final_impact_classification'],
        request.form['accountability'],
        request.form['product_line'],
        request.form['product'],
        request.form['seal_id'],
        request.form['seal_name'],
        request.form['issue_description'],
        request.form['impact'],
        request.form['timeline_summary'],
        request.form['root_cause'],
        request.form['code_review'],
        request.form['testing'],
        request.form['follow_up'],
        request.form['reviewed'],
        request.form['reviewed_date']
    )
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO incidents (
            incident_number, month, opened_date, final_impact_classification,
            accountability, product_line, product, seal_id, seal_name,
            issue_description, impact, timeline_summary, root_cause,
            code_review, testing, follow_up, reviewed, reviewed_date
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', data)
    conn.commit()
    conn.close()
    return redirect('/view')

@app.route('/view')
def view():
    search = request.args.get('search', '')
    page = int(request.args.get('page', 1))
    per_page = 20
    offset = (page - 1) * per_page

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    if search:
        query = f'''SELECT * FROM incidents WHERE
            incident_number LIKE ? OR
            reviewed LIKE ? OR
            month LIKE ?
            ORDER BY id DESC LIMIT ? OFFSET ?'''
        params = [f'%{search}%'] * 3 + [per_page, offset]
        cursor.execute(query, params)
    else:
        cursor.execute('SELECT * FROM incidents ORDER BY id DESC LIMIT ? OFFSET ?', (per_page, offset))
    incidents = cursor.fetchall()

    cursor.execute('SELECT COUNT(*) FROM incidents')
    total_records = cursor.fetchone()[0]
    total_pages = (total_records + per_page - 1) // per_page

    conn.close()
    return render_template('view.html', incidents=incidents, search=search, page=page, total_pages=total_pages)

@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit(id):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    if request.method == 'POST':
        data = (
            request.form['incident_number'],
            request.form['month'],
            request.form['opened_date'],
            request.form['final_impact_classification'],
            request.form['accountability'],
            request.form['product_line'],
            request.form['product'],
            request.form['seal_id'],
            request.form['seal_name'],
            request.form['issue_description'],
            request.form['impact'],
            request.form['timeline_summary'],
            request.form['root_cause'],
            request.form['code_review'],
            request.form['testing'],
            request.form['follow_up'],
            request.form['reviewed'],
            request.form['reviewed_date']
        )
        cursor.execute('''
            UPDATE incidents SET
                incident_number = ?, month = ?, opened_date = ?, final_impact_classification = ?,
                accountability = ?, product_line = ?, product = ?, seal_id = ?, seal_name = ?,
                issue_description = ?, impact = ?, timeline_summary = ?, root_cause = ?,
                code_review = ?, testing = ?, follow_up = ?, reviewed = ?, reviewed_date = ?
            WHERE id = ?
        ''', (*data, id))
        conn.commit()
        conn.close()
        return redirect('/view')
    else:
        cursor.execute('SELECT * FROM incidents WHERE id = ?', (id,))
        record = cursor.fetchone()
        conn.close()
        return render_template('edit.html', record=record)

@app.route('/delete/<int:id>')
def delete(id):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM incidents WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    return redirect('/view')

@app.route('/export')
def export():
    import pandas as pd
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql_query('SELECT * FROM incidents', conn)
    conn.close()
    filepath = 'exported_incidents.xlsx'
    df.to_excel(filepath, index=False)
    return f'Data exported to {filepath}'

if __name__ == '__main__':
    os.makedirs('database', exist_ok=True)
    init_db()
    app.run(debug=True)
