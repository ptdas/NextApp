# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from . import __version__ as app_version

app_name = "nextapp"
app_title = "Next App"
app_publisher = "PT. Digital Asia Solusindo"
app_description = "API Connector for ERPNext in Next App"
app_icon = "octicon octicon-file-directory"
app_color = "grey"
app_email = "digitalasiasolusindo@gmail.com"
app_license = "ptdas@copyright"

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/nextapp/css/nextapp.css"
# app_include_js = "/assets/nextapp/js/nextapp.js"

# include js, css files in header of web template
# web_include_css = "/assets/nextapp/css/nextapp.css"
# web_include_js = "/assets/nextapp/js/nextapp.js"

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
# doctype_js = {"doctype" : "public/js/doctype.js"}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
#	"Role": "home_page"
# }

# Website user home page (by function)
# get_website_user_home_page = "nextapp.utils.get_home_page"

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Installation
# ------------

# before_install = "nextapp.install.before_install"
# after_install = "nextapp.install.after_install"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "nextapp.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# Document Events
# ---------------
# Hook on document methods and events

doc_events = {
	"Leave Application": {
		"after_insert": "nextapp.app.nextess.notification.leave_application_approval",
		"on_submit": "nextapp.app.nextess.notification.leave_application_confirmation"
	},
	"Expense Claim": {
		"after_insert": "nextapp.app.nextess.notification.expense_claim_approval",
		"on_submit": "nextapp.app.nextess.notification.expense_claim_confirmation"
	} 
}

# Scheduled Tasks
# ---------------

# scheduler_events = {
	
# }

# Testing
# -------

# before_tests = "nextapp.install.before_tests"

# Overriding Whitelisted Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "nextapp.event.get_events"
# }

