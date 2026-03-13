# A* pathfinding algorithm
import pygame
import math
from queue import PriorityQueue
import sys
import os
import random
from PIL import Image, ImageSequence


def resource_path(relative_path):
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), relative_path)


pygame.init()
pygame.mixer.init()

# creating the window
width = 800
window = pygame.display.set_mode((width, width))
pygame.display.set_caption("A* algorithm")
font = pygame.freetype.Font(resource_path("runescape.ttf"), 38)

# creating variables for colors
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
DARKBLUE = (100, 100, 180)
YELLOW = (255, 255, 0)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
PURPLE = (128, 0, 128)
ORANGE = (255, 165, 0)
GREY = (128, 128, 128)
TURQUOISE = (64, 224, 208)

clock = pygame.time.Clock()

progressSound = pygame.mixer.Sound(resource_path("yipee.mp3"))
pygame.mixer.music.load(resource_path("melody.mp3"))
pygame.mixer.music.play(-1)

button_font = pygame.font.Font(None, 48)


class GifPlayer:
    def __init__(self, gif_path, delay, pos=(0, 0)):
        self.frames = []
        self.current_frame = 0
        self.last_update = 0
        self.frame_delay = delay  # ms between frames
        self.pos = pos

        # Load GIF using PIL
        pil_image = Image.open(resource_path(gif_path))
        for frame in ImageSequence.Iterator(pil_image):
            # Convert PIL image to PyGame surface
            frame = frame.convert("RGBA")
            frame_data = frame.tobytes()
            size = frame.size
            mode = frame.mode
            pg_frame = pygame.image.fromstring(frame_data, size, mode)
            self.frames.append(pg_frame)

    def update(self, current_time):
        if current_time - self.last_update > self.frame_delay:
            self.current_frame = (self.current_frame + 1) % len(self.frames)
            self.last_update = current_time

    def draw(self, screen):
        if self.frames:
            screen.blit(self.frames[self.current_frame], self.pos)


class animatedButton:
    def __init__(self, x, y, width, height, text, color, reset):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.color = color
        self.spacing = font.get_sized_height() + 5
        self.reset = reset

        self.fadeAlpha = 0
        self.fadeDir = 1
        self.fadeSpeed = 10

        self.timer = 0
        self.index = 10000
        self.speed = 0.01
        self.finished = False

    def draw(self, screen):

        if not self.finished:
            self.timer += 1
            if self.timer >= self.speed:
                self.timer = 0
                self.index += 1
                if self.index >= len(self.text):
                    self.finished = True

        if self.fadeAlpha >= 200:
            self.fadeAlpha = 255
        else:
            self.fadeAlpha += self.fadeDir * self.fadeSpeed

        if self.reset == True:
            self.fadeAlpha = 0
            self.index = 100000
            self.finished = False
            # self.timer = False
            self.reset = False

        displayed_text = self.text[: self.index]

        alphaColor = (*BLACK, self.fadeAlpha)

        current_color = self.color
        pygame.draw.rect(screen, current_color, self.rect)
        # pygame.draw.rect(screen, BLACK, self.rect, 3)

        n = displayed_text.split("\n")
        yShift = 10
        xShift = 20
        for i in range(0, len(n)):
            font.render_to(
                window,
                (self.rect.x + xShift, self.rect.y + yShift),
                str(n[i]),
                alphaColor,
            )
            yShift += 40


class Button:
    def __init__(self, x, y, width, height, text, color, hover_color):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.color = color
        self.hover_color = hover_color
        self.is_hovered = False
        self.spacing = font.get_sized_height() + 5

    def draw(self, screen):
        current_color = self.hover_color if self.is_hovered else self.color
        pygame.draw.rect(screen, current_color, self.rect)
        pygame.draw.rect(screen, BLACK, self.rect, 3)

        n = self.text.split("\n")
        temp = 10
        for i in range(0, len(n)):
            font.render_to(
                window, (self.rect.x + 20, self.rect.y + temp), str(n[i]), WHITE
            )
            temp += 40

    def check_hover(self, mouse_pos):
        self.is_hovered = self.rect.collidepoint(mouse_pos)

    def is_clicked(self, mouse_pos):
        return self.rect.collidepoint(mouse_pos)


