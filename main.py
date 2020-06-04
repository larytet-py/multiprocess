# -*- coding: UTF-8 -*-

"""Main
Implements a simple multiprocessing demo

https://bugs.python.org/issue40860?@ok_message=msg%20370695%20created%0Aissue%2040860%20created&@template=item
Try 

    docker build --tag multiprocess .
    docker run -e LOGLEVEL=DEBUG multiprocess
"""

import logging
import os
import math
import time
import random
import threading
import multiprocessing

def load_cpu(deadline):
    '''
    Consume 100% CPU for some time
    '''
    logger.debug(f"load cpu deadline={deadline}")
    start = time.time()

    while time.time() - start < 0.2*deadline:
        math.pow(random.randint(0, 1), random.randint(0, 1))
    logger.debug(f"load cpu done deadline={deadline}")

def spawn_job(deadline):
    '''
    Creat a new Process, call join(), process errors
    '''
    time_start = time.time()
    job = multiprocessing.Process(target=load_cpu, args=(deadline, ))
    job.start()
    logger.debug(f"Call job.join() deadline={deadline}")
    job.join(deadline)
    elapsed = time.time()-time_start
    if elapsed < deadline and job.is_alive():
        logger.error(f"job.join() returned while process {job.pid} is still alive elapsed={elapsed} deadline={deadline}")
        job.terminate()
        try:
            job.close()
        except Exception as e:
            logger.error(f"job.close() failed {e}")
    else:
        logger.debug(f"job.join() returned elapsed={elapsed}")

def spawn_thread(deadline):
    '''
    Spawn a thread wich in turn creates a process
    '''
    thread = threading.Thread(target=spawn_job, args=(deadline, ))
    thread.start()
    return thread

def spawn_threads(deadline, amount):
    threads = []
    for _ in range(amount):
        thread = spawn_thread(deadline)
        threads.append(thread)
    return threads

def join_random_thread(threads, deadline):
    '''
    Pick a random thread, call join()
    '''
    # By choosing random sampling you can trigger the exception faster (20s?)
    sample = random.sample(range(0, len(threads)), 1)[0]
    # Picking the oldest is a slower way to get the exception (1-2 minutes?) 
    #sample = 0
    thread = threads[sample]
    thread.join()
    return thread

def run_it_all():
    '''
    1. Create processes, 
    2. call join() for one of them,
    3. start a new one
    4. Goto step 2
    '''
    deadline=0.2
    threads = spawn_threads(deadline=deadline, amount=8)
    while True:
        thread = join_random_thread(threads, deadline)
        threads.remove(thread)

        thread = spawn_thread(deadline=deadline)
        threads.append(thread)
    
if __name__ == '__main__':
    logger_format = '%(name)s:%(levelname)s:%(filename)s:%(lineno)d:%(message)s'
    logging.basicConfig(format=logger_format)
    logger = logging.getLogger('multiprocess')
    loglevel = os.environ.get("LOGLEVEL", "DEBUG").upper()
    logger.setLevel(loglevel)
    logger.debug("Starting debug log")

    run_it_all()


