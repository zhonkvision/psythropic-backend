import http.server
import socketserver
import urllib.parse
import json
import subprocess
import os
import sys

PORT = int(os.environ.get('PORT', 8889))

class CustomThreadingHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        # Allow cross-origin requests just in case, though they are mostly same-origin
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

    def do_POST(self):
        if self.path == '/api/download':
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length).decode('utf-8')
            
            try:
                data = json.loads(post_data)
                url = data.get('url')
            except Exception as e:
                self.send_response(400)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'error': 'Invalid JSON format'}).encode('utf-8'))
                return

            if not url:
                self.send_response(400)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'error': 'No URL parameter provided'}).encode('utf-8'))
                return

            # Ensure downloads directory exists
            os.makedirs('downloads', exist_ok=True)

            # Setup Environment Path to ensure yt-dlp finds ffmpeg
            env = os.environ.copy()
            env['PATH'] = env.get('PATH', '') + ':/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin'

            print(f"Downloading stream URL via yt-dlp: {url}")
            
            # yt-dlp arguments
            cmd = [
                'yt-dlp',
                '--extractor-args', 'youtube:player_client=ios,tv,tvhtml5,android',
                '-x',
                '--audio-format', 'mp3',
                '-o', 'downloads/%(title)s.%(ext)s',
                '--restrict-filenames',
                '--no-playlist',
                '--print', 'after_move:filepath',
                url
            ]

            try:
                # Run yt-dlp
                result = subprocess.run(cmd, capture_output=True, text=True, env=env)
                
                if result.returncode == 0:
                    filepath = result.stdout.strip()
                    print(f"yt-dlp output path: {filepath}")
                    
                    # Convert to relative browser path (starting with /downloads/)
                    rel_idx = filepath.find('downloads/')
                    if rel_idx != -1:
                        file_url = '/' + filepath[rel_idx:]
                    else:
                        file_url = '/downloads/' + os.path.basename(filepath)
                        
                    self.send_response(200)
                    self.send_header('Content-Type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({
                        'status': 'success',
                        'file': file_url,
                        'title': os.path.basename(filepath)
                    }).encode('utf-8'))
                else:
                    error_msg = result.stderr.strip() or result.stdout.strip() or "Unknown yt-dlp error"
                    print(f"yt-dlp failed: {error_msg}")
                    self.send_response(500)
                    self.send_header('Content-Type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({
                        'error': 'Download failed',
                        'details': error_msg
                    }).encode('utf-8'))
            except Exception as e:
                print(f"Server exception: {str(e)}")
                self.send_response(500)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({
                    'error': 'Internal server exception',
                    'details': str(e)
                }).encode('utf-8'))
        else:
            self.send_response(404)
            self.end_headers()

def run(server_class=http.server.ThreadingHTTPServer, handler_class=CustomThreadingHTTPRequestHandler):
    server_address = ('', PORT)
    httpd = server_class(server_address, handler_class)
    print(f"Starting custom visualizer backend server on port {PORT}...")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping server...")
        httpd.server_close()

if __name__ == '__main__':
    run()
