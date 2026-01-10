from pyngrok import ngrok
import time

# Open a HTTP tunnel on the default port 3000
try:
    public_url = ngrok.connect(3000).public_url
    print(f" * Public URL: {public_url}")
    
    # Keep it alive
    while True:
        time.sleep(1)
except Exception as e:
    print(f"Error: {e}")
