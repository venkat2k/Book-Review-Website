import os
import requests
import json
from flask import *
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

app = Flask(__name__)

# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))


@app.route("/")
def index():
	if "username" in session:
		print("yes")
		return redirect(url_for('home'))
	else:
		return render_template("index.html")

@app.route("/login", methods = ["POST"])
def login():
	username = request.form.get("username")
	password = request.form.get("password")
	
	msg = "failure"
	count = db.execute("SELECT count(*) FROM userdata where username = :username and password = :password",
	 {"username": username, "password": password}).fetchone()
	db.commit()
	if count[0] == 1:
		msg = "success"     # needs login failure handling
		session["username"] = username
		session["display_name"] = db.execute("SELECT displayname FROM userdata where username = :username",
		{"username": username}).fetchone()
		db.commit()
	else: msg = str(count)
	
	return redirect(url_for('home'))

@app.route("/signup", methods = ["POST"])
def signup():
	username = request.form.get("username")
	password = request.form.get("password")
	display_name = request.form.get("display_name")
	session["username"] = username
	session["display_name"] = display_name
	db.execute("INSERT INTO userdata (username, password, displayname) VALUES (:username, :password, :displayname)",
		{"username": username, "password": password, "displayname": display_name})
	db.commit()
	return redirect(url_for('home'))

@app.route("/logout", methods = ["POST"])
def logout():
	session.pop("username", None)
	session.pop("display_name", None)
	return redirect(url_for('index'))

@app.route("/home")
def home():
	if "username" not in session:
		return redirect(url_for('index'))
	return render_template("home.html", username = session["username"], dname = session["display_name"])

@app.route("/results", methods = ["POST", "GET"])
def search():
	search_text = request.form.get("search_text")
	results = []
	results = db.execute("""SELECT title, isbn FROM books WHERE LOWER(title) LIKE '%{0}%' or LOWER(isbn) like '%{0}%' or LOWER(author) like '%{0}%' """.format(search_text)).fetchall()
	db.commit()
	return render_template("searchresults.html", search_text = search_text, results = results)


@app.route("/books/<string:isbn>", methods = ["POST", "GET"])
def book(isbn):
	title, author, year = db.execute("SELECT title, author, year FROM books WHERE isbn = :isbn", {"isbn": isbn}).fetchone()
	session["isbn"] = isbn
	db.commit()
	reviews = db.execute("SELECT username, review_text FROM reviews WHERE isbn = :isbn", {"isbn": isbn}).fetchall()
	ratings = db.execute("SELECT AVG(ratings) FROM reviews WHERE isbn = :isbn", {"isbn": isbn}).fetchone()
	db.commit()
	ratings = float(ratings[0])
	book_details = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": "qnNLAI3BNc89adBueNwUg", "isbns": isbn}).json()
	gr_ratings_count = book_details["books"][0]["ratings_count"]
	gr_avg_rating = book_details["books"][0]["average_rating"]
	return render_template("book.html", title = title, author = author, year = year, isbn = isbn, reviews = reviews, ratings = str(ratings),
			gr_ratings_count = gr_ratings_count, gr_avg_rating = gr_avg_rating)

@app.route("/submitreview", methods = ["POST"])
def submit_review():
	isbn = session["isbn"]
	review_text = request.form.get("review_text")
	ratings = int(request.form.get("ratings"))
	
	db.execute("INSERT INTO reviews (isbn, username, review_text, ratings) VALUES ('{0}', '{1}', '{2}', {3})".format(isbn, session["username"], review_text, ratings))
	db.commit()
	return redirect(url_for('book', isbn = isbn))

@app.route("/api/<string:isbn>", methods = ["GET"])
def api(isbn):
	title, author, year = db.execute("SELECT title, author, year FROM books WHERE isbn = :isbn", {"isbn": isbn}).fetchone()
	avg_ratings, ratings_count = db.execute("SELECT AVG(ratings), COUNT(*) FROM reviews WHERE isbn = :isbn", {"isbn": isbn}).fetchone()
	db.commit()
	result = {"title": title, "author": author, "year": year, "isbn": isbn, "review_count": ratings_count, "average_score": float(avg_ratings)}
	return json.dumps(result)