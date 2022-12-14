"""
Account API Service Test Suite

Test cases can be run with the following:
  nosetests -v --with-spec --spec-color
  coverage report -m
"""
import os
import logging
from unittest import TestCase
from tests.factories import AccountFactory
from service.common import status  # HTTP Status Codes
from service.models import db, Account, init_db
from service.routes import app
from service import talisman

DATABASE_URI = os.getenv(
    "DATABASE_URI", "postgresql://postgres:postgres@localhost:5432/postgres"
)

BASE_URL = "/accounts"
HTTPS_ENVIRON = {"wsgi.url_scheme": "https"}

######################################################################
#  T E S T   C A S E S
######################################################################


class TestAccountService(TestCase):
    """Account Service Tests"""

    @classmethod
    def setUpClass(cls):
        """Run once before all tests"""
        # Do not enforce https for testing
        talisman.force_https = False
        app.config["TESTING"] = True
        app.config["DEBUG"] = False
        app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URI
        app.logger.setLevel(logging.CRITICAL)
        init_db(app)

    @classmethod
    def tearDownClass(cls):
        """Runs once before test suite"""

    def setUp(self):
        """Runs before each test"""
        db.session.query(Account).delete()  # clean up the last tests
        db.session.commit()

        self.client = app.test_client()

    def tearDown(self):
        """Runs once after each test case"""
        db.session.remove()

    ######################################################################
    #  H E L P E R   M E T H O D S
    ######################################################################

    def _create_accounts(self, count):
        """Factory method to create accounts in bulk"""
        accounts = []
        for _ in range(count):
            account = AccountFactory()
            response = self.client.post(BASE_URL, json=account.serialize())
            self.assertEqual(
                response.status_code,
                status.HTTP_201_CREATED,
                "Could not create test Account",
            )
            new_account = response.get_json()
            account.id = new_account["id"]
            accounts.append(account)
        return accounts

    ######################################################################
    #  A C C O U N T   T E S T   C A S E S
    ######################################################################

    def test_index(self):
        """It should get 200_OK from the Home Page"""
        response = self.client.get("/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_health(self):
        """It should be healthy"""
        resp = self.client.get("/health")
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertEqual(data["status"], "OK")

    def test_create_account(self):
        """It should Create a new Account"""
        account = AccountFactory()
        response = self.client.post(
            BASE_URL,
            json=account.serialize(),
            content_type="application/json"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Make sure location header is set
        location = response.headers.get("Location", None)
        self.assertIsNotNone(location)

        # Check the data is correct
        new_account = response.get_json()
        self.assertEqual(new_account["name"], account.name)
        self.assertEqual(new_account["email"], account.email)
        self.assertEqual(new_account["address"], account.address)
        self.assertEqual(new_account["phone_number"], account.phone_number)
        self.assertEqual(new_account["date_joined"], str(account.date_joined))

    def test_read_an_account(self):
        """
        """
        # Arrange: Create an account in the database
        account = self._create_accounts(1)[0]
        response_get = self.client.get(
            f"{BASE_URL}/{account.id}",
            content_type="application/json"
        )

        assert response_get.status_code == status.HTTP_200_OK
        json_response_get = response_get.get_json()
        assert json_response_get["name"] == account.name
        assert json_response_get["email"] == account.email
        assert json_response_get["address"] == account.address
        assert json_response_get["phone_number"] == account.phone_number
        assert json_response_get["date_joined"] == str(account.date_joined)

    def test_read_account_not_found(self):
        # Arrange
        # Account id of zero should apparently never exist
        non_existing_account_id = 0
        response_get = self.client.get(
            f"{BASE_URL}/{non_existing_account_id}",
            content_type="application/json"
        )
        assert response_get.status_code == status.HTTP_404_NOT_FOUND

    def test_list_accounts(self):
        # Arrange
        # Create 10 accounts in the database
        self._create_accounts(count=10)
        response_get = self.client.get(
            BASE_URL,
            content_type="application/json"
        )
        assert response_get.status_code == status.HTTP_200_OK
        json_response_body = response_get.get_json()
        assert len(json_response_body) == 10
        assert type(json_response_body) == list
        assert all(type(d) == dict for d in json_response_body)

    def test_list_accounts_empty(self):
        # Test correct behaviour in case there are no accounts
        response_get = self.client.get(
            BASE_URL,
            content_type="application/json"
        )
        assert response_get.status_code == status.HTTP_200_OK
        json_response_body = response_get.get_json()
        assert len(json_response_body) == 0
        assert type(json_response_body) == list

    def test_update_account(self):
        # Create an account in the database
        created_account = self._create_accounts(count=1)[0]
        # Define changes on account
        update_account = AccountFactory()
        update_account.name = "Jeronimo"
        update_account.phone_number = 42
        update_account.id = created_account.id
        response_put = self.client.put(
            f"{BASE_URL}/{created_account.id}",
            json=update_account.serialize()
        )
        assert response_put.status_code == status.HTTP_200_OK
        put_json_response = response_put.get_json()
        assert put_json_response["name"] == "Jeronimo"
        assert put_json_response["phone_number"] == "42"

    def test_update_account_not_existing(self):
        # Send http put request on non - existing id
        response_put = self.client.put(
            f"{BASE_URL}/42",
            json={}
        )
        assert response_put.status_code == status.HTTP_404_NOT_FOUND

    def test_delete_account(self):
        # Create Account
        created_acc = self._create_accounts(count=1)[0]
        response_delete = self.client.delete(
            f"{BASE_URL}/{created_acc.id}"
        )
        assert response_delete.status_code == status.HTTP_204_NO_CONTENT
        is_response_empty = bool(response_delete.get_json())
        assert not is_response_empty

    def test_bad_request(self):
        """It should not Create an Account when sending the wrong data"""
        response = self.client.post(BASE_URL, json={"name": "not enough data"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_unsupported_media_type(self):
        """It should not Create an Account when sending the wrong media type"""
        account = AccountFactory()
        response = self.client.post(
            BASE_URL,
            json=account.serialize(),
            content_type="test/html"
        )
        self.assertEqual(response.status_code, status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)

    def test_method_not_allowed(self):
        "If a HTTP method is used on an endpoint that is not valid, return HTTP status error 405"
        account = AccountFactory()
        response = self.client.post(
            f"{BASE_URL}/{account.id}",
            content_type="application/json",
            json=account.serialize()
        )
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    def test_presence_of_http_security_headers(self):
        root_response = self.client.get(
                                "/",
                                environ_overrides=HTTPS_ENVIRON
        )
        assert root_response.status_code == status.HTTP_200_OK
        assert root_response.headers["X-Frame-Options"] == "SAMEORIGIN"
        assert root_response.headers["X-XSS-Protection"] == "1; mode=block"
        assert root_response.headers["X-Content-Type-Options"] == "nosniff"
        assert root_response.headers["Content-Security-Policy"] == 'default-src \'self\'; object-src \'none\''
        assert root_response.headers["Referrer-Policy"] == "strict-origin-when-cross-origin"

    def test_presence_of_CORS_policy_headers(self):
        root_response = self.client.get("/", environ_overrides=HTTPS_ENVIRON)
        assert root_response.status_code == status.HTTP_200_OK
        assert root_response.headers["Access-Control-Allow-Origin"] == "*"
