import os
from typing import Optional

import asyncio
from aiohttp import web
import datetime
import math
import redis.asyncio as redis
import logging
from elasticsearch import AsyncElasticsearch
from redis.asyncio.client import Redis

logging.basicConfig(level=logging.INFO)

redis_url = os.getenv('REDIS_URL')
if not redis_url:
    raise Exception('REDIS_URL environment variable not set')

elastic_url = os.getenv('ELASTIC_URL')
if not elastic_url:
    raise Exception('ELASTIC_URL environment variable not set')
logging.info("elastic_url: " + elastic_url)
logging.info("redis_url: " + redis_url)
pool = redis.connection.ConnectionPool.from_url(url=redis_url)
redis = Redis(connection_pool=pool)
params = {}
if os.getenv('ELASTIC_USER') and os.getenv('ELASTIC_PASS'):
    params['basic_auth'] = ((os.getenv('ELASTIC_USER')), (os.getenv('ELASTIC_PASS')))
if os.getenv('ELASTIC_TIMEOUT'):
    params['request_timeout'] = os.getenv('ELASTIC_TIMEOUT')
if os.getenv('ELASTIC_CA'):
    params['ca_certs'] = os.getenv('ELASTIC_CA')
if os.getenv('ELASTIC_APIKEY_ID') and os.getenv('ELASTIC_APIKEY_KEY'):
    params['api_key'] = (os.getenv('ELASTIC_APIKEY_ID'), os.getenv('ELASTIC_APIKEY_KEY'))

es = AsyncElasticsearch(hosts=elastic_url.split(","), **params)


def get_next_list(tenant_id: str, timestamp: Optional[float] = None) -> str:
    minutes = math.floor((timestamp or datetime.datetime.now().timestamp()) / 60)
    return f'{tenant_id}_{minutes}'


async def update_visit_expire(request):
    tenant_id = await get_tenant_id(request)
    browser_id = request.match_info.get('browserId')
    next_list = get_next_list(tenant_id)

    command = """
    local visitor_time = redis.call('hget', KEYS[1]..'_'..KEYS[2] ,'tt')
        if (visitor_time==false) then
            return 0
        end
        redis.call('zadd', KEYS[3], visitor_time, KEYS[2])
        redis.call('expire', KEYS[3], 120)
        redis.call('expire', KEYS[1]..'_'..KEYS[2], 45);
    """

    await redis.eval(command, 3, tenant_id, browser_id, next_list)
    return web.Response(text="")


async def get_tenant_id(request):
    return request.match_info.get('tenantId')


async def track_button_impression(request):
    tenant_id = await get_tenant_id(request)
    time = await get_time()
    command = """
    redis.call('hincrby', KEYS[1], 'c', 1)
    redis.call('hmset', KEYS[1], 'u', ARGV[1], 't', ARGV[2])
    redis.call('expire', KEYS[1], 5400)
    """
    url_param = request.query.get('p')
    await redis.eval(command, 1, tenant_id + "_" + request.query.get("i"), url_param, time)

    return web.Response(text="")


async def get_time():
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

async def is_crawler(request):
    useragent = request.headers.get('User-Agent')
    if useragent is None:
        return False
    useragent = useragent.lower()

    crawlers = ['googlebot', 'robot', 'slurp', 'yahooseeker', 'teoma', 'crawl', 'spider', 'msnbot', 'bingbot', 'adsbot', 'erbot', 'niki-bot', 'hrbot', 'yandex.com/bots', 'facebookexternalhit', 'facebot', 'bitlybot', 'tweetmemebot', 'linkisbot', 'datagnionbot', 'linkfluence.com', 'socialrankiobot', 'paperlibot', 'duckduckbot', 'skypeuripreview', 'semrushbot', 'dotbot', 'aspiegelbot', 'mediumbot', 'pinterestbot', 'nativeaibot', 'diffbot', '12bot', 'zbot', 'xbot', 'cloudflare-alwaysonline', 'abot', 'quora-bot', 'applebot']
    whitelist_crawlers = ['pixelrobot']

    if useragent in whitelist_crawlers:
        return False

    if useragent in crawlers:
        return True

    return False

async def track_visit(request):
    if await is_crawler(request):
        return web.Response(text="")
    tenant_id = await get_tenant_id(request)
    time = datetime.datetime.now().timestamp()
    next_list = get_next_list(tenant_id, time)
    current_list = get_next_list(tenant_id, time - 60)
    command = """
    redis.call('hmset', KEYS[1], 's', ARGV[1], 'dlv', ARGV[2], 'tt', ARGV[3], 'u', ARGV[4], 'r', ARGV[5], 'i', ARGV[6], 'ua', ARGV[7], 'sc', ARGV[8], 'ud', ARGV[9], 'vn', ARGV[10])
                redis.call('hsetnx', KEYS[1], 'dfv', ARGV[2])
                redis.call('expire', KEYS[1], 45)
                redis.call('zadd', KEYS[2], ARGV[3], ARGV[11])
                redis.call('expire', KEYS[2], 70)
                redis.call('zadd', KEYS[3], ARGV[3], ARGV[11])
                redis.call('expire', KEYS[3], 140)
    """

    browser = request.query.get("B")
    session = request.query.get("S")
    page_title = request.query.get("pt")
    page_url = request.query.get("url")
    page_ref = request.query.get("ref")
    screen = request.query.get("sr")
    user_details = request.query.get("ud")
    now = await get_time()
    visitor_new = request.query.get("vn")
    ip = request.remote
    request.query.get("jstk")
    index = "la_perf_pagevisit_v1.1_" + datetime.date.today().strftime("%Y_%m_%d")

    await asyncio.gather(redis.eval(command, 3, tenant_id + "_" + browser, current_list, next_list, session, now,
                                    datetime.datetime.now().timestamp(), page_url, page_ref, ip,
                                    request.headers["User-Agent"], screen,
                                    user_details, visitor_new, browser),
                         es.index(index=index,
                                  document={"b": browser, "dv": now, "t": page_title, "u": page_url, "r": page_ref,
                                            "tenant_id": tenant_id}))

    return web.Response(text="")


app = web.Application(logger=logging.root)
app.add_routes([web.get('/update_visit_expire/{session}/{tenantId}/{browserId}', update_visit_expire),
                web.get('/track_button_impression/{tenantId}', track_button_impression),
                web.get('/track_visit/{tenantId}', track_visit)
                ])

web.run_app(app, port=80)
