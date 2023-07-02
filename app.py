from flask import Flask,render_template,request,redirect,session, send_file
import mysql.connector
import csv
import os

app = Flask(__name__, static_folder='static')
app.secret_key = '18ee7769bacfbde9f36feac954e0e787'

# Configure MySQL connection
db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="root",
    database="sampdb2"
)

# Create table for login and sign in
cursor = db.cursor()
create_table_query = """
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL,
    password VARCHAR(50) NOT NULL
)
"""
cursor.execute(create_table_query)

create_ticket_table_query = """
CREATE TABLE IF NOT EXISTS tickets (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(50) NOT NULL,
    age INT(2) NOT NULL,
    aadhar_number VARCHAR(12) NOT NULL,
    train_number VARCHAR(10) NOT NULL,
    source VARCHAR(50) NOT NULL,
    destination VARCHAR(50) NOT NULL,
    compartment VARCHAR(50) NOT NULL,
    food VARCHAR(50) NOT NULL
)
"""
cursor.execute(create_ticket_table_query)

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/home2')
def home2():
    return render_template('home2.html')

@app.route('/ticket', methods=['GET', 'POST'])
def ticket():
    if 'username' not in session:
        return redirect('/login')
    
    compartment_availability = None
    
    if request.method == 'POST':
        name = request.form['name']
        age = request.form['age']
        aadhar_number = request.form['aadhar_number']
        train_number = request.form['train_number']
        source = request.form['source']
        destination = request.form['destination']
        compartment = request.form['compartment']
        food = request.form['food']
        
        cursor = db.cursor()
        availability_query = "SELECT * FROM tickets WHERE train_number = %s AND compartment = %s"
        cursor.execute(availability_query, (train_number, compartment))
        result = cursor.fetchone()

        if result:
            compartment_availability = "Compartment not available"
        else:
            # Insert the ticket details into the database
            cursor = db.cursor()
            insert_query = "INSERT INTO tickets ( name, age, aadhar_number, train_number, source, destination, compartment, food) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"
            cursor.execute(insert_query, (name, age, aadhar_number, train_number, source, destination, compartment, food))
            db.commit()
            
            return redirect('/tickets')

    return render_template('ticket.html', compartment_availability=compartment_availability)


@app.route('/tickets')
def tickets():
    if 'username' not in session:
        return redirect('/login')

    # Retrieve all tickets from the database
    cursor = db.cursor()
    select_query = "SELECT * FROM tickets"
    cursor.execute(select_query)
    tickets = cursor.fetchall()

    return render_template('tickets.html', tickets=tickets)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Check if user exists
        cursor = db.cursor()
        select_query = "SELECT * FROM users WHERE username = %s AND password = %s"
        cursor.execute(select_query, (username, password))
        result = cursor.fetchone()

        if result:
            session['username'] = username
            return redirect('/home2')
        else:
            return "Invalid username or password"

    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Check if username already exists
        cursor = db.cursor()
        select_query = "SELECT * FROM users WHERE username = %s"
        cursor.execute(select_query, (username,))
        result = cursor.fetchone()

        if result:
            return "Username already exists"

        # Insert new user
        insert_query = "INSERT INTO users (username, password) VALUES (%s, %s)"
        cursor.execute(insert_query, (username, password))
        db.commit()

        return redirect('/login')

    return render_template('signup.html')


@app.route('/download_ticket/<ticket_id>')
def download_ticket(ticket_id):
    # Fetch ticket details from the database
    cursor = db.cursor()
    select_query = "SELECT * FROM tickets WHERE id = %s"
    cursor.execute(select_query, (ticket_id,))
    ticket = cursor.fetchone()

    # Create a temporary CSV file to store the ticket details
    with open('ticket.csv', 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['Id', 'Name', 'Train Number', 'Source', 'Destination', 'Compartment', 'Food Preference'])
        writer.writerow(ticket)

    # Generate the download URL for the temporary CSV file
    download_url = "/download_ticket_report/" + ticket_id

    return render_template('download.html', download_url=download_url)

@app.route('/download_ticket_report/<ticket_id>')
def download_ticket_report(ticket_id):
    # Fetch the temporary CSV file path
    csv_file = os.path.join(os.getcwd(), 'ticket.csv')

    # Send the temporary CSV file as a response for download
    return send_file(csv_file, as_attachment=True, attachment_filename='ticket.csv')


# Run the Flask app
if __name__ == '__main__':
    app.run()
