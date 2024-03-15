import os
import csv

from cs50 import SQL
from datetime import datetime, timedelta
from flask import Flask, redirect, render_template, request, session, send_file
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required

# Configure application
app = Flask(__name__)

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///happynotes.db")


@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


# Index page that also has the "add" functionality

"""
    Option to immediately write to today if haven't already (Add). This function will ask the user to rate their day, then write some extra notes.
"""


@app.route("/", methods=["GET", "POST"])
@login_required
def index():
    # Getting list of ratings to feed into page, and also to check in POST method later
    ratings = list(range(1, 11))

    # Obtaining user streak and displayname
    rows = db.execute(
        "SELECT displayname, streak FROM users WHERE id = ?", session["user_id"]
    )
    if len(rows) != 1:
        return apology("Unable to find user streak", 400)
    try:
        streak = int(rows[0]['streak'])
        displayname = rows[0]['displayname']
    except ValueError:
        return apology("Unable to convert user streak", 400)

    # Loading page
    if request.method == "GET":

        # Getting user timezone #to check what day it is for user when they submitted the latest happy note
        timezone = timezone_check()

        # Database's timezone is currently UTC+3, we gotta do some arithmetic to calculate user's time difference
        difference = timezone - 3       # use "+" in conversion, not "-"

        # Get current time, according to user's timezone
        current_time = datetime.now() + timedelta(hours=difference)

        # Check for user's latest happy note timestamp
        rows = db.execute(
            "SELECT time FROM notes WHERE user_id = ? ORDER BY time DESC LIMIT 1", session["user_id"]
        )

        # If there is no previous note
        if len(rows) == 0:
            date = current_time
            return render_template("index.html", streak=streak, ratings=ratings, date=date, displayname=displayname)

        # If there is a previous note, check if user can write a new note
        else:

            # Making a 'timestamp' object that corresponds to python's datetime data type
            time = rows[0]['time']
            timestamp = datetime.strptime(time, '%Y-%m-%d %H:%M:%S')

            # Calculate time when submitting note according to user's timezone
            timestamp = timestamp + timedelta(hours=difference)

            # Check if it's been a new day for user, if yes then render template with add, otherwise no.
            if timestamp.date() != current_time.date():
                # Get timestamp at the start of the current day for user
                current_day = current_time.replace(hour=0, minute=0, second=0)

                # Get timestamp at the start of the day of the latest note
                latest_day = timestamp.replace(hour=0, minute=0, second=0)

                # Get how much time has passed since the start of the 2 days. If it's bigger than 1 day, user has lost the streak
                wait = current_day - latest_day
                if wait.days > 1:
                    streak = 0
                    db.execute(
                        "UPDATE users SET streak = ? WHERE id = ?", streak, session["user_id"]
                    )

                # Render index that user can add notes
                date = current_time
                return render_template("index.html", streak=streak, ratings=ratings, date=date, displayname=displayname)
            else:
                # Hours, minutes and seconds before user can write a new note
                next_day = current_time + timedelta(days=1)
                next_day = next_day.replace(hour=0, minute=0, second=0)  # Next day at midnight

                remaining = next_day - current_time  # this is a timedelta object, NOT a datetime object

                # Simple arithmetic to calculate hours, minutes and seconds
                totalseconds = remaining.total_seconds()
                hours = totalseconds // 3600
                totalseconds %= 3600
                minutes = totalseconds // 60
                totalseconds %= 60
                seconds = totalseconds

                # Render index that user can't add notes
                return render_template("index_addless.html", streak=streak, hours=hours, minutes=minutes, seconds=seconds, displayname=displayname)

    else:  # Submitting form

        # Ensure all info is provided
        if not request.form.get("rating"):
            return apology("Must provide rating", 400)
        if not request.form.get("content"):
            return apology("Must provide content/description", 400)

        # Casting rating into an int, and check if rating is within the given field 1-10
        try:
            rating = int(request.form.get("rating"))
        except ValueError:
            return apology("Unable to convert rating", 400)

        if rating not in ratings:
            return apology("Invalid rating", 400)

        # Storing content in a variable
        content = request.form.get("content")

        # Saving note
        db.execute(
            "INSERT INTO notes (user_id, rating, content, time) VALUES (?, ?, ?, CURRENT_TIMESTAMP)", session[
                "user_id"], rating, content
        )

        # Update streak
        db.execute(
            "UPDATE users SET streak = ? WHERE id = ?", streak+1, session["user_id"]
        )

        return redirect("/")


