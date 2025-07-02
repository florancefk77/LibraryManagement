import pytest
from app import app  # Replace 'yourapp' with the name of your Flask app's module

@pytest.fixture
def client():
    """Create and configure a test client for the Flask app."""
    app.config.update({
        "TESTING": True,
        "SECRET_KEY": "test_secret_key",  # A secret key for session management
    })
    
    with app.test_client() as client:
        yield client

def test_add_book_as_staff(client):
    """
    Test if a staff member can successfully add a new book.
    """
    # Use a context manager to simulate a logged-in staff user
    with client.session_transaction() as sess:
        sess['user_id'] = 'staff_user@example.com'
        sess['role'] = 'staff'

    # Prepare the form data for the new book
    form_data = {
        'title': 'A New Test Book',
        'author': 'Jane Doe',
        'year': '2025'
    }
    
    # Send a POST request to the '/add_book' endpoint
    response = client.post('/add_book', data=form_data, follow_redirects=True)
    
    # Assert that the request was successful (HTTP 200 OK)
    assert response.status_code == 200
    
    # Assert that the success message is in the response page
    assert b"Book was added." in response.data

def test_add_book_permission_denied_for_user(client):
    """
    Test if a regular user is denied permission to add a book.
    """
    # Use a context manager to simulate a logged-in regular user
    with client.session_transaction() as sess:
        sess['user_id'] = 'regular_user@example.com'
        sess['role'] = 'user' # Assuming 'user' is a non-staff role

    form_data = {
        'title': 'Unauthorized Book',
        'author': 'Hacker Man',
        'year': '2025'
    }
    
    # Send a POST request
    response = client.post('/add_book', data=form_data, follow_redirects=True)

    # Assert that the request was successful (the page loads)
    assert response.status_code == 200
    
    # Assert that the success message is NOT present
    assert b"Book was added." not in response.data
    
    # Assert that an error message is shown (adjust the message to match your app)
    assert b"You do not have permission to perform this action." in response.data