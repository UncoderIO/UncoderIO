from app.translator.core.models.platform_details import PlatformDetails

CARBON_BLACK_QUERY_DETAILS = {
    "platform_id": "carbonblack",
    "name": "Carbon Black Cloud",
    "group_name": "VMware Carbon Black",
    "group_id": "carbonblack-pack",
    "platform_name": "Query (Cloud)",
}

carbonblack_query_details = PlatformDetails(**CARBON_BLACK_QUERY_DETAILS)
