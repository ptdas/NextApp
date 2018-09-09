from __future__ import unicode_literals
import frappe

#VALIDATION NEXT SALES METHOD
def has_product_bundle(item_code):
	return frappe.db.sql("""select name from `tabProduct Bundle`
		where new_item_code=%s and docstatus != 2""", item_code)

def product_bundle_has_stock_item(product_bundle):
	"""Returns true if product bundle has stock item"""
	ret = len(frappe.db.sql("""select i.name from tabItem i, `tabProduct Bundle Item` pbi
		where pbi.parent = %s and pbi.item_code = i.name and i.is_stock_item = 1""", product_bundle))
	return ret

def validate_warehouse(items):
	for d in items:
		if (frappe.db.get_value("Item", d.item_code, "is_stock_item") == 1 or
			(has_product_bundle(d.item_code) and product_bundle_has_stock_item(d.item_code))) \
			and not d.warehouse and not cint(d.delivered_by_supplier):
			return "Delivery warehouse required for stock item {0}".format(d.item_code)
	return ""