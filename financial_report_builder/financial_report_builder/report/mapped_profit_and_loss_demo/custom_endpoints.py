def get_total_taxes(
    report_data: list,
    filters: dict,
    node: dict,
    period_list: list,
    report_executions: dict,
):
    # fake taxes data
    taxes = {p.key: 100 for p in period_list}
    taxes.update(
        {"account_name": node.label, "account": node.label, "label": node.label}
    )
    report_data.append(taxes)


# financial_report_builder.financial_report_builder.report.mapped_profit_and_loss_demo.custom_endpoints.get_total_taxes
