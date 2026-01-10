import http.server
import socketserver
import json
import sqlite3
import os
from datetime import datetime

PORT = 3000
DB_NAME = 'ramadan_company.db'

class CustomHandler(http.server.SimpleHTTPRequestHandler):
    def do_POST(self):
        if self.path == '/api/contact':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            
            try:
                data = json.loads(post_data)
                
                # Save to DB
                conn = sqlite3.connect(DB_NAME)
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO contacts (full_name, phone_number, message, created_at)
                    VALUES (?, ?, ?, ?)
                """, (data.get('name'), data.get('phone'), data.get('message'), datetime.now()))
                conn.commit()
                conn.close()
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                response = {"status": "success", "message": "Data saved"}
                self.wfile.write(json.dumps(response).encode('utf-8'))
                
            except Exception as e:
                print(f"Error: {e}")
                self.send_response(500)
                self.end_headers()
        else:
            self.send_error(404)

    def do_GET(self):
        return http.server.SimpleHTTPRequestHandler.do_GET(self)

print(f"Serving at http://localhost:{PORT}")
print("Press Ctrl+C to stop the server.")

with socketserver.TCPServer(("", PORT), CustomHandler) as httpd:
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
