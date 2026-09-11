import sys
import os
import time
import urllib.request
import urllib.error
import subprocess

# Add src to sys.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

SERVER_KS = """
main() {
    port := 18088
    server := http_listen(port)
    out "SERVER_STARTED"

    count := 0
    while count < 3 {
        req := http_accept(server)
        when req.client_id >= 0 {
            count += 1
            when req.path == "/" {
                http_respond(req.client_id, 200, "text/html", "<h1>Hello from KaniScript Server</h1>")
            } else when req.path == "/api/status" {
                json := "{\\"status\\":\\"ok\\",\\"lang\\":\\"KaniScript\\"}"
                http_respond(req.client_id, 200, "application/json", json)
            } else {
                http_respond(req.client_id, 404, "text/plain", "Not Found")
            }
        }
    }
    http_close(server)
    out "SERVER_FINISHED"
}
"""

def test_http_server():
    print("=== Testing KaniScript HTTP Server ===")
    
    # 1. Compile to executable
    exe_path = "/tmp/test_kani_server"
    c_path = "/tmp/test_kani_server.c"
    
    # Use compiler.py directly
    with open("/tmp/test_server.ks", "w") as f:
        f.write(SERVER_KS)
        
    compiler_path = os.path.join(os.path.dirname(__file__), "..", "src", "compiler.py")
    res = subprocess.run([sys.executable, compiler_path, "build", "/tmp/test_server.ks", "-o", exe_path], capture_output=True, text=True)
    if res.returncode != 0:
        print("Compilation FAILED:")
        print(res.stderr)
        print(res.stdout)
        sys.exit(1)
        
    print("Compilation SUCCESS!")
    
    # 2. Launch server in background
    proc = subprocess.Popen([exe_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    
    # Wait for server to output SERVER_STARTED
    time.sleep(0.5)
    
    try:
        # Request 1: GET /
        print("Sending GET / ...")
        resp = urllib.request.urlopen("http://127.0.0.1:18088/")
        assert resp.status == 200
        html = resp.read().decode("utf-8")
        assert "Hello from KaniScript Server" in html
        print("  -> Success:", html)

        # Request 2: GET /api/status
        print("Sending GET /api/status ...")
        resp = urllib.request.urlopen("http://127.0.0.1:18088/api/status")
        assert resp.status == 200
        assert "application/json" in resp.headers.get("Content-Type", "")
        json_body = resp.read().decode("utf-8")
        assert '"status":"ok"' in json_body
        print("  -> Success:", json_body)

        # Request 3: GET /notfound (expect 404)
        print("Sending GET /notfound ...")
        try:
            urllib.request.urlopen("http://127.0.0.1:18088/notfound")
            assert False, "Should have returned 404"
        except urllib.error.HTTPError as e:
            assert e.code == 404
            err_body = e.read().decode("utf-8")
            assert "Not Found" in err_body
            print("  -> Success 404 handled:", err_body)

        proc.wait(timeout=3)
        print("=== ALL HTTP SERVER TESTS PASSED ===")
    finally:
        if proc.poll() is None:
            proc.kill()

if __name__ == "__main__":
    test_http_server()
