from __future__ import unicode_literals
import frappe
import json
import hashlib
import time
import file_manager
from file_manager import upload
from base import validate_method
from frappe.utils import get_fullname, get_request_session
from frappe import utils
import sys

# ERPNEXT
from erpnext.stock.get_item_details import get_item_details

# CUSTOM METHOD
from app.helper import *
from app.nextsales.validation import *
from app.nextess.validation import * 
from validation import *

LIMIT_PAGE = 20
API_VERSION = 1.9

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
								"delivery_status": stat,
								"docstatus":1,
								"status":("not in",["Draft", "Closed", "Completed", "Cancelled"]) 
							})
		dataCount[stat] = len(fetch)

	#sales order billing status
	status = ['Not Billed','Fully Billed','Partly Billed']
	for stat in status:
		fetch = frappe.get_list("Sales Order", 
							filters = 
							{
								"billing_status": stat,
								"docstatus":1,
								"status":("not in",["Draft", "Closed", "Completed", "Cancelled"])
							})
		dataCount[stat] = len(fetch)

	so_data = frappe.get_list("Sales Order")
	dataCount['Total'] = len(so_data)


	#invoice
	status = ['Overdue','Unpaid','Paid','Return','Credit Note Issued','Cancelled']
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
def get_sales_by_person():
	data = dict()
	today = utils.today()
	data["sales_person_all_time"] = frappe.db.sql("SELECT st.sales_person AS 'person_name', SUM(si.rounded_total * si.conversion_rate) * st.allocated_percentage / 100 AS total_sales FROM `tabSales Invoice` si JOIN `tabSales Team` st ON si.name = st.parent WHERE si.docstatus = 1 GROUP BY st.sales_person ORDER BY total_sales DESC", as_dict=True)
	data["sales_person_day"] = frappe.db.sql("SELECT st.sales_person AS 'person_name', SUM(si.rounded_total * si.conversion_rate) * st.allocated_percentage / 100 AS total_sales FROM `tabSales Invoice` si JOIN `tabSales Team` st ON si.name = st.parent WHERE si.docstatus = 1 AND si.posting_date = '{}' GROUP BY st.sales_person ORDER BY total_sales DESC".format(today), as_dict=True)
	data["sales_person_month"] = frappe.db.sql("SELECT st.sales_person AS 'person_name', SUM(si.rounded_total * si.conversion_rate) * st.allocated_percentage / 100 AS total_sales FROM `tabSales Invoice` si JOIN `tabSales Team` st ON si.name = st.parent WHERE si.docstatus = 1 AND DATE_FORMAT(si.posting_date, '%Y-%m') = DATE_FORMAT('{}', '%Y-%m') GROUP BY st.sales_person ORDER BY total_sales DESC".format(today), as_dict=True)
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

	today = frappe.utils.today()

	if (tipe == 'daily' or tipe == ''):

		#daily total sales
		daily = frappe.db.sql("SELECT COALESCE(sales.total, 0) AS Y, daily.day AS X FROM (SELECT DATE_FORMAT('{}' - INTERVAL (0 + {}) DAY,'%e %b') AS day UNION ALL SELECT DATE_FORMAT('{}' - INTERVAL (1 + {}) DAY,'%e %b') UNION ALL SELECT DATE_FORMAT('{}' - INTERVAL (2 + {}) DAY,'%e %b') UNION ALL SELECT DATE_FORMAT('{}' - INTERVAL (3 + {}) DAY,'%e %b') UNION ALL SELECT DATE_FORMAT('{}' - INTERVAL (4 + {}) DAY,'%e %b') UNION ALL SELECT DATE_FORMAT('{}' - INTERVAL (5 + {}) DAY,'%e %b') UNION ALL SELECT DATE_FORMAT('{}' - INTERVAL (6 + {}) DAY,'%e %b')) daily LEFT JOIN (SELECT SUM(si.rounded_total * si.conversion_rate) AS total, DATE_FORMAT(si.posting_date,'%e %b') as posting_date FROM `tabSales Invoice` si WHERE docstatus != 0 AND si.posting_date >= (SELECT ('{}' - INTERVAL (6 + {}) DAY)) AND si.posting_date <= (SELECT ('{}' - INTERVAL (0 + {}) DAY)) GROUP BY posting_date) sales ON sales.posting_date = daily.day;".format(today, day, today, day, today, day, today, day, today, day, today, day, today, day, today, day, today, day),as_dict=1)
		# raw_daily = frappe.db.sql("SELECT SUM(rounded_total * conversion_rate) as total, DATEDIFF(posting_date, '2018-09-01') FROM `tabSales Invoice` WHERE posting_date >= '2018-09-01' AND posting_date <= '2018-09-07' GROUP BY posting_date")
		data["daily"] = daily

	if (tipe == 'weekly' or tipe == ''):
		#weekly total sales
		# weekly = frappe.db.sql("SELECT COALESCE(sales.total, 0) AS Y, weekly.week AS X FROM (SELECT DATE_FORMAT(NOW() - INTERVAL (1 + {}) WEEK, '%Y Week %u') AS week UNION ALL SELECT DATE_FORMAT(NOW() - INTERVAL (2 + {}) WEEK, '%Y Week %u') UNION ALL SELECT DATE_FORMAT(NOW() - INTERVAL (3 + {}) WEEK, '%Y Week %u') UNION ALL SELECT DATE_FORMAT(NOW() - INTERVAL (4 + {}) WEEK, '%Y Week %u')) weekly LEFT JOIN (SELECT SUM(si.rounded_total * si.conversion_rate) AS total, DATE_FORMAT(si.posting_date, '%Y Week %u') AS week FROM `tabSales Invoice` si WHERE docstatus != 0 AND si.posting_date >= (SELECT DATE(NOW() - INTERVAL (4 + {}) WEEK)) AND si.posting_date <= (SELECT DATE(NOW() - INTERVAL (1 + {}) WEEK)) GROUP BY (week)) sales ON sales.week = weekly.week;".format(week, week, week, week, week, week),as_dict=1)
		raw_weekly = frappe.db.sql("SELECT SUM(rounded_total * conversion_rate) as total, WEEK(posting_date, 5) - WEEK(DATE_SUB(posting_date, INTERVAL DAYOFMONTH(posting_date) - 1 DAY), 5) as week_of_the_month FROM `tabSales Invoice` WHERE MONTH(posting_date) = MONTH('{}') - {} GROUP BY week_of_the_month ORDER BY week_of_the_month ASC;".format(today,interval),as_list=1)
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
		monthly = frappe.db.sql("SELECT COALESCE(sales.total, 0) AS Y, monthly.month AS X FROM (SELECT DATE_FORMAT('{}' - INTERVAL (0 + {}) MONTH, '%b \\'%y') AS month UNION ALL SELECT DATE_FORMAT('{}' - INTERVAL (1 + {}) MONTH, '%b \\'%y') UNION ALL SELECT DATE_FORMAT('{}' - INTERVAL (2 + {}) MONTH, '%b \\'%y') UNION ALL SELECT DATE_FORMAT('{}' - INTERVAL (3 + {}) MONTH, '%b \\'%y') UNION ALL SELECT DATE_FORMAT('{}' - INTERVAL (4 + {}) MONTH, '%b \\'%y') UNION ALL SELECT DATE_FORMAT('{}' - INTERVAL (5 + {}) MONTH, '%b \\'%y')) monthly LEFT JOIN (SELECT SUM(si.rounded_total * si.conversion_rate) AS total, DATE_FORMAT(si.posting_date, '%b \\'%y') AS month FROM `tabSales Invoice` si WHERE docstatus != 0 AND si.posting_date >= (SELECT DATE('{}' - INTERVAL (5 + {}) MONTH)) AND si.posting_date <= (SELECT DATE('{}' - INTERVAL (0 + {}) MONTH)) GROUP BY (month)) sales ON sales.month = monthly.month;".format(today, month, today, month, today, month, today, month, today, month, today, month, today, month, today, month),as_dict=1)
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
		data_sales = frappe.db.sql("SELECT * FROM `tabSales Team` WHERE parent='{}'".format(d['name']),as_dict=1)
		d['sales_persons'] = data_sales
		
		fetchTotalSales  = frappe.db.sql("SELECT COALESCE(SUM(rounded_total * conversion_rate),0) FROM `tabSales Invoice` WHERE docstatus = 1 AND customer = '{}' AND posting_date BETWEEN DATE(NOW()) - INTERVAL {} DAY AND NOW()".format(d["name"],last_day))
		if (len(fetchTotalSales) > 0):
			d["last_total_sales"] = fetchTotalSales[0][0]

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
standard_fields_of_sales_order = ["customer_section","column_break0","title","naming_series","customer","customer_name","order_type","column_break1","amended_from","company","transaction_date","delivery_date","po_no","po_date","tax_id","contact_info","customer_address","address_display","contact_person","contact_display","contact_mobile","contact_email","col_break46","shipping_address_name","shipping_address","customer_group","territory","currency_and_price_list","currency","conversion_rate","column_break2","selling_price_list","price_list_currency","plc_conversion_rate","ignore_pricing_rule","items_section","items","section_break_31","column_break_33a","base_total","base_net_total","column_break_33","total","net_total","total_net_weight","taxes_section","taxes_and_charges","column_break_38","shipping_rule","section_break_40","taxes","sec_tax_breakup","other_charges_calculation","section_break_43","base_total_taxes_and_charges","column_break_46","total_taxes_and_charges","section_break_48","apply_discount_on","base_discount_amount","column_break_50","additional_discount_percentage","discount_amount","totals","base_grand_total","base_rounding_adjustment","base_rounded_total","base_in_words","column_break3","grand_total","rounding_adjustment","rounded_total","in_words","advance_paid","packing_list","packed_items","payment_schedule_section","payment_terms_template","payment_schedule","terms_section_break","tc_name","terms","more_info","project","party_account_currency","column_break_77","source","campaign","printing_details","language","letter_head","column_break4","select_print_heading","group_same_items","section_break_78","status","delivery_status","per_delivered","column_break_81","per_billed","billing_status","sales_team_section_break","sales_partner","column_break7","commission_rate","total_commission","section_break1","sales_team","subscription_section","from_date","to_date","column_break_108","subscription"]
@frappe.whitelist(allow_guest=False)
def get_field_custom_sales_order():
	standard_fields = frappe.get_meta('Sales Order')

	raw_fields = standard_fields.fields
	fields = []
	for rf in raw_fields:
		if (rf.fieldname not in standard_fields_of_sales_order):
			if (rf.fieldtype == 'Data'):
				fields.append(rf.fieldname)


	return fields



