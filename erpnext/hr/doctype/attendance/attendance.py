# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

from __future__ import unicode_literals
import frappe

from frappe.utils import getdate, nowdate, flt,cstr
from frappe import _
from frappe.model.document import Document
from erpnext.hr.utils import set_employee_name
import datetime


class Attendance(Document):
	def validate_duplicate_record(self):
		res = frappe.db.sql("""select name from `tabAttendance` where employee = %s and att_date = %s
			and name != %s and docstatus = 1""",
			(self.employee, self.att_date, self.name))
		if res:
			frappe.throw(_("Attendance for employee {0} is already marked").format(self.employee))

		set_employee_name(self)

	def check_leave_record(self):
		if self.status == 'Present':
			leave = frappe.db.sql("""select name from `tabLeave Application`
				where employee = %s and %s between from_date and to_date and status = 'Approved'
				and docstatus = 1""", (self.employee, self.att_date))

			if leave:
				frappe.throw(_("Employee {0} was on leave on {1}. Cannot mark attendance.").format(self.employee,
					self.att_date))

	def validate_att_date(self):
		if getdate(self.att_date) > getdate(nowdate()):
			frappe.throw(_("Attendance can not be marked for future dates"))

	def validate_employee(self):
		emp = frappe.db.sql("select name from `tabEmployee` where name = %s and status = 'Active'",
		 	self.employee)
		if not emp:
			frappe.throw(_("Employee {0} is not active or does not exist").format(self.employee))

	def validate(self):
		from erpnext.controllers.status_updater import validate_status
		from erpnext.accounts.utils import validate_fiscal_year
		validate_status(self.status, ["Present", "Absent", "Half Day"])
		validate_fiscal_year(self.att_date, self.fiscal_year, _("Attendance Date"), self)
		self.validate_att_date()
		self.validate_duplicate_record()
		self.check_leave_record()

	def on_update(self):
		# this is done because sometimes user entered wrong employee name
		# while uploading employee attendance
		employee_name = frappe.db.get_value("Employee", self.employee, "employee_name")
		frappe.db.set(self, 'employee_name', employee_name)

		# calculate OT worked hours
		time_in = self.att_date+" "+self.time_in
		time_out = self.att_date+" "+self.time_out
		start = datetime.datetime.strptime(time_in, '%Y-%m-%d %H:%M:%S')
		ends = datetime.datetime.strptime(time_out, '%Y-%m-%d %H:%M:%S')
		diff =  ends -start
		hrs=cstr(diff).split(':')[0]
		mnts=cstr(diff).split(':')[1]
		std_ot_hours=frappe.db.get_value("Overtime Setting", self.company, "working_hours")
		if not std_ot_hours:
			std_ot_hours=frappe.db.get_value("Overtime Setting", 'vlinku', "working_hours")
		is_holiday=frappe.db.sql("select h.description from `tabHoliday List` hl ,`tabHoliday` h where hl.name=h.parent and h.holiday_date='%s' and h.description not in ('Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday')" %(self.att_date))
		if is_holiday:
			self.holiday_ot_hours = flt(hrs+"."+mnts)-flt(std_ot_hours)
			self.ot_hours='0.0'
		else:
			self.ot_hours = flt(hrs+"."+mnts)-flt(std_ot_hours)
			self.holiday_ot_hours='0.0'
