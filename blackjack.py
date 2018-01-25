#!/Users/fgiorgetti/anaconda2/bin/python
from __future__ import print_function

import time
import os
import random


class Deck(object):
    def __init__(self):
        self.initDeck()
        self.current_card_idx = 0

    def initDeck(self, number_decks=1):
        self.cards = []

        i = 0
        while (i < number_decks):
            # Initializing 10 points cards
            for symbol in ['Q', 'J', 'K', '10']:
                for suit in Card.suits:
                    self.cards.append(Card(symbol, suit, 10))

            # Pip cards
            for symbol in range(2, 10):
                for suit in Card.suits:
                    self.cards.append(Card(str(symbol), suit, int(symbol)))

            # Aces
            for suit in Card.suits:
                self.cards.append(Card('A', suit, 11))

            i += 1

    def shuffle(self):
        for c in self.cards:
            c.face_up = True

        random.shuffle(self.cards)
        self.current_card_idx = 0

    def get_next_card(self):
        card = self.cards[self.current_card_idx]
        self.current_card_idx += 1
        return card


class Card(object):
    suit_spades = u'\u2660'
    suit_clubs = u'\u2663'
    suit_hearts = u'\u2665'
    suit_diamond = u'\u2666'
    suits = [suit_spades, suit_clubs, suit_hearts, suit_diamond]

    def __init__(self, symbol, suit, points, face_up=True):
        self.symbol = symbol
        self.suit = suit
        self.points = points
        self.face_up = face_up

    def printCard(self):
        print('%2s%s' % (self.symbol, self.suit), end='')


class Player(object):
    state_wait_nxt = 'WAIT_NXT'
    state_wait_oth = 'WAIT_OTH'
    state_wait_bet = 'WAIT_BET'
    state_playing = 'PLAYING'
    state_lost = 'LOST'
    player_commands = { 'H': 'Hit', 'S': 'Stand', 'V': 'Split', 'D': 'Double down' }

    player_states = {
        state_wait_nxt: 'Waiting next game',
        state_wait_oth: 'Waiting other players',
        state_wait_bet: 'Waiting on Bet',
        state_playing: 'Playing',
        state_lost: 'Lost'
    }

    def __init__(self, name):
        self.name = name
        self.money = 1000
        self.reset()

    def reset(self):
        self.hands = []  # One or more sets of cards (when splitting)
        self.player_state = Player.player_states[Player.state_wait_nxt];

    def allowed_commands(self):
        cmds = []

        if len(self.hands) == 0:
            return cmds

        cmds.append('H')
        cmds.append('S')

        has_money = self.money >= self.hands[0].bet + self.hands[0].insurance

        # check if split is allowed
        if has_money and len(self.hands) == 1 and len(self.hands[0].cards) == 2:
            if self.hands[0].cards[0].symbol == self.hands[0].cards[1].symbol:
                cmds.append('V')

        return cmds

    def split(self):
        self.hands.append(Hand())
        self.hands[1].add_card(self.hands[0].cards.pop())
        self.hands[1].bet = self.hands[0].bet
        self.hands[1].insurance = self.hands[0].insurance
        self.hands[0].update()
        self.hands[1].update()
        self.money -= self.hands[0].bet + self.hands[0].insurance

    def read_command(self, deck):

        # Loop through each player's hands
        handidx = 0
        for hand in self.hands:

            # If hand not allowed to play
            if hand.hand_state != Hand.state_play:
                return

            cmds = self.allowed_commands()

            # If double-down allowed in this hand
            if not hand.double:
                cmds.append('D')

            print('%-16s - Allowed moves' % self.name, end='')
            for cmd in cmds:
                print(' - [%s] %s' % (cmd, Player.player_commands[cmd]), end='')

            handidx += 1
            while True:
                cmd = raw_input('         HAND[%d] - Enter your move: ' % (handidx))
                cmd = cmd.upper()
                if cmds.count(cmd) == 0:
                    print('Invalid command, try again')
                    continue
                else:
                    break

            # If split
            if cmd == 'V':
                print('Splitting and reading move again')
                self.split()
                time.sleep(1)
                self.read_command(deck)
                return
            elif cmd == 'D':
                print('Doubling down')
                self.money -= hand.bet + hand.insurance
                hand.double = True
                hand.bet *= 2
                hand.insurance *= 2
                hand.add_card(deck.get_next_card())
                if hand.hand_state != Hand.state_busted:
                    hand.hand_state = Hand.state_stand
            elif cmd == 'H':
                hand.add_card(deck.get_next_card())
            elif cmd == 'S':
                hand.hand_state = Hand.state_stand

    def bet(self):
        self.player_state = Player.player_states[Player.state_wait_bet]

    def wait_others(self):
        self.player_state = Player.player_states[Player.state_wait_oth]

    def lost(self):
        self.player_state = Player.player_states[Player.state_lost]
        for hand in self.hands:
            hand.lost()


