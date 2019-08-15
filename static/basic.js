if (!String.prototype.format) {
	String.prototype.format = function() {
		var args = arguments;
		return this.replace(/{(\d+)}/g, function(match, number) {
			return args[number] !== undefined ? args[number] : match;
		});
	};
}

var events = {};

function intToColor(color) {
	var hex = color.toString(16);
	while (hex.length < 6) {
		hex = "0" + hex;
	}
	return hex;
}

function on_event(evt, obj, fnc) {
	if (events[evt] === undefined) {
		events[evt] = [];
	}
	events[evt].push([obj, fnc]);
	return fnc;
}
function run_event(evt) {
	if (events[evt] === undefined) {return;}
	var copy = [];
	var result = [];

	for (var index = 0; index < events[evt].length; index++) {
		var fnc = events[evt][index];
		if (fnc[0] != null) {
			if (!fnc[0].loaded) {
				continue;
			}
		}

		result.push(fnc[1].apply(fnc[0], []));
		copy.push(fnc);
	}

	events[evt] = copy;
	return result;
}
function on_ready(obj, fnc) {return on_event("ready", obj, fnc);}
function on_load(obj, fnc) {return on_event("load", obj, fnc);}
function on_pre_load(obj, fnc) {return on_event("pre_load", obj, fnc);}

var loader;
$.ajax({
	"async": true,
	type: "GET",
	url: "/static/loader.js",
	data: null,
	dataType: "script",
	success: function() {
		loader = new Loader();
	}
});