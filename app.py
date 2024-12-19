from flask import Flask, request, render_template, redirect, url_for, session
from owlready2 import get_ontology, Thing, DatatypeProperty
import statistics
from fractions import Fraction
import random

app = Flask(__name__)
app.secret_key = "secret_key"  # Required for session management

# Load the ontology
ontology_path = "student_ontology.owl"
onto = get_ontology(ontology_path).load()

# Define the Student and User classes
with onto:
    class Student(Thing):
        pass

    class User(Student):  # User is now a subclass of Student
        pass

    class name(DatatypeProperty):
        domain = [Student]
        range = [str]

    class answered_questions(DatatypeProperty):
        domain = [User]
        range = [int]

# Function to check for duplicate names
def is_duplicate_name(student_name):
    existing_students = onto.User.instances()  # Fetch instances from the User subclass
    for student in existing_students:
        if student.name.lower() == student_name.lower():
            return True
    return False

# Home Page (Start Here)
@app.route("/")
def home():
    return render_template("home.html")

# Register Page
@app.route("/register", methods=["GET", "POST"])
def register():
    error = None
    if request.method == "POST":
        student_name = request.form.get("student_name").strip()
        if not student_name:
            error = "Please enter a valid name!"
        elif is_duplicate_name(student_name):
            error = f"The name '{student_name}' already exists. Please use a different name."
        else:
            with onto:
                new_user = onto.User()  # Create an instance of the User class
                new_user.name = student_name
            onto.save(file=ontology_path, format="rdfxml")
            return redirect(url_for("login"))
    return render_template("register.html", error=error)

# Login Page
@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        student_name = request.form.get("student_name").strip()
        if not student_name:
            error = "Please enter your name!"
        elif not is_duplicate_name(student_name):
            error = f"The name '{student_name}' is not registered. Please register first."
        else:
            session['student_name'] = student_name
            return redirect(url_for("multiply_input"))
    return render_template("login.html", error=error)

# Statistics Calculation Page
@app.route("/multiply", methods=["GET", "POST"])
def multiply_input():
    student_name = session.get('student_name', 'Student')
    wmul = ""
    frac=""
    if request.method == "POST":
        try:
            f1=request.form.get("numerator1")
            f2=request.form.get("numerator2")
            wnum1= request.form.get("num1")
            wnum2= request.form.get("num2")
            if wnum1 and wnum2:
                wmul=int(wnum1)*int(wnum2)

            if f1 and f2:
                num1 = int(f1.split("/")[0])
                num2 = int(f1.split("/")[1])
                num3 = int(f2.split("/")[0])
                num4 = int(f2.split("/")[1])
                frac = (num1 / num2) * (num3 / num4)


        except ValueError:
            result = {"error": "Invalid input. Please enter numbers separated by commas."}
        except statistics.StatisticsError:
            result = {"error": "No unique mode found for the given numbers."}

    return render_template("multiply_input.html", student_name=student_name, whole=wmul,fraction=frac)

# Practice Quiz Page
@app.route("/practice", methods=["GET", "POST"])
def practice():
    student_name = session.get('student_name', 'Student')

    # Store the question and answer in session to persist data between requests
    if 'question_data' not in session or request.method == "GET":
        session['question_data'] = generate_question()

    question_data = session['question_data']
    feedback = None
    selected_answer = None

    if request.method == "POST":
        # Get the user's selected answer
        selected_answer = request.form.get("answer")
        correct_answer = question_data['answer']

        # Check if the selected answer is correct
        if selected_answer is not None:
            try:
                selected_answer = float(selected_answer)
                if selected_answer == correct_answer:
                    feedback = "Correct! 🎉"
                else:
                    feedback = f"Incorrect. 😞 The correct answer is {correct_answer}."
            except ValueError:
                feedback = f"Invalid input. The correct answer is {correct_answer}."

          

        # Generate a new question when 'Next Question' is clicked
        if "next_question" in request.form:
            session['question_data'] = generate_question()
            return redirect(url_for("practice"))

    return render_template("practice.html", student_name=student_name, question=question_data, feedback=feedback, selected_answer=selected_answer)

def generate_question():
    nums = [random.randint(1, 20) for _ in range(5)]
    mean = round(statistics.mean(nums), 2)
    median = statistics.median(nums)
    try:
        mode = statistics.mode(nums)
    except statistics.StatisticsError:
        mode = "No mode"

    question_type = random.choice(["mean", "median", "mode"])
    if question_type == "mean":
        correct_answer = mean
        question_text = f"What is the mean of the numbers: {nums}?"
    elif question_type == "median":
        correct_answer = median
        question_text = f"What is the median of the numbers: {nums}?"
    else:
        correct_answer = mode
        question_text = f"What is the mode of the numbers: {nums}?"

    options = [correct_answer, correct_answer + 1, correct_answer - 1, random.randint(1, 20)]
    random.shuffle(options)

    return {
        "question": question_text,
        "options": options,
        "answer": correct_answer
    }

# Theory Page
@app.route("/theory")
def theory():
    return render_template("theory.html")

@app.route('/quiz', methods=['GET', 'POST'])
def quiz():
    feedback = None
    question = None
    correct_answer = None
    user_answer = None

    if request.method == 'POST' and 'answer' in request.form:
        # Check the user's answer
        user_answer = request.form.get('answer')
        correct_answer = float(request.form.get('correct_answer'))
        question = request.form.get('question')

        try:
            if float(user_answer) == correct_answer:
                feedback = "Correct!"
            else:
                feedback = f"Wrong! The correct answer is {correct_answer}."
        except ValueError:
            feedback = "Invalid input! Please enter a valid number."
    else:
        # Generate a new question for GET or when the "New Question" button is clicked
        if random.choice([True, False]):
            # Whole number multiplication
            num1 = random.randint(1, 10)
            num2 = random.randint(1, 10)
            question = f"{num1} x {num2}"
            correct_answer = num1 * num2
        else:
            # Fraction multiplication
            num1 = Fraction(random.randint(1, 5), random.randint(1, 5))
            num2 = Fraction(random.randint(1, 5), random.randint(1, 5))
            question = f"{num1} * {num2}"
            correct_answer = float(num1 * num2)
    
    return render_template(
        'quiz.html',
        question=question,
        correct_answer=correct_answer,
        feedback=feedback,
        user_answer=user_answer
    )


if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=9090)