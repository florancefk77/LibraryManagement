import pytest
from flask.testing import FlaskClient
from werkzeug.datastructures import Headers
from app import app, session  # Replace 'yourapp' with your actual module name

@pytest.fixture
def client():
    """
    Creates a test client for the Flask application.
    This fixture is used to simulate HTTP requests to the application.
    """
    app.config.update({
        "TESTING": True,  # Enable testing mode
        "SECRET_KEY": "book"  # Required for session handling
    })
    
    def _get_client(user_id=None, role=None):
        """
        Helper function to create a test client with optional user authentication.
        
        Args:
            user_id (str): User ID to simulate authentication
            role (str): User role to simulate (e.g., 'staff', 'user')
        """
        client = app.test_client()
        
        # Simulate session data for authenticated tests
        if user_id is not None:
            with client.session_transaction() as sess:
                sess['user_id'] = user_id
                if role:
                    sess['role'] = role
        
        return client
    
    return _get_client

def test_edit_book_valid_post(client):
    """
    Test editing a book with valid data.
    """
    client_instance = client('testedit@gmail.com', 'staff')
    
    # Prepare valid form data
    data = {
        'title': 'Test 2',
        'author': 'reem2',
        'year': '2027'
    }
    
    response = client_instance.post('/edit_book/3', data=data, follow_redirects=True)
    
    # Print the response status code and data for debugging
    print(f"Response Status Code: {response.status_code}")
    print(f"Response Data: {response.data.decode('utf-8')}")
    
    assert response.status_code == 200
    assert 'Book was edited.' in response.data.decode('utf-8')  # Decode for assertion

    