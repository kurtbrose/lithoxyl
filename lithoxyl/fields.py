# -*- coding: utf-8 -*-

import time
import json
import datetime

from tzutils import UTC, LocalTZ
from formatutils import BaseFormatField


def timestamp2iso8601_noms(timestamp, local=False):
    """
    with time.strftime(), one would have to do fractional
    seconds/milliseconds manually, because the timetuple used doesn't
    include data necessary to support the %f flag.

    This function is about twice as fast as datetime.strftime(),
    however. That's nothing compared to time.time()
    vs. datetime.now(), which is two orders of magnitude faster.
    """
    tformat = '%Y-%m-%d %H:%M:%S'
    if local:
        tstruct = time.localtime(timestamp)
    else:
        tstruct = time.gmtime(timestamp)
    return time.strftime(tformat, tstruct)


def timestamp2iso8601(timestamp, local=False, tformat=None):
    tformat = tformat or '%Y-%m-%d %H:%M:%S.%f%z'
    if local:
        dt = datetime.datetime.fromtimestamp(timestamp, tz=LocalTZ)
    else:
        dt = datetime.datetime.fromtimestamp(timestamp, tz=UTC)
    return dt.isoformat(' ')


class FormatField(BaseFormatField):
    def __init__(self, fname, fspec, getter=None, default=None, quote=None):
        super(FormatField, self).__init__(fname, fspec)
        self.default = default
        self.getter = getter
        if quote is None:
            numeric = issubclass(self.type_func, (int, float))
            quote = not numeric
        self.quote = quote

# default, fmt_specs
FF = FormatField
FMT_BUILTINS = [FF('logger_name', 's', lambda r: r.logger.name),
                FF('logger_id', 'd', lambda r: id(r.logger)),  # TODO
                FF('record_name', 's', lambda r: r.name),
                FF('record_id', 'd', lambda r: id(r)),  # TODO
                FF('record_status', 's', lambda r: r.status, quote=False),
                FF('record_status_char', 's', lambda r: r.status_char, quote=False),
                FF('record_warn_char', 's', lambda r: 'W' if r.warnings else ' ', quote=False),
                FF('level_name', 's', lambda r: r.level),  # TODO
                FF('level_number', 'd', lambda r: r.level),
                FF('message', 's', lambda r: r.message),
                FF('raw_message', 's', lambda r: r.raw_message),
                FF('begin_timestamp', '.14g', lambda r: r.begin_time),
                FF('end_timestamp', '.14g', lambda r: r.end_time),
                FF('begin_iso8601', 's', lambda r: timestamp2iso8601(r.begin_time)),
                FF('end_iso8601', 's', lambda r: timestamp2iso8601(r.end_time)),
                FF('begin_local_iso8601', 's', lambda r: timestamp2iso8601(r.begin_time, local=True)),
                FF('end_local_iso8601', 's', lambda r: timestamp2iso8601(r.end_time, local=True)),
                FF('duration_secs', '.3f', lambda r: r.duration),
                FF('duration_msecs', '.3f', lambda r: r.duration * 1000.0),
                FF('module_name', 's', lambda r: r.callpoint.module_name),
                FF('module_path', 's', lambda r: r.callpoint.module_path),
                FF('func_name', 's', lambda r: r.callpoint.func_name, quote=False),
                FF('line_number', 'd', lambda r: r.callpoint.lineno),
                FF('exc_type', 's', lambda r: r.exc_info.exc_type, quote=False),
                FF('exc_message', 's', lambda r: r.exc_info.exc_msg),
                FF('exc_tb_str', 's', lambda r: str(r.exc_info.tb_info)),
                FF('exc_tb_list', 's', lambda r: r.exc_info.tb_info.frames),
                FF('process_id', 'd', lambda r: 'TODO')]


FMT_BUILTIN_MAP = dict([(f.fname, f) for f in FMT_BUILTINS])
BUILTIN_GETTERS = dict([(f.fname, f.getter) for f in FMT_BUILTINS])
BUILTIN_QUOTERS = dict([(f.fname, json.dumps)
                        for f in FMT_BUILTINS if f.quote])