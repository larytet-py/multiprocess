# -*- coding: UTF-8 -*-

"""Main
Implements a simple multiprocessing demo
See  https://bugs.python.org/issue40860

Try 

    docker build --tag multiprocess . && docker run -e LOGLEVEL=DEBUG multiprocess
"""

import logging
import os
import math
import time
import random
import threading
import multiprocessing
import sys

def load_cpu(deadline):
    '''
    Consume 100% CPU for some time
    '''
    start = time.time()
    # I want to complete well ahead of the deadline
    while time.time() - start < 0.2*deadline:
        math.pow(random.randint(0, 1), random.randint(0, 1))

def join_process(job, timeout):
    time_start = time.time()
    while time.time()-time_start < timeout and job.is_alive():
        time.sleep(0.1   * timeout)
        continue

job_counter = 0
def spawn_job(deadline):
    '''
    Creat a new Process, call join(), process errors
    '''    
    global job_counter
    time_start = time.time()
    job = multiprocessing.Process(target=load_cpu, args=(deadline, ))
    job.start()
    join_process(job, deadline)
    elapsed = time.time()-time_start
    if elapsed < deadline and job.is_alive():
        logger.error(f"#{job_counter}: job.join() returned while process {job.pid} is still alive elapsed={elapsed} deadline={deadline}")
        # call to job.close() fails despite the call to terminate() 
        # Call to job.kill() instead is not an improvement
        job.terminate()
        try:
            job.close()
        except Exception as e:
            logger.error(f"job.close() failed {e}")
    else:
        logger.debug(f"job.join() returned elapsed={elapsed} deadline={deadline}")
    # A not atomic counter, I do not care about precision
    job_counter += 1
    mask = 0xFF
    if (job_counter-1) & mask == mask:
        logger.info(f"#{job_counter}")
    

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
    # By choosing random sampling I can trigger the exception faster (20s?)
    sample = random.sample(range(0, len(threads)), 1)[0]
    # Picking the oldest is a slower way to get the exception (1-2 minutes?) 
    #sample = 0
    thread = threads[sample]
    thread.join()
    return thread

def run_it_all():
    '''
    1. Start a bunch of processes, 
    2. call join() for one of them,
    3. start a new process
    4. Goto step 2
    '''
    global job_counter
    deadline=0.2
    cores = multiprocessing.cpu_count()
    threads = spawn_threads(deadline=deadline, amount=2*cores)
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