@frappe.whitelist(allow_guest=False)
def get_sales_order_naming_series():
	so_meta = frappe.get_meta('Sales Order')

	
	raw_fields = so_meta.fields
	fields = []
	for rf in raw_fields:
		if (rf.fieldname == 'naming_series'):
			naming_series = rf.options.split('\n')
			data = []
			for ns in naming_series:
				dataNamingSeries = {'naming_series':ns}
				data.append(dataNamingSeries)

			return data		
			

	return []



@frappe.whitelist(allow_guest=False)
def get_sales_order(status='',query='',sort='',delivery_status='%',billing_status='%',page=0):
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
								f: ("LIKE", "%{}%".format(query)),
								"delivery_status": ("LIKE",delivery_status),
								"billing_status": ("LIKE",billing_status)
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

@frappe.whitelist(allow_guest=False)
def update_stock_sales_order(so_name,customer,selling_price_list,price_list_currency,transaction_date,company, plc_conversion_rate, conversion_rate):
	data_sales_item = frappe.db.sql("SELECT * FROM `tabSales Order Item` WHERE parent='{}'".format(so_name),as_dict=1)
	for dsi in data_sales_item:
		args = {
			"item_code": dsi['item_code'],
			"warehouse": dsi['warehouse'],
			"company": company,
			"customer": customer,
			"conversion_rate": dsi['conversion_factor'],
			"selling_price_list": selling_price_list,
			"price_list_currency": price_list_currency,
			"plc_conversion_rate": plc_conversion_rate,
			"doctype": "Sales Order",
			"transaction_date": transaction_date,
			"conversion_rate": conversion_rate,
			"ignore_pricing_rule": 1
		}

		item_details = get_item_details(args)
		frappe.db.sql("UPDATE `tabSales Order Item` SET actual_qty={}, project_qty={}, projected_qty={}, stock_qty={} WHERE name='{}'".format(item_details['actual_qty'],item_details['projected_qty'],item_details['projected_qty'],item_details['stock_qty'],dsi['name']))
		frappe.db.commit()
		
	return data_sales_item


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
										order_by="modified DESC",
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
								"is_group":0,
								"company":company,
								f: ("LIKE", "%{}%".format(query))
							},
							order_by="modified DESC",
							limit_page_length=LIMIT_PAGE,
							limit_start=page)
		temp_seen, result_list = distinct(seen,data_filter)
		seen = temp_seen
		data.extend(result_list)
	return data