class Hand(object):
    state_play = 'PLAYING'
    state_stand = 'STANDING'
    state_busted = 'BUSTED'
    state_lost = 'LOST'
    state_21 = '21'
    state_blackjack = 'BJ'
    state_won = 'WON'
    state_draw = 'DRAW'

    hand_states = {
        state_play: 'Playing',
        state_stand: 'Standing',
        state_busted: 'Busted',
        state_lost: 'Lost',
        state_21: '21',
        state_blackjack: 'BlackJack',
        state_won: 'Won',
        state_draw: 'Push'
    }

    def __init__(self):
        self.hand_state = Hand.state_play
        self.cards = []
        self.points = 0
        self.bet = 0.0
        self.insurance = 0.0
        self.double = False

    def add_card(self, card):
        self.cards.append(card)
        self.update()

    def update(self):
        points = 0
        aces = 0
        for c in self.cards:
            if not c.face_up:
                continue

            if c.symbol == 'A':
                aces += 1
            else:
                points += c.points

        # Adjust value of each ace now
        aces_min = aces
        aces_hi = 0 if aces == 0 else 11 + (aces - 1)
        if points + aces_hi <= 21:
            points += aces_hi
        else:
            points += aces_min

        if (points > 21):
            self.hand_state = Hand.state_busted
        elif (points == 21 and len(self.cards) > 2):
            self.hand_state = Hand.state_21
        elif (points == 21 and len(self.cards) == 2):
            self.hand_state = Hand.state_blackjack

        self.points = points

    def double(self):
        self.double = True

    def lost(self):
        self.hand_state = Hand.state_lost


class Dealer(object):
    hand = Hand()
    face_down = True
    has_blackjack = False

    def reset(self):
        Dealer.hand = Hand()
        Dealer.face_down = True
        Dealer.has_blackjack = False

    @staticmethod
    def check_insurance():
        has_ace = False
        for card in Dealer.hand.cards:
            if card.face_up and card.symbol == 'A':
                has_ace = True

        if has_ace:
            if Dealer.hand.points == 21:
                Dealer.has_blackjack = True
            return True

        return False

    @classmethod
    def play(cls, table, deck):
        print('Dealer will play now')
        if Dealer.face_down:
            Dealer.face_down = False

        for card in cls.hand.cards:
            card.face_up = True

        cls.hand.update()
        table.draw_table()

        # If not busted and lower than 17
        while cls.hand.hand_state == Hand.state_play:
            if cls.hand.points >= 17:
                cls.hand.hand_state = Hand.state_stand
            elif cls.hand.points < 17:
                cls.hand.add_card(deck.get_next_card())
                table.draw_table()


