本项目整体的架构是通过obs进行屏幕捕捉和推流，然后使用微调后的yolov8进行图像识别。视角的移动使用pydirectinput实现，使用pid进行移动控制。

具体实现上，使用三个线程，分别负责键盘输入监听、屏幕捕捉识别、鼠标移动控制。主要是因为使用pydirectinput包实现鼠标移动会有较高的延迟，如果放在一个线程里面实现，会出现严重的掉帧情况。所以我是用了三个线程加上相关的同步互斥机制，实现了高帧率的输出

dataset文件夹下面是全部的数据集，data文件夹下面是全部标记好的数据集，由于前后改过一些数据集，所以会有很多个。数据集标注是用label-stutdio实现的。

runs文件夹下面是训练后的模型权重

有关aimbot的实现放在了aimbot文件夹下，main.py可以看做一个驱动，调用了这个aimbot包

preprocess.ipynb对处理好的数据集进行划分

train.ipynb进行模型的微调

requirements.txt里面包含了所有需要的依赖，但是由于各种环境的问题，不一定能够在老师这里完全配好）

待完成的地方：

1. 探索更加高效的pid调参
2. 使用鼠标驱动作为鼠标移动的输入，理论上可以减少控制延迟，增加控制效果
3. 使用OpenCV或者相关的包进行屏幕捕捉，减少使用成本

待完成的地方可能在今晚就能够实现。
