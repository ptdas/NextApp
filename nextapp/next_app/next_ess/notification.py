from __future__ import unicode_literals
import frappe
from frappe.utils import get_site_name, get_request_session
import json

#firebase
def normalize_firebase_string(token):
	return token.replace("http://","").replace("https://","").replace(" ", "_").replace("-", "_").replace("(", "").replace(")", "").replace(".", "_").replace("@", "_").replace("-","_") 

def leave_application_approval(self, method):
	site_name = get_site_name(frappe.local.request.host)
	s = get_request_session()
	url = "https://fcm.googleapis.com/fcm/send"

	employee_user = frappe.db.sql("SELECT frappe_userid FROM `tabUser` WHERE email=(SELECT user_id FROM `tabEmployee` WHERE name='{}')".format(self.employee),as_dict=True)
	if len(employee_user) > 0:
		employee_user_id = employee_user[0]['frappe_userid']

		token = normalize_firebase_string(str(site_name) + "_" + employee_user_id)
		header = {"Authorization": "key=AAAAF7fHjjc:APA91bG80Es5LdTCs0fqtfktsyFHDR_r7q1QkQ3tObsgQqMbEngOhMJ1f6dJcP7mA0N0QIkBJuGIv9qGY_OFz7yC5NLChxu6Ci3ubYtB-yC6WBqbgD3iCB-1a89i9cEXHZ6hO0_EP0IZyTOp99a2uiDa6L1a433DCg","Content-Type": "application/json"}
		content = {
			"to":"/topics/{}".format(token),
			"data":
				{
					"subject":"{}".format(employee_user_id),
					"app":"next_ess",
				
					#notification
					"title_id":"leave_application_has_been_created",
					"body":"",

					#data
					"action":"leave_application_approval",
					"name":self.name,
					"leave_approver_name":self.leave_approver_name

				}
		}
		res = s.post(url=url,headers=header,data=json.dumps(content))

	
	leave_approver_user = employee_user = frappe.db.sql("SELECT frappe_userid FROM `tabUser` WHERE email='{}'".format(self.leave_approver),as_dict=True)
	if len(leave_approver_user) > 0:
		leave_approver_user_id = leave_approver_user[0]['frappe_userid']

		token = normalize_firebase_string(str(site_name) + "_" + leave_approver_user_id)
		header = {"Authorization": "key=AAAAF7fHjjc:APA91bG80Es5LdTCs0fqtfktsyFHDR_r7q1QkQ3tObsgQqMbEngOhMJ1f6dJcP7mA0N0QIkBJuGIv9qGY_OFz7yC5NLChxu6Ci3ubYtB-yC6WBqbgD3iCB-1a89i9cEXHZ6hO0_EP0IZyTOp99a2uiDa6L1a433DCg","Content-Type": "application/json"}
		content = {
			"to":"/topics/{}".format(token),
			"data":
				{
					"subject":"{}".format(leave_approver_user_id),
					"app":"next_ess",
				
					#notification
					"title_id":"leave_application_waiting_for_approve",
					"body":"",

					#data
					"action":"leave_application_approval",
					"name":self.name,
					"leave_approver_name":self.leave_approver_name

				}
		}
		res = s.post(url=url,headers=header,data=json.dumps(content))

	return "success"

