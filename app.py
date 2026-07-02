from flask import Flask, render_template, request, redirect, session, url_for 
from flask import session, send_file 
from openpyxl import Workbook
from openpyxl import load_workbook
from flask import send_file
from io import BytesIO
from flask import url_for
import os 


from datetime import datetime, timedelta , date
os.makedirs("static/uploads", exist_ok=True)
from werkzeug.utils import secure_filename

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
reservations = []
UPLOAD_FOLDER = "static/uploads"
timetable_image = None
current_history_view = []

books_from_excel = False
students_from_excel = False

books_excel_name = None
students_excel_name = None




def check_expired_reservations():

    today = date.today()

    for r in reservations:

        if not r.get("expired", False):

            try:

                end_date = datetime.strptime(
                    r["reserved_until"],
                    "%Y-%m-%d"
                ).date()

                if end_date < today:

                    # mark reservation expired
                    r["expired"] = True


                    # FIND OLD HISTORY RESERVED ROW
                    for i in issues:

                        if (

                            i["book_id"] == r["book_id"]

                            and i.get("status") == "reserved"

                        ):

                            # CHANGE RESERVED → EXPIRED
                            i["status"] = "expired"

                            # KEEP ORIGINAL END DATE
                            i["end_date"] = r["reserved_until"]

                            break

            except:
                pass




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

    check_expired_reservations()

    if "user" not in session:
        return redirect("/login")

    today = date.today()

    # CHECK LATE RETURNS
    late_returns = []

    for i in issues:

        if (

            not i.get("returned")

            and i.get("expected_return")

            and i.get("status") != "reserved"

            and i.get("status") != "expired"

        ):

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

        timetable_image=timetable_image

    )


import os

# TIMETABLE IMAGE
from werkzeug.utils import secure_filename

UPLOAD_FOLDER = "static/uploads"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)


@app.route("/upload_timetable", methods=["POST"])
def upload_timetable():

    global timetable_image

    file = request.files.get("image")

    if file and file.filename != "":

        filename = secure_filename(file.filename)

        upload_path = os.path.join(
            UPLOAD_FOLDER,
            filename
        )

        file.save(upload_path)

        timetable_image = "uploads/" + filename

    return redirect("/dashboard")


# DELETE TIMETABLE
@app.route("/delete_timetable")
def delete_timetable():

    global timetable_image

    timetable_image = None

    return redirect("/dashboard")



# ADD BOOKS PAGE
@app.route("/dashboard")
def dashboard_age():
    if "user" not in session:
        return redirect("/login")


    return render_template("dashboard.html")

