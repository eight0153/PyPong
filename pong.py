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
        else:  # other is a scalar
            return Point(self.x + other, self.y + other)

    def __sub__(self, other):
        if isinstance(other, Point):
            return Point(self.x - other.x, self.y - other.y)
        else:  # other is a scalar
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


class GameObject:
    def __init__(self, position, width, height, velocity=Point(0, 0)):
        self.position = position
        self.width = width
        self.height = height
        self.velocity = velocity

    @property
    def left(self):
        return self.position.x

    @property
    def right(self):
        return self.left + self.width

    @property
    def top(self):
        return self.position.y

    @property
    def bottom(self):
        return self.top + self.height

    @property
    def centre(self):
        return Point((self.left + self.right) / 2, (self.top + self.bottom) / 2)

    def update(self, canvas):
        self.position += self.velocity

    def draw(self, canvas):
        pass

    def intersects(self, other):
        """Check if one game object intersects another via their bounding boxes."""
        assert isinstance(other, GameObject)

        x_overlaps = self.right > other.left and other.right > self.left
        y_overlaps = self.bottom > other.top and other.bottom > self.top

        return x_overlaps and y_overlaps


class Ball(GameObject):
    BALL_SIZE = 12

    DEFAULT_SPEED = 3
    DEFAULT_MAX_SPEED = 10

    def __init__(self, position, width, height, speed=DEFAULT_SPEED, max_speed=DEFAULT_MAX_SPEED):
        """Create a ball at the specified location.

        The ball starts moving in a random direction.
        """
        x_dir = -1 if random.gauss(0, 1) < 0 else 1
        y_dir = -1 if random.gauss(0, 1) < 0 else 1
        initial_velocity = speed * Point(x_dir, y_dir)

        super().__init__(position, width, height, velocity=initial_velocity)

        self.max_speed = max_speed

    @staticmethod
    def get_centred_ball(canvas, speed=DEFAULT_SPEED, max_speed=DEFAULT_MAX_SPEED):
        """Get a ball placed at the centre of the game window."""
        x = canvas.winfo_width() / 2 - Ball.BALL_SIZE / 2
        y = canvas.winfo_height() / 2 - Ball.BALL_SIZE / 2

        return Ball(Point(x, y), Ball.BALL_SIZE, Ball.BALL_SIZE, speed=speed, max_speed=max_speed)

    def update(self, canvas):
        super().update(canvas)

        # Check if ball past upper or lower screen bounds.
        if self.top < 0 or self.bottom > canvas.winfo_height():
            self.velocity.y *= -1

            if self.top < 0:
                self.position.y = 0
            else:
                self.position.y = canvas.winfo_height() - self.height

        if self.velocity.magnitude > self.max_speed:
            self.velocity = self.max_speed * self.velocity.unit_vector

    def draw(self, canvas):
        canvas.create_oval(self.left, self.top, self.right, self.bottom, fill="red")


class Paddle(GameObject):
    PLAYER_ONE = 1
    PLAYER_TWO = 2

    PADDLE_WIDTH = 10
    PADDLE_HEIGHT = 40

    DEFAULT_SPEED = 8

    def __init__(self, position, width, height, speed=DEFAULT_SPEED):
        super().__init__(position, width, height)
        self.speed = speed

    @staticmethod
    def make_paddle(canvas, player, speed=DEFAULT_SPEED):
        """Factory method for creating a player paddle."""
        x_offset = 25

        if player == Paddle.PLAYER_ONE:
            x = x_offset
            y = (canvas.winfo_height() - Paddle.PADDLE_HEIGHT) / 2
        else:
            x = canvas.winfo_width() - x_offset - Paddle.PADDLE_WIDTH
            y = (canvas.winfo_height() - Paddle.PADDLE_HEIGHT) / 2

        return Paddle(Point(x, y), Paddle.PADDLE_WIDTH, Paddle.PADDLE_HEIGHT, speed)

    def move_up(self):
        self.velocity = Point(0, -self.speed)

    def move_down(self):
        self.velocity = Point(0, self.speed)

    def stop(self):
        self.velocity = Point()

    def update(self, canvas):
        super().update(canvas)
        # keep paddle on screen
        if self.top < 0:
            self.position.y = 0
        elif self.bottom > canvas.winfo_height():
            self.position.y = canvas.winfo_height() - self.height

    def draw(self, canvas):
        canvas.create_rectangle(self.left, self.top, self.right, self.bottom, fill="black")