def leave_application_confirmation(self, method):
	site_name = get_site_name(frappe.local.request.host)
	s = get_request_session()
	url = "https://fcm.googleapis.com/fcm/send"

	employee_user = frappe.db.sql("SELECT frappe_userid FROM `tabUser` WHERE email=(SELECT user_id FROM `tabEmployee` WHERE name='{}')".format(self.employee),as_dict=True)
	if len(employee_user) > 0:
		employee_user_id = employee_user[0]['frappe_userid']

		token = normalize_firebase_string(str(site_name) + "_" + employee_user_id)
		header = {"Authorization": "key=AAAAF7fHjjc:APA91bG80Es5LdTCs0fqtfktsyFHDR_r7q1QkQ3tObsgQqMbEngOhMJ1f6dJcP7mA0N0QIkBJuGIv9qGY_OFz7yC5NLChxu6Ci3ubYtB-yC6WBqbgD3iCB-1a89i9cEXHZ6hO0_EP0IZyTOp99a2uiDa6L1a433DCg","Content-Type": "application/json"}
		content = {
			"to":"/topics/{}".format(token),
			"data":
				{
					"subject":"{}".format(employee_user_id),
					"app":"next_ess",
				
					#notification
					"title_id":"leave_application_approval_received",
					"body":"",

					#data
					"action":"leave_application_confirmation",
					"name":self.name,
					"leave_approver_name":self.leave_approver_name,
					"status":self.status

				}
		}
		res = s.post(url=url,headers=header,data=json.dumps(content))

	
	leave_approver_user = employee_user = frappe.db.sql("SELECT frappe_userid FROM `tabUser` WHERE email='{}'".format(self.leave_approver),as_dict=True)
	if len(leave_approver_user) > 0:
		leave_approver_user_id = leave_approver_user[0]['frappe_userid']

		token = normalize_firebase_string(str(site_name) + "_" + leave_approver_user_id)
		header = {"Authorization": "key=AAAAF7fHjjc:APA91bG80Es5LdTCs0fqtfktsyFHDR_r7q1QkQ3tObsgQqMbEngOhMJ1f6dJcP7mA0N0QIkBJuGIv9qGY_OFz7yC5NLChxu6Ci3ubYtB-yC6WBqbgD3iCB-1a89i9cEXHZ6hO0_EP0IZyTOp99a2uiDa6L1a433DCg","Content-Type": "application/json"}
		content = {
			"to":"/topics/{}".format(token),
			"data":
				{
					"subject":"{}".format(leave_approver_user_id),
					"app":"next_ess",
				
					#notification
					"title_id":"leave_application_has_been_update",
					"body":"",

					#data
					"action":"leave_application_confirmation",
					"name":self.name,
					"leave_approver_name":self.leave_approver_name,
					"status":self.status

				}
		}
		res = s.post(url=url,headers=header,data=json.dumps(content))

	return "success"

def expense_claim_approval(self, method):
	site_name = get_site_name(frappe.local.request.host)
	s = get_request_session()
	url = "https://fcm.googleapis.com/fcm/send"

	employee_user = frappe.db.sql("SELECT frappe_userid FROM `tabUser` WHERE email=(SELECT user_id FROM `tabEmployee` WHERE name='{}')".format(self.employee),as_dict=True)
	if len(employee_user) > 0:
		employee_user_id = employee_user[0]['frappe_userid']

		exp_approver_name = self.exp_approver
		fetch_exp_approver = frappe.db.sql("SELECT full_name FROM `tabUser` WHERE email='{}'".format(self.exp_approver),as_dict=True)
		if len(fetch_exp_approver) > 0:
			exp_approver_name = fetch_exp_approver[0]['full_name']

		token = normalize_firebase_string(str(site_name) + "_" + employee_user_id)
		header = {"Authorization": "key=AAAAF7fHjjc:APA91bG80Es5LdTCs0fqtfktsyFHDR_r7q1QkQ3tObsgQqMbEngOhMJ1f6dJcP7mA0N0QIkBJuGIv9qGY_OFz7yC5NLChxu6Ci3ubYtB-yC6WBqbgD3iCB-1a89i9cEXHZ6hO0_EP0IZyTOp99a2uiDa6L1a433DCg","Content-Type": "application/json"}
		content = {
			"to":"/topics/{}".format(token),
			"data":
				{
					"subject":"{}".format(employee_user_id),
					"app":"next_ess",
				
					#notification
					"title_id":"expense_claim_has_been_created",
					"body":"",

					#data
					"action":"expense_claim_approval",
					"name":self.name,
					"exp_approver":self.exp_approver,
					"exp_approver_name":exp_approver_name

				}
		}
		res = s.post(url=url,headers=header,data=json.dumps(content))

	
	exp_approver_user = employee_user = frappe.db.sql("SELECT frappe_userid FROM `tabUser` WHERE email='{}'".format(self.exp_approver),as_dict=True)
	if len(exp_approver_user) > 0:
		exp_approver_user_id = exp_approver_user[0]['frappe_userid']

		token = normalize_firebase_string(str(site_name) + "_" + exp_approver_user_id)
		header = {"Authorization": "key=AAAAF7fHjjc:APA91bG80Es5LdTCs0fqtfktsyFHDR_r7q1QkQ3tObsgQqMbEngOhMJ1f6dJcP7mA0N0QIkBJuGIv9qGY_OFz7yC5NLChxu6Ci3ubYtB-yC6WBqbgD3iCB-1a89i9cEXHZ6hO0_EP0IZyTOp99a2uiDa6L1a433DCg","Content-Type": "application/json"}
		content = {
			"to":"/topics/{}".format(token),
			"data":
				{
					"subject":"{}".format(exp_approver_user_id),
					"app":"next_ess",
				
					#notification
					"title_id":"expense_claim_waiting_for_approve",
					"body":"",

					#data
					"action":"expense_claim_approval",
					"name":self.name,
					"exp_approver":self.exp_approver,
					"exp_approver_name":exp_approver_name

				}
		}
		res = s.post(url=url,headers=header,data=json.dumps(content))

	return "success"

