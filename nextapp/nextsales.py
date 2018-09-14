from __future__ import unicode_literals
import frappe
import json
import hashlib
import time
import file_manager
from file_manager import upload
from base import validate_method
from frappe.utils import get_fullname
import sys

# CUSTOM METHOD
from app.helper import *
from app.nextsales.validation import *
from app.nextess.validation import * 
from validation import *

LIMIT_PAGE = 20
API_VERSION = 1.4

@frappe.whitelist(allow_guest=True)
def me():
	me = frappe.session
	return me


@frappe.whitelist(allow_guest=True)
def ping():
	return "pong"

@frappe.whitelist(allow_guest=True)
def version():
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
def get_metadata():

	data = dict()

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

	#sales order delivery status
	status = ['Not Delivered', 'Fully Delivered', 'Partly Delivered']
	for stat in status:
		fetch = frappe.get_list("Sales Order", 
							filters = 
							{
								"delivery_status": stat
							})
		dataCount[stat] = len(fetch)

	#sales order billing status
	status = ['Not Billed','Fully Billed','Partly Billed','Closed']
	for stat in status:
		fetch = frappe.get_list("Sales Order", 
							filters = 
							{
								"billing_status": stat
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
def get_sales_report(interval=0, tipe=''):

	data = dict()
	day = int(interval) * 7
	week = int(interval) * 4
	month = int(interval) * 6

	data['daily'] = []
	data['weekly'] = []
	data['monthly'] = []

	if (tipe == 'daily' or tipe == ''):
		#daily total sales
		daily = frappe.db.sql("SELECT COALESCE(sales.total, 0) AS Y, daily.day AS X FROM (SELECT DATE_FORMAT(NOW() - INTERVAL (1 + {}) DAY,'%e %b') AS day UNION ALL SELECT DATE_FORMAT(NOW() - INTERVAL (2 + {}) DAY,'%e %b') UNION ALL SELECT DATE_FORMAT(NOW() - INTERVAL (3 + {}) DAY,'%e %b') UNION ALL SELECT DATE_FORMAT(NOW() - INTERVAL (4 + {}) DAY,'%e %b') UNION ALL SELECT DATE_FORMAT(NOW() - INTERVAL (5 + {}) DAY,'%e %b') UNION ALL SELECT DATE_FORMAT(NOW() - INTERVAL (6 + {}) DAY,'%e %b') UNION ALL SELECT DATE_FORMAT(NOW() - INTERVAL (7 + {}) DAY,'%e %b')) daily LEFT JOIN (SELECT SUM(si.rounded_total * si.conversion_rate) AS total, DATE_FORMAT(si.posting_date,'%e %b') as posting_date FROM `tabSales Invoice` si WHERE docstatus != 0 AND si.posting_date >= (SELECT DATE(NOW() - INTERVAL (7 + {}) DAY)) AND si.posting_date <= (SELECT DATE(NOW() - INTERVAL (1 + {}) DAY)) GROUP BY posting_date) sales ON sales.posting_date = daily.day;".format(day, day, day, day, day, day, day, day, day),as_dict=1)
		data["daily"] = daily

	if (tipe == 'weekly' or tipe == ''):
		#weekly total sales
		# weekly = frappe.db.sql("SELECT COALESCE(sales.total, 0) AS Y, weekly.week AS X FROM (SELECT DATE_FORMAT(NOW() - INTERVAL (1 + {}) WEEK, '%Y Week %u') AS week UNION ALL SELECT DATE_FORMAT(NOW() - INTERVAL (2 + {}) WEEK, '%Y Week %u') UNION ALL SELECT DATE_FORMAT(NOW() - INTERVAL (3 + {}) WEEK, '%Y Week %u') UNION ALL SELECT DATE_FORMAT(NOW() - INTERVAL (4 + {}) WEEK, '%Y Week %u')) weekly LEFT JOIN (SELECT SUM(si.rounded_total * si.conversion_rate) AS total, DATE_FORMAT(si.posting_date, '%Y Week %u') AS week FROM `tabSales Invoice` si WHERE docstatus != 0 AND si.posting_date >= (SELECT DATE(NOW() - INTERVAL (4 + {}) WEEK)) AND si.posting_date <= (SELECT DATE(NOW() - INTERVAL (1 + {}) WEEK)) GROUP BY (week)) sales ON sales.week = weekly.week;".format(week, week, week, week, week, week),as_dict=1)
		raw_weekly = frappe.db.sql("SELECT SUM(rounded_total * conversion_rate) as total, WEEK(posting_date, 5) - WEEK(DATE_SUB(posting_date, INTERVAL DAYOFMONTH(posting_date) - 1 DAY), 5) as week_of_the_month FROM `tabSales Invoice` WHERE MONTH(posting_date) = MONTH(NOW()) - {} GROUP BY week_of_the_month ORDER BY week_of_the_month ASC;".format(interval),as_list=1)
		X = ['','','','','']
		Y = [0,0,0,0,0]

		for rw in raw_weekly:
			if (len(rw) == 2):
				if (rw[1] < len(Y)):
					Y[rw[1]] = rw[0]

		weekly = []
		n = len(X)
		for i in range(n):
			point = dict()
			point['X'] = str(n-i-1+1)
			point['Y'] = Y[n-i-1]
			weekly.append(point)
		data["weekly"] = weekly

	if (tipe == 'monthly' or tipe == ''):
		#monthly total sales
		monthly = frappe.db.sql("SELECT COALESCE(sales.total, 0) AS Y, monthly.month AS X FROM (SELECT DATE_FORMAT(NOW() - INTERVAL (1 + {}) MONTH, '%b \\'%y') AS month UNION ALL SELECT DATE_FORMAT(NOW() - INTERVAL (2 + {}) MONTH, '%b \\'%y') UNION ALL SELECT DATE_FORMAT(NOW() - INTERVAL (3 + {}) MONTH, '%b \\'%y') UNION ALL SELECT DATE_FORMAT(NOW() - INTERVAL (4 + {}) MONTH, '%b \\'%y') UNION ALL SELECT DATE_FORMAT(NOW() - INTERVAL (5 + {}) MONTH, '%b \\'%y') UNION ALL SELECT DATE_FORMAT(NOW() - INTERVAL (6 + {}) MONTH, '%b \\'%y')) monthly LEFT JOIN (SELECT SUM(si.rounded_total * si.conversion_rate) AS total, DATE_FORMAT(si.posting_date, '%b \\'%y') AS month FROM `tabSales Invoice` si WHERE docstatus != 0 AND si.posting_date >= (SELECT DATE(NOW() - INTERVAL (6 + {}) MONTH)) AND si.posting_date <= (SELECT DATE(NOW() - INTERVAL (1 + {}) MONTH)) GROUP BY (month)) sales ON sales.month = monthly.month;".format(month, month, month, month, month, month, month, month),as_dict=1)
		data["monthly"] = monthly

	return data


@frappe.whitelist(allow_guest=False)
def submit_sales_order(name):
	try:
		doc = frappe.get_doc("Sales Order", name)
		doc.docstatus = 1
		doc.status = "To Deliver and Bill"
		doc.save()
		return doc
	except:
		return error_format(sys.exc_info()[0])

@frappe.whitelist(allow_guest=False)
def cancel_sales_order(name):
	try:
		doc = frappe.get_doc("Sales Order", name)
		doc.docstatus = 2
		doc.status = "Cancelled"
		doc.save()
		return doc
	except:
		return error_format(sys.exc_info()[0])

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

	return data

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
										order_by="name",
										limit_page_length=100000
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
								"is_group":0,
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

