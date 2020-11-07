from __future__ import unicode_literals
import frappe
import json
import hashlib
import time
import file_manager
from file_manager import upload
from base import validate_method
from frappe.utils import get_fullname

# CUSTOM METHOD
from app.helper import *
from app.nextsales.validation import *
from app.nextess.validation import * 

LIMIT_PAGE = 20
API_VERSION = 1.5

@frappe.whitelist(allow_guest=True)
def me():
	me = frappe.session
	return me


@frappe.whitelist(allow_guest=True)
def ping():
	return "pong"

@frappe.whitelist(allow_guest=True)
def sales_force_validate():
	data = dict()

	data["api_version"] = API_VERSION
	return data

# USER PERMISSION
@frappe.whitelist(allow_guest=False)
def get_user_permission():
	user = frappe.session.user

	data = dict()
	data['has_roles'] = frappe.db.sql("SELECT * FROM `tabHas Role` WHERE parent='{}'".format(user),as_dict=1)
	dataUser = frappe.db.sql("SELECT * FROM `tabUser` WHERE name='{}'".format(user),as_dict=1)
	if len(dataUser) > 0:
		data['user'] = dataUser[0] 
	data['user_permissions'] = frappe.db.sql("SELECT * FROM `tabUser Permission` WHERE user='{}'".format(user),as_dict=1)

	return data

# METADATA
@frappe.whitelist(allow_guest=False)
def get_metadata(employee='%',company='',approver='%',is_sales="0",is_employee="0"):

	data = dict()
	
	if (is_employee == "1"):
		#daily net expense claim
		fetchExpenseClaim = frappe.get_list("Expense Claim", 
										filters = {"employee": ("LIKE", employee)},
										fields = "SUM(total_claimed_amount) as net_expense_claim, posting_date",
										order_by = "posting_date DESC",
										group_by = "posting_date",
										limit_page_length = 7
									 )
		# fetchNetSales = frappe.db.sql("SELECT SUM(total_claimed_amount) as net_expense_claim, posting_date FROM `tabExpense Claim` WHERE employee LIKE '{}' AND company = '{}' AND approval_status='Approved' GROUP BY posting_date DESC LIMIT 7".format(employee,company),as_dict=1)
		data['daily_net_expense_claim'] = fetchExpenseClaim

		#leave application
		status = ["Open","Approved"]
		data['leave_application'] = dict()
		dataLA = data['leave_application']
		dataLA['count'] = dict()
		dataCount = dataLA['count']
		for stat in status:
			fetch = frappe.db.sql("SELECT COUNT(name) FROM `tabLeave Application` WHERE status='{}' AND employee LIKE '{}' AND company = '{}' ORDER BY modified".format(stat,employee,company),as_list=1)
			if (len(fetch) > 0):
				firstFetch = fetch[0]
				dataCount[stat] = firstFetch[0]

		#employee advance
		status = ['Draft','Unpaid','Claimed','Paid']
		data['employee_advance'] = dict()
		dataEA = data['employee_advance']
		dataEA['count'] = dict()
		dataCount = dataEA['count']
		for stat in status:
			fetch = frappe.db.sql("SELECT COUNT(name) FROM `tabEmployee Advance` WHERE status='{}' AND employee LIKE '{}' AND company = '{}' ORDER BY modified".format(stat,employee,company),as_list=1)
			if (len(fetch) > 0):
				firstFetch = fetch[0]
				dataCount[stat] = firstFetch[0]

		#expense claim
		status = ['Draft','Unpaid','Paid']
		data['expense_claim'] = dict()
		dataEC = data['expense_claim']
		dataEC['count'] = dict()
		dataCount = dataEC['count']
		for stat in status:
			fetch = frappe.db.sql("SELECT COUNT(name) FROM `tabExpense Claim` WHERE status='{}' AND employee LIKE '{}' AND company = '{}' ORDER BY modified".format(stat,employee,company),as_list=1)
			if (len(fetch) > 0):
				firstFetch = fetch[0]
				dataCount[stat] = firstFetch[0]

	else:
		fetchCurrency = frappe.get_list("Currency",
							fields="symbol,name",
							order_by="name")
		data['currency'] = fetchCurrency
		#delivery note
		status = ['Draft', 'To Bill','To Bill','Completed','Cancelled','Closed']
		data['delivery_note'] = dict()
		dataDN = data['delivery_note']
		dataDN['count'] = dict()
		dataCount = dataDN['count']
		for stat in status:
			fetch = frappe.get_list("Delivery Note", 
								filters = 
								{
									"status": stat
								})
			dataCount[stat] = len(fetch)

		#sales order
		status = ['Draft', 'To Deliver and Bill','To Bill','To Deliver','Completed','Cancelled','Closed']
		data['sales_order'] = dict()
		dataSO = data['sales_order']
		dataSO['count'] = dict()
		dataCount = dataSO['count']
		for stat in status:
			fetch = frappe.get_list("Sales Order", 
								filters = 
								{
									"status": stat
								})
			dataCount[stat] = len(fetch)

		#invoice
		status = ['Overdue','Unpaid','Paid']
		data['invoice'] = dict()
		dataINV = data['invoice']
		dataINV['count'] = dict()
		dataCount = dataINV['count']
		for stat in status:
			fetch = frappe.get_list("Sales Invoice", 
								filters = 
								{
									"status": stat
								})
			dataCount[stat] = len(fetch)
				

		#lead
		status = ['Lead','Open','Replied','Opportunity','Interested','Quotation','Lost Quotation','Converted','Do Not Contact']
		data['lead'] = dict()
		dataLead = data['lead']
		dataLead['count'] = dict()
		dataCount = dataLead['count']
		for stat in status:
			fetch = frappe.get_list("Lead", 
								filters = 
								{
									"status": stat
								})
			dataCount[stat] = len(fetch)

		dataCount['Quotation'] += len(frappe.get_list("Quotation",filters = {"status": ("IN", ['Submitted','Open']),"quotation_to": "Customer"}))
		dataCount['Converted'] += len(frappe.get_list("Quotation",filters = {"status": "Ordered","quotation_to": "Customer"}))
		dataCount['Opportunity'] += len(frappe.get_list("Opportunity",filters = {"status": "Open","enquiry_from": "Customer"}))
 

		#net sales
		fetchNetSales = frappe.get_list("Sales Order", 
										filters = {"status": ("IN", ["Open", "To Bill", "To Deliver", "To Deliver and Bill", "Completed"])},
										fields = ["SUM(grand_total) as net_sales", "transaction_date as posting_date"],
										order_by = "transaction_date DESC",
										group_by = "transaction_date",
										limit_page_length = 7
									 )
		data['daily_net_sales'] = fetchNetSales


		fetchPrintFormat = frappe.db.sql("SELECT name, doc_type FROM `tabPrint Format` WHERE disabled = 0",as_dict=1)

		data["print_format"] = fetchPrintFormat

	return data

