from flask import Flask, render_template, request, redirect, session, url_for
from flask import session
from flask import url_for
import os 


from datetime import datetime, date

def has_borrowed(student_name):
    return any(i for i in issues if i["student"] == student_name and not i["returned"])
app = Flask(__name__)
app.secret_key = "libmem_secret"


books = []
book_counter = 1

classes = []
students = []
issues = []
history = []
timetable_image = ""


# LOGIN
@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        username = request.form.get("username")
        password = request.form.get("password")

        # SIMPLE PASSWORD
        if password == "libmem123":

            session["user"] = username

            return redirect("/dashboard")

    return render_template("login.html")

# LOGOUT
@app.route("/logout")
def logout():

    session.pop("user", None)

    return redirect("/login")


# PROFILE
@app.route("/profile", methods=["GET", "POST"])
def profile():

    if "user" not in session:
        return redirect("/login")

    if request.method == "POST":

        new_name = request.form.get("username")

        if new_name:
            session["user"] = new_name

        return redirect("/dashboard")

    return render_template(
        "profile.html",
        user=session["user"]
    )






# DASHBOARD
@app.route("/")
@app.route("/dashboard")
def dashboard():

    if "user" not in session:
        return redirect("/login")

    today = date.today()

    late_returns = []

    for i in issues:

        if not i.get("returned") and i.get("expected_return"):

            try:
                return_date = datetime.strptime(
                    i["expected_return"],
                    "%Y-%m-%d"
                ).date()

                if return_date <= today:
                    late_returns.append(i)

            except:
                pass

    return render_template(
    "dashboard.html",
    late_returns=late_returns,
    user=session["user"],
    timetable_image=timetable_image,
   
)

import os

# TIMETABLE IMAGE
@app.route("/upload_timetable", methods=["POST"])
def upload_timetable():

    global timetable_image

    file = request.files.get("image")

    if file and file.filename != "":

        filename = file.filename

        timetable_image = filename

        upload_path = os.path.join(app.root_path, "static", filename)

        file.save(upload_path)

    return redirect("/dashboard")


# DELETE TIMETABLE
@app.route("/delete_timetable")
def delete_timetable():

    global timetable_image

    timetable_image = ""

    return redirect("/dashboard")





# ADD BOOKS PAGE
@app.route("/dashboard")
def dashboard_age():
    if "user" not in session:
        return redirect("/login")

    return render_template("dashboard.html")
@app.route("/books", methods=["GET", "POST"])
def books_page():
    global book_counter

    if request.method == "POST":
        name = request.form.get("name")
        author = request.form.get("author")
        publisher = request.form.get("publisher")
        isbn = request.form.get("isbn")
        price = request.form.get("price")
        subtitle = request.form.get("subtitle")
        cover = request.form.get("cover")
        # VALIDATION
        if not name or not author or not isbn or not price:
            return redirect("/books")

        book_id = f"S{book_counter:04d}"

        books.append({
            "id": book_id,
            "name": name,
            "author": author,
            "publisher": publisher,
            "isbn": isbn,
            "price": price,
            "subtitle": subtitle,
            "cover": cover
        })

        book_counter += 1

        return redirect("/books")

    return render_template("books.html", books=books)




# EDIT
@app.route("/edit_book/<id>", methods=["GET", "POST"])
def edit_book(id):
    book = next((b for b in books if b["id"] == id), None)

    if request.method == "POST":
        book["name"] = request.form.get("name")
        book["author"] = request.form.get("author")
        book["publisher"] = request.form.get("publisher")
        book["isbn"] = request.form.get("isbn")
        book["price"] = request.form.get("price")
        book["subtitle"] = request.form.get("subtitle")
        book["cover"] = request.form.get("cover")

        return redirect("/books")

    return render_template("edit_book.html", book=book)


# SEARCH
@app.route("/search")
def search():
    query = request.args.get("q", "").lower()
    filtered = [b for b in books if b["id"].lower().startswith(query)]
    return render_template("books.html", books=filtered)

#THE STUDENTS PAGE
@app.route("/dashboard")
def dashboard_pag():
    if "user" not in session:
        return redirect("/login")

    return render_template("dashboard.html")

@app.route("/students", methods=["GET", "POST"])
def students_page():
    if request.method == "POST":
        class_name = request.form.get("class")
        student_name = request.form.get("student")

        if not class_name or not student_name:
            return redirect("/students")

        if class_name not in classes:
            classes.append(class_name)

        students.append({
            "name": student_name,
            "class": class_name
        })

        return redirect("/students")

    search = request.args.get("search", "").lower()

    if search:
        filtered_students = [
            s for s in students
            if search in s["name"].lower() or search in s["class"].lower()
        ]
    else:
        filtered_students = students

    return render_template(
        "students.html",
        classes=classes,
        students=filtered_students
    )

#DELETE STUDENT
@app.route("/delete_student/<int:index>")
def delete_student(index):
    if 0 <= index < len(students):
        students.pop(index)
    return redirect("/students")

#DELETE CLASS
@app.route("/delete_class/<class_name>")
def delete_class(class_name):
    global students, classes

    classes = [c for c in classes if c != class_name]
    students = [s for s in students if s["class"] != class_name]

    return redirect("/students")

#EDIT STUDENT
@app.route("/edit_student/<int:index>", methods=["GET", "POST"])
def edit_student(index):
    student = students[index]

    if request.method == "POST":
        student["name"] = request.form.get("name")
        return redirect("/students")

    return render_template("edit_student.html", student=student, index=index)