@app.route("/books", methods=["GET", "POST"])
def books_page():
    if books_from_excel:

     return render_template(

        "books.html",

        books_from_excel=True

    )


    global book_counter

    if request.method == "POST":
        name = request.form.get("name")
        author = request.form.get("author")
        publisher = request.form.get("publisher")
        isbn = request.form.get("isbn")
        price = request.form.get("price")
        subtitle = request.form.get("subtitle")
        year_published = request.form.get("year_published")
        cover = request.form.get("cover")
        # VALIDATION
        if not name or not author or not isbn or not price or not year_published:
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
    "year_published": year_published,
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
        book["year_published"] = request.form.get("year_published")
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
@app.route("/students", methods=["GET", "POST"])
def students_page():

    if students_from_excel:

     return render_template(

        "students.html",

        students_from_excel=True

    )



    if request.method == "POST":

        class_name = request.form.get("class").strip()
        student_name = request.form.get("student").strip()


        # EMPTY CHECK
        if not class_name or not student_name:

            return "Please fill all fields"


        # FORMAT CHECK → Example: 3 A
        parts = class_name.split(" ")


        # EXACTLY ONE SPACE
        if len(parts) != 2:

            return "Use format like 3 A (one space only)"


        # FIRST PART MUST BE NUMBER
        if not parts[0].isdigit():

            return "Class must start with a number"


        # SECOND PART MUST BE LETTER
        if not parts[1].isalpha():

            return "Section must be a letter"


        # ONLY ONE LETTER
        if len(parts[1]) != 1:

            return "Section must be one letter only"


        # SAVE CLASS
        if class_name not in classes:

            classes.append(class_name)


        # SAVE STUDENT
        students.append({

            "name": student_name,
            "class": class_name

        })

        return redirect("/students")


    search = request.args.get("search", "").lower()


    if search:

        filtered_students = [

            s for s in students

            if search in s["name"].lower()
            or search in s["class"].lower()

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

        new_name = request.form.get("name").strip()


        # EMPTY CHECK
        if not new_name:

            return "Please enter class"


        # FORMAT CHECK
        parts = new_name.split(" ")


        if len(parts) != 2:

            return "Use format like 3 A (one space only)"


        if not parts[0].isdigit():

            return "Class must start with a number"


        if not parts[1].isalpha():

            return "Section must be a letter"


        if len(parts[1]) != 1:

            return "Section must be one letter only"


        # UPDATE CLASSES
        for i, c in enumerate(classes):

            if c == old_name:

                classes[i] = new_name


        # UPDATE STUDENTS
        for s in students:

            if s["class"] == old_name:

                s["class"] = new_name


        return redirect("/students")


    return render_template(

        "edit_class.html",

        old_name=old_name

    )



from datetime import datetime
from flask import request, redirect, render_template


@app.route("/issue", methods=["GET", "POST"])
def issue_book():

    if request.method == "POST":

        book_id = request.form.get("book_id")
        class_name = request.form.get("class_name")
        student_name = request.form.get("student_name")
        expected_return = request.form.get("return_date")


        # BLOCK PAST DATE
        today = date.today()

        selected_date = datetime.strptime(
            expected_return,
            "%Y-%m-%d"
        ).date()

        if selected_date < today:

            return "You cannot issue a book to a past date"


        # FIND BOOK
        book = next(
            (b for b in books if str(b["id"]) == str(book_id)),
            None
        )

        if not book:
            return redirect("/issue")


        # CHECK RESERVATION
        reserved = next(
            (
                r for r in reservations
                if str(r["book_id"]) == str(book_id)
                and not r.get("expired", False)
            ),
            None
        )

        if reserved:
            return (
                f"This book is reserved by "
                f"{reserved['student']} "
                f"from {reserved['class']}"
            )


        # PREVENT DUPLICATE ISSUE
        already_issued = any(
            i["book_id"] == book_id
            and not i.get("returned", False)
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
            "expected_return": expected_return,
            "return_date": "",
            "returned": False

        })

        return redirect("/issue")


    # FOR GET REQUEST → HIDE RESERVED + EXPIRED
    normal_issues = [

        i for i in issues

        if i.get("status") != "reserved"
        and i.get("status") != "expired"

    ]


    return render_template(

        "issue.html",

        books=books,
        students=students,
        classes=classes,
        issues=normal_issues,
        has_borrowed=has_borrowed,
        today=date.today().strftime("%Y-%m-%d")

    )


@app.route("/get_students/<class_name>")
def get_students(class_name):
    filtered = [s for s in students if s["class"] == class_name]
    return {"students": filtered}

@app.route("/get_book_info/<book_id>")
def get_book_info(book_id):

    book = next(

        (b for b in books if str(b["id"]) == str(book_id)),

        None

    )

    if not book:

        return {

            "found": False

        }

    return {

        "found": True,

        "name": book["name"],

        "author": book["author"],

        "publisher": book["publisher"],

        "year_published": book["year_published"],

        "isbn": book["isbn"],

        "price": book["price"],

        "subtitle": book["subtitle"]

    }






