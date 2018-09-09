def distinct(seen, new_list):
	temp_seen = seen
	result_list = []
	for nl in new_list:
		if not nl['name'] in temp_seen:
			result_list.append(nl)
			temp_seen += nl['name'] + ";"
	return (temp_seen, result_list)