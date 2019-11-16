from flask import Flask, render_template, flash, session, redirect, url_for, logging, request, jsonify 
from flask_mysqldb import MySQL
from functools import wraps
from wtforms import Form, DateField, StringField, TextAreaField, PasswordField, IntegerField, validators, StringField, SubmitField, DateTimeField, SelectField
from passlib.hash import sha256_crypt
import datetime
import smtplib

app = Flask(__name__)

# init database connection settings
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'swen90016'
app.config['MYSQL_PASSWORD'] = 'swen90016'
app.config['MYSQL_DB'] = 'swen90016'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

# init MYSQL
mysql = MySQL(app)

# init email server
email_server = smtplib.SMTP('smtp.gmail.com', 587, timeout=10)

# check if user has logged in
def is_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash('Unauthorized, Please login', 'danger')
            return redirect(url_for('login'))
    return wrap

# check if user is an administrator
def is_customer(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if  session.get('user_type') == 'customer':
            return f(*args, **kwargs)
        else:
            flash('Unauthorized Access', 'danger')
            return redirect(url_for('index'))
    return wrap

# check if user is an administrator
def is_shipper(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if  session.get('user_type') == 'shipper':
            return f(*args, **kwargs)
        else:
            flash('Unauthorized Access', 'danger')
            return redirect(url_for('index'))
    return wrap

# check if user is an administrator
def is_collector(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if  session.get('user_type') == 'collector':
            return f(*args, **kwargs)
        else:
            flash('Unauthorized Access', 'danger')
            return redirect(url_for('index'))
    return wrap

#======================================================================Login & Logout=================================================================#
@app.route('/')
def index():
    return redirect(url_for('login'))

# API for login
@app.route('/login', methods = ['GET','POST'])
def login():   
    # check if logged_in
    if session.get('logged_in'):
        # direct to pages based on user type
        if session['user_type'] == 'customer':
            return redirect(url_for('customer')) 
        elif session['user_type'] == 'shipper':
            return redirect(url_for('shipper'))
        elif session['user_type'] == 'collector':
            return redirect(url_for('collector')) 
    else:
        # init forms
        registerForm = PersonalInfoForm()
        loginForm = LoginForm(request.form)
        # validate form and request
        if request.method == 'POST' and loginForm.validate(): 
            # database connection
            email = loginForm.email.data
            password_candidate = loginForm.password.data
            cur = mysql.connection.cursor()
            result = cur.execute("SELECT * FROM users where email = %s", [email])
            # email correct
            if result > 0:
                data = cur.fetchone()
                password = data['password']
                # password correct
                if sha256_crypt.verify(password_candidate, password):
                    # session handling
                    session['logged_in'] = True
                    session['id'] = data['id']
                    session['name'] = data['name']
                    session['email'] = data['email']
                    session['address'] = data['address']
                    session['phone'] = data['phone']
                    session['user_type'] = data['type']
                    cur.close()
                    # jump to pages based on user type
                    if session['user_type'] == 'customer':
                        return redirect(url_for('customer')) 
                    elif session['user_type'] == 'shipper':
                        return redirect(url_for('shipper'))
                    elif session['user_type'] == 'collector':
                        return redirect(url_for('collector')) 
                # wrong password
                else:
                    cur.close()
                    flash('WRONG PASSWORD','danger')
            # no email matched in database  
            else:
                #app.logger.error('NO USER')
                cur.close()
                flash('NO USER MATCHED','danger')
    # render login page
    return render_template('login.html', loginForm=loginForm, registerForm = registerForm)

# API for register
@app.route('/register', methods = ['GET','POST'])
def register ():
        # init forms
        registerForm = PersonalInfoForm(request.form)
        # validate form and request
        if request.method == 'POST' and registerForm.validate(): 
            # database connection
            email = registerForm.email.data
            name = registerForm.name.data
            address = registerForm.address.data
            phone = registerForm.phone.data
            password = sha256_crypt.hash(registerForm.password.data)
            type = 'customer'
            cur = mysql.connection.cursor()
            result = cur.execute("SELECT * FROM users where email = %s", [email])
            # email exist
            if result > 0:
                flash('User Already Exist','danger')
            # email not exist
            else:
                cur.execute("INSERT INTO users (email,name,address,phone,password,type) values (%s,%s,%s,%s,%s,%s)", [email,name,address,phone,password,type] )
                #commit
                mysql.connection.commit()
                flash('Successfully Registed','success')
            cur.close()
            # jump to login page
            return redirect(url_for('login'))
        else:
            # jump to login page with error
            flash('Invalid Form','danger')
            return redirect(url_for('login'))

# API for logout
@app.route('/logout')
@is_logged_in
def logout():   
    # clear session and jump to index page (login page)
    session.clear()
    return redirect(url_for('index'))

# API for about
@app.route('/about')
def about():   
    return render_template('about.html')

# API for documents
@app.route('/documents')
def documents():   
    return render_template('documents.html')

#============================================================================Customer=================================================================#
# API for customer
@app.route('/customer')
@is_logged_in
@is_customer
def customer():
    # database connection
    updateForm = PersonalInfoForm()
    requestForm = RequestForm()
    cur = mysql.connection.cursor()
    result = cur.execute("SELECT * FROM bookings where customerID = %s", [session['id']])
    bookings = None
    # if booking exist
    if result > 0:
        bookings = cur.fetchall()
    # if booking not exist
    else:
        flash('Create new booking request by clicking [Create New Booking] button above','success')
    cur.close()
    # render customer page with data
    return render_template('customer.html', updateForm=updateForm, requestForm = requestForm, bookings = bookings)

# API for updating customer personal information
@app.route('/customer/update',methods = ['GET','POST'])
@is_logged_in
@is_customer
def update():
    # update their own booking information
    updateForm = PersonalInfoForm(request.form)
    # validate request and form
    if request.method == 'POST' and updateForm.validate(): 
        # database connection
        email = updateForm.email.data
        name = updateForm.name.data
        address = updateForm.address.data
        phone = updateForm.phone.data
        password = sha256_crypt.hash(updateForm.password.data)
        cur = mysql.connection.cursor()
        cur.execute("UPDATE users SET email=%s, name=%s, address=%s, phone=%s, password=%s WHERE id=%s", [email,name,address,phone,password,session['id']] )
        # commit
        mysql.connection.commit()
        # session handling
        session['name'] = name
        session['email'] = email
        session['address'] = address
        session['phone'] = phone
        flash('Success','success')  
        cur.close()
    else:
        flash('Invalid Form','danger')
    # jump to customer page
    return redirect(url_for('customer'))

# API for creating booking request
@app.route('/customer/bookingRequest',methods = ['GET','POST'])
@is_logged_in
@is_customer
def bookingRequest():
    # update their own booking information
    requestForm = RequestForm(request.form)
    # validate request and form
    if request.method == 'POST' and requestForm.validate():
        # database connection
        boxes = requestForm.boxes.data
        destinationAddress = requestForm.destinationAddress.data
        pickupAddress = requestForm.pickupAddress.data
        departureDate = requestForm.departureDate.data
        arrivalDate = requestForm.arrivalDate.data
        customerMessage = requestForm.message.data
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO bookings (customerID, boxes, destinationAddress, pickupAddress, departureDate, arrivalDate, customerMessage) values (%s,%s,%s,%s,%s,%s,%s)", [session['id'],boxes, destinationAddress, pickupAddress, departureDate, arrivalDate, customerMessage] )
        # commit
        mysql.connection.commit()
        cur.close()
        flash('Your booking has been created','success')
    else:
        flash('Invalid Form','danger')
    # jump to customer page
    return redirect(url_for('customer'))

#============================================================================Shipper=================================================================#
# API for shipper page
@app.route('/shipper')
@is_logged_in
@is_shipper
def shipper():
    # init forms
    ackForm = AckForm()
    # database connection
    cur = mysql.connection.cursor()
    result = cur.execute("SELECT * FROM bookings")
    bookings = None
    # if booking exist
    if result > 0:
        bookings = cur.fetchall()
    # if booking not exist
    else:
        flash('No Booking Records','danger')
    cur.close()
    # render shipper page with data
    return render_template('shipper.html',ackForm = ackForm, bookings = bookings)

# API for shipper page
@app.route('/shipper/editBookingAck/<string:bookingID>',methods = ['GET','POST'])
@is_logged_in
@is_shipper
def editBookingAck(bookingID):
    # init forms
    ackForm = AckForm(request.form)
    # validate request and form
    if request.method == 'POST' and ackForm.validate():
        # database connection
        HBL_Number = ackForm.HBL_Number.data
        status = ackForm.status.data
        pickupDate = ackForm.pickupDate.data
        message = ackForm.message.data
        cur = mysql.connection.cursor()
        cur.execute("UPDATE bookings SET HBL_Number=%s, status=%s, pickupDate=%s, shipperMessage=%s WHERE id=%s", [HBL_Number,status,pickupDate,message,bookingID] )
        # commit
        mysql.connection.commit()
        cur.execute("SELECT users.email FROM users where type='collector'")
        collectors = cur.fetchall()
        cur.execute("SELECT users.email FROM users JOIN bookings ON (users.id = bookings.customerID) WHERE bookings.id=%s ",[bookingID])
        customers = cur.fetchall()
        cur.close() 
        # initialize email server here
        email_server.ehlo()
        email_server.starttls()
        email_server.login("2018swen90016@gmail.com", "swen900162018")
        for collector in collectors:
            email = collector['email']
            msg = "Shippment information has been updated!" # The /n separates the message from the headers
            email_server.sendmail("server email", email, msg)
        for customer in customers:
            email = customer['email']
            msg = "Shippment information has been updated!" # The /n separates the message from the headers
            email_server.sendmail("server email", email, msg)
        email_server.quit()
        flash('Updated information has been send to customer and collector','success')
    else:
        flash('Invalid Form','danger')
    # jump to shipper page
    return redirect(url_for('shipper'))

#============================================================================Collector=================================================================#
# API for collector page
@app.route('/collector')
@is_logged_in
@is_collector
def collector():
    # database connection
    cur = mysql.connection.cursor()
    result = cur.execute("SELECT * FROM bookings")
    bookings = None
    # if booking exist
    if result > 0:
        bookings = cur.fetchall()
    # if booking not exist
    else:
        flash('No Booking Records','danger')
    cur.close()
    # render collector page
    return render_template('collector.html', bookings = bookings)

#============================================================================Forms=================================================================#
# specify login form
class LoginForm(Form):
    email = StringField('', [validators.Length(min=4, max=40)])  
    password = PasswordField('', [validators.Length(min=6, max=25)])

# specify register form
class PersonalInfoForm(Form):
    name = StringField('', [validators.Length(min=2, max=25)])
    email = StringField('', [validators.Length(min=4, max=40)])
    address = StringField('', [validators.Length(min=4, max=100)])
    phone = StringField('', [validators.Length(min=4, max=100)])
    password = PasswordField('', [validators.Length(min=6, max=25)])

# specify update form
class UpdateForm(Form):
    email = StringField('', [validators.Length(min=6, max=40)])  

# specify booking request form
class RequestForm(Form):
    boxes = IntegerField('', [validators.NumberRange(min=1, max=99)])  
    destinationAddress = StringField('', [validators.Length(min=4, max=100)])
    pickupAddress = StringField('', [validators.Length(min=4, max=100)])    
    departureDate = SelectField('',choices=[('2018-10-15 23:59:59', '2018-10-15 23:59:59'), ('2018-10-16 23:59:59', '2018-10-16 23:59:59'), ('2018-10-17 23:59:59', '2018-10-17 23:59:59')])
    arrivalDate = SelectField('',choices=[('2018-11-15 23:59:59', '2018-11-15 23:59:59'), ('2018-11-16 23:59:59', '2018-11-16 23:59:59'), ('2018-11-17 23:59:59', '2018-11-17 23:59:59')])
    message = StringField('', [validators.Length(min=0, max=200)])  

# specify Booking ack form
class AckForm(Form):
    status = StringField('', [validators.Length(min=1, max=100)])
    pickupDate = SelectField('',choices=[('2018-11-15 23:59:59', '2018-11-15 23:59:59'), ('2018-11-16 23:59:59', '2018-11-16 23:59:59'), ('2018-11-17 23:59:59', '2018-11-17 23:59:59')])
    HBL_Number = IntegerField('', [validators.NumberRange(min=0, max=99999)])  
    message = StringField('', [validators.Length(min=0, max=200)])  

if __name__ == '__main__':
    app.secret_key='secret123'
    app.run(debug=True)