@app.route("/search_borrowers")
def search_borrowers():

    query = request.args.get("q", "").lower()

    filtered = [

        i for i in issues

        if (

            query in i["student"].lower()

            or query in i["book_id"].lower()

            or query in i["class"].lower()

        )

        and i.get("status") != "reserved"
        and i.get("status") != "expired"

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


# RESERVATION
@app.route("/reserve", methods=["GET", "POST"])
def reserve_book():

    # CHECK EXPIRED EVERY TIME PAGE LOADS
    check_expired_reservations()

    if request.method == "POST":

        book_id = request.form.get("book_id")
        class_name = request.form.get("class_name")
        student_name = request.form.get("student_name")
        reserved_until = request.form.get("reserved_until")


        # BLOCK PAST DATES
        today_date = date.today()

        chosen_date = datetime.strptime(
            reserved_until,
            "%Y-%m-%d"
        ).date()

        if chosen_date < today_date:

            return "You cannot choose a date before today"


        # FIND BOOK
        book = next(
            (b for b in books if b["id"] == book_id),
            None
        )

        if not book:
            return "Book not found"


        # CHECK IF ALREADY RESERVED
        existing = next(
            (
                r for r in reservations
                if r["book_id"] == book_id
                and not r.get("expired", False)
            ),
            None
        )

        if existing:

            return (
                f"This book is already reserved by "
                f"{existing['student']}"
            )


        # TODAY DATE
        today = datetime.now().strftime("%Y-%m-%d")


        # SAVE RESERVATION
        reservation = {

            "book_id": book_id,
            "book_name": book["name"],
            "class": class_name,
            "student": student_name,

            "reserved_on": today,
            "reserved_until": reserved_until,

            "expired": False

        }

        reservations.append(reservation)


        # SAVE IN HISTORY
        issues.append({

            "book_id": book_id,
            "book_name": book["name"],

            "class": class_name,
            "student": student_name,

            "issue_date": "---",
            "expected_return": "---",
            "return_date": "---",

            "reserved_on": today,
            "end_date": reserved_until,

            "returned": False,
            "status": "reserved"

        })


        return redirect("/reserve")
    

    active_reservations = [

    r for r in reservations

    if not r.get("expired", False)

]

    return render_template(
    "reserve.html",
    classes=classes,
    reservations=active_reservations,
     today=date.today().strftime("%Y-%m-%d")
)


   


@app.route("/search_reservations")
def search_reservations():

    query = request.args.get("q", "").lower()

    filtered = [

        r for r in reservations

        if query in r["book_id"].lower()
        or query in r["student"].lower()
        or query in r["class"].lower()

    ]

    return render_template(
        "reserve.html",
        classes=classes,
        reservations=filtered
    )

@app.route("/delete_reservation/<book_id>")
def delete_reservation(book_id):

    global reservations

    reservations = [
        r for r in reservations
        if r["book_id"] != book_id
    ]

    return redirect("/reserve")

@app.route(
    "/edit_reservation/<book_id>",
    methods=["GET","POST"]
)
def edit_reservation(book_id):

    reservation = next(
        (
            r for r in reservations
            if r["book_id"] == book_id
        ),
        None
    )

    if not reservation:
        return redirect("/reserve")

    if request.method == "POST":

        new_date = request.form.get(
            "reserved_until"
        )

        reservation["reserved_until"] = new_date


        for i in issues:

         if i["book_id"] == book_id:

          i["end_date"] = new_date


        

        return redirect("/reserve")

    return render_template(
        "edit_reservation.html",
        reservation=reservation
    )






#RETURN MAIN PAGE
@app.route("/return")
def return_page():

    normal_issues = [

        i for i in issues

        if not i.get("returned", False)

        and i.get("status") != "reserved"

        and i.get("status") != "expired"

    ]

    return render_template(

        "return.html",

        issues=normal_issues,

        classes=classes

    )




# RETURN BY BOOK ID

@app.route("/return_book", methods=["POST"])
def return_book_post():
    book_id = request.form.get("book_id")

    if not book_id:
        return redirect("/return")

    for i in issues:
       for i in issues:

         if (
        i["book_id"] == book_id
        and not i["returned"]
        and i.get("status") != "reserved"
        and i.get("status") != "expired"
    ):
            


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

        and i.get("status") != "reserved"

        and i.get("status") != "expired"

    ):
            



            # MARK RETURNED
            i["returned"] = True

            # SAVE RETURN DATE
            i["return_date"] = datetime.now().strftime("%Y-%m-%d")

    return redirect("/return")



