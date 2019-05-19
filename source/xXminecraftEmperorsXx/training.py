import time

from referee.log import StarLog
from referee.game import Chexers
from xXminecraftEmperorsXx.algorithm import Algorithm
from xXminecraftEmperorsXx.player import MinecraftPlayer as Player


class Training:

    def train_start(self):
        algorithm = Algorithm()
        options = Options()
        red = Player("red")
        green = Player("green")
        blue = Player("blue")

        out = StarLog(level=options.verbosity, star="*") # verbosity 1 no board, 2 has board
        self.train([red, green, blue], options, out)
        pass

    def train(self, players, options, out):
        # Set up a new Chexers game and initialise a Red, Green and Blue player
        # (constructing three Player classes including running their .__init__()
        # methods).
        game = Chexers(logfilename=options.logfile, debugboard=options.verbosity > 2)
        out.section("initialising players")
        for player, colour in zip(players, ['red', 'green', 'blue']):
            # NOTE: `player` here is actually a player wrapper. Your program should
            # still implement a method called `__init__()`, not one called `init()`.
            player.init(colour)

        # Display the initial state of the game.
        out.section("game start")
        out.comment("displaying game info:")
        out.comments(game, pad=1)

        # Repeat the following until the game ends
        # (starting with Red as the current player, then alternating):
        curr_player, next_player, prev_player = players
        while not game.over():
            time.sleep(options.delay)
            out.section(f"{curr_player.name}'s turn")

            # Ask the current player for their next action (calling their .action()
            # method).
            action = curr_player.train()

            # Validate this action (or pass) and apply it to the game if it is
            # allowed. Display the resulting game state.
            game.update(curr_player.colour, action)
            out.comment("displaying game info:")
            out.comments(game, pad=1)

            # Notify all three players (including the current player) of the action
            # (or pass) (using their .update() methods).
            for player in players:
                player.update(curr_player.colour, action)

            # Next player's turn!
            curr_player, next_player, prev_player = next_player, prev_player, curr_player

        # After that loop, the game has ended (one way or another!)
        # Display the final result of the game to the user.
        result = game.end()
        out.section("game over!")
        out.print(result)


class Options:
    def __init__(self):
        self.logfile = None
        self.verbosity = 2
        self.delay = 0
        self.train = 1