@frappe.whitelist(allow_guest=False)
def get_sales_report(interval=0):

	data = dict()
	week = int(interval) * 7
	month = int(interval) * 4
	year = int(interval) * 6
	#daily total sales
	daily = frappe.db.sql("SELECT COALESCE(sales.total, 0) AS Y, daily.day AS X FROM (SELECT DATE(NOW()) - INTERVAL (1 + {}) DAY AS day UNION ALL SELECT DATE(NOW()) - INTERVAL (2 + {}) DAY UNION ALL SELECT DATE(NOW()) - INTERVAL (3 + {}) DAY UNION ALL SELECT DATE(NOW()) - INTERVAL (4 + {}) DAY UNION ALL SELECT DATE(NOW()) - INTERVAL (5 + {}) DAY UNION ALL SELECT DATE(NOW()) - INTERVAL (6 + {}) DAY UNION ALL SELECT DATE(NOW()) - INTERVAL (7 + {}) DAY) daily LEFT JOIN (SELECT SUM(si.rounded_total) AS total, si.posting_date FROM `tabSales Invoice` si GROUP BY si.posting_date) sales ON sales.posting_date = daily.day;".format(week, week, week, week, week, week, week),as_dict=1)
	data["daily"] = daily

	#weekly total sales
	weekly = frappe.db.sql("SELECT COALESCE(sales.total, 0) AS Y, weekly.week AS X FROM (SELECT DATE_FORMAT(NOW() - INTERVAL (1 + {}) WEEK, '%Y Week %u') AS week UNION ALL SELECT DATE_FORMAT(NOW() - INTERVAL (2 + {}) WEEK, '%Y Week %u') UNION ALL SELECT DATE_FORMAT(NOW() - INTERVAL (3 + {}) WEEK, '%Y Week %u') UNION ALL SELECT DATE_FORMAT(NOW() - INTERVAL (4 + {}) WEEK, '%Y Week %u')) weekly LEFT JOIN (SELECT SUM(si.rounded_total) AS total, DATE_FORMAT(si.posting_date, '%Y Week %u') AS week FROM `tabSales Invoice` si GROUP BY (week)) sales ON sales.week = weekly.week;".format(month, month, month, month),as_dict=1)
	data["weekly"] = weekly

	#monthly total sales
	monthly = frappe.db.sql("SELECT COALESCE(sales.total, 0) AS Y, monthly.month AS X FROM (SELECT DATE_FORMAT(NOW() - INTERVAL (1 + {}) MONTH, '%Y-%M') AS month UNION ALL SELECT DATE_FORMAT(NOW() - INTERVAL (2 + {}) MONTH, '%Y-%M') UNION ALL SELECT DATE_FORMAT(NOW() - INTERVAL (3 + {}) MONTH, '%Y-%M') UNION ALL SELECT DATE_FORMAT(NOW() - INTERVAL (4 + {}) MONTH, '%Y-%M') UNION ALL SELECT DATE_FORMAT(NOW() - INTERVAL (5 + {}) MONTH, '%Y-%M') UNION ALL SELECT DATE_FORMAT(NOW() - INTERVAL (6 + {}) MONTH, '%Y-%M')) monthly LEFT JOIN (SELECT SUM(si.rounded_total) AS total, DATE_FORMAT(si.posting_date, '%Y-%M') AS month FROM `tabSales Invoice` si GROUP BY (month)) sales ON sales.month = monthly.month;".format(year, year, year, year, year, year),as_dict=1)
	data["monthly"] = monthly

	return data

