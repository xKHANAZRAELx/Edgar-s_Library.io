from flask import Flask, render_template, request, redirect, session, url_for, flash
from datetime import datetime
import random 
import pyrebase


config = {
    "apiKey": "AIzaSyAZNijJ47hvPWqAUUchlBqnMjySD_jNbRc",
    "authDomain": "edgar-s-library.firebaseapp.com",
    "projectId": "edgar-s-library",
    "storageBucket": "edgar-s-library.appspot.com",
    "messagingSenderId": "672953597637",
    "appId": "1:672953597637:web:516ea77fd5936be3f4baac",
    "measurementId": "G-STRWR4NX96",
    "databaseURL":"https://edgar-s-library-default-rtdb.firebaseio.com"
}

firebase = pyrebase.initialize_app(config)
app = Flask(__name__)

db = firebase.database()
storage = firebase.storage()

app.secret_key = 'dgsgsfgggedg' 
ADMIN_USERNAME = 'admin'
ADMIN_PASSWORD = 'admin_password'

books = []

@app.route("/admin/login", methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['logged_in'] = True
            return redirect(url_for('add_book'))
        else:
            return render_template('admin.html', message='Invalid credentials')
    return render_template('admin.html', message='')

@app.route("/add_book", methods=['GET', 'POST'])
def add_book():
    if request.method == 'POST':
        if 'image' not in request.files:
            flash('No file part', 'error')
            return redirect(request.url)
        file = request.files['image']
        if file.filename == '':
            flash('No selected file', 'error')
            return redirect(request.url)
        if file:
            try:
                image_name = f"book_{datetime.now().strftime('%Y%m%d%H%M%S')}.jpg"
                storage.child("images/" + image_name).put(file)
                image_url = storage.child("images/" + image_name).get_url(None)
                title = request.form.get('title')
                author = request.form.get('author')
                price = request.form.get('price')
                category = request.form.get('category')
                new_book = {
                    "title": title,
                    "author": author,
                    "price": price,
                    "image_url": image_url,
                    "category": category
                }
                db.child("books").push(new_book)
                flash('Book added successfully', 'success')
                return redirect(url_for('book_added_successfully'))
            except Exception as e:
                flash(f'Failed to upload image: {str(e)}', 'error')

    books_data = db.child("books").get().val() or {}
    return render_template('add_book.html', books=books_data)

@app.route("/fiction")
def fiction():
    fiction_books = db.child("books").order_by_child("category").equal_to("fiction").get().val() or {}
    return render_template('fiction.html', books=fiction_books)

@app.route("/nonfiction")
def nonfiction():
    nonfiction_books = db.child("books").order_by_child("category").equal_to("nonfiction").get().val() or {}
    return render_template('nonfiction.html', books=nonfiction_books)


@app.route("/childrens")
def childrens():
    childrens_books = {}
    books_data = db.child("books").get().val() or {}
    for key, book in books_data.items():
        if book.get('category') == 'childrens':
            childrens_books[key] = book
    return render_template('childrens.html', books=childrens_books)

def manage_cart(action, book_id=None):
    if 'cart' not in session:
        session['cart'] = []

    if action == 'add':
        book_data = db.child("books").child(book_id).get().val()
        if book_data:
            book_data['id'] = book_id
            session['cart'].append(book_data)
            flash('Book added to cart successfully', 'success')
        else:
            flash('Book not found', 'error')
    elif action == 'remove':
        for idx, item in enumerate(session['cart']):
            if item.get('id') == book_id:
                del session['cart'][idx]
                flash('Book removed from cart successfully', 'success')
                break
    elif action == 'refresh':
        session['cart'] = []
        flash('Cart refreshed successfully', 'success')

@app.route("/cart", methods=['GET', 'POST'])
def cart():
    if request.method == 'POST':
        action = request.form.get('action')
        book_id = request.form.get('book_id')
        if action:
            manage_cart(action, book_id)
    return render_template('cart.html', cart=session.get('cart', [])) 

@app.route("/add_to_cart/<book_id>", methods=['POST'])
def add_to_cart(book_id):
    if 'cart' not in session:
        session['cart'] = []

    if request.method == 'POST':
        book_id = request.form['book_id']

    book_data = db.child("books").child(book_id).get().val()
    if book_data:
        book_data['id'] = book_id
        session['cart'].append(book_data)
        flash('Book added to cart successfully', 'success')
    else:
        flash('Book not found', 'error')

    return redirect(url_for('index'))

@app.route("/remove_from_cart/<book_id>", methods=['POST'])
def remove_from_cart(book_id):
    manage_cart('remove', book_id)
    return redirect(url_for('cart'))

@app.route("/refresh_cart", methods=['POST'])
def refresh_cart():
    manage_cart('refresh')
    return redirect(url_for('cart'))

@app.route("/")
def index():
    return render_template('index.html')

@app.route("/books")
def books():
    books_data = db.child("books").get().val() or {}
    return render_template('books.html', books=books_data)

@app.route("/remove_book/<string:book_id>", methods=['POST'])
def remove_book(book_id):
    db.child("books").child(book_id).remove()
    return redirect(url_for('add_book'))

@app.route("/checkout", methods=['POST'])
def checkout():
    if request.method == 'POST':
        # Retrieve user details and payment information from the form
        user_details = {
            'name': request.form.get('name'),
            'email': request.form.get('email'),
            # Add other fields as needed
        }
        payment_info = {
            'card_number': request.form.get('card_number'),
            'expiry_date': request.form.get('expiry_date'),
            # Add other fields as needed
        }

        # Generate a random 4 or 5 digit code
        confirmation_code = ''.join(random.choices('0123456789', k=random.randint(4, 5)))

        # Process the purchase (e.g., update the database, charge the payment, etc.)
        # Here, you can implement the logic to handle the purchase, update the database, etc.

        # Clear the cart after successful purchase
        session.pop('cart', None)

        # Display a success message to the user
        return render_template('confirmation.html', confirmation_code=confirmation_code)

@app.route("/confirmation", methods=['GET'])
def confirmation_page():
    return render_template('confirmation.html')

@app.route("/search", methods=["GET"])
def search():
    search_query = request.args.get("searchInput")
    search_results = {}
    
    # Query the database for matching books based on search query
    if search_query:
        books_data = db.child("books").get().val() or {}
        for key, book in books_data.items():
            if search_query.lower() in book.get('title', '').lower() or search_query.lower() in book.get('author', '').lower():
                search_results[key] = book
    
    return render_template('search_results.html', search_results=search_results, search_query=search_query)

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        message = request.form['message']
        
        # Store form submission in Firebase Realtime Database
        db.child('contact_forms').push({
            'name': name,
            'email': email,
            'message': message
        })
        
        return 'Form submitted successfully!'
    return render_template('contactus.html')

@app.route('/admin/messages')
def admin_messages():
    messages = []
    # Retrieve form submissions from Firebase Realtime Database
    contact_forms = db.child('contact_forms').get()
    if contact_forms.each():
        for contact_form in contact_forms.each():
            messages.append(contact_form.val())
    return render_template('admin_messages.html', messages=messages)


if name == 'main':
    app.run( debug=True, host='0.0.0.0', port=5000)