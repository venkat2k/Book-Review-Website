import os

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
    return render_template("index.html")

@app.route("/login", methods = ["POST"])
def login():
	username = request.form.get("username")
	password = request.form.get("password")
	msg = "failure"
	count = db.execute("SELECT count(*) FROM userdata where username = :username and password = :password", {"username": username, "password": password}).fetchone()
	if count[0] == 1:
		msg = "success"
	else: msg = str(count)
	db.commit()
	return render_template("success.html", result = msg)

@app.route("/signup", methods = ["POST"])
def signup():
	username = request.form.get("username")
	password = request.form.get("password")
	display_name = request.form.get("display_name")
	db.execute("INSERT INTO userdata (username, password, displayname) VALUES (:username, :password, :displayname)",
		{"username": username, "password": password, "displayname": display_name})
	db.commit()
	return render_template("success.html", result = "success")