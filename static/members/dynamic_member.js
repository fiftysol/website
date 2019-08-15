var page;

var Page = class {
	constructor() {
		page = this;
		this.loaded = true;

		this.roles = {
			"Module Member": {
				adapt_color: true,
				storage: "1",
				fields: [
					{name: "Member since", type: "normal", stored: "since"},
					{name: "Hosted modules", type: "normal", stored: "hosting"}
				]
			},
			"Developer": {
				adapt_color: true,
				storage: "2",
				fields: [
					{name: "Modules", type: "normal", stored: "modules"},
					{name: "GitHub", type: "link", stored: "github", prefix: "https://github.com/", suffix: "/"}
				]
			},
			"Artist": {
				adapt_color: true,
				storage: "3",
				fields: [
					{name: "DeviantArt", type: "link", stored: "deviantart", prefix: "https://www.deviantart.com/", suffix: "/"}
				]
			},
			"Translator": {
				adapt_color: true,
				storage: "4",
				fields: [
					{name: "Modules translated", type: "normal", stored: "trad"}
				]
			},
			"Mapper": {
				adapt_color: true,
				storage: "5",
				fields: [
					{name: "HighPerm maps", type: "normal", stored: "perms"}
				]
			},
			"Event Manager": {
				adapt_color: true,
				storage: "6",
				fields: [
					{name: "Events created", type: "normal", stored: "evt"},
				]
			},
			"Writer": {
				adapt_color: true,
				storage: "11",
				fields: [
					{name: "Wattpad", type: "link", stored: "github", prefix: "https://www.wattpad.com/user/", suffix: "/"}
				]
			},
			"@everyone": {
				adapt_color: false,
				storage: null,
				name: "Member",
				fields: [
					{name: "TFM nickname", type: "normal", stored: "nickname"},
					{name: "Birthday", type: "normal", stored: "bday"},
					{name: "Instagram", type: "link", stored: "insta", prefix: "https://instagram.com/", suffix: "/"}
				]
			}
		}

		on_ready(this, this.when_ready);
	}

	// @on_ready
	when_ready() {
		loader.load_limit++; // Doesn't show anything until everything has loaded.
		var user = loader.loc.match(/(?:@|\/)(\d+|me)/);
		if (user[1] !== undefined) {
			user = user[1].toLowerCase();
		} else {
			loader.schedule_error_page(400);
			loader.stop_loading();
			return;
		}

		$.ajax({
			url: "/api/members/@" + user,
			method: "GET"
		}).done(function(response) {
			var is_me = false;

			if (user == "me") {
				is_me = true;
				user = response.id;
			}
			var member = response[user];

			if (member == null || member == undefined) {
				if (is_me) {
					loader.popup({
						title: "Member not found",
						type: "error",
						html: "You must join our server first!"
					})
				} else {
					loader.popup({
						title: "Member not found",
						type: "error",
						html: "The given member was not found! Are you this member? Edit a field in your profile first!"
					});
				}
				return;
			}

			var html = '<div class="member">';
			var roles = [];
			for (var index = member.discord.roles.length - 1; index > -1; index--) {
				var role = member.discord.roles[index];
				if (role[0] == "@everyone") {continue;}

				if (page.roles[role[0]]) {
					roles.push('<span class="member-name" style="color:#' + intToColor(role[1]) + ';">' + role[0] + '</span>');
				}
			}
			html += roles.join('<span class="member-name">|</span>');
			html += '<br><br> \
					<img src="https://cdn.discordapp.com/' + member.discord.avatar + '?size=128" class="member-avatar-small big-round"> \
					<div style="display:inline-block;text-align:left;padding-left:.3rem;margin-left:.3rem;"> \
						<span class="member-name" style="margin-left:0;color:#' + intToColor(member.discord.color) + ';">' + member.discord.name + '</span>';
			if (member.status) {
				html += '<br><span class="ping">“' + member.status + '”</span>';
			}
			if (member.gender === 0) {
				html += '<br><span class="ping" style="color:rgb(45, 170, 255);background-color:rgba(45, 170, 255, .1)">Male</span>';
			} else if (member.gender === 1) {
				html += '<br><span class="ping" style="color:rgb(255, 105, 180);background-color:rgba(255, 105, 180|, .1)">Female</span>';
			}
			html += '</div><div class="outer-fields-container">';

			for (var index = member.discord.roles.length - 1; index > -1; index--) {
				var role = member.discord.roles[index];
				var role_name = role[0];
				var role_color = role[1];

				if (page.roles[role_name]) {
					var storage;
					if (page.roles[role_name].storage) {
						storage = member[page.roles[role_name].storage];
					} else {
						storage = member;
					}

					if (storage) {
						var text = "";
						var fields = page.roles[role_name].fields;

						for (var _index = 0; _index < fields.length; _index++) {
							var field = fields[_index];
							var value = storage[field.stored];

							if (value) {
								text += '<span class="field-title">' + field.name + ':</span> <code class="inline">';

								if (field.type == "link") {
									text += '<a href="' + field.prefix + value + field.suffix + '" target="_blank">' + value + '</a>';
								} else if (field.type == "normal") {
									text += value;
								}

								text += '</code><br>';
							}
						}

						if (text) {
							html += '<div class="fields-container"><span><span class="member-name"';
							if (page.roles[role_name].adapt_color) {
								html += ' style="color:#' + intToColor(role_color) + '"';
							}
							html += '>' + (page.roles[role_name].name ? page.roles[role_name].name : role_name) + '</span> fields</span>' + text + '</div>';
						}
					}
				}
			}

			$("#members-content").html(html + '</div></div>').ready(loader.stop_loading);
		}).fail(function(jqXHR) {
			if (user == "me" && jqXHR.status == 403) {
				loader.popup({
					title: "Member not found",
					type: "error",
					html: "You must log in first!"
				});
				return;
			}
			loader.schedule_error_page(jqXHR.status);
			loader.stop_loading();
		});
	}

	unload() {
		this.loaded = false;
	}
}