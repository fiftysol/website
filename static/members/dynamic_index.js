var page;

var Page = class {
	constructor() {
		page = this;
		this.loaded = true;

		on_ready(this, this.load_members);
	}

	// @on_ready
	load_members() {
		loader.load_limit++; // Doesn't show anything until everything has loaded.

		$.ajax({
			url: "/api/members/:all/",
			method: "GET"
		}).done(function(response) {
			var quantity = 0;
			var text = "";
			for (var id in response) {
				if (!isNaN(id)) {
					var member = response[id];
					quantity++;
					text += '<div class="avatar-container"><a style="text-decoration:none;" href="#members/' + id + '"> \
								<img src="https://cdn.discordapp.com/' + member.discord.avatar + '?size=128" class="member-avatar big-round" data-aos="zoom-out-up"> \
							</a></div>';
				}
			}

			$("#members-content").html(
				'<h3>These are many of our members</h3> \
				<h6>We currently show <strong>' + quantity + '</strong> of our members!</h6> \
				<small>Don\'t you appear here? Edit a field in your profile!</small><br>' + text
			).ready(loader.stop_loading).find("img").each(function(index, element) {
				loader.load_limit++;
				element.onload = loader.stop_loading;
			});
		}).fail(function(jqXHR) {
			loader.schedule_error_page(jqXHR.status);
			loader.stop_loading();
		});
	}

	unload() {
		this.loaded = false;
	}
}