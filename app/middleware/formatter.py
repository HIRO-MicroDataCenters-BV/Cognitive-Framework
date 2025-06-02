"""
    module to add custom formatters
"""

import logging


class RequestFormatter(logging.Formatter):
    """
    Its Formatter to add customised fields to be printed in logs.
    """

    def format(self, record):
        """
        @param record: record containing custom fields
        @return: formatted record
        """
        if hasattr(record, "request"):
            record.url = record.request.url.path
            record.remote_addr = record.request.client.host
        else:
            record.url = None
            record.remote_addr = None
        return super().format(record)
