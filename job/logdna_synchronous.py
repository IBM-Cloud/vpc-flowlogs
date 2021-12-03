import logging
import requests
import time
import sys

class LogdnaSynchronous:
    """Synchronously send records to logdna.  Usage:
    loggit = LogdnaSynchronous(...)
    loggit.emit("log this")
    loggit.emit("log and that")
    ...
    loggit.close()

    Logic taken from https://github.com/logdna/python
    """
    def __init__(self, ingestion_endpoint, key, hostname, options={}):
        self.url = f'{ingestion_endpoint}/logs/ingest'
        self.key = key
        self.hostname = hostname
        self.buf = []
        self.buf_size = 0
        self.retry_interval_secs = options.get('retry_interval_secs', 5)
        self.max_retry_jitter = options.get('max_retry_jitter', 0.5)
        self.max_retry_attempts = options.get('max_retry_attempts', 3)
        self.request_timeout = options.get('request_timeout', 30)
        self.user_agent = options.get('user_agent', 'python/1.18.1')
        self.buf_retention_limit = options.get('buf_retention_limit', 100000)
        self.loglevel = options.get('loglevel', 'INFO')

        # Set Internal Logger
        self.internalLogger = logging.getLogger('flowlog')


    def clean_after_success(self):
        # self.close_flusher()
        self.buf.clear()
        self.buf_size = 0
        # self.exception_flag = False


    def try_request(self):
        data = {'e': 'ls', 'ls': self.buf}
        retries = 0
        while retries < self.max_retry_attempts:
            retries += 1
            if self.send_request(data):
                self.clean_after_success()
                break

            sleep_time = self.retry_interval_secs * (1 << (retries - 1))
            sleep_time += self.max_retry_jitter
            time.sleep(sleep_time)

        if retries >= self.max_retry_attempts:
            self.internalLogger.error(
                'Flush exceeded %s tries. Discarding flush buffer',
                self.max_retry_attempts)
            #self.close_flusher()
            #self.exception_flag = True

    def send_request(self, data):
        try:
            response = requests.post(url=self.url,
                                     json=data,
                                     auth=('user', self.key),
                                     params={
                                         'hostname': self.hostname,
                                         'now': int(time.time() * 1000)
                                     },
                                     stream=True,
                                     timeout=self.request_timeout,
                                     headers={'user-agent': self.user_agent})

            response.raise_for_status()
            status_code = response.status_code
            if status_code in [401, 403]:
                self.internalLogger.error(
                    'Please provide a valid ingestion key.' +
                    ' Discarding flush buffer')
                return True

            if status_code == 200:
                return True

            if status_code in [400, 500, 504]:
                self.internalLogger.warning('The request failed %s. Retrying...',
                                          response.reason)
                return True
            else:
                self.internalLogger.warning(
                    'The request failed: %s. Retrying...', response.reason)

        except requests.exceptions.Timeout as timeout:
            self.internalLogger.warning('Timeout error occurred %s. Retrying...',
                                      timeout)

        except requests.exceptions.RequestException as exception:
            self.internalLogger.warning(
                'Error sending logs %s. ', exception)

        return False

    def buffer(self, message):
        msglen = len(message['line'])
        self.buf.append(message)
        self.buf_size += msglen

    def buffer_send_when_full(self, message):
        self.buffer(message)
        if self.buf_size > self.buf_retention_limit:
            self.try_request()

    def buffer_send(self, message):
        self.buffer(message)
        self.try_request()

    def emit(self, msg):
        "emit one message to logdna.  Note that the messages will actually be buffered"
        message = {
            'hostname': self.hostname,
            'timestamp': int(time.time() * 1000),
            'line': msg,
            'level': self.loglevel,
        }
        self.buffer_send_when_full(message)

    def close(self):
        """finish up the final buffered request"""
        self.try_request()