@frappe.whitelist(allow_guest=False)
def get_sales_by_person():
	data = dict()
	data["sales_person"] = frappe.db.sql("SELECT st.sales_person AS 'Person Name', SUM(si.rounded_total) * st.allocated_percentage / 100 AS total_sales FROM `tabSales Invoice` si JOIN `tabSales Team` st ON si.name = st.parent GROUP BY st.sales_person ORDER BY total_sales DESC", as_dict=True)
	data["sales_person_day"] = frappe.db.sql("SELECT st.sales_person AS 'Person Name', SUM(si.rounded_total) * st.allocated_percentage / 100 AS total_sales FROM `tabSales Invoice` si JOIN `tabSales Team` st ON si.name = st.parent WHERE si.posting_date = CURDATE() GROUP BY st.sales_person ORDER BY total_sales DESC", as_dict=True)
	data["sales_person_month"] = frappe.db.sql("SELECT st.sales_person AS 'Person Name', SUM(si.rounded_total) * st.allocated_percentage / 100 AS total_sales FROM `tabSales Invoice` si JOIN `tabSales Team` st ON si.name = st.parent WHERE DATE_FORMAT(si.posting_date, '%Y-%m') = DATE_FORMAT(CURDATE(), '%Y-%m') GROUP BY st.sales_person ORDER BY total_sales DESC", as_dict=True)
	return data

# TOTAL SALES PER CUSTOMER
@frappe.whitelist(allow_guest=False)
def get_customer_sales(query='',last_day=0, sort='',page=0):
	seen = ""
	data = []
	
	filters = ["name", "customer_name"]

	for f in filters:
		data_filter = frappe.get_list("Customer", 
							fields="*", 
							filters = 
							{
								f: ("LIKE", "%{}%".format(query))
							},
							order_by=sort,
							limit_page_length=LIMIT_PAGE,
							limit_start=page)
		temp_seen, result_list = distinct(seen,data_filter)
		seen = temp_seen
		data.extend(result_list)

	for d in data:
		fetchTotalSales  = frappe.db.sql("SELECT SUM(rounded_total) FROM `tabSales Invoice` WHERE customer_name = '{}' AND posting_date BETWEEN DATE(NOW()) - INTERVAL {} DAY AND NOW()".format(d["customer_name"],last_day))
		d["total_sales"] = fetchTotalSales[0]

		fetchDeposit = frappe.db.sql("SELECT SUM(unallocated_amount) FROM `tabPayment Entry` WHERE party = '{}'".format(d['customer_name']))
		d["deposit_amount"] = fetchDeposit[0]

	return data


# LEAVE APPLICATION
@frappe.whitelist(allow_guest=False)
def get_leave_allocation(status='',query='',sort='',page=0):
	filters = ['name','leave_type','employee_name']
	n_filters = len(filters)
	generate_filters = ""
	for i in range(0,n_filters-1):
		generate_filters += "{} LIKE '%{}%' OR ".format(filters[i],query)
	generate_filters += "{} LIKE '%{}%' ".format(filters[n_filters-1],query)

	statuses = status.split(',')
	generate_status = "'" + "','".join(statuses) + "'"

	sortedby = 'modified'
	if (sort != ''):
		sortedby = sort

	data = frappe.db.sql("SELECT * FROM `tabLeave Allocation` WHERE docstatus = 1 AND status IN ({}) AND ({}) ORDER BY {} DESC, status ASC LIMIT 20 OFFSET {}".format(generate_status,generate_filters,sortedby,page),as_dict=1)

	return data

@frappe.whitelist(allow_guest=False)
def request_leave_application(employee='',company='',leave_type='', from_date='', to_date='', status='Open', half_day=0, half_day_date='',docstatus=0,leave_approver=None):
	error_message = []
	warning_message = []
	total_leave_days = 0

	#VALIDATION
	if not is_lwp(leave_type):
		result = validate_dates_acorss_allocation(employee, leave_type, from_date, to_date)
		if result != "":
			error_message.append(result)
		result = validate_back_dated_application(employee, leave_type, to_date)
		if result != "":
			error_message.append(result)
	result = validate_balance_leaves(employee, leave_type, from_date, to_date, half_day, half_day_date, status)
	if str(type(result)) == "<type 'int'>":
		total_leave_days = result
	else:
		error_message.append(result)

	result = validate_leave_overlap(total_leave_days,employee,from_date,to_date,half_day,half_day_date)
	if result != "":
		error_message.append(result)
	result = validate_max_days(total_leave_days, leave_type)
	if result != "":
		error_message.append(result)
	result = show_block_day_warning(employee,company,from_date,to_date)
	if result != "":
		warning_message.append(result)
	result = validate_block_days(employee,company,from_date, to_date,status)
	if result != "":
		error_message.append(result)
	result = validate_salary_processed_days(employee,leave_type, from_date,to_date)
	if result != "":
		error_message.append(result)
	result = validate_leave_approver(employee,leave_approver,docstatus)
	if result != "":
		error_message.append(result)
	result = validate_attendance(employee, from_date, to_date)
	if result != "":
		error_message.append(result)
		
	data = dict()
	data['warning_message'] = []
	data['error_message'] = []
	if (len(warning_message) > 0):
		data['result'] = 'success with some warning'
		data['warning_message'] = warning_message
	if (len(error_message) > 0):
		data['result'] = "not success"
		data['error_message'] = error_message
	else:
		data['result'] = "success"
	return data

