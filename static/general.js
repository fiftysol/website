if (!String.prototype.format) {
	String.prototype.format = function() {
		var args = arguments;
		return this.replace(/{(\d+)}/g, function(match, number) {
			return typeof args[number] != 'undefined'
				? args[number]
				: match
			;
		});
	};
}

var after_translated_queue = [];
var after_ready_queue = [];
var translation_names = {};
var after_load_queue = [];
var get_translation_names = false;
var is_translated = false;
var is_loaded = false;
var is_ready = false;
var translate = [];
var translated = {};
var already_translated = 0;

translate.push([null, "something_happened"])
translate.push([null, "something_happened_html"])
function ajax_fail(jqXHR) {
	if (translated[null] !== undefined) {
		popup({
			title: translated[null]["something_happened"],
			type: "error",
			html: translated[null]["something_happened_html"].format(jqXHR.responseJSON.error)
		})
	} else {
		popup({
			title: "Something happened...",
			type: "error",
			html: "An internal error happened:<br><strong>" + jqXHR.responseJSON.error + "</strong>"
		})
	}
}

function after_load() {
	if (!is_loaded) {
		after_load_queue.push(arguments);
	} else {
		let args = [];
		for (var index = 1; index < arguments.length; index++)
			args.push(arguments[index]);

		arguments[0].apply(null, args);
	}
}

function after_ready() {
	if (!is_ready) {
		after_ready_queue.push(arguments);
	} else {
		let args = [];
		for (var index = 1; index < arguments.length; index++)
			args.push(arguments[index]);

		arguments[0].apply(null, args);
	}
}

function after_translated() {
	if (!is_translated) {
		after_translated_queue.push(arguments);
	} else {
		let args = [];
		for (var index = 1; index < arguments.length; index++)
			args.push(arguments[index]);

		arguments[0].apply(null, args);
	}
}

function translations_ajax(lang, when) {
	return function(response) {
		if (response.success) {
			translated[lang] = response.fields;
		} else {
			popup({
				title: "Something happened...",
				type: "error",
				html: "An internal error happened when fetching the translation texts:<br><strong>" + response.error + "</strong>"
			});
		}

		already_translated++;
		if (when == already_translated) {
			run_translated();
		}
	};
}

function request_translations() {
	var requests = {};
	var total = get_translation_names ? 1 : 0;
	for (var index = 0; index < translate.length; index++) {
		var field = translate[index];

		if (requests[field[0]] === undefined) {
			total++;
			requests[field[0]] = field[1];
		} else {
			requests[field[0]] += "/" + field[1];
		}
	}
	translate = [];

	for (var lang in requests) {
		$.ajax({
			url: "/api/translate/@website/" + ((lang == "null" || lang == null) ? "auto" : lang) + "/" + requests[lang],
			method: "GET"
		}).done(translations_ajax(lang, total)).fail(ajax_fail);
	}
	if (get_translation_names) {
		$.ajax({
			url: "/api/translate/@website/",
			method: "GET"
		}).done(function(response) {
			if (response.success) {
				translation_names = response.list;
			} else {
				popup({
					title: "Something happened...",
					type: "error",
					html: "An internal error happened when fetching the translation list:<br><strong>" + response.error + "</strong>"
				});
			}

			already_translated++;
			if (total == already_translated) {
				run_translated();
			}
		}).fail(ajax_fail);
	}
}

translate.push([null, "select_lang"]);
translate.push([null, "need_select_lang"]);
translate.push([null, "lang_set"]);
translate.push([null, "lang_set_html"]);
translate.push([null, "cant_set_lang"]);
get_translation_names = true;
function language_selector() {
	popup({
		input: "select",
		inputOptions: translation_names,
		inputPlaceholder: translated[null]["select_lang"],
		inputValidator: (value) => {
			return new Promise((resolve) => {
				if (value == "") {
					resolve(translated[null]["need_select_lang"]);
				} else {
					$.ajax({
						url: "/api/translate/",
						method: "PUT",
						data: JSON.stringify({language: value})
					}).done(function(response) {
						if (response.success) {
							Swal.fire({
								title: translated[null]["lang_set"],
								type: "success",
								html: translated[null]["lang_set_html"].format(translation_names[value])
							}).then(function() {
								location.reload(true);
							});
						} else {
							Swal.fire({
								title: translated[null]["cant_set_lang"],
								type: "error",
								text: response.error
							}).then(resolve);
						}
					}).fail(ajax_fail);
				}
			})
		}
	});
}

function _popup(args) {
	Swal.fire.apply(Swal, args);
}

function popup() {
	var args = [];
	for (var index = 0; index < arguments.length; index++) {
		args.push(arguments[index]);
	}

	after_load(_popup, args);
}

function show_loading() {
	$("body").addClass("hidden-overflow");
	$("#loading").append('<div class="lds-ellipsis"><div></div><div></div><div></div><div></div></div>');
}

function run_translated() {
	is_translated = true;
	for (var index = 0; index < after_translated_queue.length; index++) {
		let call = after_translated_queue[index],
			func = call[0],
			args = [];

		for (var subindex = 1; subindex < call.length; subindex++)
			args.push(call[subindex]);

		func.apply(null, args);
	}
}

function intToColor(color) {
    var hex = color.toString(16);
    while (hex.length < 6) {
        hex = "0" + hex;
    }
    return hex;
}

window.onload = function() {
	setTimeout(function() {
		$("body").removeClass().addClass("background");

		is_loaded = true;
		for (var index = 0; index < after_load_queue.length; index++) {
			let call = after_load_queue[index],
				func = call[0],
				args = [];

			for (var subindex = 1; subindex < call.length; subindex++)
				args.push(call[subindex]);

			func.apply(null, args);
		}

		$("#loading").remove();
	}, 250);
}

$(document).ready(function() {
	is_ready = true;
	for (var index = 0; index < after_ready_queue.length; index++) {
		let call = after_ready_queue[index],
			func = call[0],
			args = [];

		for (var subindex = 1; subindex < call.length; subindex++)
			args.push(call[subindex]);

		func.apply(null, args);
	}
});

show_loading();
after_load(request_translations);
after_load(function() {
	$("[animate]").each(function(_, element) {
		if (element.hasAttribute("hide") && element.getAttribute("hide") == "true")
			element.classList.remove("hidden");
			element.classList.add("visible");
		element.classList.add("animated");
		element.classList.add(element.getAttribute("animate"));
	})
});