import frappe

def get_node():
    
    nodes = get_schema_children("Es-Bas Report Schema")

    node_data = []

    for node in nodes:
        doc = frappe.get_doc('Report Schema', node)
        report_source = doc.report_source

        # Collect accounts from the current schema
        account_list = [account.account for account in doc.accounts]

        # Append the account list and report source as a tuple
        node_data.append((account_list, report_source,doc.name))

    return node_data
    
def get_schema_children(parent_name):
   
    parent_doc = frappe.get_doc('Report Schema', parent_name)
    
    # Use get_children to iterate over all child schemas
    children = []
    for child in parent_doc.get_children():
        children.append(child.name)  
        children.extend(get_schema_children(child.name))

    return children

