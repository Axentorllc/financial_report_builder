# Copyright (c) 2025, Axentor LLC and contributors
# For license information, please see license.txt

import frappe
from erpnext.accounts.report.financial_statements import get_columns, get_period_list

from financial_report_builder.financial_report_builder.doctype.report_schema.report_schema_view import (
    get_nodes,
)
from financial_report_builder.financial_report_builder.doctype.report_schema.utils import (
    build_formula_based_row,
    bulid_row_based_on_accounts,
    get_report_executions,
)


def execute(filters=None):
    period_list = get_period_list(
        filters.from_fiscal_year,
        filters.to_fiscal_year,
        filters.period_start_date,
        filters.period_end_date,
        filters.filter_based_on,
        filters.periodicity,
        company=filters.company,
    )
    nodes, report_sources = get_nodes(
        "Mapped Profit and Loss Schema"
    )  # get nodes docs from the report schema

    columns = get_columns(
        filters.periodicity, period_list, filters.accumulated_values, filters.company
    )

    data = get_data(period_list, filters.copy(), nodes, report_sources)

    return columns, data


def get_data(period_list: list, filters: dict, nodes: list, report_sources: set):
    data = []

    report_executions = get_report_executions(filters, report_sources)

    for node in nodes:
        if node.accounts:
            bulid_row_based_on_accounts(node, data, report_executions, period_list)

        if node.row_based_on_formula:
            row = build_formula_based_row(data, node.formula)
            row.update(
                {
                    "account": node.label,
                    "account_name": node.label,
                    "label": node.label,
                    "indent": 0,
                }
            )

            data.append(row)

        if node.use_custom_method:
            # get method using frappe.get_attr and give it the params
            frappe.get_attr(node.method)(
                data, filters, node, period_list, report_executions
            )

    for node in nodes:
        if node.hide_from_report:
            data = [row for row in data if row.get("label") != node.label]

    return data