@frappe.whitelist(allow_guest=False)
def get_leave_application(leave_approver='%',employee='',filter_requested='all',company='',status='',query='',sort='',page=0):
	seen = ""
	data = []
	
	statuses = status.split(',')
	filters = ['name','leave_type','employee_name']

	for f in filters:
		data_filter = []
		if filter_requested == 'me':
			data_filter = frappe.get_list("Leave Application", 
								fields="*", 
								filters = 
								{
									"status": ("IN", statuses),
									"company": company,
									"employee": employee,
									f: ("LIKE", "%{}%".format(query))
								},
								order_by=sort,
								limit_page_length=LIMIT_PAGE,
								limit_start=page)
		elif filter_requested == 'other':
			data_filter = frappe.get_list("Leave Application", 
								fields="*", 
								filters = 
								{
									"status": ("IN", statuses),
									"company": company,
									"leave_approver": ("LIKE", leave_approver),
									f: ("LIKE", "%{}%".format(query))
								},
								order_by=sort,
								limit_page_length=LIMIT_PAGE,
								limit_start=page)
		else:
			data_filter_me = frappe.get_list("Leave Application", 
								fields="*", 
								filters = 
								{
									"status": ("IN", statuses),
									"company": company,
									"employee": employee,
									f: ("LIKE", "%{}%".format(query))
								},
								order_by=sort,
								limit_page_length=LIMIT_PAGE,
								limit_start=page)
			data_filter_other = frappe.get_list("Leave Application", 
								fields="*", 
								filters = 
								{
									"status": ("IN", statuses),
									"company": company,
									"leave_approver": ("LIKE", leave_approver),
									f: ("LIKE", "%{}%".format(query))
								},
								order_by=sort,
								limit_page_length=LIMIT_PAGE,
								limit_start=page)
			data_filter.extend(data_filter_me)
			data_filter.extend(data_filter_other)

		temp_seen, result_list = distinct(seen,data_filter)
		seen = temp_seen
		data.extend(result_list)
	return data

@frappe.whitelist(allow_guest=False)
def get_leave_approver(employee=''):
	data = frappe.db.sql("SELECT * FROM `tabEmployee Leave Approver` WHERE parent = '{}' AND parentfield = 'leave_approvers'".format(employee),as_dict=1)

	leave_approvers = "'"
	for d in data:
		leave_approvers += d["leave_approver"] + "','"

	data = frappe.db.sql("SELECT full_name, name FROM `tabUser` WHERE name IN ({}')".format(leave_approvers),as_dict=1)

	return data

# EXPENSE

def validate_expense_approver(exp_approver):
	if exp_approver and "Expense Approver" not in frappe.get_roles(exp_approver):
		return "{0} ({1}) must have role 'Expense Approver'".format(get_fullname(exp_approver), exp_approver)
	return ""

def validate_expense_account(expense_claim_type, company):
	account = frappe.db.get_value("Expense Claim Account",
		{"parent": expense_claim_type, "company": company}, "default_account")
	if not account:
		return expense_claim_type
	return ""



@frappe.whitelist(allow_guest=False)
def request_expense_claim(exp_approver='', company='',expense_claim_type=''):
	error_message = []
	warning_message = []
	total_leave_days = 0

	result = validate_expense_approver(exp_approver)
	if result != "":
		error_message.append(result)
	ects = expense_claim_type.split(',')
	error_ects = []
	for ect in ects:
		result = validate_expense_account(ect,company)
		if result != "":
			error_ects.append(result)

	if len(error_ects) > 0:
		generated_error_ects = ",".join(error_ects)
		error_message.append("Please set default account in Expense Claim Type {0}".format(generated_error_ects))
		
	data = dict()
	data['warning_message'] = []
	data['error_message'] = []
	if (len(warning_message) > 0):
		data['result'] = 'success with some warning'
		data['warning_message'] = warning_message
	if (len(error_message) > 0):
		data['result'] = "not success"
		data['error_message'] = error_message
	else:
		data['result'] = "success"
	return data


