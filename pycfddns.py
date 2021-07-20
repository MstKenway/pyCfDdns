"""
This is a script for ddns updating used in cloudflare(cf).

Does not support ipv6. Maybe this feature will be added in the future.

There are 2 methods to update ddns though cf api. One is updating by api keys (legacy) while the other is by api token.
It is recommended to use api token since Principle of Minimum Permission. Someone using api keys to update ddns also
has the privilege to do anything else. However, this would not happen on token.

HOW_TO_USE
1. install python3.
2. replace the following User Infomation with your own.(Token or Keys must be given. Zone name, record name and account
name are also needed. It is ok without optional information but it is recommended to filled in with zone id. Because the
less information is given here, the more privilege the token should be set. If zone id is given, only right to edit dns
record is needed while if every optional information is missing, it needs rights to edit dns record, to read zone
details[to get zone id] and to read account information[to get account id to get zone id].)
3. python3 pycfddns.py -token
4. set a timing function to check the current ip periodically.(like using crond)
"""
import json
import re
import socket
import sys
import urllib.error
from os.path import exists
from urllib import request, parse

# ---------------- User Infomation ------------------------
# either token or key must be provided
api_token = "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
api_key = ""
# these are required
zone_name = "example.com"
record_name = "test.example.com"
account_name = "xxxx@example.com"
# the following is optional
zone_id = ""
account_id = ""
record_id = ""

# ---------------- Some Variables ------------------------
log_file = "ip_log"
config_file = "cloudflare.ids"
CUR_IP_SRC = ["ip.sb", "cip.cc", "ifconfig.me", "api.ipify.org", "ifconfig.co"]
CURL_HEADERS = {'User-Agent': 'curl/7.64.1'}
TOKEN_HEADERS = CURL_HEADERS.copy()
TOKEN_HEADERS['Content-Type'] = "application/json"
TOKEN_HEADERS['Authorization'] = "Bearer "
# ?: means not to be caught and cached
IP_CHECK_RE = re.compile(r'(?:25[0-5]\.|2[0-4]\d\.|[01]?\d\d?\.){3}(?:25[0-5]|2[0-4]\d|[01]?\d\d?)', re.M)


def check_for_ip(content: str) -> str:
    l = IP_CHECK_RE.findall(content)
    if not l:
        print("No ip matched.", file=sys.stderr)
        return ''
    return l[0]


def get_current_ip() -> str:
    ip = None
    for src in CUR_IP_SRC:
        try:
            req = request.Request(url="http://" + src, headers=CURL_HEADERS)
            with request.urlopen(req) as resp:
                if resp.status != 200:
                    continue
                content = resp.read().decode('utf-8')
            result = check_for_ip(content)
            # if result is not None:
            if result:
                ip = result
                break
        except urllib.error.HTTPError as e:
            if e.errno == 404:
                print(404)
            else:
                print("Something error while catch ip from ", src)
                print(e)
        except Exception as e:
            print(e)
    return ip


def query_dns_ip(dns: str) -> str:
    result = None
    try:
        result = socket.gethostbyname(dns)
    except Exception as e:
        print(e, file=sys.stderr)
    return result


def check_api_token():
    h = TOKEN_HEADERS.copy()
    h['Authorization'] += api_token
    req = request.Request(url="https://api.cloudflare.com/client/v4/user/tokens/verify", headers=h)
    try:
        with request.urlopen(req) as resp:
            content_raw = resp.read()
        content = json.loads(content_raw)
        if not content['success']:
            print("Fail to verify the token. Check the token and run script again.", file=sys.stderr)
            exit(1)
        return True
    except Exception as e:
        print(e, file=sys.stderr)
        exit(1)
    return False


def get_account_id_by_token(acc_name: str) -> str:
    h = TOKEN_HEADERS.copy()
    h['Authorization'] += api_token
    req = request.Request(url="https://api.cloudflare.com/client/v4/accounts?page=1&per_page=20&direction=desc",
                          headers=h)
    try:
        with request.urlopen(req) as resp:
            content_raw = resp.read()
        content = json.loads(content_raw)
        for item in content['result']:
            if acc_name in item['name']:
                return item['id']
    except Exception as e:
        print(e, file=sys.stderr)
    return ''


def get_zone_id_by_token(z_name: str, acc_name, acc_id):
    h = TOKEN_HEADERS.copy()
    h['Authorization'] += api_token
    data = {'name': z_name, 'account.name': acc_name, 'account.id': acc_id}
    req = request.Request(url="https://api.cloudflare.com/client/v4/zones", headers=h,
                          data=parse.urlencode(data).encode('utf-8'), method='GET')
    try:
        with  request.urlopen(req) as resp:
            content_raw = resp.read()
        content = json.loads(content_raw)
        for item in content['result']:
            if z_name == item['name']:
                return item['id']
    except Exception as e:
        print(e, file=sys.stderr)
    return ''


