# Copyright (c) 2024, Axentor LLC and contributors
# For license information, please see license.txt

import frappe
from frappe.utils.nestedset import NestedSet, get_root_of


class ReportSchema(NestedSet):
	nsm_parent_field = "parent_report_schema"

	def validate(self):
		if not self.parent_report_schema:
			root = get_root_of("Report Schema")
			if root:
				self.parent_report_schema = root

		# validate to force the report to be set based on the parent
		if self.parent_report_schema:
			report = frappe.db.get_value("Report Schema", self.parent_report_schema, "report")
			if report is not None:
				self.report = report

@frappe.whitelist()
def get_children(doctype, parent=None, company=None, is_root=False):
	fields = ["name as value", "is_group as expandable"]
	filters = {}

	if company == parent:
		filters["name"] = get_root_of("Report Schema")
	elif company:
		filters["parent_report_schema"] = parent
		filters["company"] = company
	else:
		filters["parent_report_schema"] = parent

	return frappe.get_all("Report Schema", fields=fields, filters=filters, order_by="name")

@frappe.whitelist()
def add_node():
	from frappe.desk.treeview import make_tree_args

	args = frappe.form_dict
	args = make_tree_args(**args)

	if args.parent_report_schema == args.company:
		args.parent_report_schema = None

	# validate to force the report to be set based on the parent
	if args.parent and not args.get("is_root"):
		if report := frappe.db.get_value("Report Schema", args.parent_report_schema, "report"):
			args["report"] = report

	frappe.get_doc(args).insert()
