import time
from selenium import webdriver
import os
import yaml
from selenium.webdriver.common.by import By


def chromedriver():
    #latest_chrome_stable_rss = 'https://www.ubuntuupdates.org/packages/latest_logs?dist=all%20releases&noppa=1&format=atom'
    dir_path = os.path.dirname(os.path.realpath(__file__))
    try:
        driver = webdriver.Chrome(dir_path+'/chromedriver')
        return driver
    except:
        import traceback
        print(traceback.format_exc())
        import requests
        import xml.etree.ElementTree as ET
        import platform
        import zipfile
        import io
        import subprocess
        import re
        URL = 'https://chromedriver.storage.googleapis.com/LATEST_RELEASE_'
        print('Currently installed Chrome Version')
        version = subprocess.Popen('/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome --version', shell=True,
                                 stdout=subprocess.PIPE).stdout.read().decode('utf-8')
        print(version)
        chrome_version = re.match(r'.*?(\d+\.\d+\.\d+)\.\d+.*?', version).group(1)

        print('Current chromedriver version')
        r = requests.get(url=URL + chrome_version)
        cd_version = r.content.decode('utf-8')
        dl_url = 'https://chromedriver.storage.googleapis.com/' + cd_version
        system = platform.system()
        if system == 'Darwin':  # macos
            zip_file_url = dl_url + '/chromedriver_mac64.zip'
        elif system == 'Windows':
            zip_file_url = dl_url + '/chromedriver_win32.zip'
        else:  # system == 'Linux':
            zip_file_url = dl_url + '/chromedriver_linux64.zip'
        print(zip_file_url)
        r2 = requests.get(zip_file_url)
        z = zipfile.ZipFile(io.BytesIO(r2.content))
        z.extractall(dir_path)
        if system == 'Darwin':
            os.chmod(dir_path + '/chromedriver', 0o755)
        return chromedriver()

if __name__ == '__main__':
    # Set current working directory to this files location.
    abspath = os.path.abspath(__file__)
    d_name = os.path.dirname(abspath)
    os.chdir(d_name)

    # load inventory
    with open('inventory.yaml') as f:
        inventory = yaml.load(f.read(), Loader=yaml.FullLoader)

    driver = chromedriver()
    data = list()
    for device in inventory['devices']:
        device_data = dict()
        driver.get('http://' + inventory['credentials']['username'] + ':' + inventory['credentials']['password'] + '@' + device + '/')
        time.sleep(2)
        device_data['ip'] = device
        error = True
        while error:
            try:
                device_data['hostname'] = driver.find_element_by_xpath('//*[@id="host_name"]').text
                device_data['recieved'] = driver.find_element_by_xpath('//*[@id="lan_rxbytes"]').text
                device_data['transmitted'] = driver.find_element_by_xpath('//*[@id="lan_txbytes"]').text
                device_data['rx_invalid_NWID'] = driver.find_element_by_xpath('//*[@id="err_nwids"]').text
                device_data['rx_invalid_crypt'] = driver.find_element_by_xpath('//*[@id="err_crypts"]').text
                device_data['rx_invalid_frag'] = driver.find_element_by_xpath('//*[@id="err_frags"]').text
                device_data['tx_excessive_retries'] = driver.find_element_by_xpath('//*[@id="err_retries"]').text
                device_data['missed_beacons'] = driver.find_element_by_xpath('//*[@id="err_beacons"]').text
                device_data['other_errors'] = driver.find_element_by_xpath('//*[@id="err_misc"]').text
                device_data['signal'] = driver.find_element_by_xpath('//*[@id="signal"]').text
                error = False
            except:
                error = True
        mac_table = dict()
        driver.get('http://' + inventory['credentials']['username'] + ':' + inventory['credentials']['password'] + '@' + device + '/brmacs.cgi')
        time.sleep(2)
        trs = driver.find_elements(By.TAG_NAME, "tr")
        for row in trs:
            cols = row.find_elements(By.TAG_NAME, "td")
            if len(cols) > 2:
                if cols[1].text not in mac_table.keys():
                    mac_table[cols[1].text] = list()
                mac_table[cols[1].text].append(cols[0].text.replace(':', ''))
        device_data['mac_table'] = mac_table
        data.append(device_data)

    with open('output.yaml', 'w') as f:
        f.write(yaml.dump(data))