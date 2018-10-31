import frappe

@frappe.whitelist(allow_guest=False)
def get_meta(doctype):
	return frappe.get_meta(doctype)