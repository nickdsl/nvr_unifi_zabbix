'''
Connect to Zabbix Server, search host, fetch graph names, generate zabbix screen xml file.
'''
# module for templating zabbix screen
from jinja2 import Template
# module for interacting with Zabbix Server
from pyzabbix.api import ZabbixAPI
# zabbix server url
server = "https://zabbix.example.com"
# zabbix user
zbx_user = "username"
# zabbix user password
zbx_pass = "password"
# zabbix hostname (host with attached template)
host_name = 'unifi-video'
# zabbix screen name (title in zabbix frontend)
screen_name = "UNIFI CAMS: " + host_name
# zabbix version
zabbix_version = '4.0'
# number of graph items in single screen row
col_number = 3
# graph settings of screen row
screen_row_settings = [{"graph": {"width": 450, "height": 100}},
                       {"graph": {"width": 450, "height": 100}},
                       {"graph": {"width": 500, "height": 100}}
                       ]
# check settings and exit
if(col_number>len(screen_row_settings)):
    print("Your col_number value is: {}\nYour screen_row_settings length is: {}\n".format(col_number,len(screen_row_settings)))
    print("Increase number of lines in screen_row_settings list or decrease col_number value.")
    exit(1)
# init zabbix api connection
zapi = ZabbixAPI(url=server, user=zbx_user, password=zbx_pass)
# create host search params
params = {'filter': {'name': host_name}, 'output': 'extend'}
# searching for host
res = zapi.do_request('host.get',params)
# get host id
hostid = res['result'][0]['hostid']
# create zabbix graphs search params
params = {}
# set hostid
params['hostids'] = hostid
# set param for extended output
params['output'] = 'extend'
# set graph name search criteria
params['search'] = {'name': 'CAM STATS'}
# searching for graphs
res = zapi.do_request('graph.get',params)
# close zabbix server session
zapi.user.logout()
# create empty list of graph names
names = []
# processing of found items
for cur_graph in res['result']:
    # add name of current graph item to main list
    names.append(cur_graph['name'])
# list inversion
names = names[::-1]
# calculate row number
row_number = int(len(names)/col_number)
# create empty screen graph list
screen_graphs = []
# fill screen_graphs list
# iterate rows
for row_ind in range(row_number):
    # iterate cols
    for col_ind in range(col_number):
        # set graph position on the screen
        cur_item = {'pos': {'x': col_ind, 'y': row_ind}}
        # get graph settings from the list
        cur_item['graph'] = screen_row_settings[col_ind]['graph']
        # set graph name from the names list
        cur_item['graph']['name'] = names[row_ind + col_ind*row_number]
        # append item
        screen_graphs.append(cur_item)
# open template file
file = open('zabbix_screen.xml.j2',mode='r')
# read file content
template_str = file.read()
# close file
file.close()
# init template
my_template = Template(template_str)
# init screen dict for templating
screen_dict = {'zabbix_version': zabbix_version,
               'screen_name': screen_name,
               'host_name': host_name,
               'screen_items': screen_graphs,
               'col_number': col_number,
               'row_number': row_number}
# generate zabbix screen from the template
generated = my_template.render(data=screen_dict)
# open output file
file = open('zabbix_screen.xml',mode='w')
# write generated data
file.write(generated)
# close file
file.close()
exit(0)