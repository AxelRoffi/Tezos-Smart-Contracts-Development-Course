import smartpy as sp
@sp.module
def main():

    class Raffle(sp.Contract):
        
        def __init__(self, bid_amount, deposit_amount, deadline_commit, deadline_reveal):
                self.data.bid_amount = bid_amount
                self.data.deposit_amount = deposit_amount
                self.data.deadline_commit = deadline_commit
                self.data.deadline_reveal = deadline_reveal
                self.data.players = sp.big_map()
                self.data.nb_players = 0
                self.data.total_deposits = sp.mutez(0)
                self.data.total_bids = sp.mutez(0)
                self.data.total = 0
                self.data.nb_revealed = 0
            
        
        @sp.entrypoint
        def bid(self, hash_value):
            assert sp.amount == self.data.bid_amount + self.data.deposit_amount
            assert sp.now < self.data.deadline_commit
            self.data.players[self.data.nb_players] = sp.record(address = sp.sender,
                                                                hash_value = hash_value,
                                                                revealed = False)
            self.data.nb_players += 1
            self.data.total_deposits += self.data.deposit_amount
            self.data.total_bids += self.data.bid_amount
        
        @sp.entrypoint
        def reveal(self, id_player, value):
            assert sp.now < self.data.deadline_reveal
            player = self.data.players[id_player]
            assert not player.revealed
            assert player.hash_value == sp.blake2b(sp.pack(value))
            self.data.players[id_player].revealed = True
            self.data.total += value
            self.data.nb_revealed += 1
        
        @sp.entrypoint
        def claim_prize(self):
            assert sp.now > self.data.deadline_reveal
            idWinner = sp.mod(self.data.total, self.data.nb_players)
            winner = self.data.players[idWinner].address
            assert self.data.players[idWinner].revealed
            amount = self.data.total_bids + sp.split_tokens(self.data.total_deposits, 1, self.data.nb_revealed)
            sp.send(winner, amount)
            del self.data.players[idWinner]
        
        @sp.entrypoint
        def claim_deposit(self, id_player):
            assert sp.now > self.data.deadline_reveal
            player = self.data.players[id_player]
            assert player.revealed
            user = player.address
            amount_to_share = self.data.total_deposits
            id_winner = sp.mod(self.data.total, self.data.nb_players)
            assert id_player != id_winner
            if self.data.players.contains(id_winner):
                if not self.data.players[id_winner].revealed:
                    amount_to_share += self.data.total_bids
            amount = sp.split_tokens(amount_to_share, 1, self.data.nb_revealed)
            sp.send(user, amount)
            del self.data.players[id_player]

# Tests
@sp.add_test()
def test():
    scenario = sp.test_scenario("Test", main)
    alice = sp.test_account("alice").address
    bob = sp.test_account("Bob").address
    eve = sp.test_account("Eve").address
    raffle = main.Raffle(sp.tez(1), sp.tez(1000), sp.timestamp(100), sp.timestamp(200))
    scenario += raffle
    scenario.h3("Bid phase")
    raffle.bid(sp.blake2b(sp.pack(10001)), _sender = alice, _amount = sp.tez(1001), _now = sp.timestamp(0))
    scenario.verify(raffle.data.players[0].address == alice)
    scenario.verify(raffle.data.players[0].revealed == False)
    scenario.verify(raffle.data.nb_players == 1)
    raffle.bid(sp.blake2b(sp.pack(10003)), _sender = bob, _amount = sp.tez(1001), _now = sp.timestamp(0))
    scenario.verify(raffle.data.players[1].address == bob)
    scenario.verify(raffle.data.players[1].revealed == False)
    scenario.verify(raffle.data.nb_players == 2)
    raffle.bid(sp.blake2b(sp.pack(10004)), _sender = eve, _amount = sp.tez(1001), _now = sp.timestamp(0))
    scenario.verify(raffle.data.players[2].address == eve)
    scenario.verify(raffle.data.players[2].revealed == False)
    scenario.verify(raffle.data.nb_players == 3)
    #Test the reveal entrypoint
    scenario.h1("Reveal phase")
    raffle.reveal(id_player=0, value=10001, _sender = alice, _now = sp.timestamp(150))
    scenario.verify(raffle.data.players[0].revealed == True)
    raffle.reveal(id_player=1, value=10003, _sender = bob, _now = sp.timestamp(150))
    scenario.verify(raffle.data.players[1].revealed == True)
    scenario.verify(raffle.data.players[2].revealed == False)
    # Test the claim_prize entrypoint
    scenario.h1("Claim prize phase")
    raffle.claim_prize(_sender = alice, _now = sp.timestamp(250))
    raffle.claim_deposit(1, _sender = bob, _now = sp.timestamp(250))
    raffle.claim_deposit(2, _sender = eve, _now = sp.timestamp(250), _valid = False)
    scenario.verify(raffle.balance == sp.tez(0))
    #Test the claim_deposit entrypoint
    scenario.h1("Claim deposit phase")
    raffle.claim_deposit(0, _sender = alice, _valid = False)
