# unused, device discovery UDP packet format


def ipv4_to_bytes(addr):
    return bytes(int(v) for v in addr.split('.'))


def mac_to_bytes(addr):
    return bytes(int(v, 16) for v in addr.split(':'))


base_offset = 54
packet_size = 268
offsets = dict(ip=66,
               mac=82,
               name=162,
               hwrev=297,
               fpga=306,
               subnet=314,
               )

unknown_consts = [(0, b'\x02\x01\x06'),
                  (290 - base_offset, b'\x45\x41\x4F\x52\xFF\x00\x01'),
                  (300 - base_offset, b'\x11\x00\x07\x00'),
                  (304 - base_offset, b'\xAE\xB4'),
                  (310 - base_offset, b'\x05\x80\x14\x00'),
                  ]


def device_discovery_response_packet(ip, mac_addr, name='EnsembleCP20',
                                     hwrev=b'\x00\x03\x03',
                                     fpga=b'\xf0\x10\x08\x10',
                                     subnet='255.255.255.0'):
    packet = bytearray(packet_size)

    for offset, const in unknown_consts:
        packet[offset:offset + len(const)] = const

    ip_offset = offsets['ip']
    ip = ipv4_to_bytes(ip)
    assert len(ip) == 4
    packet[ip_offset:ip_offset + 4] = ip

    subnet_offset = offsets['subnet']
    subnet = ipv4_to_bytes(subnet)
    assert len(subnet) == 4
    packet[subnet_offset:subnet_offset + 4] = [subnet[2], subnet[3], subnet[0],
                                               subnet[1]]

    mac_offset = offsets['mac']
    mac_addr = mac_to_bytes(mac_addr)
    assert len(mac_addr) == 6
    packet[mac_offset:mac_offset + len(mac_addr)] = mac_addr

    # already byte-swapped
    assert len(hwrev) == 3
    hwrev_offset = offsets['hwrev']
    packet[hwrev_offset:hwrev_offset + len(hwrev)] = hwrev

    fpga_offset = offsets['fpga']
    assert len(fpga) == 4
    packet[fpga_offset:fpga_offset + len(fpga)] = fpga

    name_offset = offsets['name']
    packet[name_offset:name_offset + len(name)] = name.encode('latin-1')
    return packet
