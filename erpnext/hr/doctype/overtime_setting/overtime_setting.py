# -*- coding: utf-8 -*-
# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from frappe import _, msgprint, throw

class OvertimeSetting(Document):
	pass

	def validate(self):
		if self.working_days >=29:
			msgprint(_("The Total working days for month should be less than or equals 28 days."), raise_exception=True)		

		if self.working_hours > 12:
			msgprint(_("The Total working hours for a day should be less than or equals 12 hours."), raise_exception=True)

		if self.normal_ot_rate_for_hour <=1:
			msgprint(_("The 'Normal Overtime Hour Rate' should be greater than 1."), raise_exception=True)

		if self.holiday_ot_rate_for_hour and self.holiday_ot_rate_for_hour < self.normal_ot_rate_for_hour:
			msgprint(_("The 'Holiday Overtime Hour Rate' should be greater than 'Normal Overtime Hour Rate'."), raise_exception=True)