class startMenu:
    def __init__(self):
        self.Tutorial = Button(300, 220, 200, 70, "Tutorial", DARKBLUE, BLUE)
        self.Title = Button(250, 0, 300, 70, "Pathfinding...?", BLACK, BLACK)
        self.Sandbox = Button(300, 320, 200, 70, "Sandbox", DARKBLUE, BLUE)

    def handle_event(self, event, mouse_pos):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.Tutorial.is_clicked(mouse_pos):
                return "tutorial"
            elif self.Sandbox.is_clicked(mouse_pos):
                return "sandbox"
        return None

    def update(self, mouse_pos):
        self.Tutorial.check_hover(mouse_pos)
        self.Sandbox.check_hover(mouse_pos)

    def draw(self, window):
        window.fill(WHITE)
        self.Tutorial.draw(window)
        self.Title.draw(window)
        self.Sandbox.draw(window)


class ObstaclesAndNeighbours:
    def __init__(self):
        self.count = 0

        self.imp = pygame.image.load(resource_path("grid.png"))
        self.imp = pygame.transform.scale_by(self.imp, 0.8)

        self.imp2 = pygame.image.load(resource_path("grid_with_blocks.png"))
        self.imp2 = pygame.transform.scale_by(self.imp2, 0.5)

        self.Text = animatedButton(
            0, 0, 800, 400, "Lets have a look at creating an actual maze.", WHITE, False
        )
        self.Next = Button(300, 720, 200, 50, "Next", DARKBLUE, BLUE)
        self.Return = Button(0, 730, 150, 60, "Back", DARKBLUE, BLUE)

    def filehandler(self, file, forward):
        if forward == True:
            with open(resource_path(file)) as f:
                f = f.read()
                f = f.split("\n\n")

                if self.count >= len(f) - 1:
                    return "exam"
                else:
                    self.count += 1
                    self.Text.text = f[self.count]

                if self.count >= len(f) - 1:
                    self.Next.text = "Finish"
                else:
                    self.Next.text = "Next"
        elif forward == False:
            with open(resource_path(file)) as f:
                f = f.read()
                f = f.split("\n\n")
                if self.count <= 0:
                    return "start"
                else:
                    self.count -= 1
                    self.Text.text = f[self.count]
                    self.Next.text = "Next"

    def update(self, mouse_pos):
        self.Next.check_hover(mouse_pos)
        self.Return.check_hover(mouse_pos)

    def draw(self, window):

        window.fill(WHITE)

        self.Text.draw(window)
        self.Next.draw(window)
        self.Return.draw(window)
        x = 100
        y = 300

        window.blit(self.imp, (x, y))

        if self.count >= 6:
            self.imp = pygame.image.load(resource_path("grid_with_blocks.png"))
            self.imp = pygame.transform.scale_by(self.imp, 0.8)

        if self.count >= 9:
            self.imp = pygame.image.load(resource_path("Start_node.png"))
            self.imp = pygame.transform.scale_by(self.imp, 1.2)

        if self.count >= 11:
            self.imp = pygame.image.load(resource_path("Others.png"))
            self.imp = pygame.transform.scale_by(self.imp, 0.7)

        if self.count >= 13:
            self.imp = pygame.image.load(resource_path("area.png"))
            self.imp = pygame.transform.scale_by(self.imp, 0.8)

        if self.count >= 15:
            self.imp = pygame.image.load(resource_path("distances.png"))
            self.imp = pygame.transform.scale_by(self.imp, 0.9)

        if self.count >= 17:
            self.imp = pygame.image.load(resource_path("lookBlock.png"))
            self.imp = pygame.transform.scale_by(self.imp, 1.1)

        if self.count >= 18:
            self.imp = pygame.image.load(resource_path("stepOne.png"))
            self.imp = pygame.transform.scale_by(self.imp, 0.7)

        if self.count >= 19:
            self.imp = pygame.image.load(resource_path("stepTwo.png"))
            self.imp = pygame.transform.scale_by(self.imp, 0.7)

        if self.count >= 20:
            self.imp = pygame.image.load(resource_path("stepThree.png"))
            self.imp = pygame.transform.scale_by(self.imp, 0.7)

        if self.count >= 21:
            self.imp = pygame.image.load(resource_path("stepFour.png"))
            self.imp = pygame.transform.scale_by(self.imp, 0.7)

    def handle_event(self, event, mouse_pos):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.Next.is_clicked(mouse_pos):
                self.Text.reset = True
                return self.filehandler("ObstaclesAndNeighbours.txt", True)
            if self.Return.is_clicked(mouse_pos):
                return self.filehandler("ObstaclesAndNeighbours.txt", False)


