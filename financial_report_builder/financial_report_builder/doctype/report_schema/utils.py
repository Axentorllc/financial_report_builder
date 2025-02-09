import re
from collections import defaultdict

import frappe


def build_formula_based_row(data: list, formula: str) -> dict:
    rows = parse_formula(formula)
    eval_locals = get_eval_locals(data, rows)
    # loop throw the eval locals and if the key not exist init it with 0
    for key, value in eval_locals.items():
        for row in rows:
            if row not in value:
                eval_locals[key].update({row: 0.0})
    row_based_on_formula = frappe._dict()
    for key, local_data in eval_locals.items():
        try:
            row_based_on_formula[key] = frappe.safe_eval(formula, None, local_data)
        except Exception as e:
            frappe.log_error(
                "Error evaluating formula",
                f"Formula: {formula}\nError: {str(e)} and local data = {local_data}",
            )
    return row_based_on_formula


def get_eval_locals(data: list, rows: list) -> dict:
    rows_used_in_formula = filter_dicts_by_label(data, "label", rows)
    eval_locals = defaultdict(dict)
    for row in rows_used_in_formula:
        for key, value in row.items():
            if isinstance(value, (int, float)) and key not in [
                "account",
                "indent",
                "label",
            ]:
                eval_locals[key].update({frappe.scrub(row["label"]).upper(): value})
    return eval_locals


def filter_dicts_by_label(dict_list, label, values):
    return [d for d in dict_list if frappe.scrub(d.get(label, "")).upper() in values]


def parse_formula(formula: str) -> list:
    # Regular expression to match variable names (assumes uppercase with underscores)
    pattern = r"[A-Z_]+"

    # Find all matches in the formula
    rows = re.findall(pattern, formula)

    return rows


def get_report_executions(data_dict, report_sources):
    report_executions = {}

    for report_source in report_sources:
        try:
            execute_function = frappe.get_doc("Report", report_source)
            columns, res_data = execute_function.get_data(data_dict)

            report_executions[report_source] = res_data
        except Exception as e:
            print(f"Error fetching or executing report {report_source}: {e}")

    return report_executions


def execute_report(report_source, data_dict, report_executions):
    if report_source not in report_executions:
        try:
            execute_function = frappe.get_doc("Report", report_source)
            columns, res_data = execute_function.get_data(data_dict)

            report_executions[report_source] = res_data
        except Exception as e:
            print(f"Error fetching or executing report {report_source}: {e}")


def bulid_row_based_on_accounts(node, data, report_executions, period_list):
    accounts_list = {row_account.account for row_account in node.accounts}

    rows = {"account": node.name, "indent": 0, "label": node.name}

    data.append(rows)
    res_data = report_executions[node.report_source]

    # Create a lookup dictionary for res_data
    res_data_lookup = {row.get("account"): row for row in res_data if "account" in row}

    for account in accounts_list:
        if account not in res_data_lookup:
            continue

        row = res_data_lookup[account]

        # Add the parent accounts
        processed_item = {
            "account": row.get("account"),
            "indent": 1,
        }

        for period in period_list:
            period_key = period.key
            processed_item[period_key] = row.get(period_key, 0.0)
            rows[period_key] = rows.get(period_key, 0.0) + processed_item[period_key]

        data.append(processed_item)

        # get childrens
        children = get_children(row.get("account"), res_data)

        # If there are children, add them with incremented indent
        if children:
            add_children_to_data(children, period_list, data)


def add_children_to_data(children, period_list, processed_items):
    for child in children:
        child_item = {
            "account": child.get("account"),
            "indent": 2,
        }
        for period in period_list:
            period_key = period.key
            child_item[period_key] = child.get(period_key, 0.0)
        processed_items.append(child_item)


def get_children(parent_account, rows):
    children = []
    rows_dict = {row.get("account"): row for row in rows}

    for row in rows_dict.values():
        if (
            row.get("parent_account") == parent_account
            and row.get("account") != parent_account
        ):
            children.append(row)

    return children