# HISTORY
@app.route("/history")
def history():

    global current_history_view

    current_history_view = issues

    check_expired_reservations()


    search_student = request.args.get("student", "").lower()
    search_class = request.args.get("class", "").lower()
    search_book = request.args.get("book", "").lower()
    search_borrow = request.args.get("borrow_date", "")
    search_return = request.args.get("return_date", "")
    search_actual = request.args.get("actual_return", "")
    search_reserve = request.args.get("reserve_date", "")
    search_expiry = request.args.get("expiry_date", "")
    search_status = request.args.get("status", "").lower()
    search_reservation = request.args.get(
        "reservation_status",
        ""
    ).lower()

    filtered = issues

    # STUDENT SEARCH
    if search_student:

        filtered = [

            i for i in filtered

            if search_student in i["student"].lower()

        ]




    # CLASS SEARCH
    if search_class:

        filtered = [

            i for i in filtered

            if search_class in i["class"].lower()

        ]

      


    # BOOK SEARCH
    if search_book:

        filtered = [

            i for i in filtered

            if search_book in i["book_id"].lower()

        ]



    # BORROW DATE SEARCH
    if search_borrow:

        filtered = [

            i for i in filtered

            if search_borrow in str(
                i.get("issue_date", "")
            )

        ]

       

        if search_reserve:

         filtered = [

        i for i in filtered

        if search_reserve in str(

            i.get("reserved_on", "")

        )

    ]
         

        


    # EXPECTED RETURN SEARCH
    if search_return:

        filtered = [

            i for i in filtered

            if search_return in str(
                i.get("expected_return", "")
            )

        ]



    # ACTUAL RETURN SEARCH
    if search_actual:

        filtered = [

            i for i in filtered

            if search_actual in str(
                i.get("return_date", "")
            )

        ]

    


    # EXPIRY DATE SEARCH
    if search_expiry:

        filtered = [

            i for i in filtered

            if search_expiry in str(
                i.get("end_date", "")
            )

        ]



    # RETURNED / BORROWED SEARCH
    if search_status:

        if search_status == "returned":

            filtered = [

                i for i in filtered

                if i.get("returned", False)

            ]

       



        elif search_status == "borrowed":

            filtered = [

                i for i in filtered

                if (

                    not i.get("returned", False)

                    and i.get("status") != "reserved"

                    and i.get("status") != "expired"

                )

            ]

          


    # RESERVED / EXPIRED SEARCH
    if search_reservation:

        if search_reservation == "reserved":

            filtered = [

                i for i in filtered

                if i.get("status") == "reserved"

            ]

          

        elif search_reservation == "expired":

            filtered = [

                i for i in filtered

                if i.get("status") == "expired"

            ]


    return render_template(

        "history.html",

        issues=filtered,

        books=books,

        classes=classes

    )

    from datetime import datetime, timedelta

