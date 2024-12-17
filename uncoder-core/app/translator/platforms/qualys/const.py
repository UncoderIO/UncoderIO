QUALYS_QUERY_DETAILS = {
    "platform_id": "qualys",
    "name": "Qualys",
    "platform_name": "IOC Query",
    "group_name": "Qualys",
    "group_id": "qualys",
}

DEFAULT_QUALYS_CTI_MAPPING = {
    "DestinationIP": "network.remote.address.ip",
    "SourceIP": "network.local.address.ip",
    "HashSha512": "file.hash.sha512",
    "HashSha256": "file.hash.sha256",
    "HashMd5": "file.hash.md5",
    "Emails": "emails",
    "Domain": "domain",
    "HashSha1": "file.hash.sha1",
    "Files": "file.name",
    "URL": "url",
}
