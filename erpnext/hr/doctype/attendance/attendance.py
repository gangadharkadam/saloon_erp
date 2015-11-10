# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

from __future__ import unicode_literals
import frappe

from frappe.utils import getdate, nowdate, flt,cstr ,get_time
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

	def validate_inout(self):
		if (get_time(self.time_in) > get_time(self.time_out)):
			frappe.throw(_("'Time In' ({0}) cannot be greater than 'Time Out' ({1})").format(self.time_in,
					self.time_out))

		if (self.time_out and not self.time_in ):
			frappe.throw(_("Please enter 'Time In' as you have entered 'Time Out'"))

		if (self.time_in and not self.time_out ):
			frappe.throw(_("Please enter 'Time Out' as you have entered 'Time In'"))


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
		self.validate_inout()
		self.calculate_ot()

	def on_update(self):
		# this is done because sometimes user entered wrong employee name
		# while uploading employee attendance
		employee_name = frappe.db.get_value("Employee", self.employee, "employee_name")
		frappe.db.set(self, 'employee_name', employee_name)

	def calculate_ot(self):
		# calculate OT worked hours
		h_list=frappe.db.sql("""select holiday_list from `tabEmployee` where name = '%s'"""%(self.employee),as_list=1)
		if self.time_in and self.time_out:
			time_in = self.att_date+" "+self.time_in
			time_out = self.att_date+" "+self.time_out
			start = datetime.datetime.strptime(time_in, '%Y-%m-%d %H:%M:%S')
			ends = datetime.datetime.strptime(time_out, '%Y-%m-%d %H:%M:%S')
			diff =  ends - start
			hrs=cstr(diff).split(':')[0]
			mnts=cstr(diff).split(':')[1]
			std_ot_hours=frappe.db.get_value("Overtime Setting", self.company, "working_hours")
			if not std_ot_hours:
				std_ot_hours=frappe.db.get_value("Overtime Setting", 'vlinku', "working_hours")
			if h_list:
				is_holiday=frappe.db.sql("select h.description from `tabHoliday List` hl ,`tabHoliday` h where hl.name=h.parent and h.holiday_date='%s' and hl.name='%s' and h.description not in ('Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday')" %(self.att_date,h_list[0][0]))
				is_fot=frappe.db.sql("select h.description from `tabHoliday List` hl ,`tabHoliday` h where hl.name=h.parent and h.holiday_date='%s' and hl.name='%s'  and h.description in ('Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday')" %(self.att_date,h_list[0][0]),as_list=1)
			if flt(std_ot_hours)>=flt(hrs+"."+mnts) :
				hours=0.0
			else: 
				hours=flt(hrs+"."+mnts)-flt(std_ot_hours)
			if is_holiday:
				day = datetime.datetime.strptime(self.att_date, '%Y-%m-%d').strftime('%A')
				if day == 'Friday':
					self.holiday_ot_hours = '0.0'
					self.ot_hours = '0.0'
					self.fot = flt(hrs+"."+mnts)
				else:
					self.holiday_ot_hours = flt(hrs+"."+mnts)
					self.ot_hours='0.0'
					self.fot='0.0'
			else:
				if is_fot:
					if is_fot[0][0]=="Friday":
						self.ot_hours = '0.0'
						self.holiday_ot_hours='0.0'
						self.fot=flt(hrs+"."+mnts)
				else:
					self.ot_hours = hours
					self.holiday_ot_hours='0.0'
					self.fot='0.0'


@frappe.whitelist()
def get_logo():
	"""
		This function is to set custom company logo
	"""
	if frappe.session['user']:
		company = frappe.db.sql("select company from `tabUser` where name = '%s'"%(frappe.session['user']),as_list=1)
		if company:
			logo = frappe.db.sql("""select file_name from `tabFile` where attached_to_doctype = 'Company' and 
				attached_to_name = '%s'"""%(company[0][0]),as_list=1)
			if logo:
				company_logo = logo[0][0]
				return company_logo
