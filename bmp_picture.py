import struct
import strings
import argparse

graphic = True
try:
    import contextlib

    with contextlib.redirect_stdout(None):
        import pygame
        from pygame.locals import FULLSCREEN
except ImportError:
    graphic = False


class Bmp_file():
    def __init__(self, filename, pixels=False):
        bmp = open(filename, 'rb')
        self.bmp_arr = bmp.read()
        bmp.close()
        self.filename = filename
        if chr(self.bmp_arr[0]) + chr(self.bmp_arr[1]) == 'BM':
            print('Тип файла: BM (bmp файл)')
        else:
            print('Это не bmp файл')
            raise SystemExit()
        if struct.unpack('I', self.bmp_arr[6:10])[0] != 0:
            print('Что-то не так с файлом '
                  '(зарезервированные байты не равны 0)')
            raise SystemExit()
        if len(self.bmp_arr) != \
                struct.unpack('I', self.bmp_arr[2:6])[0]:
            print('Внимание, указанная в заголовке длина файла'
                  ' не равна фактической.')
        self.size = struct.unpack('I', self.bmp_arr[2:6])[0]

        self.offset = struct.unpack('I', self.bmp_arr[10:14])[0]
        self.title_size = struct.unpack('I', self.bmp_arr[14:18])[0]
        self.width = struct.unpack('I', self.bmp_arr[18:22])[0]
        self.height = struct.unpack('I', self.bmp_arr[22:26])[0]
        self.bit_to_pixel = struct.unpack('H', self.bmp_arr[28:30])[0]
        self.compression = struct.unpack('I', self.bmp_arr[30:34])[0]
        self.picture_size = struct.unpack('I', self.bmp_arr[34:38])[0]
        self.has_graphic = graphic
        self.pixels = pixels

        if self.has_graphic:
            import pyautogui
            self.window_width, self.window_height = pyautogui.size()

    def start_analyze(self):
        self.print_info()
        if self.has_graphic:
            if self.pixels:
                if (self.compression == 0 and self.bit_to_pixel >= 8) \
                        or self.bit_to_pixel == 32:
                    self.draw_without_pallete()
                elif self.compression == 0 and self.bit_to_pixel < 8:
                    self.draw_1()
                else:
                    self.pixels = False
                    self.draw_without_pallete()
            else:
                self.draw_without_pallete()

    def get_pallete(self):
        if self.bit_to_pixel == 1:
            pallete_arr = list(reversed(self.bmp_arr[14 + self.title_size:self.offset]))
            self.pallete = []
            self.pallete.append((int(pallete_arr[5]), int(pallete_arr[6]),
                                 int(pallete_arr[7]), int(pallete_arr[4])))
            self.pallete.append((int(pallete_arr[1]), int(pallete_arr[2]),
                                 int(pallete_arr[3]), int(pallete_arr[0])))
        elif self.bit_to_pixel == 8:
            pallete_arr = self.bmp_arr[14 + self.title_size:self.offset]
            self.pallete = []
            for i in range(len(pallete_arr) // 4):
                self.pallete.append((int(pallete_arr[i * 4 + 2]), int(pallete_arr[i * 4 + 1]),
                                     int(pallete_arr[i * 4]), int(pallete_arr[i * 4 + 3])))
        elif self.bit_to_pixel == 4:
            pallete_arr = self.bmp_arr[14 + self.title_size:self.offset]
            self.pallete = []
            for i in range(len(pallete_arr) // 4):
                self.pallete.append((int(pallete_arr[i * 4 + 2]), int(pallete_arr[i * 4 + 1]),
                                     int(pallete_arr[i * 4]), int(pallete_arr[i * 4 + 3])))
        self.bmp_arr = self.bmp_arr[self.offset:]

    def draw_pallete(self, screen, size):
        size = (size[0] + 10, size[1] + 10)
        p = (25, 25)
        t = 0
        if self.bit_to_pixel == 8:
            p = (10, 10)
            t = 16
        if self.bit_to_pixel == 1:
            p = (50, 50)
        if self.bit_to_pixel == 4:
            p = (20, 20)
            t = 4
        if self.bit_to_pixel == 1:
            pygame.draw.rect(screen, self.pallete[0],
                             ((size[0] + 10, 0), p))
            pygame.draw.rect(screen, self.pallete[1],
                             ((size[0] + 10, 50), p))
        else:
            index = 0
            for y in range(t):
                for x in range(t):
                    pygame.draw.rect(screen, self.pallete[index],
                                     ((size[0] + x * p[0], y * p[0]), p))
                    index += 1
        pygame.display.update()

    def draw_without_pallete(self):
        if self.bit_to_pixel == 1:
            self.draw_1()
            return
        pygame.init()
        pygame.display.set_caption("BMP")
        width, height = self.width, self.height
        while width < 200 or height < 200:
            width *= 2
            height *= 2
        screen = pygame.display.set_mode((width, height))
        if self.bit_to_pixel == 8:
            screen = pygame.display.set_mode(
                (width + 170, height))
        screen.fill(pygame.Color('white'))
        if self.pixels:
            pixel_w = width // self.width
            pixel_h = height // self.height
            self.bmp_arr = list(reversed(self.bmp_arr))
            index = 0
            index += ((self.bit_to_pixel // 8) * (self.width * 3)) % 4
            c = (0, 0, 0)
            for y in range(self.height):
                for x in range(self.width - 1, -1, -1):
                    if self.bit_to_pixel == 24:
                        c = (int(self.bmp_arr[index]),
                             int(self.bmp_arr[index + 1]), int(self.bmp_arr[index + 2]))
                        index += 3
                    if self.bit_to_pixel == 16:
                        t = [hex(r) for r in self.bmp_arr[index:index + 2]]
                        c = str(bin(int(t[0] + t[1][2:], 16)))[2:]
                        for _ in range(15 - len(c)):
                            c = '0' + c
                        c = (c[0:5] + c[0:3], c[5:10] + c[5:8], c[10:] + c[10:13])
                        c = (int(c[0], 2), int(c[1], 2), int(c[2], 2))
                        index += 2
                    if self.bit_to_pixel == 32:
                        c = (int(self.bmp_arr[index + 1]), int(self.bmp_arr[index + 2]),
                             int(self.bmp_arr[index + 3]), int(self.bmp_arr[index]))
                        index += 4
                    if self.bit_to_pixel == 8:
                        c = self.pallete[int(self.bmp_arr[index])]
                        index += 1

                    pygame.draw.rect(screen, c, ((x * pixel_w, y * pixel_h),
                                                 (pixel_w, pixel_h)))
                index += ((self.bit_to_pixel // 8) * (self.width * 3)) % 4
        else:
            image = pygame.image.load(self.filename)
            scale = pygame.transform.scale(image, (width, height))
            rect = image.get_rect()
            screen.blit(scale, rect)
        if self.bit_to_pixel == 8:
            self.draw_pallete(screen, (width, height))
        pygame.display.update()
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT or \
                        (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                    raise SystemExit()

    def draw_1(self):
        pygame.init()
        pygame.display.set_caption("BMP")
        width, height = self.width, self.height
        while width < 200 or height < 200:
            width *= 2
            height *= 2
        if self.bit_to_pixel == 1:
            screen = pygame.display.set_mode(
                (width + 70, height))
        # elif self.bit_to_pixel == 8:
        #     screen = pygame.display.set_mode(
        #         (width + 170, height))
        elif self.bit_to_pixel == 4:
            screen = pygame.display.set_mode(
                (width + 100, height))
        else:
            screen = pygame.display.set_mode((width, height))
        screen.fill(pygame.Color('white'))
        if self.pixels:
            pixel_w = width // self.width
            pixel_h = height // self.height
            self.bmp_arr = list(reversed(self.bmp_arr))
            index = 0
            index += ((self.bit_to_pixel // 8) * (self.width * 3)) % 4
            if self.bit_to_pixel == 1:
                for y in range(self.height):
                    for x in range(self.width, -1, -8 // self.bit_to_pixel):
                        b = str(bin(self.bmp_arr[index]))[2:]
                        for _ in range(8 - len(b)):
                            b = '0' + b
                        b = ''.join(list(reversed(b)))
                        for i in b:
                            c = self.pallete[int(i)]
                            pygame.draw.rect(screen, c, ((x * pixel_w, y * pixel_h),
                                                         (pixel_w, pixel_h)))
                            pygame.display.update()
                            x -= 1
                        index += 1
                    index += ((self.bit_to_pixel // 8) * (self.width * 3)) % 4
            # if self.bit_to_pixel == 8:
            #     for y in range(self.height):
            #         for x in range(self.width - 1, -1, -1):
            #             c = self.pallete[int(self.bmp_arr[index])]
            #             index += 1
            #             pygame.draw.rect(screen, c, ((x * pixel_w, y * pixel_h),
            #                                          (pixel_w, pixel_h)))
            if self.bit_to_pixel == 4:
                for y in range(self.height):
                    for x in range(self.width, -1, -8 // self.bit_to_pixel):
                        b = str(bin(self.bmp_arr[index]))[2:]
                        for _ in range(8 - len(b)):
                            b = '0' + b
                        b = ''.join(list(b))
                        p2 = int(b[0:4], 2)
                        p1 = int(b[4:], 2)
                        # print(p1,p2)
                        c = self.pallete[p1]
                        pygame.draw.rect(screen, c, ((x * pixel_w, y * pixel_h),
                                                     (pixel_w, pixel_h)))
                        pygame.display.update()
                        x -= 1
                        c = self.pallete[p2]
                        pygame.draw.rect(screen, c, ((x * pixel_w, y * pixel_h),
                                                     (pixel_w, pixel_h)))
                        # pygame.display.update()
                        x -= 1
                        index += 1
                    index += ((self.bit_to_pixel // 8) * (self.width * 3)) % 4

        else:
            image = pygame.image.load(self.filename)
            scale = pygame.transform.scale(image, (width, height))
            rect = image.get_rect()
            screen.blit(scale, rect)

        pygame.display.update()
        self.draw_pallete(screen, (width, height))
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT or \
                        (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                    raise SystemExit()

    def print_info(self):
        print('Размер файла в байтах: %s' % len(self.bmp_arr))
        print('Резервные поля равны 0')
        print('Смещение начала описания изображения: %s байт' % self.offset)
        print('Размер заголовка BITMAP: %s байт' % self.title_size)
        print('Ширина изображения в пикселях: %s' % self.width)
        print('Высота изображения в пикселях: %s' % self.height)
        print('Число плоскостей: %s (по умолчанию 1)'
              % struct.unpack('H', self.bmp_arr[26:28]))
        print('Бит на пиксель: %s. Возможно иметь %s цветов.'
              % (self.bit_to_pixel, 2 ** self.bit_to_pixel))
        if self.compression == 0:
            print('Тип сжатия: 0. Сжатие не используется.')
        else:
            print('Тип сжатия: %s' % self.compression)
        print('Размер изображения в байтах: %s' % self.picture_size)
        print('Горизонтальное расширение: %s пиксель/м'
              % struct.unpack('I', self.bmp_arr[38:42]))
        print('Вертикальное расширение: %s пиксель/м'
              % struct.unpack('I', self.bmp_arr[42:46]))
        print(
            'Количество цветов в палитре: %s '
            '(если количество бит на пиксель больше 8, то палитры нет)'
            % struct.unpack('I', self.bmp_arr[46:50]))
        print('Количество "важных" цветов: %s (не используется)'
              % struct.unpack('I', self.bmp_arr[50:54]))
        if self.bit_to_pixel > 8:
            self.bmp_arr = self.bmp_arr[self.offset:]
        else:
            self.get_pallete()


def parse_args():
    '''Парсер аргументов командной строки'''
    parser = argparse.ArgumentParser(description='Разбор bmp файла.')
    parser.add_argument('filename', help=strings.FILENAME)
    parser.add_argument('-p', '--pixels', action='store_const',
                        const=True, default=False, help=strings.PIXEL)
    return parser


def main():
    parser = parse_args()
    args = parser.parse_args()
    print(args)
    try:
        s = Bmp_file(filename=args.filename, pixels=args.pixels)
    except FileNotFoundError:
        print('Файл не найден')
        return
    except:
        import sys
        e = sys.exc_info()[1]
        print(e.args[0])
        return
    s.start_analyze()


if __name__ == "__main__":
    main()
