var page;

var Page = class {
	constructor() {
		page = this;
		this.loaded = true;

		var texts = {
			"400": "Bad Request",
			"401": "Unauthorized",
			"403": "Forbidden",
			"404": "Not Found",
			"405": "Method Not Allowed",
			"406": "Not Acceptable",
			"407": "Proxy Authentication Required",
			"408": "Request Timeout",
			"409": "Conflict",
			"410": "Gone",
			"411": "Length Required",
			"412": "Precondition Failed",
			"415": "Unsupported Media Type",
			"429": "Too Many Requests",

			"500": "Internal Server Error",
			"501": "Not Implemented",
			"502": "Bad Gateway",
			"503": "Service Unavailable",
			"504": "Gateway Timeout",
			"505": "HTTP Version Not Supported",
			"507": "Insufficient Storage",
			"508": "Loop Detected",
			"511": "Network Authentication Required"
		};

		var status = loader.page_response.toString();
		var elem = $("#updatable-content");
		elem.html(
			elem.html()
			.replace("{status_code}", status)
			.replace("{status_text}", texts[status] !== undefined ? texts[status] : "Unknown Error")
		);
	}

	unload() {
		this.loaded = false;
	}
}