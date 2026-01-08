import random
from dataclasses import dataclass, field, asdict
from typing import List, Optional

SUITS = ["oros", "copas", "espadas", "bastos"]
# Ranks in Spanish deck (we use ints 1..7, 10..12)
RANKS = [1,2,3,4,5,6,7,10,11,12]

def card_value(rank):
    # scoring value for the simplified variant
    if 1 <= rank <= 7:
        return rank
    return 10  # 10,11,12 => 10 points

@dataclass
class Card:
    suit: str
    rank: int

    def to_dict(self):
        return {"suit": self.suit, "rank": self.rank}

    def __repr__(self):
        return f"{self.rank} de {self.suit}"

class Deck:
    def __init__(self):
        self.cards = [Card(s, r) for s in SUITS for r in RANKS]
        random.shuffle(self.cards)

    def deal(self, n):
        hands = []
        per = len(self.cards) // n
        for i in range(n):
            start = i*per
            hands.append(self.cards[start:start+per])
        return hands

@dataclass
class Player:
    sid: str
    name: str
    hand: List[Card] = field(default_factory=list)
    won_cards: List[Card] = field(default_factory=list)
    is_bot: bool = False
    bot_id: Optional[str] = None

    def to_public(self):
        return {"name": self.name, "is_bot": self.is_bot, "cards_in_hand": len(self.hand)}

    def to_private(self):
        return {"name": self.name, "hand": [c.to_dict() for c in self.hand], "won_cards_count": len(self.won_cards)}

class GameRoom:
    def __init__(self, room_id, max_players=4):
        self.room_id = room_id
        self.max_players = max_players
        self.players: List[Player] = []
        self.started = False
        self.current_trick = []  # list of (player, card)
        self.turn_index = 0
        self.round = 0

    def serializable(self):
        return {
            "room_id": self.room_id,
            "max_players": self.max_players,
            "players": [p.to_public() for p in self.players],
            "started": self.started
        }

    def is_full(self):
        return len(self.players) >= self.max_players

    def add_player(self, player: Player):
        self.players.append(player)

    def add_bot(self, name="Bot"):
        bot = Player(sid=f"bot-{len(self.players)}", name=name, is_bot=True, bot_id=str(len(self.players)))
        self.players.append(bot)

    def remove_player_by_sid(self, sid):
        for i,p in enumerate(self.players):
            if p.sid == sid:
                del self.players[i]
                return True
        return False

    def get_player_by_sid(self, sid) -> Optional[Player]:
        for p in self.players:
            if p.sid == sid:
                return p
        return None

    def start_game(self):
        if self.started:
            return False
        if len(self.players) < 2:
            return False
        self.started = True
        self.round += 1
        # create and deal deck
        deck = Deck()
        hands = deck.deal(len(self.players))
        for p, h in zip(self.players, hands):
            p.hand = h
            p.won_cards = []
        self.current_trick = []
        self.turn_index = 0
        return True

    def play_card(self, player: Player, card_dict):
        if not self.started:
            return False, "Game not started"
        # check it's player's turn
        if self.players[self.turn_index].sid != player.sid:
            return False, "Not your turn"
        # find card in player's hand
        card_obj = None
        for c in player.hand:
            if c.suit == card_dict.get("suit") and c.rank == card_dict.get("rank"):
                card_obj = c
                break
        if not card_obj:
            return False, "Card not in hand"
        player.hand.remove(card_obj)
        self.current_trick.append((player, card_obj))
        # advance turn
        self.turn_index = (self.turn_index + 1) % len(self.players)
        # if trick complete, resolve
        if len(self.current_trick) == len(self.players):
            self.resolve_trick()
        return True, "Card played"

    def resolve_trick(self):
        # determine winner by rank then suit order (oros>copas>espadas>bastos)
        def sort_key(pc):
            player, card = pc
            suit_order = {s:i for i,s in enumerate(SUITS)}
            rank_order = RANKS.index(card.rank)
            return (rank_order, suit_order[card.suit])
        winner_pair = max(self.current_trick, key=sort_key)
        winner = winner_pair[0]
        # winner takes all cards
        for _, c in self.current_trick:
            winner.won_cards.append(c)
        # reset trick
        self.current_trick = []
        # winner leads next
        self.turn_index = self.players.index(winner)
        # check if round finished (no cards in hands)
        if all(len(p.hand) == 0 for p in self.players):
            # scoring; keep accumulating across rounds
            # For simplicity, we compute scores elsewhere or here
            pass

    def public_state_for_all(self):
        return {
            "room_id": self.room_id,
            "players": [p.to_public() for p in self.players],
            "started": self.started,
            "current_trick": [ {"player": pc[0].name, "card": pc[1].to_dict()} for pc in self.current_trick],
            "turn_index": self.turn_index,
            "scores": {p.name: sum(card_value(c.rank) for c in p.won_cards) for p in self.players}
        }

    def private_state_for_player(self, player: Player):
        return {
            "you": player.to_private(),
            "public": self.public_state_for_all()
        }

    def play_bot_turn(self, bot: Player):
        # Basic bot: play random card
        if not bot.hand:
            return
        card = random.choice(bot.hand)
        self.play_card(bot, card.to_dict())

    def resolve_bots_turns(self):
        # while current turn is a bot, auto-play
        loop_guard = 0
        while self.players[self.turn_index].is_bot and loop_guard < 50:
            bot = self.players[self.turn_index]
            self.play_bot_turn(bot)
            loop_guard += 1
        # if round ended (no cards), check for scores and reset if desired
        if all(len(p.hand) == 0 for p in self.players):
            # accumulate points; for simplicity we end the game after a single deal if someone reaches 41
            # Calculate scores
            scores = {p.name: sum(card_value(c.rank) for c in p.won_cards) for p in self.players}
            # if someone >=41, mark game not started
            for p in self.players:
                if scores[p.name] >= 41:
                    self.started = False
                    break
            # else prepare next round: create new deck and redeal
            if self.started:
                deck = Deck()
                hands = deck.deal(len(self.players))
                for p,h in zip(self.players,hands):
                    p.hand = h
                self.current_trick = []
                self.turn_index = 0