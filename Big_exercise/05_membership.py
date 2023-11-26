import smartpy as sp

@sp.module
def main():

    param_type:type = sp.record(source = sp.address, destination = sp.address, amount = sp.nat)

    class Ledger(sp.Contract):
        def __init__(self, owner, total_supply):
            self.data.balances = sp.big_map({ owner : total_supply })
            self.data.allowances = sp.big_map({})
          
        @sp.entrypoint
        def transfer(self, source, destination, amount):
            if source != sp.sender:
                allowed = self.data.allowances[(source, sp.sender)]
                assert allowed >= amount
                self.data.allowances[(source, sp.sender)] = sp.as_nat(allowed - amount)
            assert self.data.balances[source] >= amount
            self.data.balances[source] = sp.as_nat(self.data.balances[source] - amount)
            if not self.data.balances.contains(destination):
                self.data.balances[destination] = sp.nat(0)
            self.data.balances[destination] += amount

        @sp.onchain_view
        def get_balance(self, user):
            sp.cast(user, sp.address)
            return self.data.balances[user]

        @sp.entrypoint
        def allow(self, operator, amount):
            if not self.data.allowances.contains((sp.sender, operator)):
                self.data.allowances[(sp.sender, operator)] = 0
            self.data.allowances[(sp.sender, operator)] += amount
    
    class LiquidityPool(sp.Contract):
        def __init__(self, owner, ledger):
            self.data.ledger = ledger
            self.data.ledger_transfer = None
            self.data.owner = owner
            self.data.K = sp.tez(0)
            self.data.tokens_owned = sp.nat(0)
            # tokens_owned * sp.balance = K -> should always be true

        @sp.entrypoint
        def provide_liquidity(self, deposited_tokens):
            assert sp.sender == self.data.owner
            assert self.data.K == sp.tez(0)
            self.data.K = sp.mul(sp.balance, deposited_tokens)

            self.data.tokens_owned = deposited_tokens

            self.data.ledger_transfer = sp.contract(param_type, self.data.ledger, entrypoint="transfer")
            sp.transfer(sp.record(source = sp.sender, destination = sp.self_address(), amount = deposited_tokens), sp.tez(0), self.data.ledger_transfer.unwrap_some())
            
        @sp.entrypoint
        def withdraw_liquidity(self):
            assert sp.sender == self.data.owner
            sp.send(sp.sender, sp.balance)
            
            sp.transfer(sp.record(source = sp.self_address(), destination = sp.sender, amount = self.data.tokens_owned), sp.tez(0), self.data.ledger_transfer.unwrap_some())

            self.data.tokens_owned = sp.nat(0)
            self.data.K = sp.tez(0)

        
        @sp.entrypoint
        def sell_tokens(self, nb_tokens_sold, min_tez_requested):
            ratio = sp.ediv(self.data.K, self.data.tokens_owned + nb_tokens_sold).unwrap_some()
            tez_obtained = sp.balance - sp.fst(ratio)
            assert tez_obtained >= min_tez_requested

            sp.transfer(sp.record(source = sp.sender, destination = sp.self_address(), amount = nb_tokens_sold), sp.tez(0), self.data.ledger_transfer.unwrap_some())

            self.data.tokens_owned += nb_tokens_sold
            sp.send(sp.sender, tez_obtained)

        @sp.entrypoint
        def buy_tokens(self, min_tokens_bought):
            sp.cast(min_tokens_bought, sp.nat)
            tokens_obtained = sp.as_nat(self.data.tokens_owned - sp.fst(sp.ediv(self.data.K, sp.balance).unwrap_some()))
            assert tokens_obtained >= min_tokens_bought

            sp.transfer(sp.record(source = sp.self_address(), destination = sp.sender, amount = tokens_obtained), sp.tez(0), self.data.ledger_transfer.unwrap_some())

            self.data.tokens_owned = sp.as_nat(self.data.tokens_owned - tokens_obtained)
            

        @sp.onchain_view
        def get_token_price(self):
            # returns what we would get if we sold one token
            ratio1 = sp.ediv(self.data.K, self.data.tokens_owned).unwrap_some()
            ratio2 = sp.ediv(self.data.K, sp.as_nat(self.data.tokens_owned - 1)).unwrap_some()
            trace ("The current value of K is:")
            trace(self.data.K)
            trace("The pool owns this amount of tokens:")
            trace(self.data.tokens_owned)
            trace("The balance of the pool is:")
            trace(sp.balance)
            trace("The ratios before and after a potential purchase of 1 token would be:")
            trace(ratio1)
            trace(ratio2)
            token_price = sp.fst(ratio2) - sp.fst(ratio1)
            trace("The price of the token returned is:")
            trace(token_price)
            return token_price

    class Membership(sp.Contract):
        def __init__(self, membership_price, owner, ledger, liquidity_pool):
            self.data.owner = owner
            self.data.membership_price = membership_price
            self.data.members = sp.set()
            self.data.ledger = ledger
            self.data.liquidity_pool = liquidity_pool

        @sp.entrypoint
        def join(self):
            assert sp.amount == self.data.membership_price
            self.data.members.add(sp.sender)
            sp.send(self.data.owner, sp.amount)
            self.data.members.add(sp.sender)

        @sp.entrypoint
        def join_with_tokens(self, nb_tokens):
            sp.cast(nb_tokens, sp.nat)
            token_price =  sp.view("get_token_price", self.data.liquidity_pool, (), sp.mutez).unwrap_some();
            assert sp.mul(token_price, nb_tokens) > self.data.membership_price
            ledger_contract = sp.contract(param_type, self.data.ledger, entrypoint="transfer").unwrap_some()
            sp.transfer(sp.record(source = sp.sender, destination = self.data.owner, amount = nb_tokens), sp.tez(0), ledger_contract)
            self.data.members.add(sp.sender)

@sp.add_test()
def test():
    alice = sp.test_account("alice")
    bob = sp.test_account("bob")
    carl = sp.test_account("carl")
    
    scenario = sp.test_scenario("Test", main)
    ledger = main.Ledger(owner = alice.address, total_supply = 1000000)
    scenario += ledger
    
    liquidity_pool = main.LiquidityPool(owner = alice.address, ledger = ledger.address)
    scenario += liquidity_pool

    ledger.allow(operator = liquidity_pool.address, amount = 2000, _sender = alice)
    liquidity_pool.provide_liquidity(2000, _sender = alice, _amount = sp.tez(2000))
    
    membership = main.Membership(membership_price = sp.tez(1000), owner = alice.address, ledger = ledger.address, liquidity_pool = liquidity_pool.address)
    scenario += membership

    membership.join(_sender = carl, _amount = sp.tez(1000))

    ledger.transfer(source = alice.address, destination = carl.address, amount = 2000, _sender = alice)
    ledger.allow(operator = membership.address, amount = 1000, _sender = carl)
    membership.join_with_tokens(1000, _sender = carl)
