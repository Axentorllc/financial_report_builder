# Copyright (c) 2024, Axentor LLC and contributors
# For license information, please see license.txt

import frappe
from frappe.utils.nestedset import NestedSet, get_root_of

from .utils import parse_formula


class ReportSchema(NestedSet):
    nsm_parent_field = "parent_report_schema"

    def validate(self):
        if not self.parent_report_schema:
            root = get_root_of("Report Schema")
            if root:
                self.parent_report_schema = root

        # validate to force the report to be set based on the parent
        if self.parent_report_schema:
            report = frappe.db.get_value(
                "Report Schema", self.parent_report_schema, "report"
            )
            if report is not None:
                self.report = report
            if self.name == "All Reports Schemas":
                self.report = None

        self.validate_report()

        if self.row_based_on_formula:
            self.validate_that_rows_in_formula_exists()

    def validate_report(self):
        if self.parent_report_schema and not self.report:
            frappe.throw("Report is mandatory for non-root nodes")

    def validate_that_rows_in_formula_exists(self):
        """
        Validate that all rows referenced in formula actually exist in the schema.

        NOTE: We no longer enforce that formula references have lower row_index.
        The dependency graph will determine correct execution order automatically.
        """
        self.formula = self.formula.upper()
        rows_used_in_formula = parse_formula(self.formula)

        all_nodes = frappe.get_all(
            "Report Schema",
            filters=[["report", "=", self.report], ["report", "is", "set"]],
            pluck="name"
        )

        # Convert to uppercase for case-insensitive comparison
        available_rows = {frappe.scrub(node).upper() for node in all_nodes}

        missing_rows = []
        for row in rows_used_in_formula:
            if row not in available_rows:
                missing_rows.append(row)

        if missing_rows:
            throw_msg = ""
            for row in missing_rows:
                throw_msg += f"- Row {frappe.bold(row)} not found in report schema<br>"

            help_msg = "<hr><span class='text-muted'>Please add the missing rows to the report schema.</span>"
            frappe.throw(throw_msg + help_msg)


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

    return frappe.get_all(
        "Report Schema", fields=fields, filters=filters, order_by="name"
    )


@frappe.whitelist()
def add_node():
    from frappe.desk.treeview import make_tree_args

    args = frappe.form_dict
    args = make_tree_args(**args)

    if args.parent_report_schema == args.company:
        args.parent_report_schema = None

    # validate to force the report to be set based on the parent
    if args.parent and not args.get("is_root"):
        if report := frappe.db.get_value(
            "Report Schema", args.parent_report_schema, "report"
        ):
            args["report"] = report

    frappe.get_doc(args).insert()
