import numpy as np
from pytimedinput import timedInput

# Trade itself [x]
# Remove Stale [x]
# Human Interface
    # varying times for quotes

ITERATIONS = 35
MEAN_MIN = 100
MEAN_MAX = 250

STD_MIN = 5
STD_MAX = 50
STD_SETTLEMENT = 25

CROSS_PROB = 0.4

TIME_LOW = 0.2
TIME_HIGH = 2


Bid = 1
Offer = 0
Buy = 1
Sell = -1
side_map = {1: "Bid", 0: "Offer"}

class Quote:
    def __init__(self, price, side) -> None:
        self.price = round(price)
        self.side = side  # 1 = bid, # 0 = offer

    def __repr__(self):
        return f"{side_map[self.side]} {self.price}"

class Book:
    def __init__(self):
        self.bids = []
        self.offers = []

    def best_offer(self):
        return min(self.offers) if self.offers else 2e16

    def best_bid(self):
        return max(self.bids) if self.bids else -2e16

    def display(self):
        bids = sorted(self.bids, reverse=True)
        offers = sorted(self.offers, reverse=True)

        for o in offers:
            print(f'     | {o} ')
        for b in bids:
            print(f' {b} |  ')

    def clean_book(self):
        if len(self.offers) > 5:
            worst_offer = max(self.offers)
            self.offers.remove(worst_offer)
            print(f"Removed {worst_offer} Offer")
        if len(self.bids) > 5:
            worst_bid = min(self.bids)
            self.bids.remove(worst_bid)
            print(f"Removed {worst_bid} Bid")

    def append(self, quote):
        # Appends to order book (quote is not in cross)
        print(quote)
        if quote.side:
            self.bids.append(quote.price)
        else:
            self.offers.append(quote.price)

        self.clean_book()

    def process_quote(self, quote):
        # Quote is in cross
        lift = quote.side == Bid and quote.price > self.best_offer()
        hit = quote.side == Offer and quote.price < self.best_bid()

        if lift:
            print(f"{self.best_offer()} Offer Lifted")
            self.offers.remove(self.best_offer())
        elif hit:
            print(f"{self.best_bid()} Bid Hit")
            self.bids.remove(self.best_bid())
        else:
            self.append(quote)


class Bot:
    def __init__(self):
        self.theo = np.random.uniform(MEAN_MIN, MEAN_MAX)

    def calc_var(self, i):
        var_width = STD_MAX - STD_MIN
        dec_per_it = var_width / ITERATIONS

        return STD_MAX - i*dec_per_it

    def quote(self, i):
        # bid = 1
        price = np.random.normal(self.theo, self.calc_var(i))
        cross = np.random.random() < CROSS_PROB # the bot will cross itself (quote a bad price)

        if price < self.theo:
            if cross:
                side = Offer
            else:
                side = Bid
        else:
            if cross:
                side = Bid
            else:
                side = Offer
        # side = int(price < self.theo and not cross)

        return Quote(price, side)

class Game:
    def __init__(self):
        self.bot = Bot()
        self.book = Book()
        self.position = 0
        self.settlement = np.random.normal(self.bot.theo, STD_SETTLEMENT)
        self.trades = []

    def start(self):
        difficulty=input("Set Difficulty: Easy, Medium, Hard \n")
        if difficulty == 'Easy':
            multiplier = 3
        elif difficulty == 'Medium':
            multiplier = 2
        else:
            multiplier=1
        for i in range(ITERATIONS):
            q = self.bot.quote(i)
            self.book.process_quote(q)
            player_action, missed = timedInput(timeout=1, resetOnInput=False, endCharacters='\r')

            if missed:
                if player_action:
                    print('No Action')
            else:
                self.process_action(player_action)

            self.book.display()
            variable_speed = int(round(np.random.uniform(TIME_LOW*multiplier,TIME_HIGH*multiplier)))
            player_action, missed = timedInput(timeout=variable_speed, resetOnInput=False, endCharacters='\r')

            if missed:
                if player_action:
                    print('No Action')
            else:
                self.process_action(player_action)

            print("-"*80)

        print(f"Position: {self.position}")
        print(f"Trades: {self.trades}")
        print(f'Settles @ {self.settlement}')
        print(f'Bot Theo: {self.bot.theo}')
        print(f'PnL: $ {round(self.settlement*self.position - sum(self.trades), 2)}')

    def process_action(self, action):
        """Action must be hit, lift, mine or yours"""
        if action in ['h', 'yours']:
            self.execute(Sell, self.book.best_bid())

        if action in ['l', 'mine']:
            self.execute(Buy, self.book.best_offer())

    def execute(self, side, price):
        self.position += side
        self.trades.append(side * price)
        if side > 0:
            print(f"Bought @ {self.book.best_offer()}!")
            self.book.offers.remove(self.book.best_offer())
        else:
            print(f"Sold @ {self.book.best_bid()}!")
            self.book.bids.remove(self.book.best_bid())

if __name__ == '__main__':
    g = Game()
    g.start()