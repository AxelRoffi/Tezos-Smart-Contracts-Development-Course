import smartpy as sp

@sp.module
def main():

    class NftForSale(sp.Contract):
    
       def __init__(self, owner, metadata, price):
           self.data.owner = owner
           self.data.metadata = metadata
           self.data.price = price
    
       @sp.entrypoint
       def set_price(self, new_price):
           assert sp.sender == self.data.owner, "you cannot update the price"
           self.data.price = new_price
    
       @sp.entrypoint
       def buy(self):
           assert sp.amount == self.data.price, "wrong price"
           sp.send(self.data.owner, self.data.price)
           self.data.owner = sp.sender
        
    class NFTJointAccount(sp.Contract):
        def __init__(self, owner1, owner2):
            self.data.owner1 = owner1
            self.data.owner2 = owner2
    
        @sp.entry_point
        def buy_nft(self, nft_address):
            assert (sp.sender == self.data.owner1) or (sp.sender == self.data.owner2)
            c = sp.contract(sp.unit, nft_address, entrypoint="buy").unwrap_some()
            sp.transfer((), sp.amount, c)
        
        @sp.entrypoint
        def set_nft_price(self, nft_address, new_price):
            assert (sp.sender == self.data.owner1) or (sp.sender == self.data.owner2)
            nft_contract = sp.contract(sp.mutez, nft_address, entrypoint="set_price").unwrap_some()
            sp.transfer(new_price, sp.tez(0), nft_contract)

@sp.add_test()
def test():
   alice = sp.test_account("alice").address
   bob = sp.test_account("bob").address
   eve = sp.test_account("eve").address
   scenario = sp.test_scenario("Test", main)
   c1 = main.NftForSale(owner = alice, metadata = "Gwen's first NFT", price = sp.mutez(5000000))
   c2 = main.NFTJointAccount(bob, eve)
   scenario +=c1
   scenario +=c2
   scenario.h3(" Testing set_price entrypoint")
   #testing set price
   c1.set_price(sp.mutez(7000000), _sender = alice)
   c2.buy_nft(c1.address, _sender = bob, _amount = sp.tez(7))
   c1.set_price(sp.mutez(7000000), _sender = eve, _valid = False)
   scenario.verify(c1.data.price != sp.mutez(6000000))
   scenario.verify(c1.data.price == sp.mutez(7000000))
   c2.buy_nft(c1.address, _sender = eve, _amount = sp.tez(7), _valid = False)
   c2.buy_nft(c1.address, _sender = alice, _amount = sp.tez(6), _valid = False)
   c2.set_nft_price(nft_address = c1.address, new_price = sp.tez(50), _sender = eve)
    #verify that the owner of the NFT is our NFTJointAccount contract
   scenario.verify(c1.data.price == sp.tez(50))
   scenario.verify(c1.data.owner == c2.address)
