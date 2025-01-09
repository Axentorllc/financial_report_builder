import frappe

def get_nodes():
    
    nodes = get_schema_children("Es-Bas Report Schema")

    node_data = []
    report_source_list=[]
    
    for node in nodes:
        doc = frappe.get_doc('Report Schema', node)
        report_source = doc.report_source
        report_source_list.append(report_source)

        # Append the account list and report source as a tuple
        node_data.append(doc)

    return node_data , report_source_list
    
def get_schema_children(parent_name):
   
    parent_doc = frappe.get_doc('Report Schema', parent_name)
    
    # Use get_children to iterate over all child schemas
    children = []
    for child in parent_doc.get_children():
        children.append(child.name)  
        children.extend(get_schema_children(child.name))

    return children

