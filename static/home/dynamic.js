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

var page;

var Page = class {
	constructor() {
		page = this;
		this.loaded = true;

		on_ready(this, this.set_highlight_texts);
		on_load(this, this.set_navbar_effects);
		on_load(this, this.get_sample_stuff);
	}

	// @on_ready
	set_highlight_texts() {
		$("span[show-about]").each(function(index, element) {
			element.classList.add("highlight");
			element.innerHTML = "&nbsp;" + element.innerHTML + "&nbsp;";

			element.onmouseover = show_more_info_hover;
			element.onclick = show_more_info_click;
			$(element).mouseleave(show_more_info_leave);
		});
	}

	// @on_load
	set_navbar_effects() {
		var elem = document.getElementById("navigation-bar");
		var jElem = $("#navigation-bar");
		var jWindow = $(window);

		jElem.addClass("animated");
		jElem.addClass("slideOutUp");

		var distance = $("#after-navbar").offset().top;
		var didScroll = true;
		this.is_hidden = true;

		jWindow.scroll(function() {
			didScroll = true;
		});
		this.navbar_interval = setInterval(function() {
			if (didScroll) {
				didScroll = false;

				if (jWindow.scrollTop() >= distance) {
					if (page.is_hidden) {
						elem.classList.remove("slideOutUp");
						elem.classList.add("slideInDown");

						page.is_hidden = false;
					}
				} else {
					if (!page.is_hidden) {
						elem.classList.remove("slideInDown");
						elem.classList.add("slideOutUp");

						page.is_hidden = true;
					}
				}
			}
		}, 250);
	}

	abort(jqXHR) {
		if (!this.aborted) {
			this.aborted = true;
			this.aborted_msg = jqXHR.responseJSON.error;
			this.show_stuff();
		}
	}

	show_stuff() {
		if (this.aborted) {
			$("#announcements").html(this.get_announcement({
				author: 'Darky <span class="bot-tag">BOT</span>',
				color: 9807270,
				avatar: "avatars/596775737764085781/d6b1cc1e894e824366df5a254aed68a1.png",
				timestamp: new Date().getTime() / 1000,
				message: "Seems like someone dropped some coffee in our servers and they're " +
						"not working properly right now... You'd come back later to see if this " +
						'has been fixed! While you wait, you could ' +
						'<a href="https://discord.gg/quch83R" target="_blank">join our discord server</a> ' +
						'to join our community!',
				attachments: []
			}));
		} else {
			$("#announcements").html(this.big_announcement + this.small_announcement + this.get_announcement({
				author: 'Darky <span class="bot-tag">BOT</span>',
				color: 9807270,
				avatar: "avatars/596775737764085781/d6b1cc1e894e824366df5a254aed68a1.png",
				timestamp: new Date().getTime() / 1000,
				message: 'Are you interested in reading more about the server? ' +
						'You could <a href="#announcements/index">click this link</a> ' +
						'to read more announcements, or you could click on ' +
						'<a href="https://discord.gg/quch83R" target="_blank">this one</a> ' +
						'to join our community, talk with our members and be notified when there is any new!',
				attachments: []
			}, "no"));
			$("#members").html(this.members);
		}
	}

	get_announcement(message, small) {
		var txt = '<div class="announcement" data-aos="fade-up"> \
			<div> \
				<img src="https://cdn.discordapp.com/' + message.avatar + '?size=128" class="announcement-author-avatar big-round"> \
				<span class="announcement-author-name" style="color:#' + intToColor(message.color) + ';">' + message.author + '</span> \
				<span class="announcement-author-date">' + (new Date(message.timestamp * 1000)).toLocaleString() + '</span>' +
				(small == "no" ? "" : '<span class="announcement-author-date">|</span> \
				<span class="announcement-author-date">in #' + (small ? "small-" : "") + 'announcements</span>') + ' \
			</div> \
			<hr class="announcement-separator"> \
			<div class="announcement-content"> \
				' + message.message;

		for (var index = 0; index < message.attachments.length; index++) {
			txt += '<br><br><img src="' + message.attachments[index] + '" class="announcement-attachment">';
		}

		return txt + '</div></div>';
	}

	set_big_announcement(response) {
		if (!this.aborted) {
			this.big_announcement = this.get_announcement(response.messages[0], false);

			this.ready_stuff++;
			if (this.ready_stuff == 3) {
				this.show_stuff();
			}
		}
	}

	set_small_announcement(response) {
		if (!this.aborted) {
			this.small_announcement = this.get_announcement(response.messages[0], true);

			this.ready_stuff++;
			if (this.ready_stuff == 3) {
				this.show_stuff();
			}
		}
	}

	set_members(response) {
		if (!this.aborted) {
			var role_checks = [
				["Module Member", "https://cdn.discordapp.com/emojis/456198795768889344.png?size=32"],
				["Developer", "https://cdn.discordapp.com/emojis/468936022248390687.png?size=32"],
				["Artist", "https://cdn.discordapp.com/emojis/468937377981923339.png?size=32"],
				["Translator", "https://discordapp.com/assets/487af9f8669d2659ceb859f6dc7d2983.svg"],
				["Mapper", "https://cdn.discordapp.com/emojis/463508055577985024.png?size=32"],
				["Event Manager", "https://cdn.discordapp.com/emojis/559070151278854155.png?size=32"],
				["Shades Helper", "https://cdn.discordapp.com/emojis/542115872328646666.png?size=32"],
				["Funcorp", "https://cdn.discordapp.com/emojis/559069782469771264.png?size=32"],
				["Mathematician", "https://discordapp.com/assets/b43c5c7f3fd21d04273303bc0db9cc02.svg"],
				["Fashionista", "https://cdn.discordapp.com/emojis/468937918115741718.png?size=32"],
				["Writer", "https://discordapp.com/assets/a77e0fdf1c1dddb8de08f3b67a971bff.svg"],
			]

			this.members = '<h3 data-aos="zoom-in">These are some of our members</h3> \
							<h6 data-aos="zoom-in">Do you still doubt about joining our community?</h6> \
							<small data-aos="zoom-in">You could check the complete list <a href="#members/index">clicking here</a></small><br>';

			for (var member in response) {
				if (!isNaN(member) && response[member] != null) {
					member = response[member];

					this.members += '<div style="display:inline-block;padding-left:1rem;padding-right:1rem;"> \
										<a class="member-panel" href="#members/' + member.id + '"> \
											<div class="member-panel" data-aos="zoom-out-up"> \
												<div style="position:absolute;top:.5rem;text-align:center;width:100%;">'

					if (member.discord.is_mod) {
						this.members += '<img src="https://discordapp.com/assets/ef015a42cac1a2009f9eecf8915d9e35.svg" \
										style="width:1.25rem;height:auto;" alt="Moderator">';
					}
					for (var index = 0; index < role_checks.length; index++) {
						var role = role_checks[index];
						for (var _index = 0; _index < member.discord.roles.length; _index++) {
							if (role[0] == member.discord.roles[_index][0]) {
								this.members += '<img src="' + role[1] + '"" style="width:1.25rem;height:auto;" alt="' + role[0] + '">';
								break;
							}
						}
					}

					this.members += '</div> \
									<img src="https://cdn.discordapp.com/' + member.discord.avatar + '?size=128" class="member-avatar-percentage big-round"> \
									<div style="width:100%;"> \
										<span class="member-name-2" style="color:#' + intToColor(member.discord.color) + ';">' + member.discord.name + '</span> \
									</div> \
								</div> \
							</a> \
						</div>';
				}
			}

			this.ready_stuff++;
			if (this.ready_stuff == 3) {
				this.show_stuff();
			}
		}
	}

	// @on_load
	get_sample_stuff() {
		this.big_announcement = "";
		this.small_announcement = "";
		this.members = "";
		this.aborted = false;
		this.aborted_msg = "";
		this.ready_stuff = 0;

		$.ajax({
			url: "/api/announcements/big/0",
			method: "GET"
		}).done(function(response) {page.set_big_announcement(response)}).fail(function(jqXHR) {page.abort(jqXHR)});
		$.ajax({
			url: "/api/announcements/small/0",
			method: "GET"
		}).done(function(response) {page.set_small_announcement(response)}).fail(function(jqXHR) {page.abort(jqXHR)});
		$.ajax({
			url: "/api/members/:5/",
			method: "GET"
		}).done(function(response) {page.set_members(response)}).fail(function(jqXHR) {page.abort(jqXHR)});
	}

	unload() {
		this.loaded = false;

		if (this.navbar_interval !== undefined) {
			clearInterval(this.navbar_interval);

			if (this.is_hidden) {
				var elem = document.getElementById("navigation-bar");
				elem.classList.remove("hidden");
				elem.classList.remove("slideOutUp");
				elem.classList.add("slideInDown");
			}
		}
	}
}