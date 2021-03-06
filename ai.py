from typing import Callable


class AIAgent:
    class Difficulty:
        EASY = 1
        MEDIUM = 2
        HARD = 3
        IMPOSSIBLE = 4

    def __init__(self, difficulty=Difficulty.MEDIUM):
        self.difficulty = difficulty

    @staticmethod
    def noop():
        pass

    def get_action(self, game_state) -> Callable:
        return self.noop


class RuleBased(AIAgent):
    """A rule-based AI that has a 'dead zone' for which the agent does not track the ball.
    When the agent is not tracking the ball, it tries to return its 'resting position' at the centre of the
    screen height.
    """
    def __init__(self, canvas, difficulty=AIAgent.Difficulty.MEDIUM):
        super().__init__(difficulty)

        if difficulty == AIAgent.Difficulty.EASY:
            self.dead_zone_size = canvas.winfo_width() * 0.8
        elif difficulty == self.Difficulty.MEDIUM:
            self.dead_zone_size = canvas.winfo_width() * 0.5
        elif difficulty == self.Difficulty.HARD:
            self.dead_zone_size = canvas.winfo_width() * 0.2
        elif difficulty == self.Difficulty.IMPOSSIBLE:
            self.dead_zone_size = 0

    def get_action(self, game_state):
        canvas = game_state['canvas']
        paddle = game_state['paddle']
        ball = game_state['ball']

        if abs(ball.centre.x - paddle.centre.x) > self.dead_zone_size or \
                not self.is_ball_approaching(canvas, ball, paddle):
            centre_y = canvas.winfo_height() / 2 - paddle.height / 2
            dy = centre_y - paddle.centre.y

            if paddle.top < centre_y < paddle.bottom:
                dy = 0
        else:
            dy = ball.centre.y - paddle.centre.y

            if paddle.top < ball.centre.y < paddle.bottom:
                dy = 0

        if dy < 0:
            return paddle.move_up
        elif dy > 0:
            return paddle.move_down
        else:
            return paddle.stop

    @staticmethod
    def is_ball_approaching(canvas, ball, paddle) -> bool:
        return (paddle.centre.x > canvas.winfo_width() / 2 and ball.velocity.x > 0) or\
               (paddle.centre.x < canvas.winfo_width() / 2 and ball.velocity.x < 0)




class AIType:
    NONE = None
    RULE_BASED = 0


class AIFactory:
    @staticmethod
    def make_ai(canvas, ai_type=AIType.RULE_BASED, difficulty=AIAgent.Difficulty.MEDIUM):
        if ai_type == AIType.RULE_BASED:
            return RuleBased(canvas, difficulty)
        else:
            return AIAgent(difficulty)
