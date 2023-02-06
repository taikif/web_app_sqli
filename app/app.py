from flask import Flask, flash, redirect, request, render_template, has_request_context
from flask.logging import default_handler
import sqlite3
import logging
import datetime
import requests

conn = sqlite3.connect('webapp.db')
    
app = Flask(__name__)
app.config['USERNAME'] = 'admin'
app.config['PASSWORD'] = 'password'
app.config['SECRET_KEY'] = 'secret'

class RequestFormatter(logging.Formatter):
    def format(self, record):
        if has_request_context():
            record.url = request.url
            record.remote_addr = request.remote_addr
        else:
            record.url = None
            record.remote_addr = None

        return super().format(record)

formatter = RequestFormatter(
    '[%(asctime)s] %(remote_addr)s requested %(url)s '
    '%(levelname)s in %(module)s: %(message)s'
)

default_handler.setFormatter(formatter)
default_handler.setLevel(logging.INFO)

werkzeug_logger = logging.getLogger('werkzeug')
werkzeug_logger.addHandler(default_handler)

@app.route("/")
def hello():
    return redirect('/login')

@app.route("/signup", methods=['GET'])
def signup_get():
    return render_template("signup.html")

@app.route("/signup", methods=['POST'])
def signup_post():
    username = request.form["name"]
    password = request.form["password"]
    conn = sqlite3.connect('webapp.db')
    cur = conn.cursor()
    sql = "INSERT INTO users(name, password) values(?,?)"
    data = [username, password]
    cur.execute(
        sql,data
    )
    conn.commit()
    conn.close()
    return render_template("index.html", username=username)

@app.route("/login", methods=['GET'])
def login_get():
    return render_template("login.html")

@app.route("/login", methods=['POST'])
def login_post():
    username = request.form["username"]
    password = request.form["password"]
    conn = sqlite3.connect('webapp.db')
    #logging.basicConfig(level=logging.NOTSET, format="%(asctime)s - %(levelname)s:%(name)s - %(message)s", filename="test.log")
    #脆弱な雛形を用意する。判定の仕方も脆弱。
    sql = f"SELECT * FROM users WHERE name = '{username}' and password = '{password}'"
    curs = conn.execute(
        sql
    ).fetchall()
    index_sql = f"SELECT * FROM books"
    index = conn.execute(
        index_sql
    ).fetchall()
    
    if not curs:
        #ログをローテートする処理を書く
        dt = datetime.datetime.now()
        loginfo = [ str(dt.strftime('%Y-%m-%d %H:%M:%S')),
                    request.method,
                    request.url,
                    request.path,
                    request.scheme,
                    request.form["username"],
                    request.form["password"]
        ]
        print(loginfo)
        flash('failed to login')
        
        payload={'ip_address':request.remote_addr,'event1':request.form["username"],'event2':request.form["password"]}
        
        r = requests.post("https://taikifdashboard.herokuapp.com/detection", data=payload)
        
        return redirect('/login')
    
    #ログをローテートする処理を書く
    loginfo = [ str(request.date),
                request.method,
                request.url,
                request.path,
                request.scheme,
                request.form["username"],
                request.form["password"]
    ]
    print(loginfo)
    return render_template('index.html',username=username, db=index)


@app.route("/index", methods=['POST'])
def index_post():
    username = request.form["username"]
    bookname = request.form["bookname"]
    conn = sqlite3.connect('webapp.db')
    
    #もしbooknameが空だったら全件表示するようにする
    if not bookname:
        sql = f"SELECT * FROM books"
        curs = conn.execute(
            sql
        ).fetchall()
        db = curs
        error_message = ""
    else:
        sql = f"SELECT * FROM books WHERE title = '{bookname}'"
        try:
            curs = conn.execute(
                sql
            ).fetchall()
            db = curs
            error_message = ''
        except:
            error_message = "攻撃しないでください！！( *´艸｀)"
            db = ''
            return render_template('index.html', username=username, db=db, error_message=error_message)
        if not db:
            error_message = "お探しの本はないみたいです( *´艸｀)"
    return render_template('index.html', username=username,db=db,error_message=error_message)

@app.route("/index")
def index():
    username = request.form["username"]
    if username is None:
        return redirect('/login')
    else:
        conn = sqlite3.connect('webapp.db')
        sql = f"SELECT * FROM books"
        curs = conn.execute(
            sql
        ).fetchall()
        db = curs
        return render_template('index.html', username=username, db=db)
    
@app.route("/index",methods=['GET'])
def index_get():
    username=request.form["username"]
    return render_template('index.html', username=username)
@app.route('/logout')
def logout():
    flash('ログアウトしました')
    return redirect('/login')

conn.close()