def get_record_id_by_token(z_id: str, rec_name: str):
    h = TOKEN_HEADERS.copy()
    h['Authorization'] += api_token
    data = {'type': 'A', 'name': record_name}
    req = request.Request(url="https://api.cloudflare.com/client/v4/zones/" + z_id + "/dns_records", headers=h,
                          data=parse.urlencode(data).encode('utf-8'), method='GET')
    try:
        with  request.urlopen(req) as resp:
            content_raw = resp.read()
        content = json.loads(content_raw)
        for item in content['result']:
            if rec_name == item['name']:
                return item['id']
    except Exception as e:
        print(e, file=sys.stderr)
    return ''


def log_to_file(line: str):
    with open(log_file, "a") as f:
        f.write(line)
        f.write("\n")


def get_config(type_name: str) -> str:
    if not exists(config_file):
        return ''
    try:
        with open(config_file, 'r+') as f:
            content = json.load(f)  # type:dict
        if not type_name in content:
            return ''
        return content[type_name]
    except Exception as e:
        print(e, file=sys.stderr)
    return ''


def save_config(type_name: str, type_value):
    data = {}
    try:
        if exists(config_file):
            with open(config_file, "r") as f:
                data = json.load(f)  # type:dict
        data[type_name] = type_value
        with open(config_file, "w") as f:
            json.dump(data, f)  # type:dict
    except Exception as e:
        print(e, file=sys.stderr)


def check_account_id():
    if not account_id:
        ret = get_config('account_id')
        if not ret:
            acc_id = get_account_id_by_token(account_name)
            if not acc_id:
                print("Can not get account id! Check the configure and run again.", file=sys.stderr)
                exit(2)
            save_config('account_id', acc_id)
            return acc_id
        else:
            return ret
    else:
        return account_id


def check_zone_id():
    if not zone_id:
        acc_id = check_account_id()
        ret = get_config('zone_id')
        if not ret:
            z_id = get_zone_id_by_token(zone_name, account_name, acc_id)
            if not z_id:
                print("Can not get zone id! Check the configure and run again.", file=sys.stderr)
                exit(2)
            save_config('zone_id', z_id)
            return z_id
        else:
            return ret

    else:
        return zone_id


def check_record_id(z_id: str):
    if not record_id:
        ret = get_config('record_id')
        if not ret:
            rec_id = get_record_id_by_token(z_id, record_name)
            if not rec_id:
                print("Can not get record id! Check the configure and run again.", file=sys.stderr)
                exit(2)
            save_config('record_id', rec_id)
            return rec_id
        else:
            return ret

    else:
        return record_id


def request_update_by_token(new_ip: str) -> bool:
    z_id = check_zone_id()
    rec_id = check_record_id(z_id)

    h = TOKEN_HEADERS.copy()
    h['Authorization'] += api_token
    data = {'type': 'A', 'name': record_name, 'content': new_ip, 'ttl': 1, 'proxied': False}
    req = request.Request(url="https://api.cloudflare.com/client/v4/zones/" + z_id + "/dns_records/" + rec_id,
                          headers=h,
                          data=json.dumps(data).encode('utf-8'), method='PUT')
    try:
        with  request.urlopen(req) as resp:
            content_raw = resp.read()
        content = json.loads(content_raw)
        return content['success']
    except Exception as e:
        print(e, file=sys.stderr)
    return False


def print_usage():
    print("Usage: python3 pycfdns.py -h/-token/-keys")


def update_by_token(force=False):
    cur_ip = get_current_ip()
    dns_ip = query_dns_ip(record_name)
    if cur_ip == dns_ip and not force:
        print("Nothing to do.")
    else:
        result = request_update_by_token(cur_ip)
        if result:
            if not exists(log_file):
                print("IP of ", record_name, " is set to ", cur_ip)
            log_to_file("IP of " + record_name + " is changed to " + cur_ip)
        else:
            log_to_file("Fail to update " + record_name)


def main():
    if len(sys.argv) < 2:
        print_usage()
        exit(1)
    if '-h' in sys.argv:
        print_usage()
    elif '-token' in sys.argv:
        if '-f' in sys.argv:
            update_by_token(True)
        else:
            update_by_token()
    elif '-keys' in sys.argv:
        print("To be supported in the future.")


if __name__ == '__main__':
    main()
