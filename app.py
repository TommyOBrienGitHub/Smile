from flask import Flask, render_template, request, session, redirect
import sqlite3
from sqlite3 import Error
from flask_bcrypt import Bcrypt
from datetime import datetime

DB_NAME = "smile.db"

app = Flask(__name__)
bcrypt = Bcrypt(app)
app.secret_key = "secret_key"


# creates a connection to the database
# inputs: database file
# outputs: the connection to the db or none.
def create_connection(db_file):
    """ create a connection to the sqlite db"""
    try:
        connection = sqlite3.connect(db_file)
        return connection
    except Error as e:
        print(e)

    return None


@app.route('/')
def render_homepage():
    return render_template("home.html", logged_in=is_logged_in())


@app.route('/menu')
@app.route('/menu/<products>')
def render_menu_page():
    con = create_connection(DB_NAME)

    query = "SELECT name, description, volume, price, image FROM product"

    cur = con.cursor()
    cur.execute(query)
    product_list = cur.fetchall()
    con.close()

    return render_template("menu.html", products=product_list, logged_in=is_logged_in())


@app.route('/contact')
def render_contact():
    return render_template("contact.html", logged_in=is_logged_in())


@app.route('/login', methods=['GET', 'POST'])
def render_login_page():
    if is_logged_in():
        return redirect('/')

    if request.method == 'POST':
        email = request.form['email'].strip().lower()
        password = request.form['password'].strip()

        query = """SELECT id, fname, password FROM customers WHERE email = ?"""
        con = create_connection(DB_NAME)
        cur = con.cursor()
        cur.execute(query, (email,))
        user_data = cur.fetchall()
        con.close()

        try:
            userid = user_data[0][0]
            firstname = user_data[0][1]
            db_password = user_data[0][2]
        except IndexError:
            return redirect("/login?error=Email+invalid+or+password+incorrect")

        if not bcrypt.check_password_hash(db_password, password):
            return redirect(request.referrer + "?error=Email+invalid+or+password+incorrect")

        session['email'] = email
        session['userid'] = userid
        session['firstname'] = firstname
        print(session)
        return redirect('/')
    return render_template("login.html", logged_in=is_logged_in())


@app.route('/signup', methods=['GET', 'POST'])
def render_signup_page():
    if is_logged_in():
        return redirect('/')

    if request.method == 'POST':
        print(request.form)
        fname = request.form.get('fname').strip().title()
        lname = request.form.get('lname').strip().title()
        email = request.form.get('email').strip().lower()
        password = request.form.get('password')
        password2 = request.form.get('password2')

        if password != password2:
            return redirect('/signup?error=Passwords+dont+match')

        if len(password) < 8:
            return redirect('/signup?error=Password+must+be+8+characters+or+more')

        hashed_password = bcrypt.generate_password_hash(password)
        con = create_connection(DB_NAME)

        query = "INSERT INTO customer(id, fname, lname, email, password) VALUES(NULL,?,?,?,?)"

        cur = con.cursor()
        try:
            cur.execute(query, (fname, lname, email, hashed_password))
        except sqlite3.IntegrityError:
            return redirect('/signup?error=Email+is+already+taken')

        con.commit()
        con.close()
        return redirect('/login')
    return render_template("signup.html", logged_in=is_logged_in())


@app.route('/addtocart/<productid>')
def addtocart(productid):
    try:
        productid = int(productid)
    except ValueError:
        print("{} is not an integer".format(productid))
        return redirect("/menu?error=Invalid+product+id")

    userid = session['userid']
    timestamp = datetime.now()
    print("User {} would like to add {} to cart at {}".format(userid, productid, timestamp))

    query = "INSERT INTO cart(id,userid,productid,timestamp) Values (NULL,?,?,?)"
    con = create_connection(DB_NAME)
    cur = con.cursor()
    cur.execute(query, (userid, productid, timestamp))
    con.commit()
    con.close()
    return redirect(request.referrer)


def is_logged_in():
    if session.get('email') is None:
        print('Not logged in')
        return False
    print('Logged in')
    return True


@app.route('/logout')
def logout():
    print(list(session.keys()))
    [session.pop(key) for key in list(session.keys())]
    print(list(session.keys()))
    return redirect(request.referrer + '?message=See+you+next+time!')

def create_connection(db_file):
   """create a connection to the sqlite db"""
   try:
       connection = sqlite3.connect(db_file)
       connection.execute('pragma foreign_keys=ON')
       return connection
   except Error as e:
       print(e)

   return None


app.run(host="0.0.0.0", debug=True)
