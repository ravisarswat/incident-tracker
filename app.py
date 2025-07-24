from flask import Flask, render_template, request, redirect, send_file, url_for
import sqlite3
import pandas as pd
import io
import os
import math

app = Flask(__name__)

DB_PATH = 'database/incidents.db'

# Ensure the database directory and schema are set up
def init_db():
    os.makedirs('database', exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS incidents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            incident_number TEXT,
            month TEXT,
            opened_date TEXT,
            initial_severity TEXT,
            final_impact_classification TEXT,
            accountability TEXT,
            product_line TEXT,
            product TEXT,
            seal_id TEXT,
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

# Handle form submission and store new incident entry
@app.route('/submit', methods=['POST'])
def submit():
    data = [
        request.form.get('incident_number'),
        request.form.get('month'),
        request.form.get('opened_date'),
        request.form.get('initial_severity'),
        request.form.get('final_impact_classification'),
        request.form.get('accountability'),
        request.form.get('product_line'),
        request.form.get('product'),
        request.form.get('seal_id'),
        request.form.get('issue_description'),
        request.form.get('impact'),
        request.form.get('timeline_summary'),
        request.form.get('root_cause'),
        request.form.get('code_review'),
        request.form.get('testing'),
        request.form.get('follow_up'),
        request.form.get('reviewed'),
        request.form.get('reviewed_date')
    ]

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        INSERT INTO incidents (
            incident_number, month, opened_date, initial_severity,
            final_impact_classification, accountability, product_line,
            product, seal_id, issue_description, impact, timeline_summary,
            root_cause, code_review, testing, follow_up, reviewed, reviewed_date
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', data)
    conn.commit()
    conn.close()

    return redirect('/view')

# Display incident list with optional search and pagination
@app.route('/view')
def view():
    keyword = request.args.get('search', '').strip()
    page = int(request.args.get('page', 1))
    limit = 10
    offset = (page - 1) * limit

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    if keyword:
        count_query = '''
        SELECT COUNT(*) FROM incidents
        WHERE incident_number LIKE ?
        OR issue_description LIKE ?
        OR impact LIKE ?
        OR root_cause LIKE ?
        OR follow_up LIKE ?
        OR code_review LIKE ?
        OR product LIKE ?
        OR reviewed LIKE ?
        OR reviewed_date LIKE ?
        '''
        count_params = [f"%{keyword}%"] * 9
        c.execute(count_query, count_params)
        total_rows = c.fetchone()[0]

        query = '''
        SELECT * FROM incidents
        WHERE incident_number LIKE ?
        OR issue_description LIKE ?
        OR impact LIKE ?
        OR root_cause LIKE ?
        OR follow_up LIKE ?
        OR code_review LIKE ?
        OR product LIKE ?
        OR reviewed LIKE ?
        OR reviewed_date LIKE ?
        ORDER BY id DESC
        LIMIT ? OFFSET ?
        '''
        params = [f"%{keyword}%"] * 9 + [limit, offset]
        c.execute(query, params)
    else:
        c.execute('SELECT COUNT(*) FROM incidents')
        total_rows = c.fetchone()[0]
        c.execute('SELECT * FROM incidents ORDER BY id DESC LIMIT ? OFFSET ?', (limit, offset))

    records = c.fetchall()
    conn.close()

    total_pages = math.ceil(total_rows / limit)

    return render_template('view.html', incidents=records, search=keyword, page=page, total_pages=total_pages)

# Edit an existing incident by ID
@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit(id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    if request.method == 'POST':
        data = [
            request.form.get('incident_number'),
            request.form.get('month'),
            request.form.get('opened_date'),
            request.form.get('initial_severity'),
            request.form.get('final_impact_classification'),
            request.form.get('accountability'),
            request.form.get('product_line'),
            request.form.get('product'),
            request.form.get('seal_id'),
            request.form.get('issue_description'),
            request.form.get('impact'),
            request.form.get('timeline_summary'),
            request.form.get('root_cause'),
            request.form.get('code_review'),
            request.form.get('testing'),
            request.form.get('follow_up'),
            request.form.get('reviewed'),
            request.form.get('reviewed_date'),
            id
        ]
        c.execute('''
            UPDATE incidents SET
                incident_number=?, month=?, opened_date=?, initial_severity=?,
                final_impact_classification=?, accountability=?, product_line=?,
                product=?, seal_id=?, issue_description=?, impact=?, timeline_summary=?,
                root_cause=?, code_review=?, testing=?, follow_up=?, reviewed=?, reviewed_date=?
            WHERE id=?
        ''', data)
        conn.commit()
        conn.close()
        return redirect('/view')
    else:
        c.execute('SELECT * FROM incidents WHERE id=?', (id,))
        record = c.fetchone()
        conn.close()
        return render_template('edit.html', record=record)

# Delete an incident entry
@app.route('/delete/<int:id>')
def delete(id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('DELETE FROM incidents WHERE id=?', (id,))
    conn.commit()
    conn.close()
    return redirect('/view')

# Export all incidents to an Excel file
@app.route('/export')
def export_excel():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT * FROM incidents ORDER BY id DESC", conn)
    conn.close()

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Incidents')

    output.seek(0)
    return send_file(output, download_name="incidents_export.xlsx", as_attachment=True)

if __name__ == '__main__':
    init_db()
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)