class ExplainHeuristics:
    def __init__(self):
        self.count = 0

        self.imp = pygame.image.load(resource_path("H-photo.png"))

        self.gif = GifPlayer("yellow.gif", 300, pos=(150, 220))
        self.gif2 = GifPlayer("wrongPath.gif", 300, pos=(150, 220))

        self.Text = animatedButton(
            0, 0, 800, 400, "Lets have a look at what heuristics are.", WHITE, False
        )
        self.Next = Button(300, 720, 200, 50, "Next", DARKBLUE, BLUE)
        self.Return = Button(0, 730, 150, 60, "Back", DARKBLUE, BLUE)

    def filehandler(self, file, forward):
        if forward == True:
            with open(resource_path(file)) as f:
                f = f.read()
                f = f.split("\n\n")

                if self.count >= len(f) - 1:
                    return "obstacles"
                else:
                    self.count += 1
                    self.Text.text = f[self.count]

                if self.count >= len(f) - 1:
                    self.Next.text = "Finish"
                else:
                    self.Next.text = "Next"
        elif forward == False:
            with open(resource_path(file)) as f:
                f = f.read()
                f = f.split("\n\n")
                if self.count <= 0:
                    return "nodes"
                else:
                    self.count -= 1
                    self.Text.text = f[self.count]
                    self.Next.text = "Next"

    def update(self, mouse_pos):
        self.Next.check_hover(mouse_pos)
        self.Return.check_hover(mouse_pos)

    def draw(self, window):
        window.fill(WHITE)
        currentTime = pygame.time.get_ticks()

        self.Text.draw(window)
        self.Next.draw(window)
        self.Return.draw(window)

        if self.count <= 3:
            self.imp = pygame.image.load(resource_path("H-photo.png"))
            window.blit(self.imp, (100, 200))

        if self.count == 4:
            self.gif.draw(window)
            self.gif.update(currentTime)

        if self.count == 5:
            self.imp = pygame.image.load(resource_path("toB.png"))
            window.blit(self.imp, (100, 200))

        if self.count == 6:
            self.gif2.draw(window)
            self.gif2.update(currentTime)

        if self.count == 7:
            self.imp = pygame.image.load(resource_path("checkAll.png"))
            window.blit(self.imp, (100, 200))

    def handle_event(self, event, mouse_pos):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.Next.is_clicked(mouse_pos):
                self.Text.reset = True
                return self.filehandler("Heuristics.txt", True)
            if self.Return.is_clicked(mouse_pos):
                return self.filehandler("Heuristics.txt", False)


class ExplainNodes:
    def __init__(self):
        self.count = 0

        self.Text = animatedButton(0, 0, 800, 400, "Well what is a node?", WHITE, False)
        self.Next = Button(300, 720, 200, 50, "Next", DARKBLUE, BLUE)
        self.Return = Button(0, 730, 150, 60, "Back", DARKBLUE, BLUE)

        self.imp = pygame.image.load(resource_path("Node.png"))
        self.imp2 = pygame.image.load(resource_path("realNode.png"))

        self.imp = pygame.transform.scale(
            self.imp, (self.imp.get_width() * 2, self.imp.get_height() * 2)
        )
        self.imp2 = pygame.transform.scale(
            self.imp2, (self.imp2.get_width() / 2.5, self.imp2.get_height() / 2.5)
        )

        self.x1 = 600
        self.y1 = 500

        self.x2 = 0
        self.y2 = 400

    def filehandler(self, file, forward):
        if forward == True:
            with open(resource_path(file)) as f:
                f = f.read()
                f = f.split("\n\n")

                if self.count >= len(f) - 1:
                    return "heuristic"
                else:
                    self.count += 1
                    self.Text.text = f[self.count]

                if self.count >= len(f) - 1:
                    self.Next.text = "Finish"
                else:
                    self.Next.text = "Next"
        elif forward == False:
            with open(resource_path(file)) as f:
                f = f.read()
                f = f.split("\n\n")
                if self.count <= 0:
                    return "tutorial"
                else:
                    self.count -= 1
                    self.Text.text = f[self.count]
                    self.Next.text = "Next"

    def update(self, mouse_pos):
        self.Next.check_hover(mouse_pos)
        self.Return.check_hover(mouse_pos)

    def draw(self, window):
        window.fill(WHITE)

        self.Text.draw(window)
        self.Next.draw(window)
        self.Return.draw(window)

        window.blit(self.imp, (self.x1, self.y1))
        window.blit(self.imp2, (self.x2, self.y2))

        if self.count >= 1:
            self.imp2 = pygame.image.load(resource_path("realNode.png"))
            self.imp2 = pygame.transform.scale_by(self.imp2, 0.5)
            self.x2 = 110
            self.y2 = 220

        if self.count >= 2:
            self.imp2 = pygame.image.load(resource_path("realNode.png"))
            self.imp2 = pygame.transform.scale_by(self.imp2, 0.4)
            self.x2 = 0
            self.y2 = 400

            self.imp = pygame.image.load(resource_path("Node.png"))
            self.imp = pygame.transform.scale_by(self.imp, 2.5)
            self.x1 = 350
            self.y1 = 250

        if self.count >= 3:
            self.imp = pygame.image.load(resource_path("Node.png"))
            self.imp = pygame.transform.scale_by(self.imp, 2)
            self.x1 = 600
            self.y1 = 500

        if self.count >= 6:
            self.imp2 = pygame.image.load(resource_path("nodeA.png"))
            self.imp2 = pygame.transform.scale_by(self.imp2, 0.7)
            self.x2 = 0
            self.y2 = 300

    def handle_event(self, event, mouse_pos):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.Next.is_clicked(mouse_pos):
                self.Text.reset = True
                return self.filehandler("nodes.txt", True)
            if self.Return.is_clicked(mouse_pos):
                return self.filehandler("nodes.txt", False)