def expense_claim_confirmation(self, method):
	site_name = get_site_name(frappe.local.request.host)
	s = get_request_session()
	url = "https://fcm.googleapis.com/fcm/send" 

	employee_user = frappe.db.sql("SELECT frappe_userid FROM `tabUser` WHERE email=(SELECT user_id FROM `tabEmployee` WHERE name='{}')".format(self.employee),as_dict=True)
	if len(employee_user) > 0:
		employee_user_id = employee_user[0]['frappe_userid']

		exp_approver_name = self.exp_approver
		fetch_exp_approver = frappe.db.sql("SELECT full_name FROM `tabUser` WHERE email='{}'".format(self.exp_approver),as_dict=True)
		if len(fetch_exp_approver) > 0:
			exp_approver_name = fetch_exp_approver[0]['full_name']

		token = normalize_firebase_string(str(site_name) + "_" + employee_user_id)
		header = {"Authorization": "key=AAAAF7fHjjc:APA91bG80Es5LdTCs0fqtfktsyFHDR_r7q1QkQ3tObsgQqMbEngOhMJ1f6dJcP7mA0N0QIkBJuGIv9qGY_OFz7yC5NLChxu6Ci3ubYtB-yC6WBqbgD3iCB-1a89i9cEXHZ6hO0_EP0IZyTOp99a2uiDa6L1a433DCg","Content-Type": "application/json"}
		content = {
			"to":"/topics/{}".format(token),
			"data":
				{
					"subject":"{}".format(employee_user_id),
					"app":"next_ess",
				
					#notification
					"title_id":"expense_claim_approval_received",
					"body":"",

					#data
					"action":"expense_claim_confirmation",
					"name":self.name,
					"exp_approver":self.exp_approver,
					"exp_approver_name":exp_approver_name,
					"approval_status":self.approval_status

				}
		}
		res = s.post(url=url,headers=header,data=json.dumps(content))

	
	exp_approver_user = employee_user = frappe.db.sql("SELECT frappe_userid FROM `tabUser` WHERE email='{}'".format(self.exp_approver),as_dict=True)
	if len(exp_approver_user) > 0:
		exp_approver_user_id = exp_approver_user[0]['frappe_userid']

		token = normalize_firebase_string(str(site_name) + "_" + exp_approver_user_id)
		header = {"Authorization": "key=AAAAF7fHjjc:APA91bG80Es5LdTCs0fqtfktsyFHDR_r7q1QkQ3tObsgQqMbEngOhMJ1f6dJcP7mA0N0QIkBJuGIv9qGY_OFz7yC5NLChxu6Ci3ubYtB-yC6WBqbgD3iCB-1a89i9cEXHZ6hO0_EP0IZyTOp99a2uiDa6L1a433DCg","Content-Type": "application/json"}
		content = {
			"to":"/topics/{}".format(token),
			"data":
				{
					"subject":"{}".format(exp_approver_user_id),
					"app":"next_ess",
				
					#notification
					"title_id":"expense_claim_has_been_update",
					"body":"",

					#data
					"action":"expense_claim_confirmation",
					"name":self.name,
					"exp_approver":self.exp_approver,
					"exp_approver_name":exp_approver_name,
					"approval_status":self.approval_status

				}
		}
		res = s.post(url=url,headers=header,data=json.dumps(content))

	return "success"