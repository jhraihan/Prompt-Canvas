import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

User = get_user_model()
PASSWORD = "correct-horse-battery"


@pytest.fixture
def user(db):
    return User.objects.create_user(email="painter@example.com", password=PASSWORD)


@pytest.fixture
def other_user(db):
    return User.objects.create_user(email="stranger@example.com", password=PASSWORD)


@pytest.fixture
def client():
    return APIClient()


@pytest.fixture
def auth_client(client, user):
    client.force_authenticate(user=user)
    return client
