# -*- coding: utf-8 -*-

from sinks import SensibleSink
from formatters import Formatter
from emitters import StreamEmitter, FakeEmitter
from logger import BaseLogger


fmtr = Formatter('{record_status_char}{begin_timestamp}')
strm_emtr = StreamEmitter()
fake_emtr = FakeEmitter()
strm_sink = SensibleSink(formatter=fmtr, emitter=strm_emtr)
fake_sink = SensibleSink(formatter=fmtr, emitter=fake_emtr)


def test_sensible_basic():
    log = BaseLogger('test_ss', [strm_sink, fake_sink])

    print

    log.debug('greet').success('hey')
    assert fake_emtr.entries[-1][0] == 's'

    with log.debug('greet') as t:
        t.success('hello')
        t.warn("everything ok?")

    assert fake_emtr.entries[-1][0] == 'S'

    with log.debug('greet') as t:
        t.failure('bye')
    assert fake_emtr.entries[-1][0] == 'F'

    try:
        with log.debug('greet') as t:
            raise ZeroDivisionError('narwhalbaconderp')
    except:
        pass

    assert fake_emtr.entries[-1][0] == 'E'
