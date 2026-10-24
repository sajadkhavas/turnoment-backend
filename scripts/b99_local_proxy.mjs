// Same-origin local-only test ingress; no frontend/backend contract changes.
import http from "node:http";

const host = "127.0.0.1";
const port = Number(process.env.B99_PROXY_PORT || "4173");
const frontendPort = Number(process.env.B99_FRONTEND_PORT || "4174");
const apiPort = Number(process.env.B99_BACKEND_PORT || "8000");

const server = http.createServer((req, res) => {
  const backend = /^\/(api\/v1\/|health\/)/.test(req.url || "");
  const targetPort = backend ? apiPort : frontendPort;
  const upstream = http.request(
    {
      host,
      port: targetPort,
      method: req.method,
      path: req.url,
      headers: { ...req.headers, host: req.headers.host },
    },
    (response) => {
      res.writeHead(response.statusCode || 502, response.headers);
      response.pipe(res);
    },
  );
  upstream.on("error", (error) => {
    console.error("B99 proxy upstream failed:", error.message);
    if (!res.headersSent) res.writeHead(502);
    res.end("B99 local proxy unavailable");
  });
  req.pipe(upstream);
});
server.listen(port, host, () => {
  console.log("B99 local same-origin proxy ready on " + host + ":" + port);
});