@app.route("/register", methods=["GET", "POST"])
def register():
    tz = [-12, -11, -10, -9.5, -9, -8, -7, -6, -5, -4, -3.5, -3, -2, -1, 0, +1, +2, +3, +3.5, +4, +4.5, +5, +5.5,
          +5.75, +6, +6.5, +7, +8, +8.75, +9, +9.5, +10, +10.5, +11, 12, 12.75, 13, 14]
    tz = [f"+{str(i)}" if i >= 0 else str(i) for i in tz]
    if request.method == "POST":

        # Ensuring sufficient information
        if not request.form.get("username"):
            return apology("Must provide username", 400)
        if not request.form.get("password"):
            return apology("Must provide password", 400)
        if not request.form.get("confirmation"):
            return apology("Must retype password", 400)
        if not request.form.get("displayname"):
            return apology("Must provide displayname", 400)
        if not request.form.get("timezone"):
            return apology("Must select timezone", 400)
        if not request.form.get("magicword"):
            return apology("Must provide magic word", 400)

        # Make sure password is at least 6 characters long
        if len(request.form.get("password")) < 6:
            return apology("Password must be at least 6 characters long", 400)

        # Make sure password and confirmation is identical
        if request.form.get("password") != request.form.get("confirmation"):
            return apology("Password and repeat password must be the same", 400)

        # Make sure timezone is in timezone list
        if request.form.get("timezone") not in tz:
            return apology("Invalid timezone", 400)

        # Convert string timezone to int timezone
        try:
            timezone = int(request.form.get("timezone"))
        except ValueError:
            return apology("Unable to convert timezone", 400)

        # Test if username already exists
        rows = db.execute(
            "SELECT * FROM users WHERE username = ?", request.form.get("username")
        )
        if len(rows) > 0:
            return apology("Account username already exists", 400)

        # Test if displayname already exists
        rows = db.execute(
            "SELECT * FROM users WHERE displayname = ?", request.form.get("displayname")
        )
        if len(rows) > 0:
            return apology("Account displayname already exists", 400)

        # Store new username, displayname and password hash
        db.execute("INSERT INTO users (username, hash, displayname, joindate, timezone, magicword) VALUES (?, ?, ?, CURRENT_TIMESTAMP, ?, ?)", request.form.get("username"),
                   generate_password_hash(request.form.get("password")), request.form.get("displayname"), timezone, request.form.get("magicword"))

        # Log the user in automatically
        rows = db.execute(
            "SELECT * FROM users WHERE username = ?", request.form.get("username")
        )

        # Check if the user is now in the database
        if len(rows) == 1:
            session["user_id"] = rows[0]["id"]
        else:
            return apology("Cannot log in", 400)

        return redirect("/")
    else:
        return render_template("register.html", tz=tz)


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute(
            "SELECT * FROM users WHERE username = ?", request.form.get("username")
        )

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(
            rows[0]["hash"], request.form.get("password")
        ):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


# A forget password page to help users change their password with the magic word.
@app.route("/forget", methods=["GET", "POST"])
def forget():
    if request.method == "POST":

        # Check if all fields are filled
        if not request.form.get("username"):
            return apology("Must provide username", 400)
        if not request.form.get("magicword"):
            return apology("Must provide magic word", 400)
        if not request.form.get("password"):
            return apology("Must provide new password", 400)

        # Check if username is in database
        username = request.form.get("username")
        rows = db.execute(
            "SELECT * FROM users WHERE username = ?", username
        )
        if len(rows) != 1:
            return apology("Unknown username", 400)

        # Check if magic word is correct
        magicword = request.form.get("magicword")
        if magicword != rows[0]['magicword']:
            return apology("Incorrect magic word", 400)

        # Change password
        db.execute(
            "UPDATE users SET hash = ? WHERE username = ?", generate_password_hash(request.form.get("password")), username
        )

        return redirect("/login")
    else:
        return render_template("forget.html")


