var focused_more_info_element = "more-info-text";
var change_on_leave = true;

function change_more_info_element(elem_id) {
	$("#" + focused_more_info_element).addClass("hidden");

	focused_more_info_element = elem_id;
	document.getElementById(elem_id).classList.remove("hidden");
}

function show_more_info_hover() {
	change_on_leave = true;
	change_more_info_element(this.getAttribute("show-about"));

	return false;
}

function show_more_info_click() {
	change_on_leave = false;
	change_more_info_element(this.getAttribute("show-about"));

	return false;
}

function show_more_info_leave() {
	if (change_on_leave) {
		change_more_info_element("more-info-text");
	}

	return false;
}

after_ready(function() {
	$("span[show-about]").each(function(index, element) {
		element.classList.add("highlight");
		element.innerHTML = "&nbsp;" + element.innerHTML + "&nbsp;";

		element.onmouseover = show_more_info_hover;
		element.onclick = show_more_info_click;
		$(element).mouseleave(show_more_info_leave);
	});
});

after_load(function() {
	//window.scrollTo(0, 0);

	var elem = document.getElementById("navigation-bar");
	var jElem = $("#navigation-bar");
	var jWindow = $(window);

	jElem.addClass("hidden");
	jElem.addClass("animated");

	var distance = $("#after-navbar").offset().top;
	var didScroll = true;
	var is_hidden = true;

	jWindow.scroll(function() {
		didScroll = true;
	});
	setInterval(function() {
		if (didScroll) {
			didScroll = false;

			if (jWindow.scrollTop() >= distance) {
				if (is_hidden) {
					elem.classList.remove("hidden");
					elem.classList.remove("slideOutUp");
					elem.classList.add("slideInDown");

					is_hidden = false;
				}
			} else {
				if (!is_hidden) {
					elem.classList.remove("slideInDown");
					elem.classList.add("slideOutUp");

					is_hidden = true;
				}
			}
		}
	}, 250);
});