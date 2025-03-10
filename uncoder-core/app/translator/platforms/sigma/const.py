from app.translator.core.models.platform_details import PlatformDetails

SIGMA_RULE_DETAILS = {
    "name": "Sigma",
    "platform_id": "sigma",
    "platform_name": "Sigma",
    "group_name": "Sigma",
    "group_id": "sigma",
}

DEFAULT_SIGMA_CTI_MAPPING = {
    "SourceIP": "dst_ip",
    "DestinationIP": "dst_ip",
    "Domain": "dest_domain",
    "URL": "url",
    "HashMd5": "Hashes",
    "HashSha1": "Hashes",
    "HashSha256": "Hashes",
    "HashSha512": "Hashes",
}


sigma_rule_details = PlatformDetails(**SIGMA_RULE_DETAILS)
