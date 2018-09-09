from __future__ import unicode_literals
import frappe
from erpnext.hr.doctype.leave_block_list.leave_block_list import get_applicable_block_dates
from erpnext.hr.doctype.leave_application.leave_application import get_number_of_leave_days, is_lwp, get_leave_balance_on
from frappe.utils import cint, date_diff, flt, getdate, formatdate, get_fullname

#VALIDATION NEXT ESS METHOD
def validate_dates_acorss_allocation(employee, leave_type, from_date, to_date):
	def _get_leave_alloction_record(date):
		allocation = frappe.db.sql("""select name from `tabLeave Allocation`
			where employee=%s and leave_type=%s and docstatus=1
			and %s between from_date and to_date""", (employee, leave_type, date))

		return allocation and allocation[0][0]

	allocation_based_on_from_date = _get_leave_alloction_record(from_date)
	allocation_based_on_to_date = _get_leave_alloction_record(to_date)

	if not (allocation_based_on_from_date or allocation_based_on_to_date):
		return "Application period cannot be outside leave allocation period"

	elif allocation_based_on_from_date != allocation_based_on_to_date:
		return "Application period cannot be across two alocation records"
	return ""

def validate_back_dated_application(employee, leave_type, to_date):
	future_allocation = frappe.db.sql("""select name, from_date from `tabLeave Allocation` where employee=%s and leave_type=%s and docstatus=1 and from_date > %s and carry_forward=1""", (employee, leave_type, to_date), as_dict=1)

	if future_allocation:
		return "Leave cannot be applied/cancelled before {0}, as leave balance has already been carry-forwarded in the future leave allocation record {1}".format(formatdate(future_allocation[0].from_date), future_allocation[0].name)
	return ""

def validate_balance_leaves(employee, leave_type, from_date, to_date, half_day, half_day_date, status):
	total_leave_days = 0
	if from_date and to_date:
		total_leave_days = get_number_of_leave_days(employee, leave_type, from_date, to_date, half_day, half_day_date)

		if total_leave_days == 0:
			return "The day(s) on which you are applying for leave are holidays. You need not apply for leave."

		if not is_lwp(leave_type):
			leave_balance = get_leave_balance_on(employee, leave_type, from_date, consider_all_leaves_in_the_allocation_period=True)

			if status != "Rejected" and leave_balance < total_leave_days:
				if frappe.db.get_value("Leave Type", leave_type, "allow_negative"):
					return "Note: There is not enough leave balance for Leave Type {0}".format(leave_type)
				else:
					return "There is not enough leave balance for Leave Type {0}".format(leave_type)
	return total_leave_days

def validate_leave_overlap(total_leave_days, employee, from_date, to_date, half_day, half_day_date):
	def _get_total_leaves_on_half_day(employee, half_day_date, name):
		leave_count_on_half_day_date = frappe.db.sql("""select count(name) from `tabLeave Application`
			where employee = %(employee)s
			and docstatus < 2
			and status in ("Open", "Approved")
			and half_day = 1
			and half_day_date = %(half_day_date)s
			and name != %(name)s""", {
				"employee": employee,
				"half_day_date": half_day_date,
				"name": name
			})[0][0]

		return leave_count_on_half_day_date * 0.5

	def _throw_overlap_error(employee, d):
		return "Employee {0} has already applied for {1} between {2} and {3}".format(employee, d['leave_type'], formatdate(d['from_date']), formatdate(d['to_date']))

	name = "New Leave Application"

	for d in frappe.db.sql("""
		select
			name, leave_type, posting_date, from_date, to_date, total_leave_days, half_day_date
		from `tabLeave Application`
		where employee = %(employee)s and docstatus < 2 and status in ("Open", "Approved")
		and to_date >= %(from_date)s and from_date <= %(to_date)s
		and name != %(name)s""", {
			"employee": employee,
			"from_date": from_date,
			"to_date": to_date,
			"name": name
		}, as_dict = 1):

		if cint(half_day)==1 and getdate(half_day_date) == getdate(d.half_day_date) and (
			flt(total_leave_days)==0.5
			or getdate(from_date) == getdate(d.to_date)
			or getdate(to_date) == getdate(d.from_date)):

			total_leaves_on_half_day = _get_total_leaves_on_half_day(employee,half_day_date,name)
			if total_leaves_on_half_day >= 1:
				return _throw_overlap_error(employee, d)
		else:
			return _throw_overlap_error(employee, d)

	return ""

def validate_max_days(total_leave_days, leave_type):
	max_days = frappe.db.get_value("Leave Type", leave_type, "max_days_allowed")
	if max_days and total_leave_days > cint(max_days):
		return "Leave of type {0} cannot be longer than {1}".format(leave_type, max_days)
	return ""

def show_block_day_warning(employee,company,from_date, to_date):
	block_dates = get_applicable_block_dates(from_date, to_date, employee, company, all_lists=True)
	if block_dates:
		warning = "Warning: Leave application contains following block dates\n"
		for d in block_dates:
			warning += formatdate(d.block_date) + ": " + d.reason
		return warning
	return ""

def validate_block_days(employee,company,from_date, to_date,status):
	block_dates = get_applicable_block_dates(from_date, to_date,employee, company)

	if block_dates and status == "Approved":
		return "You are not authorized to approve leaves on Block Dates"
	return ""

def validate_salary_processed_days(employee,leave_type, from_date,to_date):
	if not frappe.db.get_value("Leave Type", leave_type, "is_lwp"):
		return ""

	last_processed_pay_slip = frappe.db.sql("""
		select start_date, end_date from `tabSalary Slip`
		where docstatus = 1 and employee = %s
		and ((%s between start_date and end_date) or (%s between start_date and end_date))
		order by modified desc limit 1
	""",(employee, to_date, from_date))

	if last_processed_pay_slip:
		return "Salary already processed for period between {0} and {1}, Leave application period cannot be between this date range.".format(formatdate(last_processed_pay_slip[0][0]),formatdate(last_processed_pay_slip[0][1]))
	return ""

def validate_leave_approver(employee,leave_approver,docstatus):
	e = frappe.get_doc("Employee", employee)
	leave_approvers = [l.leave_approver for l in e.get("leave_approvers")]

	if len(leave_approvers) and leave_approver not in leave_approvers:
		return "Leave approver must be one of {0}".format(comma_or(leave_approvers))

	elif leave_approver and not frappe.db.sql("""select name from `tabHas Role`
		where parent=%s and role='Leave Approver'""", leave_approver):
		return "{0} ({1}) must have role 'Leave Approver'".format(get_fullname(leave_approver), leave_approver)

	elif docstatus==1 and len(leave_approvers) and leave_approver != frappe.session.user:
		return "Only the selected Leave Approver can submit this Leave Application"
	return ""

def validate_attendance(employee, from_date, to_date):
	attendance = frappe.db.sql("""select name from `tabAttendance` where employee = %s and (attendance_date between %s and %s)
				and status = "Present" and docstatus = 1""",
		(employee, from_date, to_date))
	if attendance:
		return "Attendance for employee {0} is already marked for this day".format(employee)
	return ""