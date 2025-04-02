// Copyright (c) 2025, Axentor LLC and contributors
// For license information, please see license.txt

frappe.query_reports["Mapped Profit and Loss Demo"] = {
	"filters": [

	]
};

frappe.query_reports["Mapped Profit and Loss Demo"] = $.extend({}, erpnext.financial_statements);
erpnext.utils.add_dimensions("Mapped Profit and Loss Demo", 10);
frappe.query_reports["Mapped Profit and Loss Demo"]["filters"].push(
	{
		"fieldname": "include_default_book_entries",
		"label": __("Include Default Book Entries"),
		"fieldtype": "Check",
		"default": 1
	},
	{
		"fieldname": "accumulated_values",
		"label": __("Accumulated Values"),
		"fieldtype": "Check",
		"default": 0
	},
	
);