#DELETE HISTORY
@app.route("/delete_history", methods=["POST"])
def delete_history():

    option = request.form.get("delete_option")

    if not option:
        return redirect("/history")

    global issues


    # DELETE ALL HISTORY
    if option == "all":

        issues = [

            i for i in issues

            if (

                not i.get("returned", False)

                and i.get("status") != "expired"

                and i.get("status") != "reserved"

            )

        ]

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

    new_issues = []


    for i in issues:


        # KEEP ACTIVE BORROWED BOOKS
        if (

            not i.get("returned", False)

            and i.get("status") != "expired"

            and i.get("status") != "reserved"

        ):

            new_issues.append(i)
            continue


        # KEEP ACTIVE RESERVED BOOKS
        if i.get("status") == "reserved":

            new_issues.append(i)
            continue


        # CHECK RETURNED BOOKS
        if i.get("returned", False):

            try:

                return_date = datetime.strptime(
                    i["return_date"],
                    "%Y-%m-%d"
                )

                if return_date > cutoff:
                    new_issues.append(i)

            except:
                new_issues.append(i)


        # CHECK EXPIRED BOOKS
        elif i.get("status") == "expired":

            try:

                expiry_date = datetime.strptime(
                    i["end_date"],
                    "%Y-%m-%d"
                )

                if expiry_date > cutoff:
                    new_issues.append(i)

            except:
                new_issues.append(i)


    issues = new_issues

    return redirect("/history")


@app.route("/history_range_class")
def history_range_class():

    global current_history_view

    current_history_view = filtered


    from_class = request.args.get("from_class")
    to_class = request.args.get("to_class")

    if not from_class or not to_class:
        return redirect("/history")


    # SORT CLASSES
    sorted_classes = sorted(classes)


    start = sorted_classes.index(from_class)
    end = sorted_classes.index(to_class)


    allowed_classes = sorted_classes[start:end+1]


    filtered = [

        i for i in issues

        if i["class"] in allowed_classes

    ]



    return render_template(

        "history.html",

        issues=filtered,

        books=books,

        classes=classes

    )

@app.route("/history_range_date")
def history_range_date():

    global current_history_view

    current_history_view = filtered

    from_date = request.args.get("from_date")
    to_date = request.args.get("to_date")

    if not from_date or not to_date:
        return redirect("/history")


    filtered = []


    for i in issues:


        # choose date depending on type

        if i.get("status") == "reserved":

            date_to_check = i.get("reserved_on")

        else:

            date_to_check = i.get("issue_date")


        if date_to_check and date_to_check != "---":

            if from_date <= date_to_check <= to_date:

                filtered.append(i)

            


    return render_template(

        "history.html",

        issues=filtered,

        books=books,

        classes=classes

    )


@app.route("/export_history")
def export_history():

    global current_history_view

    wb = Workbook()
    ws = wb.active

    ws.title = "History"

    ws.append([

        "Student",
        "Class",
        "Book ID",
        "Borrow Date",
        "Reserve Date",
        "Expected Return",
        "Actual Return",
        "Expiry Date",
        "Status"

    ])


    for i in current_history_view:

        if i.get("status") == "reserved":

            status = "RESERVED"

        elif i.get("status") == "expired":

            status = "EXPIRED"

        elif i.get("returned"):

            status = "RETURNED"

        else:

            status = "BORROWED"


        if (

            i.get("status") == "reserved"

            or

            i.get("status") == "expired"

        ):

            borrow_date = "---"

            reserve_date = i.get(

                "reserved_on",

                "---"

            )

            expected_return = "---"

            actual_return = "---"

            expiry_date = i.get(

                "end_date",

                "---"

            )

        else:

            borrow_date = i.get(

                "issue_date",

                "---"

            )

            reserve_date = "---"

            expected_return = i.get(

                "expected_return",

                "---"

            )

            actual_return = i.get(

                "return_date",

                "Not Returned"

            )

            expiry_date = "---"


        ws.append([

            i.get("student", ""),

            i.get("class", ""),

            i.get("book_id", ""),

            borrow_date,

            reserve_date,

            expected_return,

            actual_return,

            expiry_date,

            status

        ])


    # ONLY AFTER LOOP ENDS

    excel_file = BytesIO()

    wb.save(excel_file)

    excel_file.seek(0)

    return send_file(

        excel_file,

        as_attachment=True,

        download_name="history_export.xlsx",

        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

    )



@app.route("/excel_import")
def excel_import():


    return render_template(

    "excel_import.html",

    books_from_excel=books_from_excel,
    students_from_excel=students_from_excel,

    books_excel_name=books_excel_name,
    students_excel_name=students_excel_name

)


