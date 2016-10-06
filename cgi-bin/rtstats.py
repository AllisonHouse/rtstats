#!/usr/bin/env python
"""I should answer the following URIs

    /cgi-bin/rtstats/siteindex
"""
import os
import sys
import requests
import re
RE_IP = re.compile('\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$')


def get_domain(val):
    """Convert whatever this is, into a domain

    1.2.3.4 becomes 1.2.3
    mesonet.agron.iastate.edu becomes edu.iastate.agron
    blah becomes ''
    """
    if val.find(".") == -1:
        return ''
    if RE_IP.match(val):
        return val.rsplit(".", 1)[0]
    return ".".join(val.split(".")[1:][::-1])


def handle_site(hostname):
    sys.stdout.write("Content-type: text/html\n\n")
    req = requests.get(("http://rtstats.local/services/host/%s/feedtypes.json"
                        ) % (hostname, ))
    if req.status_code != 200:
        sys.stdout.write("API Service Failure...")
        return
    j = req.json()
    sys.stdout.write(("<table border=\"1\" cellpadding=\"2\" cellspacing=\"0\""
                      "><thead><tr><th>Feed Name</th>"
                      "<td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td>"
                      "<td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td>"
                      "</tr></thead>"))
    for feedtype in j['feedtypes']:
        sys.stdout.write(("<tr><th>%s</th>") % (feedtype,))
        sys.stdout.write("""
<td><a href="%(p)s/iddstats_nc?%(f)s+%(h)s">latency</a></td>
<td><a href="%(p)s/iddstats_nc?%(f)s+%(h)s+LOG">log(latency)</a></td>
<td><a href="%(p)s/iddbinstats_nc?%(f)s+%(h)s">histogram</a></td>
<td><a href="%(p)s/iddstats_vol_nc?%(f)s+%(h)s">volume</a></td>
<td><a href="%(p)s/iddstats_num_nc?%(f)s+%(h)s">products</a></td>
<td><a href="%(p)s/iddstats_topo_nc?%(f)s+%(h)s">topology</a></td>
        """ % dict(h=hostname, f=feedtype, p="/cgi-bin/rtstats/"))
        sys.stdout.write("</tr>")
    sys.stdout.write("</table>")


def handle_siteindex():
    sys.stdout.write("Content-type: text/html\n\n")
    req = requests.get("http://rtstats.local/services/hosts.geojson")
    if req.status_code != 200:
        sys.stdout.write("API Service Failure...")
        return
    j = req.json()
    domains = dict()
    for feature in j['features']:
        host = feature['properties']['hostname']
        ldmversion = feature['properties']['ldmversion']
        d = get_domain(host)
        d2 = domains.setdefault(d, dict())
        d2[host] = ldmversion

    sys.stdout.write(("<table border=\"1\" cellpadding=\"2\" cellspacing=\"0\""
                      "><thead><tr><th>Domain</th>"
                      "<th>Hosts</th></tr></thead>"))
    keys = domains.keys()
    keys.sort()
    for d in keys:
        domain = domains[d]
        dkeys = domain.keys()
        dkeys.sort()
        sys.stdout.write(("<tr><th>%s</th><td>") % (d,))
        for h in dkeys:
            sys.stdout.write(("<a href=\"/cgi-bin/rtstats/siteindex?%s\">"
                              "%s</a> [%s]<br />"
                              ) % (h, h, domain[h]))
        sys.stdout.write("</td></tr>")
    sys.stdout.write("</table>")


def main():
    uri = os.environ.get('REQUEST_URI', '')
    if uri.startswith('/cgi-bin/rtstats/siteindex'):
        host = os.environ.get('QUERY_STRING', '')[:256]
        if host == '':
            handle_siteindex()
        else:
            handle_site(host)
    else:
        # TODO: disable in production
        sys.stdout.write("Content-type: text/plain\n\n")
        for k, v in os.environ.iteritems():
            sys.stdout.write("%s -> %s\n" % (k, v))

if __name__ == '__main__':
    main()