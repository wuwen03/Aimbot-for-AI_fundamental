from threading import Thread

import keyboard
# from .conf import status,status_lock
# from .conf import offset,offset_lock
# from .conf import will_end,will_end_lock
from .logger import logger

class Monitor_Keyboard(Thread):
    def __init__(self):
        super().__init__()
        self.status = 0
        self.will_end = False
        self.offset = [0,0]
        self.recoil = False
        logger.info("Monitor Keyboard inited")

    def monitor_keyboard(self):
        def callback_p():
            self.status = 1 - self.status
            logger.info("status:{}".format(self.status))
        def callback_up():
            self.offset[1]-=10
        def callback_down():
            self.offset[1]+=10
        def callback_left():
            self.offset[0]-=10
        def callback_right():
            self.offset[0]+=10
        def callback_f12():
            self.recoil = False if self.recoil else True
            logger.info("recoil: {}".format(self.recoil))
        keyboard.add_hotkey('p',callback_p)
        keyboard.add_hotkey('up',callback_up)
        keyboard.add_hotkey('down',callback_down)
        keyboard.add_hotkey('left',callback_left)
        keyboard.add_hotkey('right',callback_right)
        keyboard.add_hotkey("F12",callback_f12)
        keyboard.wait('o')
        keyboard.remove_all_hotkeys()
        self.will_end = True
        logger.info("will end")
        return

    def run(self):
        self.monitor_keyboard()