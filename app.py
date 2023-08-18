from flask import Flask, render_template, request, redirect, url_for, session
from flask_mysql_connector import MySQL
import hashlib
import yaml
import re

app = Flask(__name__)

# ____________________________________________________________________________________
# Fills out the necessary information to connect to the dB
db = yaml.full_load(open('db.yaml'))
app.config['MYSQL_HOST'] = db['mysql_host']
app.config['MYSQL_USER'] = db['mysql_user']
app.config['MYSQL_PASSWORD'] = db['mysql_password']
app.config['MYSQL_DATABASE'] = db['mysql_db']

mysql = MySQL(app)

# ____________________________________________________________________________________
# The next blocks connect each page to the dB and posts/gets the necessary information
@app.route('/')
def home():
    return render_template('home.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        userInfo = request.form
        firstname = userInfo['firstname']
        lastname = userInfo['lastname']
        occupation = userInfo['occupation']
        email = userInfo['email']
        pword = userInfo['pword']
        salt = "gabeistired"
        saltedPW = pword + salt
        h = hashlib.md5(saltedPW.encode())
        confirm = userInfo['confirm']
        pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b'
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT email FROM userinfo")
        checkEmail = cursor.fetchall()
        if (re.match(pattern, email) and pword == confirm):
            cursor.execute("INSERT INTO userinfo VALUES(%s, %s, %s, %s, %s, -1)", (occupation, firstname, lastname, email, h.hexdigest()))
            mysql.connection.commit()
            cursor.close()
            return redirect(url_for('login'))
        else:
            # THIS NEEDS TO CHANGE -- RETURN AN ERROR MESSAGE SAYING THAT PASSWORDS MUST MATCH
            return render_template('register.html')
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        userInfo = request.form
        email = userInfo['email']
        pword = userInfo['pword']
        salt = "gabeistired"
        saltedPW = pword + salt
        h = hashlib.md5(saltedPW.encode())
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT userType FROM userinfo WHERE email = %s AND userPassword = %s", (email, h.hexdigest()))
        userType = cursor.fetchone()
        cursor.execute("SELECT firstName FROM userinfo WHERE email = %s AND userPassword = %s", (email, h.hexdigest()))
        name = cursor.fetchone()
        session['name'] = name[0]
        if userType[0] == 0:
            return redirect(url_for('student_homepage'))
        elif userType[0] == 1:
            return redirect(url_for('judge_homepage'))
        else:
            return render_template('login.html')
    return render_template('login.html')

# ____________________________________________________________________________________
# This section is for the judge dashboard
@app.route('/judge/dashboard')
def judge_homepage():
    return render_template('judge_homepage.html')

@app.route('/judge/dashboard/top_scores')
def judge_homepage_scores():
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT * FROM userinfo WHERE userType=0")
    scoreInfo = cursor.fetchall()
    scoreInfo.sort(key=lambda scoreInfo: scoreInfo[5], reverse=True)
    cursor.close()
    return render_template('scores.html', scoreInfo=scoreInfo)

@app.route('/judge/dashboard/rubric')
def judge_homepage_rubric():
    return render_template('rubric.html')

@app.route('/judge/dashboard/grade', methods=['GET', 'POST'])
def judge_homepage_grade():
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT * FROM userinfo WHERE userType=0")
    liststudents = cursor.fetchall()
    cursor.close()
    if request.method == 'POST':
        userInfo = request.form
        rawname = userInfo['rawname']
        name = rawname.split()
        rawscore = userInfo['rawscore']
        cursor = mysql.connection.cursor()
        cursor.execute("UPDATE userinfo SET score = %s WHERE firstName = %s AND lastName = %s", (rawscore, name[0], name[1]))
        mysql.connection.commit()
        cursor.close()
        return redirect(url_for('judge_homepage'))
    return render_template('grading.html', liststudents=liststudents)

# ____________________________________________________________________________________
# This section is for the student dashboard
@app.route('/student/dashboard')
def student_homepage():
    return render_template('student_homepage.html')

@app.route('/student/dashboard/top_scores')
def student_homepage_scores():
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT * FROM userinfo WHERE userType=0")
    scoreInfo = cursor.fetchall()
    scoreInfo.sort(key=lambda scoreInfo: scoreInfo[5], reverse=True)
    cursor.close()
    return render_template('scores.html', scoreInfo=scoreInfo)

@app.route('/student/dashboard/rubric')
def student_homepage_rubric():
    return render_template('rubric.html')

# ____________________________________________________________________________________
# The run command MUST ALWAYS be at the very end so that everything executes correctly
if __name__ == "__main__":
    app.secret_key = 'supersecretkey!'
    app.run()
