# -*- coding: UTF-8 -*-

"""Main
Implements a simple multiprocessing demo
See  https://bugs.python.org/issue40860

Try 

    docker build --tag multiprocess . && docker run -e LOGLEVEL=INFO multiprocess
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
cycle_counter = 0
cycle_start = time.time()
lock = threading.Lock()

def spawn_job(deadline):
    '''
    Creat a new Process, call join(), process errors
    '''    
    global job_counter
    global cycle_counter
    global cycle_start
    time_start = time.time()
    with lock:
        job = multiprocessing.Process(target=load_cpu, args=(deadline, ))
        job.start()
    job.join(deadline)
    elapsed = time.time()-time_start
    if elapsed < deadline:
        logger.debug(f"#{job_counter}: job.join() returned while process {job.pid} is still alive elapsed={elapsed} deadline={deadline}")
    else:
        logger.error(f"job.join() returned elapsed={elapsed} deadline={deadline}")
    if job.is_alive():        
        # call to job.close() fails despite the call to terminate() 
        # Call to job.kill() instead is not an improvement
        job.kill()
        try:
            job.close()
        except Exception as e:
            logger.debug(f"job.close() failed {e}")
    # A not atomic counter, I do not care about precision
    job_counter += 1
    cycle_counter += 1
    mask = 0xFFF
    if (job_counter-1) & mask == mask:
        rate = cycle_counter/(time.time() - cycle_start)
        cycle_counter = 0
        cycle_start = time.time()
        logger.info(f"#{job_counter} {rate}ops/s")
        
    

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
    deadline=0.05
    cores = multiprocessing.cpu_count()
    threads = spawn_threads(deadline=deadline, amount=4*cores)
    while True:
        thread = join_random_thread(threads, deadline)
        threads.remove(thread)

        thread = spawn_thread(deadline=deadline)
        threads.append(thread)

if __name__ == '__main__':
    logger_format = '%(name)s:%(levelname)s:%(filename)s:%(lineno)d:%(message)s'
    logging.basicConfig(format=logger_format)
    logger = logging.getLogger('multiprocess')
    loglevel = os.environ.get("LOGLEVEL", "INFO").upper()
    logger.setLevel(loglevel)
    logger.debug("Starting debug log")

    run_it_all()


