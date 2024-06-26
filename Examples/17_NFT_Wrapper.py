import smartpy as sp
@sp.module
def main():

    class NftForSale(sp.Contract):
       def __init__(self, owner, metadata, price):
           self.data.owner = owner
           self.data.metadata = metadata
           self.data.price = price
           self.data.deadline = sp.timestamp(0)
         
    
       @sp.entrypoint
       def set_price(self, new_price, deadline):
           assert sp.sender == self.data.owner, "you cannot update the price"
           self.data.price = new_price
           self.data.deadline = deadline
    
       @sp.entrypoint
       def buy(self):
           assert sp.amount == self.data.price, "wrong price"
           assert sp.now <= self.data.deadline
           sp.send(self.data.owner, self.data.price) 
           self.data.owner = sp.sender
        
    class NftWrapperContract(sp.Contract):
        def __init__(self, allowSales, owner, price):
            self.data.allowSales = allowSales
            self.data.price = price
            self.data.owner_wrapper = owner
            
    
        @sp.entrypoint
        def buy_nft(self, nft_address):
            assert sp.sender == self.data.owner_wrapper
            nft_contract = sp.contract(sp.unit, nft_address, entrypoint="buy").unwrap_some()
            sp.transfer((), sp.amount, nft_contract)
                        
        @sp.entrypoint
        def set_price(self, new_price):
            assert sp.sender == self.data.owner_wrapper
            self.data.price = new_price
    
    
        @sp.entrypoint
        def buy(self):
            assert sp.amount == self.data.price
            #assert self.data.allowSales == True
            sp.send(self.data.owner_wrapper, self.data.price)
            self.data.owner_wrapper = sp.sender
            
        @sp.entrypoint
        def set_allow_sale(self, new_boolean):
            assert sp.sender == self.data.owner_wrapper
            self.data.allowSales = new_boolean
    
        @sp.entrypoint
        def default(self):
            assert self.data.allowSales == True

@sp.add_test()
def test():
   alice = sp.test_account("alice").address
   bob = sp.test_account("bob").address
   eve = sp.test_account("eve").address
   dan = sp.test_account("dan").address
   scenario = sp.test_scenario("Test", main)
   c1 = main.NftForSale(owner = alice, metadata = "My first NFT", price = sp.mutez(5000000))
   c2 = main.NftWrapperContract(allowSales = sp.bool(True), price = sp.mutez(5000000), owner = bob)
   scenario +=c1
   scenario +=c2
   scenario.h3("Testing set_price entrypoint")
   c1.set_price(new_price = sp.mutez(7000000), deadline = sp.timestamp(100), _sender = bob, _valid = False)
   c1.set_price(new_price = sp.mutez(7000000), deadline = sp.timestamp(100), _sender = alice)
   scenario.h3("testing buy NFT from Wrapper")
   c2.buy_nft(c1.address, _sender = bob, _amount = sp.tez(7), _now = sp.timestamp(50))
   scenario.verify(c1.data.owner == c2.address)
   scenario.h3("testing allowSales")
   c2.set_allow_sale(False, _sender = eve, _valid = False)
   c2.set_allow_sale(False, _sender = bob)
   scenario.h3("testing setPrice NFT Wrapper")
   c2.set_price(sp.tez(50), _sender = eve, _valid = False)
   c2.set_price(sp.tez(50), _sender = bob)
   scenario.verify(c2.data.price == sp.tez(50))
   scenario.verify(c2.data.owner_wrapper == bob)
   scenario.h3("trying to buy nft from NFTforSale while not possible")
   scenario.verify(c1.data.price == sp.tez(7))
   c1.buy(_sender = dan, _amount = sp.tez(7), _valid = False)
   scenario.h3("buying NftWrapper i.e. buying NFT at nftwrapper set_price()")
   c2.buy(_sender = dan, _amount = sp.tez(50))
   scenario.verify(c2.data.owner_wrapper == dan)
