#%%
import numpy as np
from pytimedinput import timedInput

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
Buy = 1
Offer = -1
Sell = -1
side_map = {1: "Bid", -1: "Offer"}

def calc_decayed_var(i):
    """Linear decaying variance"""
    var_width = STD_MAX - STD_MIN
    dec_per_it = var_width / ITERATIONS

    return STD_MAX - i*dec_per_it

def calc_n_quotes(n_books, scale=2):
    return max(np.ceil(np.random.exponential(scale=scale)), n_books)

def display_books(lst):
    # TODO
    pass

class Trader:
    def __init__(self, books):
        self.log = {
            b.label: {
                "book": b,
                "trades": []
            }
        for b in books}

    def process_action(self, trade, book_label):
        self.log[book_label]['trades'].append(trade)

    def reconcile(self):
        pnls = []
        for _, v in self.log.items():
            b = v['book']
            trades = v['trades']
            pos = sum([np.sign(t) for t in trades])

            pnl = round(b.settlement*pos - sum(trades), 2)
            pnls.append(pnl)
            
            book_res = {
                "Position": pos,
                "Trades": v['trades'],
                "Settles": b.settlement,
                "Market Theo": b.theo,
                "PnL": f"$ {pnl}"
            }
            print(f"{b.name}: ")
            print(book_res)

        
class Quote:
    def __init__(self, price, side, book_name) -> None:
        self.book_name = book_name
        self.price = round(price)
        self.side = side  # 1 = bid, # 0 = offer

    def __repr__(self):
        return f"{self.book_name}: {side_map[self.side]} {self.price}"

class Book:
    def __init__(self, name='Future A', label='a'):
        self.bids = []
        self.offers = []
        self.name = name
        self.label = label
        self.theo = np.random.uniform(MEAN_MIN, MEAN_MAX)
        self.settlement = np.random.normal(self.theo, STD_SETTLEMENT)

    def get_best_offer(self):
        return min(self.offers) if self.offers else 2e16

    def get_best_bid(self):
        return max(self.bids) if self.bids else -2e16
    
    def clean(self):
        if len(self.offers) > 5:
            worst_offer = max(self.offers)
            self.offers.remove(worst_offer)
            print(f"{self.name}: Removed {worst_offer} Offer")
        if len(self.bids) > 5:
            worst_bid = min(self.bids)
            self.bids.remove(worst_bid)
            print(f"{self.name}: Removed {worst_bid} Bid")
    
    def append(self, quote):
        # Appends to order book (quote is not in cross)
        print(quote)
        if quote.side:
            self.bids.append(quote.price)
        else:
            self.offers.append(quote.price)

        self.clean()

    def generate_quote(self, i):
        # bid = 1
        price = np.random.normal(self.theo, calc_decayed_var(i))
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

        return Quote(price, side)

    def process_quote(self, quote):
        # Quote is in cross
        best_offer = self.get_best_offer()
        best_bid = self.get_best_bid()
        lift = quote.side == Bid and quote.price > best_offer
        hit = quote.side == Offer and quote.price < best_bid

        if lift:
            print(f"{self.name}: {best_offer} Offer Lifted")
            self.offers.remove(best_offer)
        elif hit:
            print(f"{self.name}: {best_bid} Bid Hit")
            self.bids.remove(best_bid)
        else:
            self.append(quote)

    def process_action(self, raw_action) -> bool:
        """Returns true if the action was able to be processed correctly"""
        if raw_action == 'h':
            price = self.get_best_bid()
            print(f'{self.name}: Sold @ {price}!')
            self.bids.remove(price)
            return True, Sell * price

        elif raw_action == 'l':
            price = self.get_best_offer()
            print(f'{self.name}: Bought @ {price}!')
            self.offers.remove(price)
            return True, Buy * price
        
        return False, None


class Market:
    def __init__(self, books: list, trader: Trader):
        self.books = books
        self.book_map = {b.label: b for b in books}
        self.trader = trader

    def input_valid(self, string) -> bool:
        return len(string) == 2 and string[0] in ['l', 'h'] and string[1] in self.book_map.keys()

    def input_parse(self, user_input):
        actions = user_input.split(' ')
        valid_actions = [a for a in actions if self.input_valid(a)]
        return valid_actions
    
    def input_request(self, timeout):
        user_input, missed = timedInput(timeout=timeout, resetOnInput=False, endCharacters='\r')

        if missed:
            if user_input:
                print('No Action')
            else:
                actions = self.input_parse(user_input)
                return actions

    def process_actions(self, actions:list):
        if actions is None:
            return
        
        for action, book_label in actions:
            book = self.book_map[book_label]
            processed, trade = book.process_action(action)
            if processed:
                self.trader.process_action(trade, book_label)
            
    def start(self):
        n_books = len(self.books)
        for i in range(ITERATIONS):
            # Generate and print quotes
            n_quotes = calc_n_quotes(n_books)
            quote_books = np.random.choice(self.books, n_quotes, replace=False)
            for b in quote_books:
                q = b.generate_quote(i)
                b.process_quote(q)

            # Listen for user actions & execute
            actions = self.input_request(timeout=1.5)
            self.process_actions(actions)
            
            # Display Book
            # TODO
            # Listen for user actions & execute
            # TODO

        # End result

if __name__ == '__main__':
    future_a = Book('Future A', 'a')
    future_b = Book('Future B', 'b')
    books = [future_a, future_b]

    t = Trader(books=books, name='Warren Buffet')
    m = Market(books=books, trader=t)
    m.start()

    t.reconcile()