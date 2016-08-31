import sqlite3
import time
import hashlib
from flask import Flask, request, session, g, redirect, url_for, \
      abort, render_template, flash
from contextlib import closing

DATABASE = 'db/woj.db'
DEBUG = True
SECRET_KEY = 'development key'

app = Flask(__name__)
app.config.from_object(__name__)

def connect_db():
    return sqlite3.connect(app.config['DATABASE'])

def init_db():
    with closing(connect_db()) as db:
        with app.open_resource('schema.sql', 'r') as f:
            db.cursor().executescript(f.read())
        db.commit()

@app.before_request
def before_request():
    g.db = connect_db()

@app.teardown_request
def teardown_request(exception):
    db = getattr(g, 'db', None)
    if db is not None:
        db.close()

@app.route('/')
def show_diaries():
    diaries = [(),]
    if session.get('logged_in'):
        userId = session.get('userId')
        cur = g.db.execute('select title, text, date from diaries where userId = ? order by id desc', [userId])
        diaries = [dict(title=row[0], text=row[1], date=row[2]) for row in cur.fetchall()]
    
    return render_template('show_diaries.html', diaries=diaries)

@app.route('/add_diary', methods=['POST'])
def add_diary():
    if not session.get('logged_in'):
        abort(401)
    userId = session.get('userId')
    now_date = time.strftime("%Y-%m-%d %H:%M %p", time.localtime())
    g.db.execute('insert into diaries (userId, title, text, date) values (?,?,?,?)',[userId, request.form['title'], request.form['text'], now_date])
    g.db.commit()
    flash('New diary was witten down')
    return redirect(url_for('show_diaries'))

@app.route('/register', methods=['GET','POST'])
def register():
    error = None
    if request.method == 'POST':
        username = request.form['username']
        if username == None:
            error = 'What?! Do you want to register without Username?'
            return render_template('register.html', error=error)
        password = request.form['password']
        if password == None:
            error = 'Fuck up you stupid asshole! Do you want to register without Password?'
            return render_template('register.html', error=error)
        cur = g.db.execute("select username from users where username = ?", [username])
        user = cur.fetchone()
        if user != None:
            error = 'Username already exists'
        else:
            p_md5 = hashlib.md5()
            p_md5.update(password.encode("ascii"))
            password_md5 = p_md5.hexdigest() 
            g.db.execute("insert into users (username, password) values (?,?)", [username, password_md5])
            g.db.commit()
            flash('Successfully registered')
            return redirect(url_for('login'))
    return render_template('register.html', error=error)


@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form['username']
        if username == '':
            error = 'What?! Do you want to login without Username?'
            return render_template('login.html', error=error)
        password = request.form['password']
        p_md5 = hashlib.md5()
        p_md5.update(password.encode('ascii'))
        password_md5 = p_md5.hexdigest()
        cur = g.db.execute('select username, password, userId from users where username = ?', [username])
        user = cur.fetchone()
        if user == None:
            error = 'User not exists'
        elif password_md5 != user[1]:
            error = 'Invalid password'
        else:
            session['logged_in'] = True
            session['userId'] = user[2]
            flash('You were logged in')
            return redirect(url_for('show_diaries'))
    return render_template('login.html', error=error)

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    session.pop('userId', None)
    flash('You were logged out')
    return redirect(url_for('show_diaries'))



if __name__ == "__main__":
    app.run()
