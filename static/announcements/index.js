var selected_channel = "";
var selected_page = -1;

function add_listeners(element) {
	var activation = element.getAttribute("shows");
	element.onmouseover = function() {
		document.getElementById(activation).classList.add("inline");
		document.getElementById(activation).classList.remove("hidden");
	};
	element.onmouseout = function() {
		document.getElementById(activation).classList.add("hidden");
		document.getElementById(activation).classList.remove("inline");
	};
}

function parse_ping_elements() {
	var elements = document.getElementsByClassName("ping-channel");
	for (var index = 0; index < elements.length; index++) {
		add_listeners(elements[index]);
	}
}

translate.push([null, "something_happened"])
translate.push([null, "something_happened_html"])
function received_announcements(response) {
	$("#announcements-loader").addClass("hidden").empty();

	if (response.success) {
		var elem = $("#announcements-content");
		for (var index = 0; index < response.messages.length; index++) {
			var message = response.messages[index];
			var txt = '<div class="announcement"> \
				<div> \
					<img src="https://cdn.discordapp.com/' + message.avatar + '?size=128" class="announcement-author-avatar big-round"> \
					<span class="announcement-author-name" style="color:#' + intToColor(message.color) + ';">' + message.author + '</span> \
					<span class="announcement-author-date">' + (new Date(message.timestamp * 1000)).toLocaleString() + '</span> \
				</div> \
				<hr class="announcement-separator"> \
				<div class="announcement-content"> \
					' + message.message;

			for (var _index = 0; _index < message.attachments.length; _index++) {
				txt += '<br><br><img src="' + message.attachments[_index] + '" class="announcement-attachment">';
			}

			elem.append(txt + '</div></div>');
		}

		elem.append('<div class="announcements-pagination">' + $("#announcements-pagination").html() + '</div>');
		parse_ping_elements();
	} else {
		popup({
			title: translated[null]["something_happened"],
			type: "error",
			html: translated[null]["something_happened_html"].format(response.error)
		})
	}
}
function announcements_fail() {
	$("#announcements-loader").addClass("hidden").empty();
	return ajax_fail.apply(null, arguments);
}

function load_announcements(where, page) {
	if (where == selected_channel && page == selected_page) {
		return;
	}
	selected_channel = where;
	selected_page = page;
	$("#announcements-loader").removeClass().append('<div class="lds-ellipsis"><div></div><div></div><div></div><div></div></div>');
	$("#announcements-content").empty();

	$.ajax({
		url: "/api/announcements/" + where + "/" + page,
		method: "GET"
	}).done(received_announcements).fail(announcements_fail);
}

function change_channel(channel) {
	$("#channel-" + selected_channel).removeClass().addClass("page-item");
	$("#channel-" + channel).addClass("active");
	load_announcements(channel, selected_page);
	return false;
}

function change_page(page) {
	$("#page-" + selected_page).removeClass().addClass("page-item");
	$("#page-" + page).addClass("active");
	load_announcements(selected_channel, page);
	return false;
}

if (!dont_load_announcements_on_start) {
	after_translated(load_announcements, "big", 0);
}