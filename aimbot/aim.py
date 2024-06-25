import pydirectinput
import threading
from math import sqrt
import time

# from .conf import offset,offset_lock,will_end
from .logger import logger
from .monitor_keyboard import Monitor_Keyboard

class PID:
    def __init__(self,current,target,p,i,d,int_lim,out_lim) -> None:
        self.kp,self.ki,self.kd = p,i,d
        self.target,self.current = target,current
        self.int_lim,self.out_lim = int_lim,out_lim
        self.integral = 0
        self.pre_err = 0
        self.last_time = time.time()
    
    def update(self,current,target,now_time = time.time()):
        self.current = self.current if current == None else current
        self.target = self.target if target == None else target

        err = self.target-self.current
        
        p_out = err * self.kp

        self.integral += err * (now_time - self.last_time)
        self.integral = min(self.integral,self.int_lim)
        self.integral = max(self.integral,-self.int_lim)
        i_out = self.integral * self.ki

        d = (err - self.pre_err) / (now_time-self.last_time)
        d_out = d * self.kd

        self.pre_err = err
        self.last_time = now_time

        out = p_out + i_out + d_out
        out = min(out,self.out_lim)
        out = max(out,-self.out_lim)
        logger.info("p:{},i:{},d:{}".format(p_out,i_out,d_out))
        # out = 0 if abs(int(out)) <= 1 else out
        return out


class Aim(threading.Thread):
    def __init__(self,mk:Monitor_Keyboard,cx=0,cy=0,p=0.75,i=0.1,d=0.07) -> None:
        super().__init__()
        self.mk = mk
        #c表示目标位置，r表示准星位置，id表示目标的标号（track模式下使用，已弃用
        self.cx = int(cx)
        self.cy = int(cy)
        self.rx = 320
        self.ry = 240
        self.id = -1
        #pid控制的参数
        self.kp = p
        self.ki = i
        self.kd = d
        #pid控制器
        self.x_pid = PID(320,320,p,i,d,50,100)
        self.y_pid = PID(240,240,p,i,d,50,100)
        #用于update和move操作的同步，测试发现信号量和自旋锁的性能差距几乎没有
        self.lock_1 = threading.Lock()
        self.lock_2 = threading.Lock()
        # self.lock_1 = threading.Semaphore()
        # self.lock_2 = threading.Semaphore()
        self.lock_1.acquire()
        logger.info("Aim inited")


    def update(self,xywh,clses,confs):
        if len(xywh) == 0 :
            self.id = -1
            return
        if self.lock_2.acquire(blocking=False) == False:
            return
        if 0 not in clses:
            self.id = 0
            max_conf = 0
            for ((x,y,_,_),conf) in zip(xywh,confs):
                if max_conf < conf :
                    self.rx,self.ry = int(x),int(y)
                    max_conf = conf 
            self.cx = 320
            self.cy = 240
            self.lock_1.release()
            return
        # if id == None:
        #     self.id = -1
        #     self.lock_2.release()
        #     return
        # if self.id in id :
        #     for ind,(x,y,_,h) in enumerate(xywh):
        #         if id[ind] == self.id:
        #             self.cx = x
        #             self.cy = y

        #             self.cy = self.cy - int(h * 0.4)

        #             self.lock_1.release()
        #             return
        candidate = None
        length = 1000000000
        max_conf = 0
        self.rx = 320 
        self.ry = 240
        for ind,((x,y,_,h),cls,conf) in enumerate(zip(xywh,clses,confs)):
            if cls == 1:
                if max_conf < conf :
                    self.rx,self.ry = int(x),int(y)
                    max_conf = conf
                continue
            l = sqrt((x - 2 - 320) ** 2 + (y - (h * 0.4) -240)**2)
            if l < length:
                length = l
                candidate = ind
        self.cx,self.cy,_,h = xywh[candidate]

        self.cy = self.cy - int(h * 0.4)
        self.cx = self.cx - int(2)
        
        # self.id = id[candidate]
        self.id = 1
        self.lock_1.release()

    def move(self):
        x,y = pydirectinput.position()

        tar_x,tar_y = self.cx, self.cy
        cur_x,cur_y = self.rx, self.ry

        now_time = time.time()
        dx = self.x_pid.update(cur_x,tar_x,now_time)
        dy = self.y_pid.update(cur_y,tar_y,now_time)
        dx,dy = int(dx), int(dy)

        pydirectinput.moveTo(x + dx, y + dy, relative=True)
        logger.info("off_x:{},off_y:{},cur_x:{},cur_y:{},tar_x:{},tar_y:{}".format(dx,dy,cur_x,cur_y,tar_x,tar_y))

    def move_back(self):
        x,y = pydirectinput.position()
        
        off_x = 320-self.cx 
        off_y = 240-self.cy

        # length = max(1,sqrt(off_x**2+off_y**2))
        length = sqrt(off_x**2+off_y**2)
        if length == 0 and not self.mk.recoil :
            return
        length = max(1,length)
        w = 20 / length
        w = min(w,1000)
        w = max(w,0.95)

        off_x = int(off_x/w) if abs(off_x) > 2 else int(off_x)
        off_y = int(off_y/w) if abs(off_y) > 2 else int(off_y)

        off_x = off_x - ((320 - self.rx)/w if self.mk.recoil else 0)
        off_y = off_y - ((240 - self.ry)/w if self.mk.recoil else 0)

        off_x,off_y = int(off_x),int(off_y)
        pydirectinput.moveTo(x-off_x,y-off_y,relative=True)
        logger.info("off_x:{},off_y:{},w:{}".format(off_x,off_y,w))

    def end(self):
        if self.lock_1.locked():
        # if self.lock_1._value == 0:
            self.lock_1.release()

    def run(self):
        # global will_end
        while True:
            self.lock_1.acquire()
            if self.id != -1:
                self.move()
            if self.mk.will_end:
                break
            self.lock_2.release()
        logger.info("aim end")
