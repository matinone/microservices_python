import os
import requests

def auth_login(request):
    auth = request.authorization
    if not auth:
        return None, ("Missing credentials", 401)

    basic_auth = (auth.username, auth.password)
    response = requests.post(
        f"http://{os.environ.get('AUTH_SERVICE_ADDRESS')}/login",
        auth=basic_auth,
    )

    if response.status_code == 200:
        return response.text, None
    
    return None, (response.text, response.status_code)


def validate_token(request):
    if not "Authorization" in request.headers:
        return None, ("Missing credentials", 401)

    token = request.headers["Authorization"]
    if not token:
        return None, ("Missing credentials", 401)

    response = requests.post(
        f"http://{os.environ.get('AUTH_SERVICE_ADDRESS')}/validate",
        headers={"Authorization": token}
    )

    if response.status_code == 200:
        return response.text, None

    return None, (response.text, response.status_code)
