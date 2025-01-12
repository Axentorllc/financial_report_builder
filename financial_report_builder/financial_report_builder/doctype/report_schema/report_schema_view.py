import frappe

def get_nodes():
    
    nodes = get_schema_children("Es-Bas Report Schema")
    node_data = []

    for node in nodes:
        doc = frappe.get_doc('Report Schema', node)
        node_data.append(doc)
    
    node_data.sort(key=lambda x: x.row_index)

    return node_data
    
def get_schema_children(parent_name):
    parent_doc = frappe.get_doc('Report Schema', parent_name)
    
    # Use get_children to iterate over all child schemas
    children = []
    for child in parent_doc.get_children():
        children.append(child.name)  
        children.extend(get_schema_children(child.name))

    return children