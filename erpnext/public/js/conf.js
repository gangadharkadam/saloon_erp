// Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
// License: GNU General Public License v3. See license.txt

frappe.provide('erpnext');

// add toolbar icon
$(document).bind('toolbar_setup', function() {
	frappe.app.name = "ERPNext";

	frappe.help_feedback_link = '<p><a class="text-muted" \
		href="https://discuss.erpnext.com">Feedback</a></p>'

	frappe.call({
			method: "erpnext.hr.doctype.attendance.attendance.get_logo",
			callback: function(r) {
				if( r.message) {
					var logo = frappe.urllib.get_base_url()+"/files/"+r.message
					$('.navbar-home').html('<img class="erpnext-icon" src="'+logo+'" />');

				}
				else{
					$('.navbar-home').html('<img class="erpnext-icon" src="'+ frappe.urllib.get_base_url()+'/assets/erpnext/images/erp-icon1.svg" />');
				}
			}
		});


	/*$('.navbar-home').html('<img class="erpnext-icon" src="'+
			frappe.urllib.get_base_url()+'/assets/erpnext/images/erp-icon.svg" />');
	*/

	//$('[data-link="docs"]').attr("href", "https://manual.erpnext.com")
});

// doctypes created via tree
$.extend(frappe.create_routes, {
	"Customer Group": "Sales Browser/Customer Group",
	"Territory": "Sales Browser/Territory",
	"Item Group": "Sales Browser/Item Group",
	"Sales Person": "Sales Browser/Sales Person",
	"Account": "Accounts Browser/Account",
	"Cost Center": "Accounts Browser/Cost Center"
});

// preferred modules for breadcrumbs
$.extend(frappe.breadcrumbs.preferred, {
	"Item Group": "Stock",
	"Customer Group": "Selling",
	"Supplier Type": "Buying",
	"Territory": "Selling",
	"Sales Person": "Selling",
	"Sales Partner": "Selling",
	"Brand": "Selling"
});
