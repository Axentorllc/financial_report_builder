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

    rows = {"account": node.label, "indent": 0, "label": node.label, "node_label": node.label}

    res_data = report_executions[node.report_source]

    res_data_lookup = {row.get("account"): row for row in res_data if "account" in row}

    for account in accounts_list:
        if account not in res_data_lookup:
            continue

        row = res_data_lookup[account]

        # Sum values into the header row
        for period in period_list:
            period_key = period.key
            rows[period_key] = rows.get(period_key, 0.0) + row.get(period_key, 0.0)

    data.append(rows)

    # If show_only_node_header is checked, skip adding account details
    if node.get("show_only_node_header"):
        return

    for account in accounts_list:
        if account not in res_data_lookup:
            continue

        row = res_data_lookup[account]

        processed_item = {
            "account": row.get("account"),
            "indent": 1,
            "node_label": node.label,  # Track which node this account belongs to
        }

        for period in period_list:
            period_key = period.key
            processed_item[period_key] = row.get(period_key, 0.0)

        data.append(processed_item)

        children = get_children(row.get("account"), res_data)

        if children:
            add_children_to_data(children, period_list, data, node.label)


def add_children_to_data(children, period_list, processed_items, node_label=None):
    for child in children:
        child_item = {
            "account": child.get("account"),
            "indent": 2,
        }
        if node_label:
            child_item["node_label"] = node_label  # Track which node this child belongs to
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


# ============================================================================
# DEPENDENCY GRAPH FUNCTIONS
# ============================================================================


def extract_dependencies_from_formula(formula: str, nodes: list) -> list:
    """
    Extract row labels that a formula depends on.

    Example:
        formula = "GROSS_REVENUE - COST_OF_SALES - OPERATING_EXPENSES"
        returns: ["Gross Revenue", "Cost of Sales", "Operating Expenses"]
        (returns ORIGINAL node labels, not uppercase)

    Args:
        formula: Formula string with uppercase row references
        nodes: List of all Report Schema nodes in this report

    Returns:
        List of original node labels this formula references
    """
    label_map = {}
    for node in nodes:
        label_upper = frappe.scrub(node.label).upper()
        label_map[label_upper] = node.label

    rows_used = parse_formula(formula)

    dependencies = []
    for row in rows_used:
        if row in label_map:
            dependencies.append(label_map[row])

    return dependencies


def build_execution_graph(nodes: list) -> dict:
    """
    Build a dependency graph showing which nodes depend on which.

    Returns a dictionary where:
    - key: node label
    - value: list of nodes it depends on

    Example:
        {
            "REVENUE": [],
            "EXPENSES": [],
            "PROFIT": ["REVENUE", "EXPENSES"]
        }
    """
    graph = {}

    for node in nodes:
        if node.row_based_on_formula:
            dependencies = extract_dependencies_from_formula(node.formula, nodes)
            graph[node.label] = dependencies
        else:
            graph[node.label] = []

    return graph


def topological_sort(nodes: list) -> list:
    """
    Sort nodes in dependency order using Kahn's algorithm (breadth-first).

    Ensures that for every node, all its dependencies come before it in the result.

    Raises:
        frappe.ValidationError: If circular dependency detected

    Returns:
        List of nodes sorted in execution order (dependencies first)

    Example:
        input_nodes = [PROFIT_formula, REVENUE, EXPENSES]
        output = [REVENUE, EXPENSES, PROFIT_formula]  # Order matters!
    """
    graph = build_execution_graph(nodes)

    # Calculate in_degree (how many dependencies each node has)
    in_degree = {}
    for node in nodes:
        in_degree[node.label] = len(graph[node.label])

    # Find all nodes with no dependencies (starting points)
    queue = [node for node in nodes if in_degree[node.label] == 0]

    # Kahn's algorithm: process nodes with no remaining dependencies
    sorted_nodes = []

    while queue:
        # Process the first node in queue
        current = queue.pop(0)
        sorted_nodes.append(current)

        # For each other node, check if it depends on current
        for node in nodes:
            if current.label in graph[node.label]:
                # Reduce the dependency count for this node
                in_degree[node.label] -= 1

                # If all dependencies are now satisfied, add to queue
                if in_degree[node.label] == 0:
                    queue.append(node)

    # Safety check: did we process all nodes?
    if len(sorted_nodes) != len(nodes):
        # Some nodes were never added to queue = circular dependency
        unprocessed = [n for n in nodes if n not in sorted_nodes]
        processed = [n.label for n in sorted_nodes]

        frappe.throw(
            f"Circular dependency detected in Report Schema formulas. "
            f"Unprocessed nodes: {[n.label for n in unprocessed]}. "
            f"These nodes form a dependency cycle. "
            f"Check the console logs for dependency details."
        )

    return sorted_nodes


def execute_nodes_in_dependency_order(nodes: list, report_executions: dict, period_list: list) -> list:
    """
    Main execution function: Build all nodes in dependency order.

    This is the key function that replaces the old loop-over-all-nodes approach.

    Args:
        nodes: List of Report Schema nodes
        report_executions: Dictionary of executed reports {report_name: [rows]}
        period_list: List of period objects with .key attribute

    Returns:
        List of data rows (in dependency order, not display order)
    """
    data = []

    # Step 1: Determine execution order based on dependencies
    sorted_nodes = topological_sort(nodes)

    # Step 2: Execute nodes in dependency order
    for node in sorted_nodes:

        if node.accounts:
            bulid_row_based_on_accounts(node, data, report_executions, period_list)

        elif node.row_based_on_formula:
            row = build_formula_based_row(data, node.formula)
            row.update({
                "account": node.label,
                "account_name": node.label,
                "label": node.label,
                "indent": 0,
                "node_label": node.label  
            })
            data.append(row)

        elif node.use_custom_method:
            # Custom method: user-defined logic
            frappe.get_attr(node.method)(data, node, period_list, report_executions)

    return data


def reorder_data_by_row_index(data: list, nodes: list) -> list:
    """
    Re-sort data by row_index for final display while preserving parent-child relationships.

    After calculating all values (in dependency order),
    we need to show rows in the order specified by row_index.
    BUT we must keep child accounts (indent > 0) together with their parents!

    Args:
        data: Calculated data rows (in dependency order)
        nodes: Original nodes (contain row_index values)

    Returns:
        Same data rows, sorted by row_index but with parent-child hierarchy preserved
    """
    # Build lookup: node label → row_index
    row_index_map = {}
    for node in nodes:
        row_index_map[node.label] = node.row_index if node.row_index else 999

    parent_rows = []
    child_rows_by_parent = {}  

    current_parent = None
    current_parent_label = None

    for row in data:
        indent = row.get("indent", 0)

        if indent == 0:
            # This is a parent/header row
            current_parent = row
            current_parent_label = row.get("label")
            parent_rows.append(row)
            child_rows_by_parent[current_parent_label] = []
        else:
            # This is a child row - attach it to current parent
            if current_parent_label and current_parent_label in child_rows_by_parent:
                child_rows_by_parent[current_parent_label].append(row)

    parent_rows.sort(key=lambda row: row_index_map.get(row.get("label", ""), 999))

    # Rebuild data with parents and their children in correct order
    reordered_data = []
    for parent_row in parent_rows:
        reordered_data.append(parent_row)
        parent_label = parent_row.get("label")
        if parent_label in child_rows_by_parent:
            reordered_data.extend(child_rows_by_parent[parent_label])

    return reordered_data
