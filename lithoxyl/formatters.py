# -*- coding: utf-8 -*-

import time
import datetime
from operator import itemgetter
from json import dumps as escape_str

from tzutils import UTC, LocalTZ
from formatutils import tokenize_format_str, _TYPE_MAP, BaseFormatField


class RecordFormatter(object):
    builtin_field_list = []  # TODO
    builtin_field_map = {}  # TODO

    def __init__(self, record):
        self.record = record

    def format(self, format_str, *args, **kwargs):
        # TODO: if 2.6, fix up positional args
        # tokenize format_str into BaseFormatFields
        # FormatField either comes from args, kwargs, builtin, or record itemgetter
        # (TODO: default needs to become a string)
        # format()
        try:
            return format_str.format(*args, **kwargs)
        except:
            pass
        base_fields = tokenize_format_str(format_str)
        pos_count = 0
        value_dict = dict(kwargs)
        pos_args = list(args)
        field_map = {}  # tmp
        ret = ''
        for bf in base_fields:
            try:
                ff = FMT_BUILTIN_MAP[bf.fname]
            except AttributeError:
                continue
            except KeyError:
                if not bf.base_name or bf.base_name.isdigit():
                    pos_count += 1
                    if len(pos_args) < pos_count:
                        pos_args.append(bf.type_func())
                    # TODO: save type of pos args
                    continue
                ff = FormatField(bf.fname, bf.fspec or 's',
                                 itemgetter(bf.fname), quote=False)
            field_map[ff.fname] = ff  # tmp
            if ff.fname not in value_dict:
                try:
                    value_dict[ff.fname] = ff.getter(self.record)
                except:
                    value_dict[ff.fname] = ff.type_func()
        return format_str.format(*pos_args, **value_dict)


class FormatField(BaseFormatField):
    def __init__(self, fname, fspec, getter=None, default=None, quote=None):
        super(FormatField, self).__init__(fname, fspec)
        self.getter = getter
        self._raw_default = default
        if default is None:
            self.default = self.fstr
        elif isinstance(default, str):
            self.default = default
        else:
            raise TypeError('default expected str or None, not %r' % default)
        self.quote_output = quote
        if quote is None:
            is_numeric = issubclass(self.type_func, (int, float))
            self.quote_output = not is_numeric
        print self.fname, self.quote_output

    def get_formatted(self, *a, **kw):
        try:
            val = self.getter(*a, **kw)
            ret = self.fstr.format(**{self.fname: val})
            # TODO: handle positionals
        except:
            ret = self.default
        if self.quote_output:
            ret = escape_str(ret)
        return ret

    def __repr__(self):
        cn = self.__class__.__name__
        return '%s(%r, %r, %r)' % (cn, self.fname, self.fspec, self.getter)


# default, fmt_specs
FF = FormatField
FMT_BUILTINS = [FF('logger_name', 's', lambda r: r.logger.name),
                FF('logger_id', 'd', lambda r: id(r.logger)),  # TODO
                FF('record_name', 's', lambda r: r.name),
                FF('record_id', 'd', lambda r: id(r)),  # TODO
                FF('record_status', 's', lambda r: r.status, quote=False),
                FF('record_status_char', 's', lambda r: r.status[0].upper(), quote=False),
                FF('level_name', 's', lambda r: r.level),  # TODO
                FF('level_number', 'd', lambda r: r.level),
                FF('message', 's', lambda r: r.message),
                FF('raw_message', 's', lambda r: r.raw_message),
                FF('start_timestamp', '.14g', lambda r: r.start_time),
                FF('end_timestamp', '.14g', lambda r: r.end_time),
                FF('start_iso8601', 's', lambda r: timestamp2iso8601(r.start_time)),
                FF('end_iso8601', 's', lambda r: timestamp2iso8601(r.end_time)),
                FF('start_local_iso8601', 's', lambda r: timestamp2iso8601(r.start_time, local=True)),
                FF('end_local_iso8601', 's', lambda r: timestamp2iso8601(r.end_time, local=True)),
                FF('duration_secs', '.3f', lambda r: r.duration),
                FF('duration_msecs', '.3f', lambda r: r.duration * 1000.0),
                FF('module_name', 's', lambda r: r.callpoint.module_name),
                FF('module_path', 's', lambda r: r.callpoint.module_path),
                FF('func_name', 's', lambda r: r.callpoint.func_name),
                FF('line_number', 'd', lambda r: r.callpoint.lineno),
                FF('exc_type', 's', lambda r: 'TODO'),
                FF('exc_message', 's', lambda r: 'TODO'),
                FF('exc_tb_str', 's', lambda r: 'TODO'),
                FF('exc_tb_dict', 's', lambda r: 'TODO'),
                FF('process_id', 'd', lambda r: 'TODO')]


FMT_BUILTIN_MAP = dict([(f.fname, f) for f in FMT_BUILTINS])


class Formatter(object):
    def __init__(self, format_str, defaults=None, getters=None):
        self.raw_format_str = format_str
        getters = dict(getters or {})
        self.defaults = dict(defaults or {})
        self.field_map = {}
        self.token_chain = []
        self.format_str = ''
        base_fields = tokenize_format_str(format_str)
        for bf in base_fields:
            # TODO: if anonymous and/or positional, raise
            # TODO: no subfields allowed, either
            # TODO: and no compound things, gershdernit
            # TODO: try the field out on its own default, to be sure
            # TODO: assert that there's whitespace or some static marker
            #       between all fields (or only all unquote fields?)
            try:
                ff = FMT_BUILTIN_MAP[bf.fname]
                self.format_str += str(ff)
            except AttributeError:
                self.format_str += bf
            except KeyError:
                ff = 'TODO'
                raise
                #ff = FormatField(bf.fname, '', '')
            self.field_map[ff.fname] = ff

    def format_record(self, record):
        items = {}
        try:
            for fname, field in self.field_map.items():
                items[fname] = field.getter(record)  # TODO
            return self.format_str.format(**items)
        except:
            pass
            # switch to safe mode

        ret = ''
        for token in self.token_chain:
            try:
                fname = token.fname
            except AttributeError:
                ret += token
                continue
            cur = token.get_formatted(record)
            ret += cur
        return ret

    __call__ = format_record


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
