import sys, os
import contextlib
from math import *
with contextlib.redirect_stdout(None):
    import pygame
    from pygame.locals import *

pygame.init()
myfont = pygame.font.SysFont('monospace', 90)
path = os.path.join(os.path.split(__file__)[0], "files")

debug = 0

pygame.display.set_caption("Ray Casting")
pygame.mouse.set_visible(False)

SCREEN = pygame.display.set_mode((1360, 768), pygame.FULLSCREEN | pygame.HWSURFACE | pygame.DOUBLEBUF)

rotation = 0.002
move = 0.1
strafe = 0.04
wall_height = 1.25
resolution = 6
map_size = int((768 / 680) * 64)

texture = pygame.image.load(os.path.join(path, "wall.png"))
texture = texture.convert()
textureW = texture.get_width()
textureH = texture.get_height()
textureArr = pygame.PixelArray(texture)

def create_level(file):
    if file[-4:] != ".txt":
        file += ".txt"
    f = open(os.path.join(path, file), "r")
    file = f.readlines()

    for x, y in enumerate(file):
        file[x] = list(y.rstrip("\n"))
        for z, w in enumerate(file[x]):
            if w == " ":
                file[x][z] = 0
            else:
                file[x][z] = int(w)
    f.close()
    mapLength = len(file)
    mapWidth = len(file[0])
    map = []

    for x, y in enumerate(file):
        map.append([])
        for z, w in enumerate(file[x]):
            if w == 0:
                map[x].append(0)
            else:
                map[x].append(w)

    if debug == 1:
        print(map)
    return mapLength, mapWidth, map

