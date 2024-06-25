from threading import Lock
import psutil
# from aimbot import Aim,Model,Monitor_Keyboard
from aimbot.monitor_keyboard import Monitor_Keyboard
from aimbot.aim import Aim
from aimbot.model import Model


if __name__=="__main__":
    pid = psutil.Process().pid
    psutil.Process(pid).nice(psutil.ABOVE_NORMAL_PRIORITY_CLASS)

    monitor_keyboard = Monitor_Keyboard()
    monitor_keyboard.start()
    
    aim = Aim(monitor_keyboard)
    aim.start()

    model_path = None
    model_path = "runs\\detect\\Aimbot6\\weights\\best.pt"
    model = Model(aim,monitor_keyboard,model_path=model_path)
    model.start()

    monitor_keyboard.join()
    aim.join()
    model.join()
    