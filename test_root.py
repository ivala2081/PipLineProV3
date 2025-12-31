from app import create_app

app = create_app()
with app.test_client() as client:
    response = client.get('/')
    print(f"Status: {response.status_code}")
    print(f"Headers: {dict(response.headers)}")
    if response.status_code == 302:
        print(f"Redirect to: {response.location}")
    print(f"Data length: {len(response.data)}")
    if len(response.data) < 500:
        print(f"Data: {response.data.decode('utf-8')}")