#EDIT CLASS
@app.route("/edit_class/<old_name>", methods=["GET", "POST"])
def edit_class(old_name):
    if request.method == "POST":
        new_name = request.form.get("name")

        for i, c in enumerate(classes):
            if c == old_name:
                classes[i] = new_name

        for s in students:
            if s["class"] == old_name:
                s["class"] = new_name

        return redirect("/students")

    return render_template("edit_class.html", old_name=old_name)



from datetime import datetime
from flask import request, redirect, render_template

# ISSUE BOOK
@app.route("/dashboard")
def dashboard_pge():
    if "user" not in session:
        return redirect("/login")

    return render_template("dashboard.html")

@app.route("/issue", methods=["GET", "POST"])
def issue_book():

    if request.method == "POST":

        book_id = request.form.get("book_id")
        class_name = request.form.get("class_name")
        student_name = request.form.get("student_name")

        # EXPECTED RETURN DATE
        expected_return = request.form.get("return_date")

        # FIND BOOK
        book = next((b for b in books if str(b["id"]) == str(book_id)), None)

        if not book:
            return redirect("/issue")

        # PREVENT SAME BOOK MULTIPLE TIMES
        already_issued = any(
            i["book_id"] == book_id and not i.get("returned", False)
            for i in issues
        )

        if already_issued:
            return "Book already issued!"

        # TODAY DATE
        issue_date = datetime.now().strftime("%Y-%m-%d")

        # SAVE ISSUE
        issues.append({
            "book_id": book_id,
            "book_name": book["name"],
            "class": class_name,
            "student": student_name,

            "issue_date": issue_date,

            # EXPECTED RETURN DATE
            "expected_return": expected_return,

            # ACTUAL RETURN DATE
            "return_date": "",

            "returned": False
        })

        return redirect("/issue")

    return render_template(
        "issue.html",
        books=books,
        students=students,
        classes=classes,
        issues=issues,
        has_borrowed=has_borrowed
    )

        
@app.route("/get_students/<class_name>")
def get_students(class_name):
    filtered = [s for s in students if s["class"] == class_name]
    return {"students": filtered}

@app.route("/search_borrowers")
def search_borrowers():
    query = request.args.get("q", "").lower()

    filtered = [
        i for i in issues
        if query in i["student"].lower()
        or query in i["book_id"].lower()
    ]

    return render_template(
        "issue.html",
        books=books,
        students=students,
        classes=classes,
        issues=filtered,
        has_borrowed=has_borrowed
    )

# EDIT EXPECTED RETURN DATE
@app.route("/edit_return_date/<book_id>", methods=["GET", "POST"])
def edit_return_date(book_id):

    issue = next(
        (i for i in issues if i["book_id"] == book_id and not i["returned"]),
        None
    )

    if not issue:
        return redirect("/issue")

    if request.method == "POST":

        # ONLY CHANGE EXPECTED RETURN DATE
        issue["expected_return"] = request.form.get("return_date")

        return redirect("/issue")

    return render_template(
        "edit_return_date.html",
        issue=issue
    )



# RETURN PAGE (MAIN PAGE LOAD)
@app.route("/return")
def return_page():
    return render_template(
        "return.html",
        issues=issues,
        classes=classes
    )


# RETURN BY BOOK ID

@app.route("/return_book", methods=["POST"])
def return_book_post():
    book_id = request.form.get("book_id")

    if not book_id:
        return redirect("/return")

    for i in issues:
        if i["book_id"] == book_id and not i["returned"]:

            # MARK AS RETURNED
            i["returned"] = True

            # SAVE RETURN DATE
            i["return_date"] = datetime.now().strftime("%Y-%m-%d")

            break

    return redirect("/return")


# RETURN BY CLASS (MULTIPLE STUDents)
@app.route("/return_class", methods=["POST"])
def return_class():

    class_name = request.form.get("class_name")
    selected_students = request.form.getlist("students")

    if not class_name or not selected_students:
        return redirect("/return")

    for i in issues:
        if (
            i["class"] == class_name
            and i["student"] in selected_students
            and not i["returned"]
        ):

            # MARK RETURNED
            i["returned"] = True

            # SAVE RETURN DATE
            i["return_date"] = datetime.now().strftime("%Y-%m-%d")

    return redirect("/return")



# HISTORY PAGE
@app.route("/history")
def history():

    search_student = request.args.get("student", "").lower()
    search_class = request.args.get("class", "").lower()
    search_book = request.args.get("book", "").lower()
    search_borrow = request.args.get("borrow_date", "")
    search_return = request.args.get("return_date", "")
    search_status = request.args.get("status", "").lower()

    filtered = issues

    if search_student:
        filtered = [i for i in filtered if search_student in i["student"].lower()]

    if search_class:
        filtered = [i for i in filtered if search_class in i["class"].lower()]

    if search_book:
        filtered = [i for i in filtered if search_book in i["book_id"].lower()]

    if search_borrow:
        filtered = [i for i in filtered if search_borrow in i["issue_date"]]

    if search_return:
        filtered = [i for i in filtered if search_return in i.get("return_date", "")]

    if search_status:
        if search_status == "returned":
            filtered = [i for i in filtered if i.get("returned", False)]
        elif search_status == "borrowed":
            filtered = [i for i in filtered if not i.get("returned", False)]

    return render_template("history.html", issues=filtered,books=books,)

from datetime import datetime, timedelta

@app.route("/delete_history", methods=["POST"])
def delete_history():

    option = request.form.get("delete_option")

    if not option:
        return redirect("/history")

    days_map = {
        "5": 5,
        "10": 10,
        "20": 20,
        "30": 30
    }

    days = days_map.get(option)

    if not days:
        return redirect("/history")

    cutoff = datetime.now() - timedelta(days=days)

    global issues
    issues = [
        i for i in issues
        if datetime.strptime(i["issue_date"], "%Y-%m-%d") > cutoff
    ]

    return redirect("/history")




if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)