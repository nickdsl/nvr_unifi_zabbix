import json
import requests
import sys
import urllib3
import subprocess

# unifi server url
server_url = "https://127.0.0.1:7443"
# api url
api_url = server_url + "/api/2.0/"
# api key/token
api_key = "#your_api_key#"
# list of valid commands
valid_commands = ["cam.discovery", "cam.stats", "server.stats", "cam.ping"]
# max ping count (1 try = 1 second, zabbix has 30 sec max timeout. Default: 3
# i choose 15 as maximum
ping_count_max = 15
# minimum ping tries
ping_count_min = 1
# default - average value
ping_count_default = int((ping_count_max + ping_count_min)/2)
# function returns json from server
def get_stats(api_param="server"):
    # generate get request url
    url = "{}{}?apiKey={}".format(api_url,api_param.lower(),api_key)
    # disable warnings
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    # do request (verify=False - no ssl certificate validation)
    response = requests.get(url, verify=False)
    # if response code 200 (OK) then
    if response.status_code == 200:
        # we create dictionary from string json
        result = json.loads(response.content.decode('utf-8'))
        # for security. if we want to get server stats
        if(api_param.lower() == "server"):
            # and replace camera password param
            result['data'][0]['systemSettings']['cameraPassword'] = "#VALUE_HIDED#"
        # return our result
        return result
    else:
        # return empty dictionary
        return {}
# function return zabbix-like json discovery string
def get_cameras_discovery():
    # do request for camera stats
    cam_stats = get_stats("camera")
    # init empty zabbix discovery dict
    zbx_discovery = {"data": []}
    # request result processing
    for cur_cam in cam_stats['data']:
        # init empty discovery init dictionary
        discovery_item = {}
        # set uuid param
        discovery_item['{#UUID}'] = cur_cam['uuid']
        # set name param
        discovery_item['{#NAME}'] = cur_cam['name']
        # set host param
        discovery_item['{#HOST}'] = cur_cam['host']
        # set mac param
        discovery_item['{#MAC}'] = cur_cam['mac']
        # set model param
        discovery_item['{#MODEL}'] = cur_cam['model']
        # set fw version param
        discovery_item['{#FIRMWAREVERSION}'] = cur_cam['firmwareVersion']
        # set fw build param
        discovery_item['{#FIRMWAREBUILD}'] = cur_cam['firmwareBuild']
        # set managed param
        discovery_item['{#MANAGED}'] = cur_cam['managed']
        # set controller host address param
        discovery_item['{#CONTROLLERHOSTADDRESS}'] = cur_cam['controllerHostAddress']
        # set controller host port
        discovery_item['{#CONTROLLERHOSTPORT}'] = cur_cam['controllerHostPort']
        # append discovery list
        zbx_discovery['data'].append(discovery_item)
    # return json
    return json.dumps(zbx_discovery)
    pass
# get camera statistics
def get_cameras_stats():
    # do request for camera stats
    cam_stats = get_stats("camera")
    # init empty zabbix stats dictionary
    zbx_stats = {}
    # cam stats processing
    for cur_cam_stat in cam_stats['data']:
        # append item into dictionary with uuid key
        zbx_stats[cur_cam_stat['uuid']] = cur_cam_stat
    # return json result
    return json.dumps(zbx_stats)
    pass
# get camera network statistics
def get_cameras_ping(ping_count=ping_count_default):
    try:
        # try to set int value from param
        ping_count = int(ping_count)
    except:
        # if we got not number value
        # we will set default value
        ping_count = ping_count_defaut
    # if ping count > max or < min value
    if ping_count not in range(ping_count_min,ping_count_max+1):
        # we will set default value
        ping_count = ping_count_defaut
    # do request for camera stats
    cam_stats = get_stats("camera")
    # init ip list
    zbx_ips = []
    # init cam uuid dictionary
    cam_uuids_ips = {}
    # processing cam statistics
    for cur_cam_stat in cam_stats['data']:
        # get current cam ip
        cur_ip = cur_cam_stat['host']
        # append uuid <-> ip entry into dictionary
        cam_uuids_ips[cur_cam_stat['uuid']] = cur_ip
        # append current ip into list
        zbx_ips.append(cur_ip)
    # generate string splitted by space from cam ip list
    zbx_ips_string = " ".join(zbx_ips)
    # generate fping command string (parallel ping to all camera ip's)
    ping_command = "fping -C {} -q ".format(ping_count) + zbx_ips_string
    # execute fping and read data (from stderr stream!)
    result = subprocess.run(ping_command.split(' '),stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    # if return code 0 (success)
    if result.returncode == 0:
        # init empty pings dictionary
        result_pings_dict = {}
        # get data from stderr stream (decode from utf8 and split into list by '\n'
        result_output = result.stderr.decode('utf-8').split('\n')
        # remove last item (empty string)
        trash = result_output.pop()
        # process lines from list
        for result_line in result_output:
            # split line by space to list of values
            result_line_list = result_line.split(' ')
            # get filter empty values (strings)
            result_line_list = list(filter(lambda x: x != '', result_line_list))
            # get cam ip
            result_line_ip = result_line_list.pop(0)
            # get list of pings
            result_line_data = result_line_list[1:]
            # filter dashes. dash = packet loss
            result_line_pings = list(map(float,list(filter(lambda x: x != '-', result_line_data))))
            # calculate packet loss %
            result_line_loss = ((len(result_line_data) - len(result_line_pings))/len(result_line_pings))/100
            # calculate ping average value
            result_line_avg = float("{0:.2f}".format(sum(result_line_pings) / len(result_line_pings)))
            # add ip <-> ping stats item into dictionary
            result_pings_dict[result_line_ip] = { "min": min(result_line_pings),
                                                  "max": max(result_line_pings),
                                                  "avg": result_line_avg,
                                                  "loss": int(result_line_loss)
                                                  }
        # init final dictionary
        result_for_return = {}
        # iterate all cam uuids
        for cur_cam_uuid in cam_uuids_ips.keys():
            # add uuid <-> ping stats dictionary item
            result_for_return[cur_cam_uuid] = result_pings_dict[cam_uuids_ips[cur_cam_uuid]]
        # return result json
        return json.dumps(result_for_return)
# get server statistics
def get_server_stats():
    # do request
    server_stats = get_stats()
    # return json value
    return json.dumps(server_stats['data'][0])
    pass
# boolean flag
exit_now = False
# if we have 1 argument
if len(sys.argv) == 1:
    # script executed without any params
    # activate exit_now flag
    exit_now = True
    print("Script parameter not set")
# if we got wrong parameter
elif sys.argv[1] not in valid_commands:
    print("Wrong script parameter: {}".format(sys.argv[1]))
    exit_now = True
# if we got exit_now = True
if exit_now:
    # print default message
    print("Usage: python3 {} ".format(sys.argv[0]) + "|".join(valid_commands))
    # exit with errors
    exit(1)
# case/switch-like construction
# we create dictionary with values = functuon names
switcher = {
        "cam.discovery": get_cameras_discovery,
        "cam.stats": get_cameras_stats,
        "cam.ping": get_cameras_ping,
        "server.stats": get_server_stats
        }
# if we got two arguments
if(len(sys.argv)==2):
    # call function with no parameters
    print(switcher[sys.argv[1]]())
else:
    # call function with parameter
    print(switcher[sys.argv[1]](sys.argv[2]))
exit(0)