@app.route("/upload_books_excel", methods=["POST"])
def upload_books_excel():

    global books
    global books_from_excel
    global books_excel_name

    file = request.files["books_file"]

    try:

        # DELETE OLD MANUAL BOOKS
        books.clear()

        book_counter = 1

        books_from_excel = True
       

        # SAVE FILE NAME
        books_excel_name = file.filename

        # OPEN EXCEL
        wb = load_workbook(file)

        ws = wb.active

        # SKIP HEADER ROW
        for row in ws.iter_rows(

            min_row=2,

            values_only=True

        ):

            book_id = row[0]

            name = row[1]

            author = row[2]

            publisher = row[3]

            year_published = row[4]

            isbn = row[5]

            price = row[6]

            # SAFE OPTIONAL FIELDS
            subtitle = row[7] if len(row) > 7 else ""

            cover = row[8] if len(row) > 8 else ""

            books.append({

                "id": str(book_id),

                "name": name,

                "author": author,

                "publisher": publisher,

                "year_published": year_published,

                "isbn": isbn,

                "price": price,

                "subtitle": subtitle,

                "cover": cover

            })

        return redirect("/excel_import")

    except:

        return """

        <h2 style='color:red;'>

        Oops! Looks like you made a mistake.

        </h2>

        <br>

        Either:

        <br><br>

        1. You uploaded the wrong file

        <br>

        2. The Excel format is incorrect

        <br><br>

        Required format:

        <br>

        Column A → Book ID (S0001)

        <br>

        Column B → Book Name

        <br>

        Column C → Author

        <br>

        Column D → Publisher

        <br>

        Column E → Year Published

        <br>

        Column F → ISBN

        <br>

        Column G → Price

        <br>

        Column H → Subtitle (optional)

        <br>

        Column I → Cover (optional)

        """
    


@app.route("/upload_students_excel", methods=["POST"])
def upload_students_excel():

    global students
    global classes
    global students_from_excel
    global students_excel_name

    file = request.files["students_file"]

    try:

        # DELETE OLD MANUAL DATA
        students.clear()

        classes.clear()

        # EXCEL MODE ON
        students_from_excel = True

        # SAVE FILE NAME
        students_excel_name = file.filename

        # OPEN EXCEL
        wb = load_workbook(file)

        # LOOP THROUGH EVERY SHEET
        for sheet_name in wb.sheetnames:

            ws = wb[sheet_name]

            class_name = sheet_name

            # SAVE CLASS
            classes.append(class_name)

            # READ STUDENT NAMES
            for row in ws.iter_rows(

                values_only=True

            ):

                student_name = row[0]

                # SKIP EMPTY CELLS
                if not student_name:

                    continue

                students.append({

                    "name": student_name,

                    "class": class_name

                })

        return redirect("/excel_import")

    except:

        return """

        <h2 style='color:red;'>

        Oops! Looks like you made a mistake.

        </h2>

        <br>

        Either:

        <br><br>

        1. You uploaded the wrong file

        <br>

        2. The Excel format is incorrect

        <br><br>

        Required format:

        <br>

        Each sheet name = Class Name

        <br>

        Example:

        <br>

        3 A

        <br>

        3 B

        <br><br>

        Inside each sheet:

        <br>

        Student names only

        <br>

        No column headers

        """
    


@app.route("/delete_books_excel")
def delete_books_excel():

    global books
    global books_from_excel
    global books_excel_name
    global book_counter


    books = []

    book_counter = 1


    books_from_excel = False

    books_excel_name = None


    return redirect("/excel_import")


@app.route("/delete_students_excel")
def delete_students_excel():

    global students
    global classes

    global students_from_excel
    global students_excel_name


    students = []

    classes = []


    students_from_excel = False

    students_excel_name = None


    return redirect("/excel_import")









if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)