# 'Edit' will most likely return 2 html pages, one for edit and one for editing
"""
    Either a selection, a number input or a calendar selection for user to edit any day
    A view button for said day
    After viewing, it displays a text input for user to edit, as well as a button to remove.
    """


@app.route("/edit", methods=["GET", "POST"])
@login_required
def edit():
    # Dict of note timestamps
    timestamps = {}

    # Obtain user's notes' timestamps and note IDs
    rows = db.execute(
        "SELECT id, time FROM notes WHERE user_id = ?", session["user_id"]
    )

    # Return a different html page if user has no notes
    if len(rows) == 0:
        return render_template("edit_empty.html")

    # If user does have notes, obtain list of dates that user wrote a note
    timezone = timezone_check()

    # Database's timezone is currently UTC+3, we gotta do some arithmetic to calculate user's time difference
    difference = timezone - 3       # use "+" in conversion, not "-"

    # Turning each note timestamp into user's local time, then strip the hours, and append it to the "dates" list
    for row in rows:
        time = row['time']

        # Obtaining note id for each note
        try:
            Id = int(row['id'])
        except ValueError:
            return apology("Unable to obtain note ID", 400)

        timestamp = datetime.strptime(time, '%Y-%m-%d %H:%M:%S')  # strp, meaning creating a datetime object in that format

        # Calculate time when submitting note according to user's timezone
        timestamp = timestamp + timedelta(hours=difference)

        # Adding timestamp to the timestamps dict
        timestamps[Id] = timestamp

    # When user loads edit page, this displays when there is at least one note available
    if request.method == "GET":
        return render_template("edit.html")
    else:
        # Note: MUST check for valid date on server-side, as I failed to check that on client-side

        # Boolean to check for input date validity
        isValid = False

        # Integer to keep track of valid note ID
        noteId = 0

        # Ensure user provided a date
        if not request.form.get("dateInput"):
            return apology("Must provide date", 400)

        date = request.form.get("dateInput")

        # Check for date validity
        for Id in timestamps:
            # Convert timestamp to a string, then compare
            validDate = datetime.strftime(timestamps[Id], "%Y-%m-%d")
            if validDate == date:
                isValid = True
                try:
                    noteId = int(Id)
                except ValueError:
                    return apology("Unable to convert timestamp id", 400)
                break

        # If date is not valid after checking through all timestamps
        if not isValid:
            return apology("Invalid date", 400)

        # Check if note belongs to user, using note id
        checkRow = db.execute(
            "SELECT * FROM notes WHERE user_id = ? AND id = ?", session["user_id"], noteId
        )

        if len(checkRow) != 1:
            return apology("Invalid note", 400)

        # Save note id into session/cookie whatever, in order to access in the next page
        session["note_id"] = noteId

        # Redirect user to an "editing" page, where they can edit for their selected date.
        return redirect("/editing")


""" An extra function/route to handle specific modification of the specific day after selection in /edit """


@app.route("/editing", methods=["GET", "POST"])
@login_required
def editing():
    # Getting list of ratings to feed into page, and also to check in POST method later
    ratings = list(range(1, 11))

    # Obtain id of specific note that user wants to edit
    try:
        noteId = int(session["note_id"])
    except (ValueError, KeyError):
        return apology("Unable to convert noteID", 400)

    # Check for validity of noteId, if user accessed page without going through /edit
    if noteId == 0 or not noteId:
        return apology("Invalid note ID", 400)

    # Check if note belongs to user, using note id
    rows = db.execute(
        "SELECT * FROM notes WHERE user_id = ? AND id = ?", session["user_id"], noteId
    )

    if len(rows) != 1:
        return apology("Invalid note", 400)

    # Variables to keep track of original note info
    try:
        rating = int(rows[0]['rating'])
        content = rows[0]['content']
        timestamp = datetime.strptime(rows[0]['time'], '%Y-%m-%d %H:%M:%S')

        # Calculate time difference between database time and user local time
        difference = timezone_check() - 3

        # Calculate time when submitting note according to user's timezone
        timestamp = timestamp + timedelta(hours=difference)

        # Date variable
        date = timestamp.date()
    except ValueError:
        return apology("Database value failure", 400)

    # When user loads page
    if request.method == "GET":
        return render_template("editing.html", rating=rating, content=content, date=date, ratings=ratings)

    # When user submits new edit
    else:
        # Ensure sufficient form provision
        if not request.form.get("rating"):
            return apology("Must provide new rating", 400)
        if not request.form.get("content"):
            return apology("Must provide new content", 400)

        # Convert values to variables for ease
        try:
            new_rating = int(request.form.get("rating"))
            new_content = request.form.get("content")
        except ValueError:
            return apology("Unable to convert values", 400)

        # Ensure rating validity
        if new_rating not in range(1, 11):
            return apology("Invalid rating", 400)

        # Update database
        db.execute(
            "UPDATE notes SET rating = ?, content = ? WHERE id = ?", new_rating, new_content, noteId
        )

        # Clear session value
        session.pop('note_id', None)

        return redirect("/")


