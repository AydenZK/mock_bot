import numpy as np
import pandas as pd
from pytimedinput import timedInput
from abc import ABC, abstractmethod

Bid = 1
Buy = 1
Offer = -1
Sell = -1
side_map = {1: "Bid", -1: "Offer"}

def calc_n_quotes(n_books: int, scale: float = 2) -> int:
    """Calculate number of quotes for a given update."""
    return int(min(np.ceil(np.random.exponential(scale=scale)), n_books))

def display_books(lst: list) -> None:
    """Takes in a list of books"""
    seperator = ['|']*10
    padding = ['']*5

    data = {}
    for i, book in enumerate(lst):
        data[book.name] = padding + sorted(book.bids, reverse=True) + [''] * (5-len(book.bids)) # bids col
        data['.'*i] = seperator # sepreator col
        data[book.label] = [''] * (5-len(book.offers)) + sorted(book.offers, reverse=True) + padding # offers col

    df = pd.DataFrame(data=data)
    print(df.to_string())

class Book:
    """A book is a collection of quotes for a given market."""
    def __init__(self, name: str, label: str, iterations: int, 
                 std_min: int, std_max: int, theo_min: int, theo_max: int,
                 settlement_std: int, cross_prob: float):
        self.bids = []
        self.offers = []
        self.name = name
        self.label = label
        self.iterations = iterations
        self.std_min = std_min
        self.std_max = std_max
        self.cross_prob = cross_prob
        self.theo = np.random.uniform(theo_min, theo_max)
        self.settlement = np.random.normal(self.theo, settlement_std)

    def get_best_offer(self) -> float:
        """Returns the best offer in the book."""
        return min(self.offers) if self.offers else 2e16

    def get_best_bid(self):
        """Returns the best bid in the book."""
        return max(self.bids) if self.bids else -2e16
    
    def clean(self):
        """Removes the worst bid and offer"""
        if len(self.offers) > 5:
            worst_offer = max(self.offers)
            self.offers.remove(worst_offer)
            print(f"{self.name}: Removed {worst_offer} Offer")
        if len(self.bids) > 5:
            worst_bid = min(self.bids)
            self.bids.remove(worst_bid)
            print(f"{self.name}: Removed {worst_bid} Bid")
    
    def append(self, quote):
        """Appends a quote to the book"""
        print(quote)
        if quote.side == Bid:
            self.bids.append(quote.price)
        elif quote.side == Offer:
            self.offers.append(quote.price)

        self.clean()

    def generate_quote(self, i: int):
        """Generates a quote for the book. Returns a Quote object."""
        # bid = 1
        price = np.random.normal(self.theo, self.calc_decayed_var(i))
        cross = np.random.uniform() < self.cross_prob # the bot will cross itself (quote a bad price)

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

        return Quote(price, side, self.name)

    def process_quote(self, quote):
        """Processes a quote and updates the book."""
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
    
    def calc_decayed_var(self, i: int) -> float:
        """Linear decaying variance"""
        var_width = self.std_max - self.std_min
        dec_per_it = var_width / self.iterations

        return self.std_max - i*dec_per_it

class Trader:
    def __init__(self, books: list[Book], name: str) -> None:
        self.log = {
            b.label: {
                "book": b,
                "trades": []
            }
        for b in books}

    def process_action(self, trade: float, book_label: str) -> None:
        self.log[book_label]['trades'].append(trade)

    def reconcile(self) -> None:
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

        print(f"Overall PnL: $ {sum(pnls)}")
        
class Quote:
    """A quote on an order book."""
    def __init__(self, price, side, book_name) -> None:
        self.book_name = book_name
        self.price = round(price)
        self.side = side  # 1 = bid, # 0 = offer

    def __repr__(self):
        """String representation of a quote."""
        return f"{self.book_name}: {side_map[self.side]} {self.price}"

