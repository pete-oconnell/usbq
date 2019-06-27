import logging
import time

import attr
from statemachine import State, StateMachine

from ..hookspec import hookimpl
from ..pm import pm

log = logging.getLogger(__name__)


@attr.s(cmp=False)
class Hostfuzz(StateMachine):
    'Fuzz device packets heading to the host.'

    delay = attr.ib(default=15)

    # States
    idle = State('idle', initial=True)
    waiting = State('waiting')

    # Valid state transitions
    start = idle.to(waiting)
    timeout = waiting.to(idle)

    def __attrs_post_init__(self):
        # Workaround to mesh attr and StateMachine
        super().__init__()
        self.proxy = pm.get_plugin('proxy')
        self.device = pm.get_plugin('device')

    @hookimpl
    def usbq_tick(self):
        if self.is_idle:
            self.start()

        if time.time() - self._start_time > self.delay:
            self.timeout()

    def on_start(self):
        log.info(f'Starting host fuzzing test.')

        if self.proxy.is_idle:
            self.proxy.start()

        self.device.connect()

        self._start_time = time.time()

    def on_timeout(self):
        if self.device.connected:
            self.device.disconnect()
