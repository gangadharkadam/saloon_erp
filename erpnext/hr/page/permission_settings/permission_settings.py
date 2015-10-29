# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# MIT License. See license.txt

from __future__ import unicode_literals
import frappe
import frappe.defaults
from frappe.modules.import_file import get_file_path, read_doc_from_file
from frappe.translate import send_translations
from frappe.desk.notifications import delete_notification_count_for
from frappe.permissions import reset_perms, get_linked_doctypes

@frappe.whitelist()
def users():
	#frappe.only_for("System Manager")
	#send_translations(frappe.get_lang_dict("doctype", "DocPerm"))
	return {
		"users": [d[0] for d in frappe.db.sql("""select name from tabUser """)]
	}