@frappe.whitelist(allow_guest=False)
def get_expense_claim(exp_approver='%',filter_requested='all',employee='',company='',status='',approval_status='',query='',sort='',page=0):
	seen = ""
	data = []

	approval_statuses = approval_status.split(',')
	statuses = status.split(',')
	filters = ['name','employee_name']

	for f in filters:
		data_filter = []
		if filter_requested == 'me':
			data_filter = frappe.get_list("Expense Claim", 
								fields="*", 
								filters = 
								{
									"status": ("IN", statuses),
									"company": company,
									"employee": employee,
									"approval_status": ("IN", approval_statuses),
									f: ("LIKE", "%{}%".format(query))
								},
								order_by=sort,
								limit_page_length=LIMIT_PAGE,
								limit_start=page)
		elif filter_requested == 'other':
			data_filter = frappe.get_list("Expense Claim", 
								fields="*", 
								filters = 
								{
									"status": ("IN", statuses),
									"company": company,
									"approval_status": ("IN", approval_statuses),
									"exp_approver": ("LIKE", exp_approver),
									f: ("LIKE", "%{}%".format(query))
								},
								order_by=sort,
								limit_page_length=LIMIT_PAGE,
								limit_start=page)
		else:
			data_filter_me = frappe.get_list("Expense Claim", 
								fields="*", 
								filters = 
								{
									"status": ("IN", statuses),
									"company": company,
									"employee": employee,
									"approval_status": ("IN", approval_statuses),
									f: ("LIKE", "%{}%".format(query))
								},
								order_by=sort,
								limit_page_length=LIMIT_PAGE,
								limit_start=page)
			data_filter_other = frappe.get_list("Expense Claim", 
								fields="*", 
								filters = 
								{
									"status": ("IN", statuses),
									"company": company,
									"approval_status": ("IN", approval_statuses),
									"exp_approver": ("LIKE", exp_approver),
									f: ("LIKE", "%{}%".format(query))
								},
								order_by=sort,
								limit_page_length=LIMIT_PAGE,
								limit_start=page)
			data_filter.extend(data_filter_me)
			data_filter.extend(data_filter_other)

		temp_seen, result_list = distinct(seen,data_filter)
		seen = temp_seen
		data.extend(result_list)


	return data

	
	# n_filters = len(filters)
	# generate_filters = ""
	# for i in range(0,n_filters-1):
	# 	generate_filters += "{} LIKE '%{}%' OR ".format(filters[i],query)
	# generate_filters += "{} LIKE '%{}%' ".format(filters[n_filters-1],query)

	# approval_statuses = approval_status.split(',')
	# generate_approval_status = "'" + "','".join(approval_statuses) + "'"
	# statuses = status.split(',')
	# generate_status = "'" + "','".join(statuses) + "'"

	# sortedby = 'modified'
	# if (sort != ''):
	# 	sortedby = sort

	# if filter_requested == 'me':
	# 	query = "SELECT * FROM `tabExpense Claim` WHERE employee LIKE '{}' AND company = '{}' AND (status IN ({}) AND approval_status IN ({})) AND ({}) ORDER BY {} DESC, status ASC LIMIT 20 OFFSET {}".format(employee,company,generate_status,generate_approval_status,generate_filters,sortedby,page)
	# elif filter_requested == 'other':
	# 	query = "SELECT * FROM `tabExpense Claim` WHERE exp_approver LIKE '{}' AND company = '{}' AND (status IN ({}) AND approval_status IN ({})) AND ({}) ORDER BY {} DESC, status ASC LIMIT 20 OFFSET {}".format(exp_approver,company,generate_status,generate_approval_status,generate_filters,sortedby,page)
	# elif filter_requested == 'all':
	# 	query = "SELECT * FROM `tabExpense Claim` WHERE (exp_approver LIKE '{}' OR employee LIKE '{}') AND company = '{}' AND (status IN ({}) AND approval_status IN ({})) AND ({}) ORDER BY {} DESC, status ASC LIMIT 20 OFFSET {}".format(exp_approver, employee,company,generate_status,generate_approval_status,generate_filters,sortedby,page)
	# data = frappe.db.sql(query,as_dict=1)

	# return data


@frappe.whitelist(allow_guest=True)
def attach_image_to_expense_claim():
	response = {}

	validate = validate_method(frappe.local.request.method,["POST"])
	if validate != True:
		return validate

	req = frappe.local.form_dict

	hash = hashlib.sha1()
	hash.update(str(time.time()))
	hash_now = hash.hexdigest()[:10]
	req.filename = "attachment_{}.jpg".format(hash_now)




	data = json.loads(req.data)
	req.filedata = data['filedata']
	req.expense_claim = data['expense_claim']

	try:

		uploaded = upload("Expense Claim",req.expense_claim,1)

		response["code"] = 200
		response["message"] = "Success"
		response["data"] = uploaded

	except Exception as e:
		response["code"] = 400
		response["message"] = e.message
		response["data"] = ""
	except UnboundLocalError as e:
		response["code"] = 400
		response["message"] = e.message
		response["data"] = ""

	return response


@frappe.whitelist(allow_guest=False)
def get_expense_approver():
	user = frappe.session.user
	data = frappe.db.sql("SELECT parent FROM `tabHas Role` WHERE role ='Expense Approver'".format(user),as_dict=1)

	exp_approvers = "'"
	for d in data:
		exp_approvers += d["parent"] + "','"

	data = frappe.db.sql("SELECT full_name, name FROM `tabUser` WHERE name IN ({}')".format(exp_approvers),as_dict=1)

	return data

@frappe.whitelist(allow_guest=False)
def approve_expense_claim(approve='',is_paid='',name=''):
	status = 'Draft'
	approval_status = 'Draft'
	if approve == '1':
		approval_status = 'Approved'
		if is_paid == '1':
			status = 'Paid'
		else:
			status = 'Unpaid'
	else:
		approval_status = 'Rejected'
		status = 'Rejected'

	result = frappe.db.sql("UPDATE `tabExpense Claim` SET status = '{}', docstatus=1, approval_status = '{}' WHERE name = '{}'".format(status, approval_status, name))
	frappe.db.commit()
	return result

