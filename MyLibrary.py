# MyLibrary.py - 优化版

import sys, time, random, math, pygame
from pygame.locals import *


def print_text(font, x, y, text, color=(255, 255, 255)):
    """
    在屏幕上绘制文本
    
    Args:
        font: Pygame 字体对象
        x: X 坐标
        y: Y 坐标
        text: 要显示的文本
        color: RGB 颜色元组，默认白色
    """
    imgText = font.render(text, True, color)
    screen = pygame.display.get_surface()
    screen.blit(imgText, (x, y))


class MySprite(pygame.sprite.Sprite):
    """自定义精灵类，支持动画和位置管理"""
    
    def __init__(self):
        pygame.sprite.Sprite.__init__(self)
        self.master_image = None
        self.frame = 0
        self.old_frame = -1
        self.frame_width = 1
        self.frame_height = 1
        self.first_frame = 0
        self.last_frame = 0
        self.columns = 1
        self.last_time = 0
        self.direction = 0
        self.velocity = Point(0.0, 0.0)

    # X property
    def _getx(self):
        return self.rect.x
    
    def _setx(self, value):
        self.rect.x = value
    
    X = property(_getx, _setx)

    # Y property
    def _gety(self):
        return self.rect.y
    
    def _sety(self, value):
        self.rect.y = value
    
    Y = property(_gety, _sety)

    # position property
    def _getpos(self):
        return self.rect.topleft
    
    def _setpos(self, pos):
        self.rect.topleft = pos
    
    position = property(_getpos, _setpos)

    def load(self, filename, width, height, columns):
        """
        从精灵表加载图像
        
        Args:
            filename: 图片文件路径
            width: 单帧宽度
            height: 单帧高度
            columns: 精灵表列数
        """
        try:
            self.master_image = pygame.image.load(filename).convert_alpha()
        except pygame.error as e:
            print(f"错误：无法加载图片 {filename} - {e}")
            # 创建一个占位图片
            self.master_image = pygame.Surface((width, height))
            self.master_image.fill((255, 0, 255))  # 洋红色占位
        
        self.frame_width = width
        self.frame_height = height
        self.rect = Rect(0, 0, width, height)
        self.columns = columns
        
        # 自动计算总帧数
        rect = self.master_image.get_rect()
        self.last_frame = (rect.width // width) * (rect.height // height) - 1

    def update(self, current_time, rate=30):
        """
        更新动画帧
        
        Args:
            current_time: 当前时间（毫秒）
            rate: 帧切换速率（毫秒）
        """
        # 更新动画帧编号
        if current_time > self.last_time + rate:
            self.frame += 1
            if self.frame > self.last_frame:
                self.frame = self.first_frame
            self.last_time = current_time

        # 仅在帧变化时重新截取图像
        if self.frame != self.old_frame:
            frame_x = (self.frame % self.columns) * self.frame_width
            frame_y = (self.frame // self.columns) * self.frame_height
            rect = Rect(frame_x, frame_y, self.frame_width, self.frame_height)
            self.image = self.master_image.subsurface(rect)
            self.old_frame = self.frame

    def __str__(self):
        return "{},{},{},{},{},{},{}".format(
            self.frame, self.first_frame, self.last_frame,
            self.frame_width, self.frame_height, self.columns, self.rect
        )


class Point(object):
    """二维点/向量类"""
    
    def __init__(self, x, y):
        self.__x = float(x)
        self.__y = float(y)

    # X property
    def getx(self):
        return self.__x
    
    def setx(self, x):
        self.__x = float(x)
    
    x = property(getx, setx)

    # Y property
    def gety(self):
        return self.__y
    
    def sety(self, y):
        self.__y = float(y)
    
    y = property(gety, sety)

    def __str__(self):
        return "{{X:{:.0f},Y:{:.0f}}}".format(self.__x, self.__y)
