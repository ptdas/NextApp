# -*- coding: utf-8 -*-
# Copyright (c) 2017, Bobzz and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
import os, base64, re
import hashlib
import mimetypes
from datetime import datetime
from frappe.utils import get_hook_method, get_files_path, random_string, encode, cstr, call_hook_method, cint
from frappe import _
from frappe import conf
from copy import copy
from six.moves.urllib.parse import unquote
from six import text_type


#firebase
def normalize_firebase_string(token):
	return token.replace("http://","").replace("https://","").replace(" ", "_").replace("-", "_").replace("(", "").replace(")", "").replace(".", "_").replace("@", "_").replace("-","_") 


def validate_method(request,allow):
	response={}

	if request not in allow:
		response["code"] = 400
		response["message"] = "Invalid Request Method Type"
		response["data"] = ""
		
		return response

	return True

def validate_param_value(value,allow):
	response={}

	if value not in allow:
		response["code"] = 400
		response["message"] = "Invalid value allowed for parameter"
		response["data"] = ""
		
		return response

	return True

def validate_dict_exist(keys,ary,required=""):
	response={}
	isPass = True

	for key in keys:
		if key not in ary:
			isPass = False
			break

	if isPass == False:
		response["code"] = 400
		response["message"] = "Missing Required Parameter: "+required+""
		response["data"] = ""

		return response

	return True

def validate_time_format(value,timeformat,required=""):
	response={}

	for val in value:
	    try:
	        datetime.strptime(val, timeformat)
	    except ValueError as e:
	    	return False

	return True


def validate_param_exist(value, required=""):
	response={}
	isPass = True

	for val in value:
		if val == None:
			isPass = False
			break

	if isPass == False:
		response["code"] = 400
		response["message"] = "Missing Required Parameter: "+required+""
		response["data"] = ""

		return response

	return True

def save_uploaded(dt, dn, folder, is_private):
	fname, content = get_uploaded_content()
	if content:
		return save_file(fname, content, dt, dn, folder, is_private=is_private);
	else:
		raise Exception

def get_uploaded_content():
	# should not be unicode when reading a file, hence using frappe.form
	if 'filedata' in frappe.form_dict:
		if "," in frappe.form_dict.filedata:
			frappe.form_dict.filedata = frappe.form_dict.filedata.rsplit(",", 1)[1]
		frappe.uploaded_content = base64.b64decode(frappe.form_dict.filedata)
		frappe.uploaded_filename = frappe.form_dict.filename
		return frappe.uploaded_filename, frappe.uploaded_content
	else:
		frappe.msgprint(_('No file attached'))
		return None, None

def save_file(fname, content, dt, dn, folder=None, decode=False, is_private=0):
	if decode:
		if isinstance(content, text_type):
			content = content.encode("utf-8")

		if "," in content:
			content = content.split(",")[1]
		content = base64.b64decode(content)

	file_size = check_max_file_size(content)
	content_hash = get_content_hash(content)
	content_type = mimetypes.guess_type(fname)[0]
	fname = get_file_name(fname, content_hash[-6:])
	file_data = get_file_data_from_hash(content_hash, is_private=is_private)
	if not file_data:
		call_hook_method("before_write_file", file_size=file_size)

		write_file_method = get_hook_method('write_file', fallback=save_file_on_filesystem)
		file_data = write_file_method(fname, content, content_type=content_type, is_private=is_private)
		file_data = copy(file_data)

	file_data.update({
		"doctype": "File",
		"attached_to_doctype": dt,
		"attached_to_name": dn,
		"folder": folder,
		"file_size": file_size,
		"content_hash": content_hash,
		"is_private": is_private
	})

	f = frappe.get_doc(file_data)
	f.flags.ignore_permissions = True
	try:
		f.insert()
	except frappe.DuplicateEntryError:
		return frappe.get_doc("File", f.duplicate_entry)

	return f

def check_max_file_size(content):
	max_file_size = get_max_file_size()
	file_size = len(content)

	if file_size > max_file_size:
		frappe.msgprint(_("File size exceeded the maximum allowed size of {0} MB").format(
			max_file_size / 1048576),
			raise_exception=MaxFileSizeReachedError)

	return file_size

def get_max_file_size():
	return conf.get('max_file_size') or 10485760

def get_content_hash(content):
	return hashlib.md5(content).hexdigest()

def get_file_data_from_hash(content_hash, is_private=0):
	for name in frappe.db.sql_list("select name from `tabFile` where content_hash=%s and is_private=%s", (content_hash, is_private)):
		b = frappe.get_doc('File', name)
		return {k:b.get(k) for k in frappe.get_hooks()['write_file_keys']}
	return False

def get_file_name(fname, optional_suffix):
	# convert to unicode
	fname = cstr(fname)

	n_records = frappe.db.sql("select name from `tabFile` where file_name=%s", fname)
	if len(n_records) > 0 or os.path.exists(encode(get_files_path(fname))):
		f = fname.rsplit('.', 1)
		if len(f) == 1:
			partial, extn = f[0], ""
		else:
			partial, extn = f[0], "." + f[1]
		return '{partial}{suffix}{extn}'.format(partial=partial, extn=extn, suffix=optional_suffix)
	return fname

def save_url(file_url, filename, dt, dn, folder, is_private):
	# if not (file_url.startswith("http://") or file_url.startswith("https://")):
	# 	frappe.msgprint("URL must start with 'http://' or 'https://'")
	# 	return None, None

	file_url = unquote(file_url)

	f = frappe.get_doc({
		"doctype": "File",
		"file_url": file_url,
		"file_name": filename,
		"attached_to_doctype": dt,
		"attached_to_name": dn,
		"folder": folder,
		"is_private": is_private
	})
	f.flags.ignore_permissions = True
	try:
		f.insert();
	except frappe.DuplicateEntryError:
		return frappe.get_doc("File", f.duplicate_entry)
	return f
	
def save_file_on_filesystem(fname, content, content_type=None, is_private=0):
	fpath = write_file(content, fname, is_private)

	if is_private:
		file_url = "/private/files/{0}".format(fname)
	else:
		file_url = "/files/{0}".format(fname)

	return {
		'file_name': os.path.basename(fpath),
		'file_url': file_url
	}