class Table(object):
    state_wait_start = 'Waiting to start'
    state_wait_player = 'Waiting on players'
    state_wait_bet = 'Waiting on bets'
    state_results = 'Match is over'

    const_min_bet = 10

    def __init__(self):
        self.players = []
        self.dealer = Dealer()
        self.deck = Deck()
        self.state = Table.state_wait_start

    def number_of_players(self):
        while True:
            try:
                number = int(raw_input('Enter the number of players: '))
            except:
                print('Enter a positive number of players')
                continue
            else:
                break

        idx = 0
        while (idx < number):
            name = raw_input('Name for player {id}: '.format(id=idx + 1))
            self.players.append(Player(name))
            idx += 1

        self.state = Table.state_wait_bet

    def read_bets(self):

        for player in self.players:

            player.bet()
            self.draw_table()

            player.hands.append(Hand())
            bet = 0;
            while True:
                try:
                    bet = int(raw_input('Player [ %16s ] - enter your bet [ min = %5d / max = %5d ]: '
                                        % (player.name, Table.const_min_bet, player.money)))
                except:
                    print('Invalid bet value')
                    continue
                else:
                    if bet < Table.const_min_bet:
                        print('Bet value is below min')
                        continue
                    elif bet > player.money:
                        print('You do not have all this money')
                        continue
                    else:
                        break
            player.hands[0].bet = bet
            player.money -= bet
            player.wait_others()

        self.state = Table.state_wait_player

    def draw_table(self):

        os.system("clear")
        print('Black Jack Game - Python')
        print()
        print('Game state -> %s' % (self.state))

        if self.state not in [ Table.state_wait_player, Table.state_results ]:
            return

        print()
        print('%16s - Hand   ( %2d - %-10s ) = ' % ('Dealer', self.dealer.hand.points, self.dealer.hand.hand_state),
              end='')
        for card in self.dealer.hand.cards:
            card.printCard() if card.face_up == True or self.dealer.face_down == False else print("???", end='')
            print(' ', end='')
        print()

        for player in self.players:
            handidx = 1
            for hand in player.hands:
                if hand.insurance > 0:
                    side_bet_str = '- Insurance bet: %8.2f ' % hand.insurance
                else:
                    side_bet_str = ''
                print('%16s [ %22s ] - Bet %8.2f %s- Hand %d ( %2d - %-10s ) = ' % (player.name, player.player_state,
                                                                                   hand.bet, side_bet_str,
                                                                                   handidx, hand.points,
                                                                                   hand.hand_state), end='')
                for card in hand.cards:
                    card.printCard()
                    print(' ', end='')
                print()
                handidx += 1

        print()
        time.sleep(1)

    def distribute_initial_cards(self):
        self.deck.shuffle()

        idx = 0
        while idx < 2:

            for player in self.players:
                player.hands[0].add_card(self.deck.get_next_card())
                self.draw_table()

            dealer_card = self.deck.get_next_card()
            dealer_card.face_up = True if idx > 0 else False
            self.dealer.hand.add_card(dealer_card)
            self.draw_table()
            idx += 1

        if Dealer.check_insurance():
            self.offer_insurance()

    def offer_insurance(self):
        for player in self.players:
            insurance_yn = raw_input('Player [ %16s ] - Do you want insurance (y/N): ' % (player.name))
            if 'y' != insurance_yn.lower():
                continue
            while True:
                max_bet = player.hands[0].bet / 2.0
                try:
                    bet = float(raw_input('Player [ %16s ] - Enter your insurance bet [ min = 1 / max = %5d ]: '
                                          % (player.name, max_bet)))
                except:
                    print('Invalid insurance bet value, try again')
                    continue
                else:
                    if bet < 1 or bet > max_bet:
                        print("Insurance bet must be between 1 and %8.2f" % (max_bet))
                        continue
                    break
            player.hands[0].insurance = bet
            self.draw_table()

        if Dealer.has_blackjack:
            print('Dealer has BlackJack!')
            Dealer.hand.cards[0].face_up = True
            Dealer.hand.update()
            self.draw_table()
            for player in self.players:
                if player.hands[0].hand_state != Hand.state_blackjack:
                    player.lost()
                    self.draw_table()
                else:
                    # Insurance bet pays twice
                    player.money += player.hands[0].insurance * 2

    def interact(self):

        # Read player commands
        has_valid_hands = True
        while has_valid_hands:
            for player in self.players:
                player.read_command(self.deck)
                self.draw_table()

            has_valid_hands = False
            for player in self.players:
                for hand in player.hands:
                    if hand.hand_state == Hand.state_play:
                        has_valid_hands = True
                        break
                if has_valid_hands:
                    break


        Dealer.play(self, self.deck);
        self.draw_table()

        ## Check results
        self.state = Table.state_results

        # Check winning hands
        winning_hands = [ ]

        if Dealer.hand.points == 21:
            winning_hands.append(Dealer.hand)
            Dealer.hand.hand_state = Hand.state_won
        for player in self.players:
            for hand in player.hands:
                if hand.hand_state == Hand.state_busted:
                    continue

                if hand.hand_state in [ Hand.state_blackjack, Hand.state_21 ]:
                    # Paying winners
                    if Dealer.hand.points != 21:
                        Dealer.hand.hand_state = Hand.state_lost
                        winning_hands.append(hand)
                        player.money += hand.bet * 2
                    else:
                        player.money += hand.bet
                        hand.hand_state = Hand.state_draw
                        Dealer.hand.hand_state = Hand.state_draw
                elif Dealer.hand.hand_state == Hand.state_won:
                    hand.hand_state = Hand.state_lost

        # If no blackjack or 21, check highest scores that were not busted
        if len(winning_hands) > 0:
            self.new_match()
            return;

        hi_score = 0
        
        # Checking if dealer won
        if Dealer.hand.points < 21:
            hi_score = Dealer.hand.points
            Dealer.hand.hand_state = Hand.state_won

        # Defining and paying winners
        for player in self.players:
            for hand in player.hands:
                if hand.hand_state == Hand.state_busted:
                    continue

                if hand.points > hi_score:
                    hand.hand_state = Hand.state_won
                    player.money += hand.bet * 2
                elif hand.points == hi_score:
                    hand.hand_state = Hand.state_draw
                    player.money += hand.bet
                else:
                    hand.hand_state = Hand.state_lost

        self.new_match()

    def new_match(self):

        self.draw_table()

        print('Preparing next match...')
        time.sleep(5)
        self.state = Table.state_wait_bet

        self.dealer.reset()
        for player in self.players:
            player.reset()


