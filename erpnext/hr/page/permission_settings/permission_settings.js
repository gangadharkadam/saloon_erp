frappe.pages['permission-settings'].on_page_load = function(wrapper) {
	var page = frappe.ui.make_app_page({
		parent: wrapper,
		title: __('Permission Settings'),
		icon: "icon-lock",
		single_column: true
	});

	frappe.breadcrumbs.add("Setup");

	$("<div class='perm-engine' style='min-height: 200px; padding: 15px;'></div>").appendTo(page.main);
	wrapper.permission_engine = new frappe.PermissionEngine(wrapper);

}

frappe.pages['permission-settings'].refresh = function(wrapper) {
	wrapper.permission_engine.set_from_route();
}

frappe.PermissionEngine = Class.extend({
	init: function(wrapper) {
		this.wrapper = wrapper;
		this.body = $(this.wrapper).find(".perm-engine");
		this.make();
		this.refresh();
		this.add_check_events();
	},
	make: function() {
		var me = this;

		me.make_reset_button();
		return frappe.call({
			module:"erpnext.hr",
			page:"permission_settings",
			method: "users",
			callback: function(r) {
				me.options = r.message;
				me.setup_page();
			}
		});

	},
	setup_page: function() {
		var me = this;
		this.role_select
			= this.wrapper.page.add_select(__("Users"),
				[__("Select User")+"..."].concat(this.options.users))
				.change(function() {
					me.refresh();
				});
		this.set_from_route();
	},
	set_from_route: function() {
		var me = this;
		this.refresh();
	},
	reset_std_permissions: function(data) {
		var me = this;
		var d = frappe.confirm(__("Reset Permissions for {0}?", [me.get_doctype()]), function() {
			return frappe.call({
				module:"frappe.core",
				page:"permission_manager",
				method:"reset",
				args: {
					doctype: me.get_doctype(),
				},
				callback: function() { me.refresh(); }
			});
		});

		// show standard permissions
		var $d = $(d.wrapper).find(".frappe-confirm-message").append("<hr><h4>Standard Permissions:</h4><br>");
		var $wrapper = $("<p></p>").appendTo($d);
		$.each(data.message, function(i, d) {
			d.rights = [];
			$.each(me.rights, function(i, r) {
				if(d[r]===1) {
					d.rights.push(__(toTitle(r.replace("_", " "))));
				}
			});
			d.rights = d.rights.join(", ");
			$wrapper.append(repl('<div class="row">\
				<div class="col-xs-5"><b>%(role)s</b>, Level %(permlevel)s</div>\
				<div class="col-xs-7">%(rights)s</div>\
			</div><br>', d));
		});

	},
	get_doctype: function() {
		var doctype = this.doctype_select.val();
		return this.doctype_select.get(0).selectedIndex==0 ? null : doctype;
	},
	get_role: function() {
		var role = this.role_select.val();
		return this.role_select.get(0).selectedIndex==0 ? null : role;
	},
	refresh: function() {
		var me = this;
		if(!me.doctype_select) {
			this.body.html("<p class='text-muted'>" + __("Loading") + "...</div>");
			return;
		}
		if(!me.get_doctype() && !me.get_role()) {
			this.body.html("<p class='text-muted'>"+__("Select Document Type or Role to start.")+"</div>");
			return;
		}
		// get permissions
		frappe.call({
			module: "frappe.core",
			page: "permission_manager",
			method: "get_permissions",
			args: {
				doctype: me.get_doctype(),
				role: me.get_role()
			},
			callback: function(r) {
				me.render(r.message);
			}
		});
	},
	render: function(perm_list) {
		this.body.empty();
		this.perm_list = perm_list || [];
		if(!this.perm_list.length) {
			this.body.html("<p class='text-muted'>"
				+__("No Permissions set for this criteria.")+"</p>");
		} else {
			this.show_permission_table(this.perm_list);
		}
		this.make_reset_button();
	},
	show_permission_table: function(perm_list) {

		var me = this;
		this.table = $("<div class='table-responsive'>\
			<table class='table table-bordered'>\
				<thead><tr></tr></thead>\
				<tbody></tbody>\
			</table>\
		</div>").appendTo(this.body);

		$.each([[__("Document Type"), 150], [__("Role"), 170], [__("Level"), 40],
			[__("Permissions"), 350], ["", 40]], function(i, col) {
			$("<th>").html(col[0]).css("width", col[1]+"px")
				.appendTo(me.table.find("thead tr"));
		});

		$.each(perm_list, function(i, d) {
			if(!d.permlevel) d.permlevel = 0;
			var row = $("<tr>").appendTo(me.table.find("tbody"));
			me.add_cell(row, d, "parent");
			var role_cell = me.add_cell(row, d, "role");
			me.set_show_users(role_cell, d.role);

			if (d.permlevel===0) {
				me.setup_user_permissions(d, role_cell);
				me.setup_if_owner(d, role_cell);
			}

			var cell = me.add_cell(row, d, "permlevel");
			if(d.permlevel==0) {
				cell.css("font-weight", "bold");
				row.addClass("warning");
			}

			var perm_cell = me.add_cell(row, d, "permissions").css("padding-top", 0);
			var perm_container = $("<div class='row'></div>").appendTo(perm_cell);

			$.each(me.rights, function(i, r) {
				me.add_check(perm_container, d, r);
			});

			// buttons
			me.add_delete_button(row, d);
		});
	},

	add_cell: function(row, d, fieldname) {
		return $("<td>").appendTo(row)
			.attr("data-fieldname", fieldname)
			.html(__(d[fieldname]));
	},

	add_check: function(cell, d, fieldname, label) {
		var me = this;

		if(!label) label = toTitle(fieldname.replace(/_/g, " "));
		if(d.permlevel > 0 && ["read", "write"].indexOf(fieldname)==-1) {
			return;
		}

		var checkbox = $("<div class='col-md-4'><div class='checkbox'>\
				<label><input type='checkbox'>"+__(label)+"</input></label>"
				+ (d.help || "") + "</div></div>").appendTo(cell)
			.attr("data-fieldname", fieldname);

		checkbox.find("input")
			.prop("checked", d[fieldname] ? true: false)
			.attr("data-ptype", fieldname)
			.attr("data-name", d.name)
			.attr("data-doctype", d.parent)

		checkbox.find("label")
			.css("text-transform", "capitalize");

		return checkbox;
	},

	setup_user_permissions: function(d, role_cell) {
		var me = this;
		d.help = frappe.render('<ul class="user-permission-help small hidden" style="margin-left: -10px;">\
				<li style="margin-top: 7px;"><a class="show-user-permission-doctypes grey">{%= __("Select Document Types") %}</a></li>\
				<li style="margin-top: 3px;"><a class="show-user-permissions grey">{%= __("Show User Permissions") %}</a></li>\
			</ul>', {});

		var checkbox = this.add_check(role_cell, d, "apply_user_permissions")
			.removeClass("col-md-4")
			.css({"margin-top": "15px"});


		var toggle_user_permissions = function() {
			checkbox.find(".user-permission-help").toggleClass("hidden", !checkbox.find("input").prop("checked"));
		};

		toggle_user_permissions();
		checkbox.find("input").on('click', function() {
			toggle_user_permissions();
		});

		d.help = "";
	},

	setup_if_owner: function(d, role_cell) {
		var checkbox = this.add_check(role_cell, d, "if_owner")
			.removeClass("col-md-4")
			.css({"margin-top": "15px"});
	},

	rights: ["read", "write", "create"],

	
	add_check_events: function() {
		var me = this;

		this.body.on("click", ".show-user-permissions", function() {
			frappe.route_options = { doctype: me.get_doctype() || "" };
			frappe.set_route("user-permissions");
		});

		this.body.on("click", "input[type='checkbox']", function() {
			var chk = $(this);
			var args = {
				name: chk.attr("data-name"),
				doctype: chk.attr("data-doctype"),
				ptype: chk.attr("data-ptype"),
				value: chk.prop("checked") ? 1 : 0
			}
			return frappe.call({
				module: "frappe.core",
				page: "permission_manager",
				method: "update",
				args: args,
				callback: function(r) {
					if(r.exc) {
						// exception: reverse
						chk.prop("checked", !chk.prop("checked"));
					} else {
						me.get_perm(args.name)[args.ptype]=args.value;
					}
				}
			})
		})
	},
	
	
	make_reset_button: function() {
		var me = this;
		$('<button class="btn btn-default btn-sm" style="margin-left: 10px;">\
			<i class="icon-refresh"></i> ' + __("Restore Original Permissions") + '</button>')
			.appendTo(this.body.find(".permission-toolbar"))
			.on("click", function() {
				me.get_standard_permissions(function(data) {
					me.reset_std_permissions(data);
				});
			})
	}
});
