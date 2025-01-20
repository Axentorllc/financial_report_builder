frappe.treeview_settings["Report Schema"] = {
  ignore_fields: ["parent_report_schema"],
  get_tree_nodes:
    "financial_report_builder.financial_report_builder.doctype.report_schema.report_schema.get_children",
  add_tree_node:
    "financial_report_builder.financial_report_builder.doctype.report_schema.report_schema.add_node",
  filters: [
    {
      fieldname: "company",
      fieldtype: "Link",
      options: "Company",
      label: __("Company"),
    },
  ],
  fields: [
    {
      fieldtype: "Check",
      fieldname: "is_group",
      label: __("Is Group"),
      default: 0,
    },
    { fieldtype: "Data", fieldname: "label", label: __("Label"), reqd: true },
    {
      fieldtype: "Link",
      fieldname: "report",
      label: __("Report"),
      options: "Report",
      description: __("the report that you will build..."),
    },
  ],
  breadcrumb: "Accounting",
  root_label: "All Report Schemas",
  get_tree_root: true,
  menu_items: [
    {
      label: __("New Report Schema"),
      action: function () {
        frappe.new_doc("Report Schema", true);
      },
      condition: 'frappe.boot.user.can_create.indexOf("Report Schema") !== -1',
    },
  ],
  onload: function (treeview) {
    treeview.make_tree();
  },
  on_get_node: function (nodes) {
    // triggered when `get_tree_nodes` returns nodes
    console.log(nodes);
  },
};
