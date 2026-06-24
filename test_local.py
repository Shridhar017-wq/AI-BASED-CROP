from app import app
import json

client = app.test_client()

payload = {
    "phone": "+919876543210",
    "location": "Mumbai"
}

response = client.post('/api/subscribe_alerts', 
                       data=json.dumps(payload), 
                       content_type='application/json')

print("Status Code:", response.status_code)
print("Response Data:", response.get_data(as_text=True))
