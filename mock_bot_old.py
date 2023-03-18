#%%
class Game:
    def __init__(self):
        self.bot = Bot()
        self.book = Book(pos=1)
        self.position = 0
        self.settlement = np.random.normal(self.bot.theo, STD_SETTLEMENT)
        self.trades = []

    def start(self):
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
            variable_speed = int(round(np.random.uniform(TIME_LOW,TIME_HIGH)))
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
        if action in ['h']:
            self.execute(Sell, self.book.best_bid())

        if action in ['l']:
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

class BookOld:
    def __init__(self, title='A', pos=0):
        self.bids = []
        self.offers = []
        self.title = title
        self.pos = pos
        self.so = " "*15*self.pos # string start offset

    def best_offer(self):
        return min(self.offers) if self.offers else 2e16

    def best_bid(self):
        return max(self.bids) if self.bids else -2e16

    def display(self):
        bids = sorted(self.bids, reverse=True)
        offers = sorted(self.offers, reverse=True)

        print(f'{self.so}Book: {self.title}')
        print(f'{self.so}{"-"*15}')
        for o in offers:
            print(f'{self.so}     | {o} ')
        for b in bids:
            print(f'{self.so} {b} |  ')

    def clean_book(self):
        if len(self.offers) > 5:
            worst_offer = max(self.offers)
            self.offers.remove(worst_offer)
            print(f"{self.so}Removed {worst_offer} Offer")
        if len(self.bids) > 5:
            worst_bid = min(self.bids)
            self.bids.remove(worst_bid)
            print(f"{self.so}Removed {worst_bid} Bid")

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
            print(f"{self.so}{self.best_offer()} Offer Lifted")
            self.offers.remove(self.best_offer())
        elif hit:
            print(f"{self.so}{self.best_bid()} Bid Hit")
            self.bids.remove(self.best_bid())
        else:
            self.append(quote)

