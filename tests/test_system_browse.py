from common.system_browse_parse import instance_names, service_from_lookup, services_from_avahi

_BROWSE = """
Browsing for _uscan._tcp
23:58:28.827  Add        2  12 local.               _uscan._tcp.         EPSON ET-8500 Series
"""
_LOOKUP = """
23:58:42.637  can be reached at EPSON5CD187.local.:443 (interface 12)
"""
_ADDRESS = """
Timestamp     A/R  Flags         IF  Hostname                               Address                                      TTL
 0:30:03.275  Add  40000002      12  EPSON5CD187.local.                     192.168.1.2                                  120
"""
_AVAHI = "\n".join((
    "=;eth0;IPv6;ET-8500;_uscan._tcp;local;EPSON5CD187.local;fe80::1;443;",
    "=;eth0;IPv4;ET-8500;_uscan._tcp;local;EPSON5CD187.local;192.0.2.8;443;",
))


def test_dns_sd_text_becomes_one_escl_service() -> None:
    names = instance_names(_BROWSE)
    service = service_from_lookup(names[0], _LOOKUP, _ADDRESS)
    assert names == ("EPSON ET-8500 Series",)
    assert service is not None
    assert service.host == "EPSON5CD187.local"
    assert service.port == 443
    assert service.addresses == ("192.168.1.2",)


def test_avahi_keeps_one_service_and_its_ipv4_address() -> None:
    found = services_from_avahi(_AVAHI)
    assert len(found) == 1
    assert found[0].host == "EPSON5CD187.local"
    assert found[0].port == 443
    assert found[0].addresses == ("192.0.2.8",)