#
# Loop info
#
# - Player Bet
# - Dealer distributes 2 cards to the player
# - Dealer gets two cards to himself
# - Dealer shows off one of his cards
# - The other card remains face down (hole card)
# - If the dealer has an ace facing up, then it offers an Insurance bet
#     (Basically the player that takes insurance bet, will win 2:1 on the side bet value,
#     which cannot exceeds 50% of initial bet, if the dealer has a blackjack)
#   - This side bet cannot exceed half of the original's player bet
#   - If dealer has a blackjack (ace + any 10 points card), he will show it
#       - At this point, all players without insurance bet will lose
#       - Players with insurance will lose their initial bet and win 2:1 the insurance bet
#           - If player initial bet was 5, the side bet (insurance) will be 2.5.
#           - Supposing dealer had blackjack, player wins 5 back and loses initial bet (5).
# - If dealer has blackjack, he wins the match
#   - If another player starts with a blackjack, then pot is split between dealer and players with blackjack
# - If player has two cards with same value (10 points card, or any duplicated card), he can split:
#   - Split:
#       - Player will have 2 hands and 2 parallel games do handle
# - Hit:
#   - Player gets an extra card
# - Stand:
#   - Player wants to stay with the cards he already has and wait on others
# - Double:
#   - Player will get only 1 more card and wait (if not busted)
# - If player busted, he loses his money to the house
# - If player stand or reached 21 / blackjack, he waits till match is over
# - After player stand, dealer will get extra cards till it has less or equal 17 points
#
os.system("clear")
print('Welcome to Python BlackJack!')
table = Table()

table.number_of_players()

while True:
    idx = 0
    while idx < len(table.players):
        player = table.players[idx]
        if player.money > 0:
            idx += 1
            continue
        else:
            print('Player [ %s ] is out of money and is being removed' %(player.name))
            time.sleep(1)
            del table.players[idx]

    if len(table.players) == 0:
        print('Everybody is poor now and house is happy')
        print('Game Over')
        break

    table.read_bets()
    table.distribute_initial_cards()
    table.interact()