from __future__ import annotations
from typing import Callable
from tkinter import *
from math import sqrt
import random

from ai import *


class Point:
    def __init__(self, x=0, y=0):
        self.x = x
        self.y = y

    def copy(self):
        return Point(self.x, self.y)

    @property
    def magnitude(self):
        """Treat the point as a vector and compute its magnitude."""
        return sqrt(self.x ** 2 + self.y ** 2)

    @property
    def unit_vector(self):
        """Treat the point as a vector and compute its unit vector."""
        return self / self.magnitude

    def __add__(self, other):
        if isinstance(other, Point):
            return Point(self.x + other.x, self.y + other.y)
        else: # other is a scalar
            return Point(self.x + other, self.y + other)

    def __sub__(self, other):
        if isinstance(other, Point):
            return Point(self.x - other.x, self.y - other.y)
        else: # other is a scalar
            return Point(self.x - other, self.y - other)

    def __mul__(self, other):
        assert isinstance(other, int) or isinstance(other, float)

        return Point(self.x * other, self.y * other)

    def __rmul__(self, other):
        return self.__mul__(other)

    def __truediv__(self, other):
        assert isinstance(other, int) or isinstance(other, float)

        return Point(self.x / other, self.y / other)
        
    def __floordiv__(self, other):
        assert isinstance(other, int) or isinstance(other, float)

        return Point(self.x // other, self.y // other)

    def __eq__(self, other):
        assert isinstance(other, Point)

        return self.x == other.x and self.y == other.y


class BoundingBox:
    def __init__(self, origin: Point, width, height):
        self.origin = origin
        self.width = width
        self.height = height

    @property
    def left(self):
        return self.origin.x

    @property
    def right(self):
        return self.left + self.width

    @property
    def top(self):
        return self.origin.y

    @property
    def bottom(self):
        return self.top + self.height

    @property
    def centre(self) -> Point:
        return Point(self.origin.x + self.width / 2, self.origin.y + self.height / 2)

    def intersects(self, other) -> bool:
        assert isinstance(other, BoundingBox)

        x_overlaps = self.right > other.left and other.right > self.left
        y_overlaps = self.bottom > other.top and other.bottom > self.top

        return x_overlaps and y_overlaps


class GameObject:
    def __init__(self, canvas, x1, y1, x2, y2, velocity=Point(0, 0)):
        self.canvas = canvas
        self.canvas_object = None
        self.bounding_box = BoundingBox(Point(x1, y1), x2 - x1, y2 - y1)
        self.velocity = velocity

    @property
    def position(self):
        return self.canvas.coords(self.canvas_object)        

    @property
    def left(self):
        x1, _, _, _ = self.position

        return x1

    @property
    def right(self):
        _, _, x2, _ = self.position
        
        return x2

    @property
    def top(self):
        _, y1, _, _ = self.position
        
        return y1

    @property
    def bottom(self):
        _, _, _, y2 = self.position
        
        return y2

    @property
    def centre(self):
        x1, y1, x2, y2 = self.position

        return Point((x1 + x2) / 2, (y1 + y2) / 2)

    @property
    def width(self):
        x1, _, x2, _ = self.position

        return x2 - x1

    @property
    def height(self):
        _, y1, _, y2 = self.position

        return y2 - y1

    def update(self):
        self.move(self.velocity)

    def move(self, delta_pos: Point):
        """Move the object by moving its origin to 'origin + delta_pos'"""
        self.bounding_box.origin += delta_pos
        self.canvas.move(self.canvas_object, delta_pos.x, delta_pos.y)

    def intersects(self, other: GameObject):
        """Check if one game object intersects another via their bounding boxes."""
        assert isinstance(other, GameObject)

        return self.bounding_box.intersects(other.bounding_box)

    def is_out_of_bounds(self):
        return self.left < 0 or self.right > self.canvas.winfo_width() or\
            self.top < 0 or self.bottom > self.canvas.winfo_height()


class Ball(GameObject):
    BALL_SIZE = 12

    DEFAULT_SPEED = 3
    DEFAULT_MAX_SPEED=10

    def __init__(self, canvas, x1, y1, x2, y2, speed=DEFAULT_SPEED, max_speed=DEFAULT_MAX_SPEED):
        """Create a ball at the specified location.

        The ball starts moving in a random direction.
        """
        x_dir = -1 if random.gauss(0, 1) < 0 else 1
        y_dir = -1 if random.gauss(0, 1) < 0 else 1
        initial_velocity = speed * Point(x_dir, y_dir)

        super().__init__(canvas, x1, y1, x2, y2, velocity=initial_velocity)

        self.canvas_object = canvas.create_oval(x1, y1, x2, y2, fill="red")
        self.max_speed = max_speed

    @staticmethod
    def get_centred_ball(canvas, speed=DEFAULT_SPEED, max_speed=DEFAULT_MAX_SPEED):
        """Get a ball placed at the centre of the game window."""
        x = canvas.winfo_width() / 2 - Ball.BALL_SIZE / 2
        y = canvas.winfo_height() / 2 - Ball.BALL_SIZE / 2

        return Ball(canvas, x, y, x + Ball.BALL_SIZE, y + Ball.BALL_SIZE, speed=speed)

    def update(self):
        super().update()

        # Check if ball past upper or lower screen bounds.
        if self.top <= 0 or self.bottom >= self.canvas.winfo_height():
            self.velocity.y *= -1

            if self.top <= 0:
                dy = -self.top
            else:
                dy = self.canvas.winfo_height() - self.bottom

            self.move(Point(0, dy))

        if self.velocity.magnitude > self.max_speed:
            self.velocity = self.max_speed * self.velocity.unit_vector


class Paddle(GameObject):
    PLAYER_ONE = 1
    PLAYER_TWO = 2

    PADDLE_WIDTH = 10
    PADDLE_HEIGHT = 40

    DEFAULT_SPEED = 8

    def __init__(self, canvas, x1, y1, x2, y2, speed=DEFAULT_SPEED):
        super().__init__(canvas, x1, y1, x2, y2)
        self.canvas_object = canvas.create_rectangle(x1, y1, x2, y2, fill="black")  
        self.speed = speed

    @staticmethod
    def make_paddle(canvas, player, speed=DEFAULT_SPEED):
        """Factory method for creating a player paddle."""
        x_offset = 25
        x = 0
        y = 0

        if player == Paddle.PLAYER_ONE:
            x = x_offset
            y = (canvas.winfo_height() - Paddle.PADDLE_HEIGHT) / 2
        else:
            x = canvas.winfo_width() - x_offset - Paddle.PADDLE_WIDTH
            y = (canvas.winfo_height() - Paddle.PADDLE_HEIGHT) / 2

        return Paddle(canvas, x, y, x + Paddle.PADDLE_WIDTH, y + Paddle.PADDLE_HEIGHT, speed)

    def move_up(self):
        self.velocity = Point(0, -self.speed)

    def move_down(self):
        self.velocity = Point(0, self.speed)

    def stop(self):
        self.velocity = Point()

    def update(self):
        super().update()

        _, y1, _, y2 = self.position

        # keep paddle on screen
        dy = 0

        if y1 < 0:
            dy = -y1
        elif y2 > self.canvas.winfo_height():
            dy = self.canvas.winfo_height() - y2

        self.move(Point(0, dy))


class PongGame:
    """A game of Pong.

    You can add 'spin' to the ball by hitting the ball with your paddle while moving.
    Each hit speeds up the ball.

    Call run() to start the game.
    """

    def __init__(self, spin=0.2, hit_speedup=1.05, ball_max_speed=Ball.DEFAULT_MAX_SPEED, window_width=800, window_height=400,
                 p1_ai_type=None, p2_ai_type=None, ai_difficulty=AIAgent.Difficulty.MEDIUM):
        """Set up a game of Pong.

        Arguments:
            spin: ratio of a paddle's y velocity that will be added to the ball's velocity as 'spin' when the ball
                  is hit.
            hit_speedup: multiplier for the ball's x velocity when it bounces off a paddle.
            ball_max_speed: the max speed in either of the x or y axes.
            window_width: the width of the game window. min of 600.
            window_height: the height of the game window. min of 300.
        """
        window = Tk()
        window.title("Pong")
        window.resizable(False, False)
        window.bind('<KeyPress>', lambda event: self.handle_key_pressed(event))
        window.bind('<KeyRelease>', lambda event: self.handle_key_released(event))

        window_width = max(600, window_width)
        window_height = max(300, window_height)

        canvas = Canvas(window, width=window_width, height=window_height)
        canvas.pack()
        canvas.update()

        self.window = window
        self.canvas = canvas

        # paddles and ball setup later in reset()
        self.pad1 = None
        self.pad2 = None
        self.ball = None
        self.ai_difficulty = ai_difficulty
        self.ai_players = [None, None]

        self.ai_players[0] = AIFactory.make_ai(canvas, p1_ai_type, ai_difficulty)
        self.ai_players[1] = AIFactory.make_ai(canvas, p2_ai_type, ai_difficulty)

        self.spin = spin
        self.ball_max_speed = ball_max_speed
        self.hit_speedup = hit_speedup
        
        self.p1_score = 0
        self.p1_score_display = self.canvas.create_text(10, 10, text=str(self.p1_score))
        self.p2_score = 0        
        self.p2_score_display = self.canvas.create_text(window_width - 10, 10, text=str(self.p2_score))

        self.paused = False
        self.pause_text = self.canvas.create_text(window_width / 2, window_height / 2 - 20, text="Press Space to Start")
        self.reset()

    def reset(self):
        """Reset the game by placing the ball back in the center and the paddles in their starting positions."""
        if self.ball is not None:
            self.canvas.delete(self.ball.canvas_object)

        self.ball = Ball.get_centred_ball(self.canvas, max_speed=self.ball_max_speed)

        if self.pad1 is not None:
            self.canvas.delete(self.pad1.canvas_object)
        if self.pad2 is not None:            
            self.canvas.delete(self.pad2.canvas_object)

        self.pad1 = Paddle.make_paddle(self.canvas, Paddle.PLAYER_ONE)
        self.pad2 = Paddle.make_paddle(self.canvas, Paddle.PLAYER_TWO)

        self.pause()

    def toggle_pause(self):
        if self.paused:
            self.unpause()
        else:
            self.pause()

    def pause(self):
        self.paused = True
        self.canvas.itemconfig(self.pause_text, text="Press Space to Start")

    def unpause(self):
        self.paused = False
        self.canvas.itemconfig(self.pause_text, text="")

    def handle_key_pressed(self, event):
        key = event.keysym.lower()

        if key == 'w':
            self.pad1.move_up()
        elif key == 's':
            self.pad1.move_down()

        if key == 'up':
            self.pad2.move_up()            
        elif key == 'down':
            self.pad2.move_down()

        if key == 'space':
            self.toggle_pause()
        if key == 'r':
            self.reset()
        
    def handle_key_released(self, event):
        key = event.keysym.lower()
        
        if key == 'w' or key == 's':
            self.pad1.velocity = Point()

        if key == 'up' or key == 'down':
            self.pad2.velocity = Point()

    def run(self):
        self.mainloop()
        self.window.mainloop()

    def mainloop(self):
        if not self.paused:
            self.update()

        self.canvas.after(16, self.mainloop)

    def update(self):
        if self.ai_players[0] is not None:
            move = self.ai_players[0].get_move({'ball': self.ball, 'paddle': self.pad1})
            move()

        if self.ai_players[1] is not None:
            move = self.ai_players[1].get_move({'ball': self.ball, 'paddle': self.pad2})
            move()

        for paddle in [self.pad1, self.pad2]:            
                paddle.update()

        self.ball.update()
        self.physics()

        self.canvas.itemconfig(self.p1_score_display, text=str(self.p1_score))
        self.canvas.itemconfig(self.p2_score_display, text=str(self.p2_score))

    def physics(self):
        if self.ball.intersects(self.pad1):
            self.ball.velocity.x *= -1 * self.hit_speedup
            self.ball.velocity.y += self.spin * self.pad1.velocity.y

            # put ball on the rhs of the paddle
            pad1_x = self.pad1.right
            ball_x = self.ball.left
            dx = pad1_x - ball_x

            self.ball.move(Point(dx, 0))

        elif self.ball.intersects(self.pad2):
            self.ball.velocity.x *= -1 * self.hit_speedup
            self.ball.velocity.y += self.spin * self.pad2.velocity.y

            # put ball on the lhs of the paddle
            pad2_x = self.pad2.left
            ball_x = self.ball.right
            dx = pad2_x - ball_x

            self.ball.move(Point(dx, 0))

        if self.ball.is_out_of_bounds():
            if self.ball.left < 0:
                self.p2_score += 1
                self.reset()
            elif self.ball.right > self.canvas.winfo_width():
                self.p1_score += 1
                self.reset()


if __name__ == "__main__":
    game = PongGame(p2_ai_type=AIType.DEAD_ZONE)
    game.run()
