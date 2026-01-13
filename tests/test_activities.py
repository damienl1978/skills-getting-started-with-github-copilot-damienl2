"""
Tests for the Mergington High School Activities API
"""

import pytest
from fastapi.testclient import TestClient
import sys
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from app import app

@pytest.fixture
def client():
    """Create a test client for the FastAPI app"""
    return TestClient(app)


@pytest.fixture
def reset_activities(client):
    """Reset activities to initial state before each test"""
    # The app is stateful, so we need to work with existing data
    yield
    

class TestActivityEndpoints:
    """Tests for activity endpoints"""

    def test_root_redirect(self, client):
        """Test that root path redirects to static/index.html"""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert response.headers["location"] == "/static/index.html"

    def test_get_activities(self, client):
        """Test fetching all activities"""
        response = client.get("/activities")
        assert response.status_code == 200
        
        activities = response.json()
        assert isinstance(activities, dict)
        assert len(activities) > 0
        
        # Verify expected activities exist
        expected_activities = [
            "Chess Club", 
            "Programming Class", 
            "Gym Class",
            "Basketball Team",
            "Tennis Club",
            "Drama Club",
            "Art Studio",
            "Robotics Club",
            "Debate Team"
        ]
        for activity in expected_activities:
            assert activity in activities
        
        # Verify structure of activity data
        for activity_name, details in activities.items():
            assert "description" in details
            assert "schedule" in details
            assert "max_participants" in details
            assert "participants" in details
            assert isinstance(details["participants"], list)

    def test_signup_success(self, client):
        """Test successful signup for an activity"""
        # Use a test email
        test_email = "test.student@mergington.edu"
        activity_name = "Chess Club"
        
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": test_email}
        )
        
        assert response.status_code == 200
        result = response.json()
        assert "message" in result
        assert test_email in result["message"]
        assert activity_name in result["message"]
        
        # Verify participant was added
        activities = client.get("/activities").json()
        assert test_email in activities[activity_name]["participants"]

    def test_signup_duplicate(self, client):
        """Test that duplicate signup returns error"""
        test_email = "michael@mergington.edu"  # Already in Chess Club
        activity_name = "Chess Club"
        
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": test_email}
        )
        
        assert response.status_code == 400
        result = response.json()
        assert "already signed up" in result["detail"].lower()

    def test_signup_nonexistent_activity(self, client):
        """Test signup for activity that doesn't exist"""
        test_email = "test@mergington.edu"
        activity_name = "Nonexistent Activity"
        
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": test_email}
        )
        
        assert response.status_code == 404
        result = response.json()
        assert "not found" in result["detail"].lower()

    def test_unregister_success(self, client):
        """Test successful unregistration from an activity"""
        # First add a participant
        test_email = "temp.student@mergington.edu"
        activity_name = "Programming Class"
        
        # Sign up
        client.post(
            f"/activities/{activity_name}/signup",
            params={"email": test_email}
        )
        
        # Verify they're signed up
        activities = client.get("/activities").json()
        assert test_email in activities[activity_name]["participants"]
        
        # Unregister
        response = client.post(
            f"/activities/{activity_name}/unregister",
            params={"email": test_email}
        )
        
        assert response.status_code == 200
        result = response.json()
        assert "Unregistered" in result["message"]
        
        # Verify they're removed
        activities = client.get("/activities").json()
        assert test_email not in activities[activity_name]["participants"]

    def test_unregister_not_signed_up(self, client):
        """Test unregistration for someone not signed up"""
        test_email = "not.signed.up@mergington.edu"
        activity_name = "Tennis Club"
        
        response = client.post(
            f"/activities/{activity_name}/unregister",
            params={"email": test_email}
        )
        
        assert response.status_code == 400
        result = response.json()
        assert "not signed up" in result["detail"].lower()

    def test_unregister_nonexistent_activity(self, client):
        """Test unregistration from activity that doesn't exist"""
        test_email = "test@mergington.edu"
        activity_name = "Nonexistent Activity"
        
        response = client.post(
            f"/activities/{activity_name}/unregister",
            params={"email": test_email}
        )
        
        assert response.status_code == 404
        result = response.json()
        assert "not found" in result["detail"].lower()

    def test_activity_details_structure(self, client):
        """Test that activity details have correct structure"""
        response = client.get("/activities")
        activities = response.json()
        
        for activity_name, details in activities.items():
            assert isinstance(details["description"], str)
            assert len(details["description"]) > 0
            assert isinstance(details["schedule"], str)
            assert isinstance(details["max_participants"], int)
            assert details["max_participants"] > 0
            assert isinstance(details["participants"], list)
            assert len(details["participants"]) <= details["max_participants"]
