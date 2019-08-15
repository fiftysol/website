var page;

var Page = class {
	constructor() {
		page = this;
		this.loaded = true;

		this.channel = "big";
		this.page = 0;

		on_load(this, this.load_announcements);
	}

	show_loading() {
		$("#announcements-content").addClass("hidden");
		$("#announcements-loader").removeClass();
	}

	stop_loading() {
		$("#announcements-loader").addClass("hidden");
		$("#announcements-content").removeClass();
	}

	add_listeners(element) {
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

	parse_ping_elements() {
		var elements = document.getElementsByClassName("ping-channel");
		for (var index = 0; index < elements.length; index++) {
			this.add_listeners(elements[index]);
		}
	}

	get_announcement(message) {
		var txt = '<div class="announcement"> \
			<div> \
				<img src="https://cdn.discordapp.com/' + message.avatar + '?size=128" class="announcement-author-avatar big-round"> \
				<span class="announcement-author-name" style="color:#' + intToColor(message.color) + ';">' + message.author + '</span> \
				<span class="announcement-author-date">' + (new Date(message.timestamp * 1000)).toLocaleString() + '</span> \
			</div> \
			<hr class="announcement-separator"> \
			<div class="announcement-content"> \
				' + message.message;

		for (var index = 0; index < message.attachments.length; index++) {
			txt += '<br><br><img src="' + message.attachments[index] + '" class="announcement-attachment">';
		}

		return txt + '</div></div>';
	}

	// @on_load
	load_announcements() {
		this.show_loading();

		$.ajax({
			url: "/api/announcements/" + this.channel + "/" + this.page,
			method: "GET"
		}).done(function(response) {
			var text = "";
			for (var index = 0; index < response.messages.length; index++) {
				text += page.get_announcement(response.messages[index]);
			}

			text += '<div class="announcements-pagination">' + $("#announcements-pagination").html() + '</div>';
			page.stop_loading();
			$("#announcements-content").html(text);
			page.parse_ping_elements();
		}).fail(function(jqXHR) {
			page.stop_loading();
			loader.ajax_fail(jqXHR);
		});
	}

	unload() {
		this.loaded = false;
	}
}

function change_channel(channel) {
	$("#channel-" + page.channel).removeClass().addClass("page-item");
	$("#channel-" + channel).addClass("active");
	page.channel = channel;
	page.load_announcements();
	return false;
}
function change_page(_page) {
	$("#page-" + page.page).removeClass().addClass("page-item");
	$("#page-" + _page).addClass("active");
	page.page = _page;
	page.load_announcements();
	return false;
}