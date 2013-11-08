import requests
import mm_util
import urllib

def sign_in(creds):
    r = requests.get('https://mavensmate.appspot.com/github', params={'username':creds['username'], 'password':creds['password']}, proxies=urllib.getproxies(), verify=False)
    r.raise_for_status()
    return mm_util.parse_rest_response(r.text)

    