class Exam:
    def __init__(self):
        self.count = 0
        self.userText = ""
        self.Text = animatedButton(
            0,
            0,
            800,
            40,
            "lets have a go at answering some questions now.",
            WHITE,
            False,
        )

    def update(self, mouse_pos):
        pass

    def filehandler(self, file):
        with open(resource_path(file)) as f:
            f = f.read()
            f = f.split("\n\n")

            if self.count >= len(f) - 1:
                return "heuristic"
            else:
                self.count += 1
                self.Text.text = f[self.count]

    def checkAnswer(self, text, correct):
        if text == correct:
            return True
        else:
            return False

    def draw(self, window):
        window.fill(WHITE)
        self.Text.draw(window)
        font.render_to(window, (20, 150), self.userText, BLACK)

    def handle_event(self, event, mouse_pos):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_BACKSPACE:
                self.userText = self.userText[:-1]
            elif event.key == pygame.K_RETURN:
                if self.count == 0:
                    self.filehandler("Exam.txt")
                elif self.checkAnswer(self.userText, "heuristics") and self.count <= 1:
                    self.filehandler("Exam.txt")
                elif self.checkAnswer(self.userText, "C") and self.count == 2:
                    self.filehandler("Exam.txt")
            else:
                self.userText += event.unicode


class Tutorial:
    def __init__(self):
        self.count = 0
        self.Text = animatedButton(0, 0, 800, 400, "Welcome", WHITE, False)
        self.Next = Button(350, 620, 150, 60, "Next", DARKBLUE, BLUE)
        self.Return = Button(0, 730, 150, 60, "Back", DARKBLUE, BLUE)
        self.gif = GifPlayer("AStar.gif", 100, pos=(225, 220))

    def update(self, mouse_pos):
        self.Next.check_hover(mouse_pos)
        self.Return.check_hover(mouse_pos)

    def filehandler(self, file, forward):
        if forward == True:
            with open(resource_path(file)) as f:
                f = f.read()
                f = f.split("\n\n")

                if self.count >= len(f) - 1:
                    progressSound.play()
                    return "nodes"
                else:
                    self.count += 1
                    self.Text.text = f[self.count]

                if self.count >= len(f) - 1:
                    self.Next.text = "Finish"
                else:
                    self.Next.text = "Next"

        elif forward == False:
            with open(resource_path(file)) as f:
                f = f.read()
                f = f.split("\n\n")
                if self.count <= 0:
                    return "start"
                else:
                    self.count -= 1
                    self.Text.text = f[self.count]
                    self.Next.text = "Next"

    def handle_event(self, event, mouse_pos):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.Next.is_clicked(mouse_pos):
                self.Text.reset = True
                return self.filehandler("texts.txt", True)

            if self.Return.is_clicked(mouse_pos):
                return self.filehandler("texts.txt", False)

    def draw(self, window):
        window.fill(WHITE)
        currentTime = pygame.time.get_ticks()
        self.Next.draw(window)
        self.Text.draw(window)
        self.Return.draw(window)
        if self.count >= 3 and self.count <= 5:
            self.gif.draw(window)
            self.gif.update(currentTime)


