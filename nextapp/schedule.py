from __future__ import unicode_literals
import frappe
from frappeclient import FrappeClient
from frappe.utils import get_site_name, get_request_session
import json
from base import normalize_firebase_string

#daily summaries
# @frappe.whitelist(allow_guest=True)
# def ddebcad():
# 	site_name = get_site_name(frappe.local.request.host)
# 	user = "salesdemo@force.com"

# 	fetch_sales_order_count = frappe.db.sql("SELECT COUNT(*) FROM `tabSales Order` WHERE status IN ('To Bill','To Deliver & Bill') AND docstatus = 1 AND owner='{}'".format(user),as_list=True)
# 	sales_order_to_bill = 0
# 	if (len(fetch_sales_order_count) > 0):
# 		sales_order_to_bill = fetch_sales_order_count[0][0]

# 	fetch_sales_invoice_count = frappe.db.sql("SELECT COUNT(*) FROM `tabSales Invoice` WHERE status IN ('Overdue') AND docstatus = 1",as_list=True)
# 	sales_invoice_overdue = 0
# 	if (len(fetch_sales_invoice_count) > 0):
# 		sales_invoice_overdue = fetch_sales_invoice_count[0][0]


# 	s = get_request_session()
# 	url = "https://fcm.googleapis.com/fcm/send"


# 	token = normalize_firebase_string(str(site_name) + "_" + user)
# 	header = {"Authorization": "key=AAAAF7fHjjc:APA91bG80Es5LdTCs0fqtfktsyFHDR_r7q1QkQ3tObsgQqMbEngOhMJ1f6dJcP7mA0N0QIkBJuGIv9qGY_OFz7yC5NLChxu6Ci3ubYtB-yC6WBqbgD3iCB-1a89i9cEXHZ6hO0_EP0IZyTOp99a2uiDa6L1a433DCg","Content-Type": "application/json"}
# 	content = {
# 		"to":"/topics/{}".format(token),
# 		"data":
# 			{
# 				"subject":"{}".format(user),
				
# 				#notification
# 				"title_id":"good_morning",

# 				#data
# 				"action":"daily_summaries",
# 				"sales_order_to_bill":sales_order_to_bill,
# 				"sales_invoice_overdue":sales_invoice_overdue

# 			}
# 	}
# 	res = s.post(url=url,headers=header,data=json.dumps(content))

# 	return res