class PongGame:
    """A game of Pong.

    You can add 'spin' to the ball by hitting the ball with your paddle while moving.
    Each hit speeds up the ball.

    Call run() to start the game.
    """
    FRAME_RATE = 60
    FRAME_DELAY = 1000 // 60

    def __init__(self, spin=0.2, hit_speedup=1.05, ball_max_speed=Ball.DEFAULT_MAX_SPEED, window_width=800,
                 window_height=400, p1_ai_type=None, p2_ai_type=None, ai_difficulty=AIAgent.Difficulty.MEDIUM):
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
        self.ai_players = [AIFactory.make_ai(canvas, p1_ai_type, ai_difficulty),
                           AIFactory.make_ai(canvas, p2_ai_type, ai_difficulty)]

        self.spin = spin
        self.ball_max_speed = ball_max_speed
        self.hit_speedup = hit_speedup
        
        self.p1_score = 0
        self.p2_score = 0

        self.paused = False
        self.reset()

    def reset(self):
        """Reset the game by placing the ball back in the center and the paddles in their starting positions."""
        self.ball = Ball.get_centred_ball(self.canvas, max_speed=self.ball_max_speed)
        self.pad1 = Paddle.make_paddle(self.canvas, Paddle.PLAYER_ONE)
        self.pad2 = Paddle.make_paddle(self.canvas, Paddle.PLAYER_TWO)

        self.paused = True

    def toggle_pause(self):
        self.paused = not self.paused

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
            self.physics_update()

        self.draw()
        self.canvas.after(self.FRAME_DELAY, self.mainloop)

    def update(self):
        for ai_player, paddle in zip(self.ai_players, [self.pad1, self.pad2]):
            action = ai_player.get_action({'canvas': self.canvas, 'ball': self.ball, 'paddle': paddle})
            action()

        for paddle in [self.pad1, self.pad2]:            
            paddle.update(self.canvas)

        self.ball.update(self.canvas)

    def physics_update(self):
        if self.ball.intersects(self.pad1):
            self.ball.velocity.x *= -1 * self.hit_speedup
            self.ball.velocity.y += self.spin * self.pad1.velocity.y
            self.ball.position.x = self.pad1.right

        elif self.ball.intersects(self.pad2):
            self.ball.velocity.x *= -1 * self.hit_speedup
            self.ball.velocity.y += self.spin * self.pad2.velocity.y
            self.ball.position.x = self.pad2.left - self.ball.width

        if self.is_out_of_bounds(self.ball):
            if self.ball.left < 0:
                self.p2_score += 1
                self.reset()
            elif self.ball.right > self.canvas.winfo_width():
                self.p1_score += 1
                self.reset()

    def is_out_of_bounds(self, game_object):
        return game_object.left < 0 or game_object.right > self.canvas.winfo_width() or \
               game_object.top < 0 or game_object.bottom > self.canvas.winfo_height()

    def draw(self):
        self.canvas.delete("all")

        self.draw_gui()
        self.pad1.draw(self.canvas)
        self.pad2.draw(self.canvas)
        self.ball.draw(self.canvas)

    def draw_gui(self):
        if self.paused:
            self.canvas.create_text(self.canvas.winfo_width() / 2, self.canvas.winfo_height() / 2 - 20,
                                    text="Press Space to Start")
        self.canvas.create_text(10, 10, text=str(self.p1_score))
        self.canvas.create_text(self.canvas.winfo_width() - 10, 10, text=str(self.p2_score))


if __name__ == "__main__":
    game = PongGame(p2_ai_type=AIType.RULE_BASED)
    game.run()