""" A route to just remove notes (POST method) """


@app.route("/remove", methods=["POST"])
@login_required
def remove():
    # Obtain id of specific note that user wants to edit
    try:
        noteId = int(session["note_id"])
    except (ValueError, KeyError):
        return apology("Unable to convert noteID", 400)

    # Check for validity of noteId, if user accessed page without going through /edit
    if noteId == 0 or not noteId:
        return apology("Invalid note ID", 400)

    # Check if note belongs to user, using note id
    checkRow = db.execute(
        "SELECT * FROM notes WHERE user_id = ? AND id = ?", session["user_id"], noteId
    )

    if len(checkRow) != 1:
        return apology("Invalid note", 400)

    # Remove note
    db.execute(
        "DELETE FROM notes WHERE id = ?", noteId
    )

    # Clear session value
    session.pop('note_id', None)

    return redirect("/")


# Lets user see their entire notes list
"""
    + Displays days in a table, ratings will be colored using html classes
    + Each day has an edit button. Edit button might send user to edit page that's already given the info of the day
    + Option to download this in a .csv or .xls file (if possible)
"""


@app.route("/view", methods=["GET", "POST"])
@login_required
def view():

    # Get all notes from user, with descending order of time (latest -> oldest)
    rows = db.execute(
        "SELECT id, rating, content, time FROM notes WHERE user_id = ? ORDER BY time DESC", session["user_id"]
    )

    # If user has no notes, return now
    if len(rows) == 0:
        return apology("You have no notes", 400)

    # User loads page
    if request.method == "GET":
        return render_template("view.html", rows=rows)

    # User clicks button to edit specific day
    else:
        # Check if note id is empty
        if not request.form.get("noteId"):
            return apology("Must provide note", 400)

        # Get note id
        try:
            noteId = int(request.form.get("noteId"))
        except (ValueError, KeyError):
            return apology("Unable to get note", 400)

        # Check if note belongs to user, using note id
        checkRow = db.execute(
            "SELECT * FROM notes WHERE user_id = ? AND id = ?", session["user_id"], noteId
        )

        if len(checkRow) != 1:
            return apology("Invalid note", 400)

        # Redirect user to editing page with session note id value
        session["note_id"] = noteId
        return redirect("/editing")


""" A route that allows user to download the whole table as a csv file """


