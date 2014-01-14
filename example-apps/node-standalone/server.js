var http = require("http");

http.createServer(function(request, response) {
	response.writeHead(200, {"Content-Type": "text/plain"});
	response.end("Hello");
}).listen(parseInt(process.argv[2], 10), "127.0.0.1");
