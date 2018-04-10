"""Implements MCST, based on https://jeffbradberry.com/posts/2015/09/intro-to-monte-carlo-tree-search/"""

import datetime
from monte_carlo import MonteCarloBot
from math import log, sqrt
from random import choice


class MonteCarloSearchTreeBot(MonteCarloBot):
	def __init__(self, starting_hit_points=0, current_mana=0, starting_mana=0, max_moves=200, simulation_time=2, C=1.4, states=[]):

		# previous states the game has been in
		self.states = states

		# the starting stats for the bot
		self.mana = starting_mana
		self.current_mana = current_mana
		self.hit_points = starting_hit_points

		# the amount of time to call run_simulation as much as possible 		
		self.calculation_time = datetime.timedelta(seconds=simulation_time)

		# the max_moves for any simulation
		self.max_moves = max_moves
		
		# Larger C encourages more exploration of the possibilities, smaller causes the AI to prefer concentrating on known good moves
		self.C = C

		# statistics about previously simulated game states
		self.wins = {}
		self.plays = {}

	def play_move(self, game):
		"""Play a move in game and append it to self.states."""
		move = self.get_play()
		game.do_move(move)

	def get_play(self):
		"""Return the best play after simulating possible plays and updating the plays and wins stats."""
		state = self.states[-1]
		legal = self.board.legal_plays(self.states[:], self.current_mana)

		# Bail out early if there is no real choice to be made.
		if not legal:
			return []
		if len(legal) == 1:
			return legal[0]

		games = 0
		begin = datetime.datetime.utcnow()
		while datetime.datetime.utcnow() - begin < self.calculation_time:
			self.run_simulation()
			games += 1

		moves_states = [(p, self.board.next_state(state, p)) for p in legal]

		player = self.board.current_player(state)

		# Pick the move with the highest percentage of wins.
		percent_wins, move = max(
			(self.wins.get((player, S), 0) * 1.0 /
			 self.plays.get((player, S), 1),
			 p)
			for p, S in moves_states
		)

		# Display the stats for each possible play.
		'''
		for x in sorted(
			((100 * self.wins.get((player, S), 0) * 1.0 /
				self.plays.get((player, S), 1),
				self.wins.get((player, S), 0),
				self.plays.get((player, S), 0), p)
			 for p, S in moves_states),
			reverse=True
		):
			print "{3}: {0:.2f}% ({1} / {2})".format(*x)
		'''

		return move

	def run_simulation(self):
		# A bit of an optimization here, so we have a local
		# variable lookup instead of an attribute access each loop.
		plays, wins = self.plays, self.wins

		visited_states = set()
		states_copy = self.states[:]
		state = states_copy[-1]
		player = self.board.current_player(state)

		expand = True
		for t in xrange(1, self.max_moves + 1):
			curr_play_num = state[9]
			curr_player_mana = 0
			if curr_play_num == 1:
				curr_player_mana = state[4]
			else:
				curr_player_mana = state[7]

			legal = self.board.legal_plays(states_copy, curr_player_mana)
			moves_states = [(p, self.board.next_state(state, p)) for p in legal]
			if all(plays.get((player, S)) for p, S in moves_states):
				# If we have stats on all of the legal moves here, use them.
				log_total = log(
					sum(plays[(player, S)] for p, S in moves_states))
				value, move, state = max(
					((wins[(player, S)] / plays[(player, S)]) +
					 self.C * sqrt(log_total / plays[(player, S)]), p, S)
					for p, S in moves_states
				)
			else:
				# Otherwise, just make an arbitrary decision.
				move, state = choice(moves_states)
			# print "moving to state {}".format(state)
			states_copy.append(state)

			# `player` here and below refers to the player
			# who moved into that particular state.
			if expand and (player, state) not in plays:
				expand = False
				plays[(player, state)] = 0
				wins[(player, state)] = 0

			visited_states.add((player, state))

			player = self.board.current_player(state)
			winner = self.board.winner(states_copy)
			if winner > 0:
				break

		for player, state in visited_states:
			if (player, state) not in plays:
				continue
			plays[(player, state)] += 1
			if player == winner:
				wins[(player, state)] += 1