@app.route("/download", methods=["POST"])
@login_required
def download():
    # Get all notes from user, with descending order of time (latest -> oldest)
    rows = db.execute(
        "SELECT id, rating, content, time FROM notes WHERE user_id = ? ORDER BY time DESC", session["user_id"]
    )

    # If user has no notes, return now
    if len(rows) == 0:
        return apology("You have no notes", 400)

    # Field names to create csv
    fieldnames = ['id', 'rating', 'content', 'time']

    # Name of csv file
    filename = f"csv/sample_{session['user_id']}.csv"

    # Write to csv file
    with open(filename, 'w') as csvFile:
        writer = csv.DictWriter(csvFile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    # Return file
    return send_file(filename)


# Lets user change username and password, as well as add a personal bio (most likely multiple html pages, or heck, even multiple app.py functions)
"""
+ Allows user to change display name and password, but not username
+ Allows user to add bio
+ Allows user to change timezone
+ Allows user to log out
# If change timezone, streak automatically resets
"""


@app.route("/settings", methods=["GET"])
@login_required
def settings():
    return render_template("settings.html")


# Info
@app.route("/info", methods=["GET", "POST"])
@login_required
def info():
    # List of timezones to render and check
    tz = [-12, -11, -10, -9.5, -9, -8, -7, -6, -5, -4, -3.5, -3, -2, -1, 0, +1, +2, +3, +3.5, +4, +4.5, +5, +5.5,
          +5.75, +6, +6.5, +7, +8, +8.75, +9, +9.5, +10, +10.5, +11, 12, 12.75, 13, 14]
    tz = [f"+{str(i)}" if i >= 0 else str(i) for i in tz]

    # Get row of bio and displayname from database (because timezone has its own function)
    rows = db.execute(
        "SELECT bio, displayname, timezone FROM users WHERE id = ?", session["user_id"]
    )

    if len(rows) != 1:
        return apology("Unable to find user", 400)

    # Get bio, displayname and timezone
    bio = rows[0]['bio']
    displayname = rows[0]['displayname']
    timezone = timezone_check()

    # Render page with prefilled information
    if request.method == "GET":
        return render_template("info.html", bio=bio, displayname=displayname, tz=tz)

    # When user submits form
    else:
        # Ensure displayname and timezone is filled, bio is optional.
        if not request.form.get("displayname"):
            return apology("Must provide displayname", 400)
        if not request.form.get("timezone"):
            return apology("Must select timezone", 400)

        # Make sure timezone is in timezone list
        if request.form.get("timezone") not in tz:
            return apology("Invalid timezone", 400)

        # Convert string timezone to int new timezone
        try:
            new_timezone = int(request.form.get("timezone"))
        except ValueError:
            return apology("Unable to convert timezone", 400)

        # If new timezone is different from old timezone, reset user streak and no need to update user timezone
        if new_timezone != timezone:
            db.execute(
                "UPDATE users SET streak = 0, bio = ?, displayname = ?, timezone = ? WHERE id = ?", request.form.get("bio"),
                request.form.get("displayname"), new_timezone, session["user_id"]
            )

        # If timezone is the same with old timezone, no need to update streak nor timezone
        else:
            db.execute(
                "UPDATE users SET bio = ?, displayname = ? WHERE id = ?", request.form.get(
                    "bio"), request.form.get("displayname"), session["user_id"]
            )

        # Bring user to settings after process
        return redirect("/settings")


# Route to change password and magic word
@app.route("/security", methods=["GET", "POST"])
@login_required
def security():
    # Get user's old password and magic word rows
    rows = db.execute(
        "SELECT hash, magicword FROM users WHERE id = ?", session["user_id"]
    )

    if len(rows) != 1:
        return apology("Unable to get info", 400)

    # Get old magic word
    oldMagicWord = rows[0]['magicword']

    # Load page
    if request.method == "GET":
        return render_template("security.html", magicword=oldMagicWord)
    # User submits form
    else:
        # Check if any field is empty
        if not request.form.get("oldpassword"):
            return apology("Must provide old password", 400)
        if not request.form.get("newpassword"):
            return apology("Must provide new password", 400)
        if not request.form.get("magicword"):
            return apology("Must provide magic word", 400)

        # Check if old password is correct
        if not check_password_hash(rows[0]['hash'], request.form.get("oldpassword")):
            return apology("Incorrect old password", 400)

        # Make sure password is at least 6 characters long
        if len(request.form.get("newpassword")) < 6:
            return apology("Password must be at least 6 characters long", 400)

        # Update database with new password hash and magic word
        db.execute(
            "UPDATE users SET hash = ?, magicword = ? WHERE id = ?", generate_password_hash(request.form.get("newpassword")),
            request.form.get("magicword"), session["user_id"]
        )

        return redirect("/settings")

# Function to check for user's timezone


def timezone_check():

    rows2 = db.execute(
        "SELECT timezone FROM users WHERE id = ?", session["user_id"]
    )

    if len(rows2) != 1:
        return apology("Unable to find user timezone", 400)

    try:
        timezone = int(rows2[0]['timezone'])
    except ValueError:
        return apology("Unable to convert user timezone", 400)

    return timezone