class Node:
    def __init__(self, row, col, width, total_rows):
        self.row = row
        self.col = col
        self.x = row * width
        self.y = col * width
        self.color = WHITE
        self.neighbours = []
        self.width = width
        self.total_rows = total_rows

    # identfying different states of the cubes in the grid with different colors
    def get_pos(self):
        return self.row, self.col

    def isClosed(self):
        return self.color == RED

    def isOpen(self):
        return self.color == GREEN

    def isBlock(self):
        return self.color == BLACK

    def isStart(self):
        return self.color == ORANGE

    def isEnd(self):
        return self.color == TURQUOISE

    # setting different blocks in the grid to different colors to represent different objects
    def reset(self):
        self.color = WHITE

    def makeClosed(self):
        self.color = RED

    def makeOpen(self):
        self.color = GREEN

    def makeBlock(self):
        self.color = BLACK

    def makeStart(self):
        self.color = ORANGE

    def makeEnd(self):
        self.color = TURQUOISE

    def makePath(self):
        self.color = PURPLE

    # creating the method to allow the user to draw
    def draw(self, window):
        pygame.draw.rect(window, self.color, (self.x, self.y, self.width, self.width))

    # checking neighbours of each traversable node
    def updateNeighbours(self, grid):
        self.neighbours = []
        if (
            self.row < self.total_rows - 1
            and not grid[self.row + 1][self.col].isBlock()
        ):  # DOWN
            self.neighbours.append(grid[self.row + 1][self.col])

        if self.row > 0 and not grid[self.row - 1][self.col].isBlock():  # UP
            self.neighbours.append(grid[self.row - 1][self.col])

        if (
            self.col < self.total_rows - 1
            and not grid[self.row][self.col + 1].isBlock()
        ):  # RIGHT
            self.neighbours.append(grid[self.row][self.col + 1])

        if self.col > 0 and not grid[self.row][self.col - 1].isBlock():  # LEFT
            self.neighbours.append(grid[self.row][self.col - 1])

    def __lt__(self, other):
        return False