def main():
    mapLength, mapWidth, map = create_level('Level')

    posX, posY = 8.5, 10.5
    dirX, dirY = 1.0, 0.0
    planeX, planeY = 0.0, 0.66
    ammo = 30

    while True:
        for event in pygame.event.get():
            if event.type == KEYDOWN:
                if event.key == K_ESCAPE:
                    pygame.quit()
                    sys.exit()
            if event.type == QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if ammo >= 1:
                    ammo -= 1

        pygame.draw.rect(SCREEN, (127, 217, 255), (0, 0, 1360, (768 - map_size) / 2))
        pygame.draw.rect(SCREEN, (0, 128, 0), (0, (768) / 2, 1360, (768) / 2))

        for x in range(0, 1360, resolution):
            cameraX = 2 * x / 1360 - 1
            rayDirX = dirX + planeX * cameraX
            rayDirY = dirY + planeY * cameraX
            rayX = posX
            rayY = posY

            # which map box currently in
            mapX = int(rayX)
            mapY = int(rayY)

            # length of ray from x/y side to next x/y side
            deltaDistX = sqrt(1 + rayDirY ** 2 / rayDirX ** 2)
            deltaDistY = sqrt(1 + rayDirX ** 2 / rayDirY ** 2)

            # Calculate step and initial sideDist
            if rayDirX < 0:
                stepX = -1
                sideDistX = (rayX - mapX) * deltaDistX
            else:
                stepX = 1
                sideDistX = (mapX + 1.0 - rayX) * deltaDistX

            if rayDirY < 0:
                stepY = -1
                sideDistY = (rayY - mapY) * deltaDistY
            else:
                stepY = 1
                sideDistY = (mapY + 1 - rayY) * deltaDistY

            # perform DDA
            while True:
                # jump to next map square
                if sideDistX < sideDistY:
                    sideDistX += deltaDistX
                    mapX += stepX
                    side = 0
                else:
                    sideDistY += deltaDistY
                    mapY += stepY
                    side = 1

                # check if ray hits wall
                if mapX >= mapLength or mapY >= mapWidth or mapX < 0 or mapY < 0 or map[mapX][mapY] > 0:
                    if map[mapX][mapY] == 2:
                        cond = 1
                    else:
                        cond = 0
                        break

            # calculate distance projected on camera
            if side == 0:
                rayLength = (mapX - rayX + (1 - stepX) / 2) / rayDirX
            else:
                rayLength = (mapY - rayY + (1 - stepY) / 2) / rayDirY

            # calculate height of line to draw
            lineHeight = (768 / rayLength) * wall_height

            # calculate lowest/highest pixel to fill stripe
            drawStart = -lineHeight / 2 + (768) / 2
            drawEnd = lineHeight / 2 + (768) / 2

            # calculate wall hit
            if side == 0:
                wallX = rayY + rayLength * rayDirY
            else:
                wallX = rayX + rayLength * rayDirX
            wallX = abs((wallX - floor(wallX)) - 1)

            # find texture coordinates
            texX = int(wallX * textureW)
            if side == 0 and rayDirX > 0:
                texX = textureW - texX - 1
            if side == 1 and rayDirY < 0:
                texX = textureW - texX - 1

            for y in range(textureH):
                # Ignore pixels that are off of the screen
                if drawStart + (lineHeight / textureH) * (y + 1) < 0:
                    continue
                if drawStart + (lineHeight / textureH) * y > 768:
                    break

                # Load pixel's color from array
                color = pygame.Color(textureArr[texX][y])

                # Darkens environment with distance
                darker = 255.0 - abs(int(rayLength * 32)) * 0.55
                if darker < 1:
                    darker = 1
                if darker > 255:
                    darker = 255

                # change lighting of different sides
                if side == 1:
                    darker = darker * 0.4

                # adjust lighting
                new_color = []
                for i, value in enumerate(color):
                    if i == 0:
                        continue
                    new_color.append(value * (darker / 255))
                color = tuple(new_color)
                pygame.draw.line(SCREEN, color, (x, drawStart + (lineHeight / textureH) * y), (x, drawStart + (lineHeight / textureH) * (y + 1)), resolution)

        # minimap
        for x in range(mapLength):
            for y in range(mapWidth):
                if map[y][x] != 0:
                    pygame.draw.rect(SCREEN, (128, 0, 0), ((x * (map_size / mapLength) + 1360) - map_size,
                                     y * (map_size / mapWidth) + 768 - map_size, (map_size / mapLength), (map_size / mapWidth)))

        pos_on_map = (posY * (map_size / mapWidth) + 1360 - map_size, posX * (map_size / mapLength) + 768 - map_size)

        # Draw player on mini map
        pygame.draw.rect(SCREEN, (255, 0, 0), pos_on_map + (4, 4))

        # Movement controls
        keys = pygame.key.get_pressed()

        if keys[K_w]:
            if not map[int(posX + dirX * 0.1)][int(posY)]:
                posX += dirX * 0.1
            if not map[int(posX)][int(posY + dirY * 0.1)]:
                posY += dirY * 0.1

        if keys[K_a]:
            if not map[int(posX + dirY * 0.04)][int(posY)]:
                posX += dirY * 0.04
            if not map[int(posX)][int(posY - dirX * 0.04)]:
                posY -= dirX * 0.04

        if keys[K_s]:
            if not map[int(posX - dirX * 0.1)][int(posY)]:
                posX -= dirX * 0.1
            if not map[int(posX)][int(posY - dirY * 0.1)]:
                posY -= dirY * 0.1

        if keys[K_d]:
            if not map[int(posX - dirY * 0.04)][int(posY)]:
                posX -= dirY * 0.04
            if not map[int(posX)][int(posY + dirX * 0.04)]:
                posY += dirX * 0.04

        if keys[K_r]:
            ammo = 30

        # Look left and right
        # Mouse input
        difference = pygame.mouse.get_pos()[0] - (1360 / 2)
        pygame.mouse.set_pos([1360 / 2, 768 / 2])

        # Vector rotation
        if difference != 0:
            temp = dirX
            dirX = dirX * cos(difference * 0.002) - dirY * sin(difference * 0.002)
            dirY = temp * sin(difference * 0.002) + dirY * cos(difference * 0.002)
            temp = planeX
            planeX = planeX * cos(difference * 0.002) - planeY * sin(difference * 0.002)
            planeY = temp * sin(difference * 0.002) + planeY * cos(difference * 0.002)

        textsurface = myfont.render('Ammo: ' + str(ammo), 1, (255, 0, 0))
        SCREEN.blit(textsurface, (100, 680))

        pygame.display.update()

if __name__ =="__main__":
    main()