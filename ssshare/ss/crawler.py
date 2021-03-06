#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
{
    "server": server['server'],
    "server_ipv6": "::",
    "server_port": int(server['server_port']),
    "local_address": "127.0.0.1",
    "local_port": 1080,
    "password": server['password'],
    "timeout": 300,
    "udp_timeout": 60,
    "method": method,
    "protocol": ssr_protocol,
    "protocol_param": "",
    "obfs": obfs,
    "obfs_param": "",
    "fast_open": False,
    "workers": 1,
    "group": "ss.pythonic.life"
}
"""
from ast import literal_eval
import json
import logging
import regex as re
import requests
import cfscrape
import js2py
from bs4 import BeautifulSoup
from ssshare.ss.parse import parse, scanNetQR, gen_uri
from ssshare.ss.ssr_check import validate


fake_ua = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.87 Safari/537.36'}


def request_url(url, headers=None, name=''):
    print('req', url)

    data = set()
    servers = list()
    try:
        response = requests.get(url, headers=headers, verify=False).text
        data.update(map(lambda x: re.sub('\s', '', x), re.findall('ssr?://[a-zA-Z0-9_]+=*', response)))
        soup = BeautifulSoup(response, 'html.parser')
        title = soup.find('title').text

        info = {'message': '', 'url': url, 'name': str(title)}
        for i, server in enumerate(data):
            try:
                servers.append(parse(server, ' '.join([title, name, str(i)])))
            except Exception as e:
                logging.exception(e, stack_info=False)
                print('URL:', url, 'SERVER', server)
    except Exception as e:
        print(url)
        logging.exception(e, stack_info=False)
        return [], {'message': str(e), 'url': '', 'name': ''}
    return servers, info


def crawl_sstool(
        api_url=[
            'https://www.ssrtool.com/tool/api/free_ssr?page=1&limit=1000',
            'https://www.ssrtool.com/tool/api/share_ssr?page=1&limit=1000',
        ],
        headers=fake_ua):
    print('req sstool')
    info = {
        'message': 'GayHub订阅(3天自动更新一次):\nhttps://raw.githubusercontent.com/AmazingDM/sub/master/ssrshare.com',
        'name': 'SSCAP/SSTAP 小工具/SSR/SS/V2Ray/Vmess/Socks5免费账号',
        'url': 'https://www.ssrtool.com/tool/free_ssr'
    }
    data = list()
    try:
        for url in api_url:
            respond = requests.get(url, headers=fake_ua)
            if respond.status_code == 200:
                json_data = respond.json()
                data.extend(json_data.get('data', []))
        for i in data:
            if 'protocol' in i:
                i['ssr_protocol'] = i['protocol']
            if 'protocolparam' in i:
                i['protoparam'] = i['protocolparam']
            else:
                print(i)
        servers = data

    except Exception as e:
        logging.exception(e, stack_info=True)
        print('-' * 30)
    return servers, info


def crawl_free_ss_site(url='https://free-ss.site/', headers=fake_ua):
    print('req free_ss_site/...')
    info = {'message': '', 'name': '免费上网帐号', 'url': 'https://free-ss.site/'}
    try:
        fake_ua = headers

        sess = cfscrape.create_scraper()

        encc_url = url + 'ajax/libs/encc/0.0.0/encc.min.js'
        crypto_url = url + 'ajax/libs/crypto-js/3.1.9-1/crypto-js.min.js'

        headers = {'Referer': url, 'Origin': url}
        headers.update(fake_ua)

        html = sess.get(url, headers=fake_ua).text
        print('html')
        encc_js = sess.get(encc_url, headers=headers).text
        print('encc')
        crypto_js = sess.get(crypto_url, headers=headers).text
        print('crypto')

        soup = BeautifulSoup(html, 'html.parser')
        script = next(filter(lambda x: 'src' not in x.attrs, soup.findAll('script'))).contents[0]

        def get_value(char):
            value_exp = re.findall(r'(?<=var)\s+{char}\s*=\s*[^;]+(?=;)'.format(char=char), script)[1]
            return literal_eval(value_exp.split('=')[1])

        value_dict = {
            'a': get_value('a'),
            'b': get_value('b'),
            'c': get_value('c'),
        }

        value_dict['c'] = js2py.eval_js(encc_js + 'encc("{c}");'.format(c=value_dict['c']))
        replace_char = re.findall(r'(?<=function\()\w(?=\)\{\s*\$.post\()', script, flags=re.MULTILINE)[0]
        img = re.findall(r"(?<=decodeImage\(')data:image[^']+(?=')", script)[0]
        value_dict[replace_char] = scanNetQR(img)

        d = sess.post(
            url + "data.php",
            headers=headers,
            data={
                'a': value_dict['a'],
                'b': value_dict['b'],
                'c': value_dict['c']
            })
        print(d.status_code)
        d = d.text
        assert len(d) > 0, 'request for encrypted data failed'

        variables = ';var a = "{a}";var d = "{d}";var b = "{b}"'.format(
            a=value_dict['a'],
            b=value_dict['b'],
            d=d
        )
        xy = ';var x=CryptoJS.enc.Latin1.parse(a);var y=CryptoJS.enc.Latin1.parse(b);'
        ev = js2py.eval_js(re.findall(r'(?<=eval)\(function.*', script)[1]) + 'dec.toString(CryptoJS.enc.Utf8);'

        json_data = js2py.eval_js(crypto_js + variables + xy + ev)
        try:
            data = json.loads(json_data)
            data = data['data']
        except Exception as e:
            print(e)
            print(json_data)

        servers = [{
            'remarks': x[6],
            'server': x[1],
            'server_port': x[2],
            'password': x[4],
            'method': x[3],
        } for x in data]
    except Exception as e:
        logging.exception(e, stack_info=True)
        print(respond.text)
        print('-' * 30)
    return servers, info


def main(debug=list()):

    result = list()
    # Specified functions for requesting servers
    websites = [globals()[i] for i in filter(lambda x: x.startswith('crawl_'), globals())]
    from ssshare.config import url

    websites.extend([(i, None) for i in url])

    for website in websites:
        try:
            if type(website) is tuple:
                data, info = request_url(*website)
            else:
                data, info = website()
            result.append({'data': gen_uri(data), 'info': info})
        except Exception as e:
            logging.exception(e, stack_info=False)
            print('Error in', website, type(website))

    # check ssr configs
    if 'no_validate' in debug:
        validated_servers = result
    else:
        validated_servers = validate(result)
    # remove useless data
    servers = list(filter(lambda x: len(x['data']) > 0, validated_servers))
    print('-' * 10, '数据获取完毕', '-' * 10)
    return servers
