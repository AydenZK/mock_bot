import numpy as np
from pytimedinput import timedInput

# Trade itself [x]
# Remove Stale [x]
# Human Interface
    # varying times for quotes

ITERATIONS = 75
B_MEAN_MIN = 100
B_MEAN_MAX = 250
A_MEAN_MIN = 250
A_MEAN_MAX = 400

STD_MIN = 5
STD_MAX = 50
STD_SETTLEMENT = 25

CROSS_PROB = 0.4

TIME_LOW = 2
TIME_HIGH = 4


Bid = 1
Offer = 0
Buy = 1
Sell = -1
side_map = {1: "Bid", 0: "Offer"}

class Quote:
    def __init__(self, price, side, book_title) -> None:
        self.price = round(price)
        self.side = side  # 1 = bid, # 0 = offer
        self.book_title = book_title

    def __repr__(self):
        return f"{self.book_title} {side_map[self.side]} {self.price}"

class Book:
    def __init__(self, title):
        self.bids = []
        self.offers = []
        self.title = title

    def best_offer(self):
        return min(self.offers) if self.offers else 2e16

    def best_bid(self):
        return max(self.bids) if self.bids else -2e16

    def display(self):
        bids = sorted(self.bids, reverse=True)
        offers = sorted(self.offers, reverse=True)

        print(f"{self.offset}Book: {self.title}")
        print(f'{self.offset}' + ' '*15)
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
            print(f"{self.title} {self.best_offer()} Offer Lifted")
            self.offers.remove(self.best_offer())
        elif hit:
            print(f"{self.title} {self.best_bid()} Bid Hit")
            self.bids.remove(self.best_bid())
        else:
            self.append(quote)

        self.bids = sorted(self.bids, reverse=True)
        self.offers = sorted(self.offers, reverse=True)


class Bot:
    def __init__(self,mean_min=0,mean_max=0, theo=None, bot_title = ""):
        self.bot_title = bot_title
        if theo is None:
            self.theo = np.random.uniform(mean_min, mean_max)
        else:
            self.theo = theo
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

        return Quote(price, side, self.bot_title)

class Game:
    def __init__(self):
        self.abot = Bot(A_MEAN_MIN,A_MEAN_MAX, bot_title='A')
        self.bbot = Bot(B_MEAN_MIN,B_MEAN_MAX, bot_title='B')
        self.sbot = Bot(theo=self.abot.theo-self.bbot.theo, bot_title='A-B (Spread)')
        self.abook = Book(title='A')
        self.bbook = Book(title='B')
        self.sbook = Book(title='A-B (Spread)')
        self.aposition = 0
        self.bposition = 0
        self.sposition = 0
        self.asettlement = np.random.normal(self.abot.theo, STD_SETTLEMENT)
        self.bsettlement = np.random.normal(self.bbot.theo, STD_SETTLEMENT)
        self.ssettlement = self.asettlement - self.bsettlement
        self.atrades = []
        self.btrades = []
        self.strades = []
        self.books = [self.abook, self.bbook, self.sbook]

    def start(self):
        difficulty=input("Set Difficulty: Easy, Medium, Hard \n")
        if difficulty == 'Easy':
            multiplier = 3
        elif difficulty == 'Medium':
            multiplier = 2
        else:
            multiplier=1
        bots=[self.abot,self.bbot,self.sbot]
        books=[self.abook,self.bbook,self.sbook]
        for i in range(ITERATIONS):
            market=np.random.randint(0,3)
            q = bots[market].quote(i)
            books[market].process_quote(q)
            player_action, missed = timedInput(timeout=1, resetOnInput=False, endCharacters='\r')

            if missed:
                if player_action:
                    print('No Action')
            else:
                self.process_action(player_action)
            
            display_books(books)
            variable_speed = int(round(np.random.uniform(TIME_LOW*multiplier,TIME_HIGH*multiplier)))
            player_action, missed = timedInput(timeout=variable_speed, resetOnInput=False, endCharacters='\r')

            if missed:
                if player_action:
                    print('No Action')
            else:
                self.process_action(player_action)

            print("-"*80)
        apnl=self.asettlement*self.aposition - sum(self.atrades)
        bpnl=self.asettlement*self.bposition - sum(self.btrades)
        spnl=self.asettlement*self.sposition - sum(self.strades)

        print(f"Position A: {self.aposition}, B: {self.bposition}, S: {self.sposition}")
        print(f"Trades A: {self.atrades}")
        print(f"Trades B: {self.btrades}")
        print(f"Trades S: {self.strades}")
        print(f"Settles @ A: {self.asettlement}, B: {self.bsettlement}")
        print(f'Bot Theo A: {self.abot.theo}, B: {self.bbot.theo}')
        print(f'PnL: $ {round(apnl+bpnl+spnl, 2)}')

    def process_action(self, user_input):
        """Action must be hit, lift, mine or yours"""
        if len(user_input) != 2:
            print('Invalid Action')
            return
        book_map = {'a': self.abook, 'b': self.bbook, 's': self.sbook}
        action_i, book_i = user_input

        try:
            book = book_map[book_i]
        except KeyError:
            print('Invalid Action')
            return

        action_map = {'h': (Sell, book.best_bid()), 'l': (Buy, book.best_offer())}
        try:
            action, price = action_map[action_i]
        except KeyError:
            print('Invalid Action')
            return

        
        
        self.execute(action, price, book_i)


    def execute(self, side, price, market):
        if market == 'a':
            self.aposition += side
            self.atrades.append(side * price)
            if side > 0:
                print(f"Bought A @ {self.abook.best_offer()}!")
                self.abook.offers.remove(self.abook.best_offer())
            else:
                print(f"Sold A @ {self.abook.best_bid()}!")
                self.abook.bids.remove(self.abook.best_bid())
        elif market == 'b':
            self.bposition += side
            self.btrades.append(side * price)
            if side > 0:
                print(f"Bought B @ {self.bbook.best_offer()}!")
                self.bbook.offers.remove(self.bbook.best_offer())
            else:
                print(f"Sold B @ {self.bbook.best_bid()}!")
                self.bbook.bids.remove(self.bbook.best_bid())
        elif market == 's':
            self.sposition += side
            self.strades.append(side * price)
            if side > 0:
                print(f"Bought Spread @ {self.sbook.best_offer()}!")
                self.sbook.offers.remove(self.sbook.best_offer())
            else:
                print(f"Sold Spread @ {self.sbook.best_bid()}!")
                self.sbook.bids.remove(self.sbook.best_bid())

def display_books(lst):
    offsets = ["", " "*15, " "*30]

    for i, book in enumerate(lst):
        offset = offsets[i]
        print(f"{offset}Book: {book.title}", end='')
    print()

    for i in range(3):
        man_offsets = [0,7,22]
        offset = man_offsets[i]
        print(f"{' '*offset}{'-'*15}", end='')
    print()


    for row in range(10):
        for i, book in enumerate(lst):
            pad_start = 5 - len(book.offers)
            pad_end = 5 - len(book.bids)
            orders = [""]*pad_start + book.offers + book.bids + [""]*pad_end
            offset = offsets[i]

            offer_side = row <= 4

            x = orders[row]
            if offer_side:
                print(f'{offset}     | {x or "   "} ', end = "")
            else:
                print(f'{offset} {x or "   "} |     ', end = "")

        print()

if __name__ == '__main__':
    g = Game()
    g.start()