import frappe
import re
from collections import defaultdict


def build_formula_based_row(data: list, formula: str) -> dict:
    rows = parse_formula(formula)
    eval_locals = get_eval_locals(data, rows)
    row_based_on_formula = frappe._dict()
    for key, local_data in eval_locals.items():
        row_based_on_formula[key] = frappe.safe_eval(formula, None, local_data)
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



def get_report_executions(data_dict):
    report_executions = {}
    financial_reports = ['Profit and Loss Statement', 'Balance Sheet','Mapped Cash Flow' ]

    for report_source in set(financial_reports):
        try:
            execute_function = frappe.get_doc('Report', report_source)
            columns, res_data = execute_function.get_data(data_dict)

            report_executions[report_source] = res_data
        except Exception as e:
            print(f"Error fetching or executing report {report_source}: {e}")
    
    return report_executions

def execute_report(report_source,data_dict,report_executions):

    if report_source not in report_executions:
        try:
            execute_function = frappe.get_doc('Report', report_source)
            columns, res_data = execute_function.get_data(data_dict)

            report_executions[report_source] = res_data
        except Exception as e:
            print(f"Error fetching or executing report {report_source}: {e}")
    

    