"""
Account Service

This microservice handles the lifecycle of Accounts
"""
# pylint: disable=unused-import
from flask import jsonify, request, make_response, abort, url_for   # noqa; F401
from service.models import Account
from service.common import status  # HTTP Status Codes
from . import app  # Import Flask application


############################################################
# Health Endpoint
############################################################
@app.route("/health")
def health():
    """Health Status"""
    return jsonify(dict(status="OK")), status.HTTP_200_OK


######################################################################
# GET INDEX
######################################################################
@app.route("/")
def index():
    """Root URL response"""
    return (
        jsonify(
            name="Account REST API Service",
            version="1.0",
            # paths=url_for("list_accounts", _external=True),
        ),
        status.HTTP_200_OK,
    )


######################################################################
# CREATE A NEW ACCOUNT
######################################################################
@app.route("/accounts", methods=["POST"])
def create_accounts():
    """
    Creates an Account
    This endpoint will create an Account based the data in the body that is posted
    """
    app.logger.info("Request to create an Account")
    check_content_type("application/json")
    account = Account()
    account.deserialize(request.get_json())
    account.create()
    message = account.serialize()
    # Uncomment once get_accounts has been implemented
    # location_url = url_for("get_accounts", account_id=account.id, _external=True)
    location_url = "/"  # Remove once get_accounts has been implemented
    return make_response(
        jsonify(message), status.HTTP_201_CREATED, {"Location": location_url}
    )

######################################################################
# LIST ALL ACCOUNTS
######################################################################


@app.route("/accounts", methods=["GET"])
def list_accounts() -> tuple:
    """
    List all accounts that are in the database.
    """
    app.logger.info("GET request to /accounts")
    all_accounts = Account.all()
    # Serialize into list of dicts
    all_accounts = [acc.serialize() for acc in all_accounts]
    return jsonify(all_accounts), status.HTTP_200_OK

######################################################################
# READ AN ACCOUNT
######################################################################


@app.route("/accounts/<id>", methods=["GET"])
def read_account(id: int) -> tuple:
    search_result = Account.find(id)
    was_found = bool(search_result)
    status_code = status.HTTP_200_OK if was_found else status.HTTP_404_NOT_FOUND
    response_body = search_result.serialize() if was_found else {}

    if not was_found:
        abort(status_code, f"Account with id {id} could not be found :(")

    return jsonify(response_body), status_code

######################################################################
# UPDATE AN EXISTING ACCOUNT
######################################################################


@app.route("/accounts/<id>", methods=["PUT"])
def update_accounts(id: int) -> tuple:
    search_result = Account.find(id)
    was_found = bool(search_result)
    status_code = status.HTTP_200_OK if was_found else status.HTTP_404_NOT_FOUND
    if was_found:
        # Deserialize json into python dictionary
        search_result.deserialize(request.get_json())
        search_result.update()

        return search_result.serialize(), status_code
    else:
        abort(status_code)

######################################################################
# DELETE AN ACCOUNT
######################################################################


@app.route("/accounts/<id>", methods=["DELETE"])
def delete_account(id: int) -> tuple:
    search_result = Account.find(id)
    was_found = bool(search_result)
    if was_found:
        search_result.delete()
    return "", status.HTTP_204_NO_CONTENT

######################################################################
#  U T I L I T Y   F U N C T I O N S
######################################################################


def check_content_type(media_type):
    """Checks that the media type is correct"""
    content_type = request.headers.get("Content-Type")
    if content_type and content_type == media_type:
        return
    app.logger.error("Invalid Content-Type: %s", content_type)
    abort(
        status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
        f"Content-Type must be {media_type}",
    )
