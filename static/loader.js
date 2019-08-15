var loader;

class Loader {
	constructor() {
		loader = this;

		this.loc = undefined;
		this.anchor = undefined;
		this.loaded = true;
		this.initalized = false;
		this.popups = [];
		this.popup_loaded = false;
		this.can_stop = true;
		this.scheduled_error_page = false;
		this.scheduled_error_page_status = 0;
		this.translated = false;
		this.translation = {};

		$(window).bind("hashchange", function() {
			loader.on_hash_change.apply(loader, []);
		});
		if (window.location.pathname != "/" && (window.location.hash == "" || window.location.hash == "#")) {
			window.location.hash = "#" + window.location.pathname.slice(1);
		}
		this.on_hash_change();

		on_load(this, this.show_popups);
		on_load(this, this.move_to_anchor);
		on_load(this, this.init_animations);
		on_load(this, this.add_fixed_navbar);
		on_pre_load(this, this.run_error_page_schedule);
	}

	// @on_pre_load
	run_error_page_schedule() {
		if (this.scheduled_error_page) {
			this.schedule_error_page(this.scheduled_error_page_status);
			return true;
		}
	}

	// @on_load
	show_popups() {
		for (var index = 0; index < this.popups.length; index++) {
			Swal.fire.apply(Swal, this.popups[index]);
		}
		this.popups = [];
		this.popup_loaded = true;
	}

	// @on_load
	move_to_anchor() {
		if (this.anchor !== undefined) {
			var offset = $("#" + this.anchor).offset();

			if (offset !== undefined) {
				$(document).scrollTop(offset.top);
			}
		}
	}

	// @on_load
	init_animations() {
		if (this.initalized) {
			var elements = document.getElementsByClassName("aos-animate");
			for (var index = 0; index < elements.length; index++) {
				elements[index].classList.remove("aos-animate");
			}
			AOS.refresh();
		}
		AOS.init({
			once: true
		});
		this.initalized = true;
	}

	// @on_load
	add_fixed_navbar() {
		if (!this.initialized) {
			$("#navigation-bar").addClass("fixed-top");
		}
	}

	popup() {
		if (!this.popup_loaded) {
			this.popups.push(arguments);
		} else {
			Swal.fire.apply(Swal, arguments);
		}
	}

	unload_page() {
		if (this.page !== undefined) {
			this.page.unload();
			this.page = undefined;
		}
	}

	ajax_fail(jqXHR) {
		if (this.translated && this.translation.something_happened !== undefined && this.translation.something_happened_html !== undefined) {
			var can_translate = jqXHR.responseJSON.error.startsWith("%") && jqXHR.responseJSON.error.endsWith("%");
			if (can_translate) {
				var field = jqXHR.responseJSON.error.slice(1, -1);
			}
			this.popup({
				title: this.translation.something_happened,
				type: "error",
				html: this.translation.something_happened_html.format(
					can_translate ?
					(this.translation[field] !== undefined ? this.translation[field] : "%" + field + "%") :
					jqXHR.responseJSON.error
				)
			});
		} else {
			this.popup({
				title: "Something happened...",
				type: "error",
				html: "An internal error happened:<br><strong>" + jqXHR.responseJSON.error + "</strong>"
			});
		}
	}

	show_loading() {
		$(document).scrollTop(0);
		$("#updatable-content").addClass("hidden");
		$("#whole-page-loading").removeClass()
	}

	real_stop_loading() {
		this.can_stop = true;
		var evt = run_event("pre_load");
		for (var index = 0; index < evt.length; index++) {
			if (evt[index] === true) {
				return;
			}
		}
		$("#updatable-content").removeClass();
		$("#whole-page-loading").addClass("hidden")
		run_event("load");
		loader.move_to_anchor();
	}

	stop_loading() {
		loader.loaded_elements++;
		if (loader.loaded_scripts && loader.loaded_elements == loader.load_limit) {
			loader.real_stop_loading();
		}
	}

	load_scripts(scripts) {
		$.getScript(scripts.pop()).done(function() {
			if (scripts.length == 0) {
				loader.page = new Page();
				run_event("ready");

				if (loader.loaded_elements == loader.load_limit) {
					loader.real_stop_loading();
				}
				loader.loaded_scripts = true;
				return;
			}

			loader.load_scripts(scripts);
		});
	}

	schedule_error_page(status) {
		if (!loader.can_stop) {
			loader.scheduled_error_page = true;
			loader.scheduled_error_page_status = status;
			return;
		}

		loader.scheduled_error_page = false;
		this.show_loading();
		this.unload_page();
		$.ajax({
			url: "/api/dynamic/error",
			method: "GET"
		}).done(function(response, textStatus, jqXHR) {
			jqXHR.status = status;
			loader.render_page(response, textStatus, jqXHR);
		}).fail(function(jqXHR, textStatus) {
			// Doesn't modify jqXHR status here since a new error happened!
			console.log("Scheduled error page threw an error when requesting the error page to the server.");
			loader.render_page(jqXHR.responseJSON, textStatus, jqXHR);
		});
	}

	render_page(page, textStatus, jqXHR) {
		loader.can_stop = false;
		loader.page_response = jqXHR.status;
		loader.loaded_scripts = false;
		loader.loaded_elements = 0;
		loader.load_limit = 0;

		$("title").html(page.title);
		$("#updatable-content").html(page.content).find("img").each(function(index, element) {
			loader.load_limit++;
			element.onload = loader.stop_loading;
		});

		if (page.script !== undefined) {
			var scripts = [];
			if (typeof page.script == "string") {
				scripts = [page.script];
			} else {
				scripts = page.script;
			}

			loader.load_scripts(scripts.reverse());
		} else {
			run_event("ready");

			if (loader.loaded_elements == loader.load_limit) {
				loader.real_stop_loading();
			}
			loader.loaded_scripts = true;
		}
	}

	load_page() {
		this.show_loading();
		this.unload_page();
		$.ajax({
			url: "/api/dynamic/" + this.loc,
			method: "GET"
		}).done(this.render_page).fail(function(jqXHR, textStatus) {
			loader.render_page(jqXHR.responseJSON, textStatus, jqXHR);
		});
	}

	on_hash_change() {
		var loc = this.loc;
		var hash = location.hash == "" ? "#home/index" : location.hash;
		var spl = hash.slice(1).split("!");
		this.loc = spl[0];
		this.anchor = spl[1];

		if (loc != this.loc) {
			this.load_page();
		} else {
			this.move_to_anchor();
		}
	}
}