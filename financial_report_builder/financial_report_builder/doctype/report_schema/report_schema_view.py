import frappe


def get_nodes(report_schema_name: str):
    nodes = get_schema_children(report_schema_name)
    node_data = []
    report_sources = []

    for node in nodes:
        doc = frappe.get_doc("Report Schema", node)
        report_sources.append(doc.report_source)
        node_data.append(doc)

    node_data.sort(key=lambda x: x.row_index)

    return node_data, set(report_sources)


def get_schema_children(parent_name):
    parent_doc = frappe.get_doc("Report Schema", parent_name)

    # Use get_children to iterate over all child schemas
    children = []
    for child in parent_doc.get_children():
        children.append(child.name)
        children.extend(get_schema_children(child.name))

    return children
