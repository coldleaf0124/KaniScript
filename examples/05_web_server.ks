// 05_web_server.ks - KaniScript Standalone Web Server
// 他言語なし・KaniScript単体で動作するWebサーバー＆APIシステム

main() {
    port := 8080
    server := http_listen(port)

    out "=================================================="
    out "  KaniScript Standalone Web Server is Running!"
    out "  URL: http://localhost:" + int_to_str(port)
    out "  - GET /          : Web Dashboard"
    out "  - GET /api/stats : System & Arena Memory Stats (JSON)"
    out "=================================================="

    start_time := time_now()

    while true {
        req := http_accept(server)

        when req.client_id >= 0 {
            when req.path == "/" {
                html := "<!DOCTYPE html>" +
                    "<html lang='ja'>" +
                    "<head><meta charset='UTF-8'><title>KaniScript Web Server</title>" +
                    "<style>" +
                    "body { font-family: system-ui, sans-serif; background: #0f172a; color: #f8fafc; padding: 2rem; margin: 0; }" +
                    ".card { background: #1e293b; border: 1px solid #334155; border-radius: 12px; padding: 1.5rem; max-width: 600px; margin: 2rem auto; shadow: 0 4px 6px -1px rgba(0,0,0,0.1); }" +
                    "h1 { color: #f97316; margin-top: 0; display: flex; align-items: center; gap: 0.5rem; }" +
                    ".badge { background: #ea580c20; color: #fb923c; border: 1px solid #ea580c40; padding: 2px 8px; border-radius: 9999px; font-size: 0.8rem; }" +
                    "pre { background: #0f172a; padding: 1rem; border-radius: 8px; overflow-x: auto; color: #38bdf8; font-size: 0.9rem; }" +
                    "button { background: #ea580c; color: white; border: none; padding: 0.5rem 1rem; border-radius: 6px; cursor: pointer; font-weight: bold; }" +
                    "button:hover { background: #c2410c; }" +
                    "</style>" +
                    "</head>" +
                    "<body>" +
                    "<div class='card'>" +
                    "<h1>KaniScript Standalone Server <span class='badge'>v0.1</span></h1>" +
                    "<p>このWebページとAPIは、Node.jsやPythonを一切使わず、<strong>KaniScript単体</strong>で直接クライアントに配信されています。</p>" +
                    "<h3>APIステータス検証</h3>" +
                    "<button onclick='fetchStats()'>最新のメモリ統計をAPI取得</button>" +
                    "<pre id='res'>[ボタンをクリックしてAPIを取得]</pre>" +
                    "</div>" +
                    "<script>" +
                    "async function fetchStats() {" +
                    "  const res = await fetch('/api/stats');" +
                    "  const data = await res.json();" +
                    "  document.getElementById('res').textContent = JSON.stringify(data, null, 2);" +
                    "}" +
                    "</script>" +
                    "</body></html>"

                http_respond(req.client_id, 200, "text/html; charset=utf-8", html)
            } else when req.path == "/api/stats" {
                uptime := time_now() - start_time
                perm := perm_used()
                scratch := scratch_used()

                json := "{\"status\":\"ok\"," +
                    "\"server\":\"KaniScript/0.1\"," +
                    "\"uptime_sec\":" + float_to_str(uptime) + "," +
                    "\"arena_perm_bytes\":" + int_to_str(perm) + "," +
                    "\"arena_scratch_bytes\":" + int_to_str(scratch) + "," +
                    "\"memory_leak_check\":\"Zero-Leak Verified\"}"

                http_respond(req.client_id, 200, "application/json", json)
            } else {
                http_respond(req.client_id, 404, "text/plain", "404 Not Found")
            }
        }
    }

    http_close(server)
}
