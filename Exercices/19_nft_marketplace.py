import smartpy as sp

@sp.module
def main():

    paramType:type = sp.record(token_id = sp.int, new_owner = sp.address)
    
    class Ledger(sp.Contract):
        
        def __init__(self, admin):
            self.data.admin = admin
            self.data.tokens = sp.big_map()
            self.data.next_token_id = 1

        @sp.entrypoint
        def mint(self, metadata):
            sp.cast(metadata, sp.string)
            self.data.tokens[self.data.next_token_id] = sp.record(owner = sp.sender, metadata = metadata)
            self.data.next_token_id += 1

        @sp.onchain_view()
        def get_token_owner(self, token_id):
            sp.cast(token_id, sp.int)
            return self.data.tokens[token_id].owner

        @sp.entrypoint
        def change_owner(self, token_id, new_owner):
            assert sp.sender == self.data.admin
            self.data.tokens[token_id].owner = new_owner


    class Marketplace(sp.Contract):
        def __init__(self):
            self.data.offers = sp.big_map({})
            self.data.nextOfferID = 1
     
        @sp.entrypoint
        def new_offer(self, sold_tokens, bought_tokens):
           self.data.offers[self.data.nextOfferID] = sp.record(seller = sp.sender,
                                                            sold_tokens = sold_tokens,
                                                            bought_tokens = bought_tokens)
           self.data.nextOfferID += 1
        
        @sp.entrypoint
        def accept_offer(self, idOffer):
            offer = self.data.offers[idOffer]

            for sold_token in offer.sold_tokens:
                owner = sp.view("get_token_owner", sold_token.contract_address, sold_token.token_id, sp.address).unwrap_some()
                assert owner == offer.seller
                ledger_contract = sp.contract(paramType, sold_token.contract_address, entrypoint="change_owner").unwrap_some()
                sp.transfer(sp.record(token_id = sold_token.token_id, new_owner = sp.sender), sp.tez(0), ledger_contract)

            for bought_token in offer.bought_tokens:
                owner = sp.view("get_token_owner", bought_token.contract_address, bought_token.token_id, sp.address).unwrap_some()
                assert owner == sp.sender
                ledger_contract = sp.contract(paramType, bought_token.contract_address, entrypoint="change_owner").unwrap_some()
                sp.transfer(sp.record(token_id = bought_token.token_id, new_owner = offer.seller), sp.tez(0), ledger_contract)

            del self.data.offers[idOffer]    
       
@sp.add_test()
def test():
    alice = sp.test_account("Alice")
    bob = sp.test_account("Bob")
    eve = sp.test_account("Eve")
    axel = sp.test_account("Axel")
    scenario = sp.test_scenario("Test", main)
    marketplace = main.Marketplace()
    scenario += marketplace
    ledger1 = main.Ledger(marketplace.address)
    scenario += ledger1
    ledger2 = main.Ledger(marketplace.address)
    scenario += ledger2
    ledger1.mint("Alice NFT 1", _sender = alice)
    ledger2.mint("Alice NFT 2", _sender = alice)
    ledger1.mint("Bob NFT 1", _sender = bob)
    ledger2.mint("Bob NFT 2", _sender = bob)
    ledger2.mint("Bob NFT 3", _sender = bob)
    
    marketplace.new_offer(sold_tokens = [
                            sp.record(contract_address = ledger1.address, token_id = 1),
                            sp.record(contract_address = ledger2.address, token_id = 1),
                          ],
                          bought_tokens = [
                            sp.record(contract_address = ledger1.address, token_id = 2),
                            sp.record(contract_address = ledger2.address, token_id = 2),
                            sp.record(contract_address = ledger2.address, token_id = 3),
                          ],
                         _sender = alice)
    marketplace.accept_offer(1, _sender = bob)