class Sandbox:
    def __init__(self):
        self.BackToStart = Button(250, 720, 300, 70, "Back", DARKBLUE, BLUE)

        self.ROWS = 50
        self.grid = self.makeGrid(self.ROWS, width)
        self.start = None
        self.end = None
        self.started = False

    # setting up the heuristic function for the pathfindnig algorithm
    @staticmethod
    def h(p1, p2):
        x1, y1 = p1
        x2, y2 = p2
        return abs(x1 - x2) + abs(y1 - y2)

    @staticmethod
    def reconstruct_path(came_from, current, draw):
        while current in came_from:
            current = came_from[current]
            current.makePath()
            draw()

    def algorithm(self, draw, grid, start, end):
        count = 0
        open_set = PriorityQueue()

        # we start by putting the start node in the open set
        open_set.put((0, count, start))

        # this keeps track of where we came from, what nodes came from where, so we can find the best path at the end
        came_from = {}

        # keeps track of the current shortest distance to get from the start node to this node
        g_score = {node: float("inf") for row in grid for node in row}
        g_score[start] = 0

        # keeps track of our predicted distance to this node
        f_score = {node: float("inf") for row in grid for node in row}

        # we set the initial f score to be the heuristic
        f_score[start] = self.h(start.get_pos(), end.get_pos())

        # checks if there is any item in the piority queue
        open_set_hash = {start}

        while not open_set.empty():
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()

            # this allows us to get the minimum f score and the node associated from that
            current = open_set.get()[2]
            open_set_hash.remove(current)

            # if we have reached the end node, we have finished the pathfind
            if current == end:
                self.reconstruct_path(came_from, end, draw)
                end.makeEnd()
                return True

            # otherwise, consider all the neighbours of the current node
            for neighbour in current.neighbours:
                # calculate the temporary g score of each node
                temp_g_score = g_score[current] + 1

                # if the temporary g score is less than the g score stored in the table..
                if temp_g_score < g_score[neighbour]:
                    # update the g score, since we have found a better path
                    came_from[neighbour] = current
                    g_score[neighbour] = temp_g_score
                    f_score[neighbour] = temp_g_score + self.h(
                        neighbour.get_pos(), end.get_pos()
                    )

                    # add the node into the open set hash
                    if neighbour not in open_set_hash:
                        count += 1
                        open_set.put((f_score[neighbour], count, neighbour))
                        open_set_hash.add(neighbour)
                        neighbour.makeOpen()

            draw()

            if current != start:
                current.makeClosed()

            pygame.time.delay(20)

        return False

    # creating a grid on screen
    @staticmethod
    def makeGrid(rows, width):
        grid = []
        gap = width // rows
        for i in range(rows):
            grid.append([])
            for j in range(rows):
                node = Node(i, j, gap, rows)
                grid[i].append(node)

        return grid

    @staticmethod
    def drawGrid(window, rows, width):
        gap = width // rows
        # this multiplies the current index of the row with the gap to know where to draw the lines to make the grid
        for i in range(rows):
            pygame.draw.line(window, GREY, (0, i * gap), (width, i * gap))
            for j in range(rows):
                pygame.draw.line(window, GREY, (j * gap, 0), (j * gap, width))

    def handle_event(self, event, mouse_pos):
        if self.started:
            return None

        if event.type == pygame.MOUSEBUTTONDOWN:
            if pygame.mouse.get_pressed()[0]:  # left mouse button
                row, col = self.getClicked(mouse_pos, self.ROWS, width)
                node = self.grid[row][col]

                if not self.start and node != self.end:
                    self.start = node
                    self.start.makeStart()
                elif not self.end and node != self.start:
                    self.end = node
                    self.end.makeEnd()
                elif node != self.end and node != self.start:
                    node.makeBlock()
            if self.BackToStart.is_clicked(mouse_pos):
                return "start"

        if pygame.mouse.get_pressed()[2]:  # right mouse button
            row, col = self.getClicked(mouse_pos, self.ROWS, width)
            node = self.grid[row][col]
            node.reset()
            if node == self.start:
                self.start = None
            elif node == self.end:
                self.end = None

        if event.type == pygame.KEYDOWN:
            if (
                event.key == pygame.K_SPACE
                and not self.started
                and self.start
                and self.end
            ):
                for row in self.grid:
                    for node in row:
                        node.updateNeighbours(self.grid)

                def draw_and_update():
                    self.draw(window)
                    pygame.display.update()

                self.algorithm(draw_and_update, self.grid, self.start, self.end)

            # Press 'c' to clear the grid
            if event.key == pygame.K_c:
                self.grid = self.makeGrid(self.ROWS, width)
                self.start = None
                self.end = None
                self.started = False

        return None

    def update(self, mouse_pos):
        self.BackToStart.check_hover(mouse_pos)

        if not self.started:
            if pygame.mouse.get_pressed()[0]:  # left mouse held down
                row, col = self.getClicked(mouse_pos, self.ROWS, width)
                node = self.grid[row][col]

                # Only draw barriers if start and end are already placed
                if self.start and self.end and node != self.end and node != self.start:
                    node.makeBlock()

            elif pygame.mouse.get_pressed()[2]:  # right mouse held down
                row, col = self.getClicked(mouse_pos, self.ROWS, width)
                node = self.grid[row][col]
                if node != self.start and node != self.end:
                    node.reset()

    # draw function that draws everything
    def draw(self, window):
        window.fill(WHITE)

        for row in self.grid:
            for node in row:
                node.draw(window)

        self.drawGrid(window, self.ROWS, width)
        self.BackToStart.draw(window)

    @staticmethod
    def getClicked(pos, rows, width):
        gap = width // rows
        y, x = pos

        row = y // gap
        col = x // gap
        return row, col


class Game:
    def __init__(self):
        self.windows = {
            "start": startMenu(),
            "tutorial": Tutorial(),
            "sandbox": Sandbox(),
            "nodes": ExplainNodes(),
            "heuristic": ExplainHeuristics(),
            "obstacles": ObstaclesAndNeighbours(),
            "exam": Exam(),
        }
        self.current_window = "start"
        self.running = True

    def run(self):
        while self.running:
            mouse_pos = pygame.mouse.get_pos()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False

                next_window = self.windows[self.current_window].handle_event(
                    event, mouse_pos
                )
                if next_window:
                    self.current_window = next_window

            self.windows[self.current_window].update(mouse_pos)
            self.windows[self.current_window].draw(window)
            pygame.display.flip()

            clock.tick(60)
        pygame.quit()


if __name__ == "__main__":
    game = Game()
    game.run()
