import frappe
import sys

@frappe.whitelist(allow_guest=True)
def test_validation():
	try:
		frappe.throw("baca aku")
	except:
		return sys.exc_info()[0]


@frappe.whitelist(allow_guest=True)
def validate_get_list(doctype):
	try:
		tryFetch = frappe.get_list(doctype)
		return "success"
	except:
		return sys.exc_info()[0]

@frappe.whitelist(allow_guest=True)
def get_list(doctype):
	try:
		tryFetch = frappe.get_list(doctype)
		return "success"
	except:
		return sys.exc_info()[0]

