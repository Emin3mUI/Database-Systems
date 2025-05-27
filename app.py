from flask import Flask, request, jsonify
from flask_cors import CORS
import psycopg2
import logging
from flask import render_template  

# Connect to PostgreSQL
conn = psycopg2.connect(
    dbname="Library_Management",
    user="postgres",
    password="",  # Add your password here
    host="localhost",
    port="5432"
)
cur = conn.cursor()

app = Flask(__name__)
CORS(app)

logging.basicConfig(level=logging.DEBUG)

# -------------------- ROUTES -------------------- #

@app.route('/')
def home():
    return render_template('index.html')

# -------------------- BOOK ROUTES -------------------- #

@app.route('/books', methods=['GET'])
def get_books():
    cur.execute("SELECT * FROM book")
    rows = cur.fetchall()
    books = []
    for row in rows:
        books.append({
            'book_id': row[0],
            'title': row[1],
            'author': row[2],
            'genre': row[3],
            'publisher': row[4],
            'quantity': row[5],
            'available': row[6],
            'place': row[7]
        })
    return jsonify(books)

@app.route('/books', methods=['POST'])
def add_book():
    data = request.json
    cur.execute("""
        INSERT INTO book (book_id, title, author, genre, publisher, quantity, available, place)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """, (
        data['book_id'], data['title'], data['author'], data['genre'],
        data['publisher'], data['quantity'], data['available'], data['place']
    ))
    conn.commit()
    return jsonify({'message': 'Book added successfully'})

@app.route('/books/<book_id>', methods=['DELETE'])
def delete_book(book_id):
    cur.execute("DELETE FROM book WHERE book_id = %s", (book_id,))
    conn.commit()
    return jsonify({'message': f'Book {book_id} deleted successfully'})

# -------------------- BORROWING ROUTES -------------------- #

@app.route('/borrow', methods=['POST'])
def borrow_book():
    data = request.json
    book_id = data['book_id']
    borrower_email = data['borrower_email']
    start_date = data['start_date']
    return_date = data['return_date']

    # Check if book is available
    cur.execute("SELECT available FROM book WHERE book_id = %s", (book_id,))
    result = cur.fetchone()
    if not result or not result[0]:  # available is FALSE or book doesn't exist
        return jsonify({'error': 'Book not available'}), 400

    # Insert borrow record
    cur.execute("""
        INSERT INTO borrowing (borrower_email, book_id, start_date, return_date, is_it_returned)
        VALUES (%s, %s, %s, %s, %s)
    """, (borrower_email, book_id, start_date, return_date, False))

    # Mark book unavailable
    cur.execute("UPDATE book SET available = FALSE WHERE book_id = %s", (book_id,))
    conn.commit()
    return jsonify({'message': 'Book borrowed successfully'})

@app.route('/return', methods=['POST'])
def return_book():
    data = request.json
    borrower_id = data['borrower_id']
    book_id = data['book_id']

    # Mark as returned
    cur.execute("""
        UPDATE borrowing SET is_it_returned = TRUE WHERE borrower_id = %s
    """, (borrower_id,))

    # Make book available again
    cur.execute("""
        UPDATE book SET available = TRUE WHERE book_id = %s
    """, (book_id,))
    conn.commit()
    return jsonify({'message': 'Book returned successfully'})

# -------------------- BORROWER ROUTES -------------------- #

@app.route('/borrowers', methods=['POST'])
def add_borrower():
    data = request.json
    cur.execute("""
        INSERT INTO borrower (email, password)
        VALUES (%s, %s)
    """, (data['email'], data['password']))
    conn.commit()
    return jsonify({'message': 'Borrower registered successfully'})

# -------------------- RUN APP -------------------- #

if __name__ == '__main__':
    app.run(debug=True)
