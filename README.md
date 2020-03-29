# nvr_unifi_zabbix
Monitoring script of Unifi Video + script for generating zabbix screen xml file
# Requirements
Developed for zabbix >= 3.4
Required python3 and modules:
- json
- requests
- sys
- subprocess
- urllib3
- py-zabbix (for screen generator)
- jinja2 (for screen generator)
# Gathered statistics
- cams:
  - network statistics: ping min/avg/max, packets loss
  - common cam statistics
- server: common server statistics
 * common statistics - as is from Unifi API (except secret information like passwords etc.) 