# EMPLOYEE ADVANCE
@frappe.whitelist(allow_guest=False)
def get_employee_advance(owner='%',employee='%', company='', status='',query='',sort='',page=0):
	seen = ""
	data = []

	statuses = status.split(',')
	filters = ['name','employee_name','purpose']

	for f in filters:
		data_filter = frappe.get_list("Employee Advance", 
							fields="*", 
							filters = 
							{
								"status": ("IN", statuses),
								"company": company,
								f: ("LIKE", "%{}%".format(query))
							},
							order_by=sort,
							limit_page_length=LIMIT_PAGE,
							limit_start=page)
		temp_seen, result_list = distinct(seen,data_filter)
		seen = temp_seen
		data.extend(result_list)
	return data

	# filters = ['name','employee_name','purpose']
	# n_filters = len(filters)
	# generate_filters = ""
	# for i in range(0,n_filters-1):
	# 	generate_filters += "{} LIKE '%{}%' OR ".format(filters[i],query)
	# generate_filters += "{} LIKE '%{}%' ".format(filters[n_filters-1],query)

	# statuses = status.split(',')
	# generate_status = "'" + "','".join(statuses) + "'"

	# sortedby = 'modified'
	# if (sort != ''):
	# 	sortedby = sort



	# data = frappe.db.sql("SELECT * FROM `tabEmployee Advance` WHERE (owner LIKE '{}' OR employee LIKE '{}') AND company='{}' AND status IN ({}) AND ({}) ORDER BY {} DESC, status ASC LIMIT 20 OFFSET {}".format(owner,employee,company,generate_status,generate_filters,sortedby,page),as_dict=1)
		 
	# return data

# ========================================================CUSTOMER====================================================
@frappe.whitelist(allow_guest=False)
def get_customer(query='',sort='',page=0):
	seen = ""
	data = []
	

	filters = ["name", "customer_name","territory"]

	for f in filters:
		data_filter = frappe.get_list("Customer", 
							fields="*", 
							filters = 
							{
								f: ("LIKE", "%{}%".format(query))
							},
							order_by=sort,
							limit_page_length=LIMIT_PAGE,
							limit_start=page)
		temp_seen, result_list = distinct(seen,data_filter)
		for df in result_list:
			data_sales = frappe.db.sql("SELECT * FROM `tabSales Team` WHERE parent='{}'".format(df['name']),as_dict=1)
			df['sales_persons'] = data_sales
		seen = temp_seen
		data.extend(result_list)
	return data	

# ========================================================SALES ORDER====================================================
@frappe.whitelist(allow_guest=False)
def get_sales_order(status='',query='',sort='',page=0):
	seen = ""
	data = []
	
	statuses = status.split(',')
	filters = ["name", "customer_name"]

	for f in filters:
		data_filter = frappe.get_list("Sales Order", 
							fields="*", 
							filters = 
							{
								"status": ("IN", statuses),
								f: ("LIKE", "%{}%".format(query))
							},
							order_by=sort,
							limit_page_length=LIMIT_PAGE,
							limit_start=page)
		temp_seen, result_list = distinct(seen,data_filter)
		for df in result_list:
			data_sales = frappe.db.sql("SELECT * FROM `tabSales Team` WHERE parent='{}'".format(df['name']),as_dict=1)
			df['sales_persons'] = data_sales
		seen = temp_seen
		data.extend(result_list)
	return data

@frappe.whitelist(allow_guest=False)
def validate_sales_order(items):
	return validate_warehouse(items)


# ========================================================SALES INVOICE====================================================

@frappe.whitelist(allow_guest=False)
def get_sales_invoice(status='',query='',sort='',page=0):
	seen = ""
	data = []
	
	statuses = status.split(',')
	filters = ["name", "customer_name"]

	for f in filters:
		data_filter = frappe.get_list("Sales Invoice", 
							fields="*", 
							filters = 
							{
								"status": ("IN", statuses),
								f: ("LIKE", "%{}%".format(query))
							},
							order_by=sort,
							limit_page_length=LIMIT_PAGE,
							limit_start=page)
		temp_seen, result_list = distinct(seen,data_filter)
		for df in result_list:
			data_sales = frappe.db.sql("SELECT * FROM `tabSales Team` WHERE parent='{}'".format(df['name']),as_dict=1)
			df['sales_persons'] = data_sales
		seen = temp_seen
		data.extend(result_list)
	return data

@frappe.whitelist(allow_guest=False)
def get_item(is_sales_item='1',is_stock_item='1',ref='',sort='',page='0'):
	seen = ""
	data = []

	filters = ["item_name", "item_code"]

	for f in filters:
		data_filter = frappe.get_list("Item", 
							fields="*", 
							filters = 
							{
								"has_variants": 0,
								"is_sales_item":is_sales_item,
								"is_stock_item":is_stock_item,
								f: ("LIKE", "%{}%".format(ref))
							},
							order_by=sort,
							limit_page_length=LIMIT_PAGE,
							limit_start=page)
		temp_seen, result_list = distinct(seen,data_filter)
		seen = temp_seen
		data.extend(result_list)

	for row in data:
		row['product_bundle_item'] = list("")
		if (row['is_stock_item'] == 0):
			fetchBundleItem = frappe.get_list("Product Bundle Item", 
							fields="*", 
							filters = 
							{
								"parent":row['item_code']
							},
							limit_page_length=1000000)
			data_bundle_item = list("")
			for bundleItem in fetchBundleItem:
				fetchBundleItemDetails = frappe.get_list("Item", 
							fields="item_name", 
							filters = 
							{
								"item_code":bundleItem['item_code']
							})
				bundleItem['item_name'] = ""
				if (len(fetchBundleItemDetails) > 0):
					bundleItem['item_name'] = fetchBundleItemDetails[0]['item_name']
				data_bundle_item.append(bundleItem)
			row['product_bundle_item'] = data_bundle_item
	return data