class Market:
    """A class to trigger and maintain market simulation."""
    def __init__(self, books: list[Book], trader: Trader, iterations: int):
        self.books = books
        self.book_map = {b.label: b for b in books}
        self.trader = trader
        self.iterations = iterations

    def input_valid(self, string) -> bool:
        """Check if user input is valid."""
        return string[0] in ['l', 'h'] and string[1] in self.book_map.keys()

    def input_parse(self, user_input: str) -> list[str]:
        """Parse user input into a list of actions.
        Args:
            user_input (str): User input.
        Returns:
            list[str]: List of user actions.
        """
        actions = user_input.split(' ')
        valid_actions = [a for a in actions if self.input_valid(a)]
        return valid_actions
    
    def input_request(self, timeout: int) -> list[str]:
        """Request user input.
        Args:
            timeout (int): Number of seconds to wait for user input.
        Returns:
            list[str]: List of user actions."""
        user_input, missed = timedInput(
            prompt = 'Enter Trades: ', timeout=timeout, 
            resetOnInput=False, endCharacters='\r')

        if user_input == 'end':
            return 'END'

        if missed:
            if user_input:
                print('No Action')
        else:
            actions = self.input_parse(user_input)
            return actions

    def process_actions(self, actions:list) -> None:
        """Process user actions. 
        Args:
            actions (list): List of tuples of the form (action, book_label)
        """
        if actions is None:
            return
        
        for action, book_label in actions:
            book = self.book_map[book_label]
            processed, trade = book.process_action(action)
            if processed:
                self.trader.process_action(trade, book_label)
            
    def start(self):
        """Start the market simulation. 
        Each iteration generates quotes and processes user actions.
        """
        n_books = len(self.books)
        for i in range(self.iterations):
            # Generate and print quotes
            n_quotes = calc_n_quotes(n_books)
            quote_books = np.random.choice(self.books, size=n_quotes, replace=False)
            for b in quote_books:
                q = b.generate_quote(i)
                b.process_quote(q)

            # Listen for user actions & execute
            actions = self.input_request(timeout=2)
            if actions == 'END': break
            self.process_actions(actions)
            
            # Display Books
            display_books(self.books)

            # Listen for user actions & execute
            actions = self.input_request(timeout=2)
            if actions == 'END': break
            self.process_actions(actions)

class Option(Book):
    def __init__(self, underlying, strike) -> None:
        super().__init__()
        self.underlying = underlying
        self.strike = strike
        self.theo = self.calc_option_theo()
        self.iterations = self.underlying.iterations

    def calc_option_theo(self) -> float:
        """Calculate theoretical value of option."""
        raise NotImplementedError
    
    def calc_option_price(self) -> float:
        """Calculate option price."""
        raise NotImplementedError

class Call(Option):
    def __init__(self) -> None:
        super().__init__()
        self.theo = self.calc_option_theo()
        self.name = f"{self.underlying.label} {self.strike} Call"
        self.label = f"{self.underlying.label}{self.strike}c"

    def calc_option_theo(self) -> float:
        """Calculate theoretical value of call option."""
        return max(self.underlying.theo - self.strike, 0)
    
    def calc_option_price(self) -> float:
        """Calculate option price."""
        raise NotImplementedError
    
class Put(Option):
    def __init__(self) -> None:
        super().__init__()
        self.theo = self.calc_option_theo()
        self.name = f"{self.underlying.label} {self.strike} Put"
        self.label = f"{self.underlying.label}{self.strike}p"

    def calc_option_theo(self) -> float:
        """Calculate theoretical value of put option."""
        return max(self.strike - self.underlying.theo, 0)
    
    def calc_option_price(self) -> float:
        """Calculate option price."""
        raise NotImplementedError

if __name__ == '__main__':
    iterations = 20

    future_a = Book(
        name='Future A', label='a', iterations=iterations, 
        std_min=5, std_max=50, theo_min=100, theo_max=250,
        settlement_std=25, cross_prob = 0.4
    )
    call_a = Call(underlying = future_a, strike=100)

    future_b = Book(
        name='Future B', label='b', iterations=iterations, 
        std_min=5, std_max=50, theo_min=100, theo_max=250,
        settlement_std=25, cross_prob = 0.4
    )
    books = [future_a, future_b]

    t = Trader(books=books, name='Warren Buffet')
    m = Market(books=books, trader=t)
    m.start()

    t.reconcile()