"""
Dsportal: a monitoring portal

Usage: %s <server address> <key>

"""
import sys
from os import path
import aiohttp
import asyncio
from threading import Thread
from dsportal import healthchecks
from dsportal import base
import queue
import logging
from dsportal.util import setup_logging

setup_logging(debug=False)
log = logging.getLogger(__name__)

class Worker(object):
    def __init__(self):
        self.work_queue = queue.Queue(maxsize=10)
        # checks should not pile up
        self.result_queue = queue.Queue(maxsize=1)

    def start_workers(self,count=4):
        for x in range(count):
            t = Thread()
            t = Thread(target=self._worker)
            t.daemon = True
            t.start()

        return t

    def enqueue(self,id,fn_name,**kwargs):
        try:
            log.debug
            fn = base.HEALTHCHECKS[fn_name]
            self.work_queue.put((id,fn,kwargs),block=False)
            log.debug('Check enqueued: %s',fn_name)
        except queue.Full:
            self.result_queue.put((id,{
                    'id':id,
                    'healthy': None,
                    'error_message' : 'Worker was too busy to run this health check',
                }))
            log.warn('Check dropped: %s',fn_name)
            pass


    def _worker(self):
        while True:
            id,fn,kwargs = self.work_queue.get(block=True)
            log.debug('Processing check: %s',fn.__name__)
            result = fn(**kwargs)
            self.work_queue.task_done()

            if result['healthy']:
                log.info('Check passed: %s %s',fn.__name__,kwargs)
            elif result['healthy'] == False:
                log.warn('Check failed: %s %s %s',fn.__name__,kwargs,result['error_message'])
            else:
                log.warn('Check error: %s %s %',fn.__name__,kwargs,result['error_message'])

            try:
                self.result_queue.put((id,result),block=False)
            except queue.Full:
                log.error('Could not report result, blocked.')


async def websocket_client(loop,worker,host,key):
    url = path.join(host,'worker-websocket')
    session = aiohttp.ClientSession(
            loop=loop,
            headers={
                'Authorization':'Token ' + key,
                },
            )

    connection = session.ws_connect(
            url=url,
            autoping=True,
            heartbeat=10,
        )


    async with connection as ws:
        # TODO consider this implementation
        # https://aiohttp.readthedocs.io/en/v2.1.0/faq.html#how-to-receive-an-incoming-events-from-different-sources-in-parallel

        task = loop.create_task(read_results(worker,ws))

        try:
            async for msg in ws:
                if msg.type == aiohttp.WSMsgType.TEXT:
                    jobspec = msg.json()
                    worker.enqueue(**jobspec)
                elif msg.type == aiohttp.WSMsgType.CLOSED:
                    print('error')
                    break
                elif msg.type == aiohttp.WSMsgType.ERROR:
                    print('closed')
                    break
        finally:
            task.cancel()

# TODO reconnect forever

async def read_results(worker,ws):
    # TODO there's got to be a better way
    while True:
        try:
            result = worker.result_queue.get(block=False)
            ws.send_json(result)
        except queue.Empty:
            pass

        await asyncio.sleep(0.01)


def main():
    # run as executable, must be remote worker
    if len(sys.argv) < 2:
        print(__doc__ % sys.argv[0])
        sys.exit(1)

    host = sys.argv[1]
    key = sys.argv[2]

    worker = Worker()
    worker.start_workers()

    loop = asyncio.get_event_loop()
    client = websocket_client(loop,worker,host,key)
    loop.run_until_complete(client)