# ========================================================OFFER====================================================

@frappe.whitelist(allow_guest=False)
def get_lead(status='',query='',sort='',page=0):
	data = dict()
	
	#lead
	statuses = status.split(',')
	filters = ['name','company_name','lead_name','email_id']

	seen_leads = ""
	data['leads'] = []
	for f in filters:
		data_filter = frappe.get_list("Lead", 
							fields="*", 
							filters = 
							{
								"status": ("IN", statuses),
								f: ("LIKE", "%{}%".format(query))
							},
							order_by=sort,
							limit_page_length=LIMIT_PAGE,
							limit_start=page)
		temp_seen_leads, result_list = distinct(seen_leads,data_filter)
		seen_leads = temp_seen_leads
		data['leads'].extend(result_list)
	

	#quotation
	if 'Quotation' in statuses:
		quotation_statuses = ['Submitted', 'Open']
	elif 'Converted' in statuses:
		quotation_statuses = ['Ordered']
	else:
		quotation_statuses = []


	data['quotations'] = []
	if len(quotation_statuses) > 0:
		filters = ['name','customer_name','contact_email']

		seen_quotations = ""
		for f in filters:
			data_filter = frappe.get_list("Quotation", 
								fields="*", 
								filters = 
								{
									"status": ("IN", quotation_statuses),
									"quotation_to": "Customer",
									f: ("LIKE", "%{}%".format(query))
								},
								order_by=sort,
								limit_page_length=LIMIT_PAGE,
								limit_start=page)
			temp_seen_quotations, result_list = distinct(seen_quotations,data_filter)
			seen_quotations = temp_seen_quotations
			data['quotations'].extend(result_list)


	#opportunity
	data['opportunities'] = []
	if 'Opportunity' in statuses:
		opportunity_statuses = ['Open']
		filters = ['name','customer_name','contact_email']

		seen_opportunities = ""
		for f in filters:
			data_filter = frappe.get_list("Opportunity", 
								fields="*", 
								filters = 
								{
									"status": ("IN", opportunity_statuses),
									"enquiry_from": "Customer",
									f: ("LIKE", "%{}%".format(query))
								},
								order_by=sort,
								limit_page_length=LIMIT_PAGE,
								limit_start=page)
			temp_seen_opportunities, result_list = distinct(seen_opportunities,data_filter)
			seen_opportunities = temp_seen_opportunities
			data['opportunities'].extend(result_list)

	return data


@frappe.whitelist(allow_guest=False)
def get_quotation(status='',query='',sort='',page=0):
	quotation_statuses = status.split(',')
	filters = ['name','customer_name','contact_email']

	seen_quotations = ""
	for f in filters:
		data_filter = frappe.get_list("Quotation", 
							fields="*", 
							filters = 
							{
								"status": ("IN", quotation_statuses),
								"quotation_to": "Customer",
								f: ("LIKE", "%{}%".format(query))
							},
							order_by=sort,
							limit_page_length=LIMIT_PAGE,
							limit_start=page)
		temp_seen_quotations, result_list = distinct(seen_quotations,data_filter)
		seen_quotations = temp_seen_quotations
		data['quotations'].extend(result_list)

	return data


@frappe.whitelist(allow_guest=False)
def get_opportunity(status='',query='',sort='',page=0):
	opportunity_statuses = status.split(',')
	filters = ['name','customer_name','contact_email']

	seen_opportunities = ""
	for f in filters:
		data_filter = frappe.get_list("Opportunity", 
							fields="*", 
							filters = 
							{
								"status": ("IN", opportunity_statuses),
								"enquiry_from": "Customer",
								f: ("LIKE", "%{}%".format(query))
							},
							order_by=sort,
							limit_page_length=LIMIT_PAGE,
							limit_start=page)
		temp_seen_opportunities, result_list = distinct(seen_opportunities,data_filter)
		seen_opportunities = temp_seen_opportunities
		data['opportunities'].extend(result_list)

	return data

@frappe.whitelist(allow_guest=False)
def get_lead_item(lead_no=''):
	
	fetch_opportunity = frappe.get_list("Opportunity", 
							fields="*", 
							filters = 
							{
								"lead": lead_no
							},
							limit_page_length=1000)
	fetch_quotation = frappe.get_list("Quotation", 
							fields="*", 
							filters = 
							{
								"lead": lead_no
							},
							limit_page_length=1000)
	data = dict()
	data['opportunity'] = fetch_opportunity
	data['quotation'] = fetch_quotation
	return data


