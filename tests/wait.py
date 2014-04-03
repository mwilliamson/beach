import time


def retry(func, error, timeout, interval=0.1):
    start_time = time.time()
    while True:
        try:
            return func()
        except error:
            if time.time() - start_time > timeout:
                raise
            else:
                time.sleep(interval)
