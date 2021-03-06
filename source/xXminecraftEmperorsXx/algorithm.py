import queue
import math
import operator
import time
import itertools
import math
import numpy as np

from xXminecraftEmperorsXx import Formatting

_FILE_PATH = ".\\xXminecraftEmperorsXx\\weights.txt"
unit_moves = np.array([(1,-1), (1,0), (0,1), (-1,1), (-1,0), (0,-1)])

# TD Leaf
LEARNING_RATE = 0.2
FEATURE_MULTIPLIER = 0.02
LAMBDA = 1


class Algorithm:

    def __init__(self):
        file = open(_FILE_PATH, "r")
        weights = Formatting.string_to_tuple(file.read())
        self.weights = np.array(weights)
        file.close()

    def weight_update(self, weights, features, rewards, real_reward):
        N = len(features)
        weight_updates = []
        for i in range(0, N-1):
            # i iterates over turns in the game
            dr_dw = []      # a vector representing derivative of the feature vector over the weight vector
            for feature in features[i]:
                # this computes derivative over each element of feature vector of the step
                cow = feature
                # coefficient of weight, i.e. the 2 in 2x, is the feature,
                # since they were multiplied together to get reward
                derivative = 2*cow/np.cosh(2*cow)+1
                dr_dw.append(derivative)
                # derivative of tanh(a*x) = 2a/(cosh(2ax)+1) where a is constant and x is the variable

            adjustments = []
            rewards[N-1] = real_reward                  # change last reward from predicted to actual game result
            # print("# DEBUG", rewards)
            for m in range(i, N-1):
                diff = rewards[i+1] - rewards[i]        # difference between state m's utility and state m+1's utility
                importance = LAMBDA**(m-i)              # LAMBDA scales the importance of this difference
                adjustments.append(diff*importance)

            weight_update = []
            for element in dr_dw:
                weight_update.append(element * sum(adjustments))
                # weight_update is the due update incurred by a single state in the game,
                # but is a vector (list) since weight is a vector

            weight_updates.append(weight_update)
            # weight_updates plural is the due updates incurred by all states of the game

        np_updates = np.array(weight_updates)
        compressed = np_updates.sum(0)              # element wise sum of all sublists
        compressed *= LEARNING_RATE
        new_weights = np.add(weights, compressed)

        return new_weights

    def eval(self, board, player_color, my_pieces, my_exits, goal, training=False):
        # Returns a float value in range (0,1) to indicate the goodness of the current board state for the player
        # board : Dictionary
        # my_pieces : Tuple, e.g.(piece1, piece2, piece3)
        #   piece in my_pieces : Tuple, e.g. (0,1), (1,2), (3,-1)
        # goal : Tuple, in format of (axis_number, axis_value), e.g. (0,3)
        features = self.features(board, player_color[0], my_pieces, my_exits, goal)
        assert(features.size == len(self.weights))      # make sure same size so we can calculate dot product
        evaluation = features.dot(self.weights)


        # evaluate current utility considering all features and their importances
        reward = math.tanh(evaluation)                  # normalize evaluation

        # print("DEBUG evals = ", evaluation)
        # print("DEBUG rewards = ", reward)

        # unclean, refactor this later
        if training:
            return (reward, features)
        else:
            return reward

    def features(self, board, player_color, my_pieces, my_exits, goal):
        # Returns a numpy vector that contains the features of the current board state
        # board : Dictionary
        # my_pieces : tuple
        # goal : tuple

        pieces_3axis = Algorithm.piece_3axis(my_pieces)    # add third axis to piece

        f1 = len(my_pieces)
        f2 = my_exits
        f3 = self.piece_separation(pieces_3axis)
        f4 = self.dist_to_goal(pieces_3axis, goal)
        f5 = self.jumps(board, my_pieces, player_color, enemy_only=False)
        f6 = self.jumps(board, my_pieces, player_color, enemy_only=True)

        f7 = self.dist_from_enemy(board, my_pieces)
        f8 = self.second_dist_from_enemy(board, my_pieces)
        # f9 = self.dist_btw_enemy(board)
        # f10 = self.dist_btw_enemy(board)

        features = [f1, f2, f3, f4, f5, f6, f7, f8]
        features_vector = np.array(features)*FEATURE_MULTIPLIER

        # print("DEBUG features = ", features_vector)

        return features_vector

    @staticmethod
    def piece_separation(my_pieces):
        # Returns an integer value indicating total separation between all pieces (combinatorial)
        # my_pieces : tuple
        total_separation = 0
        for i in range(0, len(my_pieces)):
            for j in range(i, len(my_pieces)):
                p1 = np.array(my_pieces[i])
                p2 = np.array(my_pieces[j])
                axis_sep_min = min(np.absolute(p1-p2))
                total_separation += axis_sep_min
        return total_separation

    @staticmethod
    def dist_intercept(my_pieces, goal):
        # Returns the integer distance that pairs of pieces have to travel to arrive at an "intercept" point
        # "Intercept" is defined as the hex which has the same value on one of two non-goal axes for both pieces in pair
        # e.g. pair of pieces: (1,2,-3), (-2,0,2); goal: q=3 (q being first axis); intercept: (3,0,-3)
        # my_pieces: tuple
        pass

    @staticmethod
    def dist_to_goal(my_pieces, goal):
        # Returns the total integer distance of pieces from their goal
        # my_pieces: tuple
        # goal: tuple
        # goal[0] is goal axis (0,1,2) = (p,q,r); goal[1] is goal value - either +3 or -3
        total_distance = 0
        for piece in my_pieces:
            total_distance += abs(piece[goal[0]] - goal[1])
        return total_distance

    @staticmethod
    def piece_3axis(pieces):
        pieces_3axis = []
        for piece in pieces:
            (q, r) = piece
            s = -q - r
            piece = (q, r, s)
            pieces_3axis.append(piece)
        return tuple(pieces_3axis)

    @staticmethod
    def jumps(board, my_pieces, player_color, enemy_only):
        # Returns the number of pieces that my pieces can jump over
        #      if enemy_only == true: only counts enemy pieces that my pieces can jump over
        # board: Dictionary
        # my_pieces: Tuple
        jumps, conquests = 0, 0
        for piece in my_pieces:
            adjacent_hexes = [tuple(map(operator.add, piece, unit_move)) for unit_move in unit_moves]
            for hex in adjacent_hexes:
                if hex in board and board[hex] != "":
                    jumps += 1
                    if board[hex] != player_color:
                        conquests += 1
        if enemy_only: return conquests
        else: return jumps

    @staticmethod
    def dist_from_enemy(board, my_pieces, num_enemies=1):
        # Returns minimum distance between a self piece and an enemy piece
        # Returns array of smallest distances from any self piece to enemy pieces (enemy pieces are counted only once)
        #   i.e. if two player pieces are next to two enemy pieces, the two player pieces will count 2 enemies and not 4
        # board : Dictionary
        # my_pieces : Tuple
        # num_enemies : integer
        assert(num_enemies>=1)
        distances = []
        checked_enemies = []
        rad = 3     # how do we generalize this to board radius? board passed in is pure dict, not board structure
        for i in range(1, 4):   # we don't really care about pieces further than 4 units away
            for piece in my_pieces:
                check_hexes = [tuple(map(operator.add, piece, unit_move*i)) for unit_move in unit_moves]
                for hex in check_hexes:
                    if hex in my_pieces:
                        # avoid treating own pieces as enemy
                        continue
                    (q, r) = hex
                    if abs(q)>rad or abs(r)>rad or abs(-q-r)>rad:
                        # don't bother checking hexes not in the board
                        continue

                    if hex in board and board[hex] != "" :
                        if hex in checked_enemies:
                            # go to next hex if this hex has already been checked (avoid repeat counting enemies)
                            continue

                        checked_enemies.append(hex)
                        if num_enemies==1:
                            return i
                        else:
                            distances.append(i)
                            if len(distances) >= num_enemies:
                                return distances

        # no enemies in sight, return large distance (super unclean code)
        return 5

    def second_dist_from_enemy(self, board, my_pieces):
        distances = self.dist_from_enemy(board, my_pieces, num_enemies=2)

        # when not enough enemies in sight, return large distance (unclean)
        if type(distances) == type(5):
            distances = [5]
        while len(distances) < 2:
            distances.append(5)
        return distances[1]