@frappe.whitelist(allow_guest=False)
def get_user():
	data = frappe.get_list("User", 
				fields="*",
				limit_page_length=1000)
	return data


# ========================================================WAREHOUSE====================================================
@frappe.whitelist(allow_guest=False)
def check_item(item_code='',query=""):

	data = dict()
	data_price_lists = frappe.get_list("Price List",
										fields="*",
										filters={
											"selling":1,
											"enabled":1
										})
	data_prices = []
	for data_price_list in data_price_lists:
		data_price = frappe.db.sql("SELECT price_list,price_list_rate FROM `tabItem Price` WHERE item_code = '{}' AND price_list = '{}'".format(item_code,data_price_list["name"]),as_dict=True)
		# data_price = frappe.get_list("Item Price",
		# 								fields="price_list,price_list_rate",
		# 								filters={
		# 									"item_code":item_code,
		# 									"price_list":data_price_list["name"]
		# 								},
		# 								limit_page_length=100000)
		if (len(data_price) > 0):
			data_prices.append(data_price[0])
	data["item_price_list_rate"] = data_prices

	data_warehouses = frappe.get_list("Warehouse",
										fields="*",
										filters={
											"warehouse_name": ("LIKE","%{}%".format(query)),
											"is_group":0
										},
										order_by="modified", 
										limit_page_length=1000000
										)
	data_stocks = []
	for data_warehouse in data_warehouses:
		data_stock = frappe.get_list("Bin",
										fields="warehouse,actual_qty,projected_qty",
										filters={
											"item_code":item_code,
											"warehouse": data_warehouse["name"]
										})
		if (len(data_stock) > 0):
			data_stocks.append(data_stock[0])
	data["warehouse_stocks"] = data_stocks
	return data

@frappe.whitelist(allow_guest=False)
def get_warehouse(company='',query='',sort='',page=0):
	seen = ""
	data = []
	
	filters = ["name", "warehouse_name", "city", "address_line_1","address_line_2"]

	for f in filters:
		data_filter = frappe.get_list("Warehouse", 
							fields="*", 
							filters = 
							{
								"company":company,
								f: ("LIKE", "%{}%".format(query))
							},
							order_by=sort,
							limit_page_length=LIMIT_PAGE,
							limit_start=page)
		temp_seen, result_list = distinct(seen,data_filter)
		seen = temp_seen
		data.extend(result_list)
	return data

@frappe.whitelist(allow_guest=False)
def upload_image_profile():
	response = {}

	req = frappe.local.form_dict
	if (req == None):
		return {}


	user_id = get_user_id_by_session()
	if (user_id == ''):
		response['code'] = 417
		response['message'] = 'Session user invalid'
		response['data'] = None 
		return response
	req.filename = "profile_{}.jpg".format(user_id)


	data = json.loads(req.data)
	req.filedata = data['filedata']
	req.role = data['role']
	req.name = data['name']

	# try:

	frappe.db.sql("DELETE FROM `tabFile` WHERE attached_to_name='{}' AND attached_to_doctype='{}'".format(req.name,req.role))
	frappe.db.commit()
	
	uploaded = upload(req.role,req.name,1)

	response["code"] = 200
	response["message"] = "Success"
	response["data"] = uploaded


	doc_user = frappe.get_doc(req.role,req.name)
	doc_user.profile_photo = uploaded['file_url']
	doc_user.submit()
	frappe.db.commit()


	# except Exception as e:
	# 	response["code"] = 400
	# 	response["message"] = e.message
	# 	response["data"] = ""
	# except UnboundLocalError as e:
	# 	response["code"] = 401
	# 	response["message"] = e.message
	# 	response["data"] = ""

	return response

@frappe.whitelist(allow_guest=False)
def get_top_item_report(interval=1, customer="", time=""):
	if time == "day":
		data = frappe.db.sql("SELECT item_code, SUM(qty) AS delivered_quantity FROM `tabDelivery Note Item` WHERE parent IN (SELECT name FROM `tabDelivery Note` WHERE status = 'Completed' AND customer = '{}' AND posting_date BETWEEN DATE(NOW() - INTERVAL {} DAY) AND DATE(NOW())) GROUP BY item_code ORDER BY SUM(qty) LIMIT 10".format(customer, interval), as_dict=True)
	elif time == "month":
		data = frappe.db.sql("SELECT item_code, SUM(qty) AS delivered_quantity FROM `tabDelivery Note Item` WHERE parent IN (SELECT name FROM `tabDelivery Note` WHERE status = 'Completed' AND customer = '{}' AND posting_date BETWEEN DATE(NOW() - INTERVAL {} MONTH) AND DATE(NOW())) GROUP BY item_code ORDER BY SUM(qty) LIMIT 10".format(customer, interval), as_dict=True)
	elif time == "year":
		data = frappe.db.sql("SELECT item_code, SUM(qty) AS delivered_quantity FROM `tabDelivery Note Item` WHERE parent IN (SELECT name FROM `tabDelivery Note` WHERE status = 'Completed' AND customer = '{}' AND posting_date BETWEEN DATE(NOW() - INTERVAL {} YEAR) AND DATE(NOW())) GROUP BY item_code ORDER BY SUM(qty) LIMIT 10".format(customer, interval), as_dict=True)
	return data