# -*- coding: utf-8 -*-
#
# 2016 Darko Poljak (darko.poljak at gmail.com)
#
# This file is part of cdist.
#
# cdist is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# cdist is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with cdist. If not, see <http://www.gnu.org/licenses/>.
#
#

import socket
import logging


def resolve_target_addresses(host, family=0):
    host_name = resolve_target_host_name(host, family)
    host_fqdn = resolve_target_fqdn(host)
    return (host, host_name, host_fqdn)


def resolve_target_host_name(host, family=0):
    log = logging.getLogger(host)
    try:
        # getaddrinfo returns a list of 5-tuples:
        # (family, type, proto, canonname, sockaddr)
        # where sockaddr is:
        # (address, port) for AF_INET,
        # (address, port, flow_info, scopeid) for AF_INET6
        ip_addr = socket.getaddrinfo(
                host, None, family=family, type=socket.SOCK_STREAM)[0][4][0]
        # gethostbyaddr returns triple
        # (hostname, aliaslist, ipaddrlist)
        host_name = socket.gethostbyaddr(ip_addr)[0]
        log.debug("derived host_name for host \"%s\": %s", host, host_name)
    except (socket.gaierror, socket.herror) as e:
        # in case of error provide empty value
        host_name = ''
    return host_name


def resolve_target_fqdn(host):
    log = logging.getLogger(host)
    try:
        host_fqdn = socket.getfqdn(host)
        log.debug("derived host_fqdn for host \"%s\": %s", host, host_fqdn)
    except socket.herror as e:
        # in case of error provide empty value
        host_fqdn = ''
    return host_fqdn


# check whether addr is IPv6
try:
    # python 3.3+
    import ipaddress

    def is_ipv6(addr):
        try:
            return ipaddress.ip_address(addr).version == 6
        except ValueError:
            return False
except ImportError:
    # fallback for older python versions
    def is_ipv6(addr):
        try:
            socket.inet_aton(addr)
            return False
        except socket.error:
            pass
        try:
            socket.inet_pton(socket.AF_INET6, addr)
            return True
        except socket.error:
            pass
        return False
