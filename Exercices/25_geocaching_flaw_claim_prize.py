import smartpy as sp

@sp.module
def main():
    class Geocaching(sp.Contract):
    
        def __init__(self, owner, deadline):
            self.data.treasures = sp.big_map({})
            self.data.score_per_player = sp.big_map({})
            self.data.current_winner = owner
            self.data.score_per_player[owner] = 0
            self.data.owner = owner
            self.data.deadline = deadline
            self.data.nb_treasures = 0

        @sp.entrypoint
        def create_treasure(self, password_hash):
            assert sp.now < self.data.deadline
            assert sp.sender == self.data.owner
            self.data.nb_treasures += 1
            self.data.treasures[self.data.nb_treasures] = sp.record(hash = password_hash, found = False)

        @sp.entrypoint
        def discover_treasure(self, id, password):
            assert sp.now < self.data.deadline
            treasure = self.data.treasures[id]
            assert not treasure.found
            assert sp.blake2b(password) == treasure.hash
            self.data.treasures[id].found = True
            if not self.data.score_per_player.contains(sp.sender):
                self.data.score_per_player[sp.sender] = 0
            self.data.score_per_player[sp.sender] += 1
            if self.data.score_per_player[sp.sender] > self.data.score_per_player[self.data.current_winner]:
                self.data.current_winner = sp.sender

        @sp.entrypoint
        def claim_prize(self):
            assert sp.now >= self.data.deadline
            assert sp.sender == self.data.owner
            sp.send(self.data.current_winner, sp.balance)
                   
@sp.add_test()
def test():
    alice = sp.test_account("alice").address
    bob = sp.test_account("bob").address
    carl = sp.test_account("carl").address
    scenario = sp.test_scenario("Test", main)
    geocaching = main.Geocaching(alice, sp.timestamp(1000))
    scenario += geocaching
    geocaching.create_treasure(sp.blake2b(sp.pack("secret password 1")), _sender = alice, _amount = sp.tez(100))
    geocaching.create_treasure(sp.blake2b(sp.pack("secret password 2")), _sender = alice)
    geocaching.create_treasure(sp.blake2b(sp.pack("secret password 3")), _sender = alice)
    geocaching.discover_treasure(id = 1, password = sp.pack("secret password 1"), _sender = bob, _now = sp.timestamp(100))
    geocaching.discover_treasure(id = 2, password = sp.pack("false password"), _sender = bob, _now = sp.timestamp(100), _valid = False)
    geocaching.discover_treasure(id = 2, password = sp.pack("secret password 2"), _sender = carl, _now = sp.timestamp(100))
    geocaching.discover_treasure(id = 3, password = sp.pack("secret password 3"), _sender = carl, _now = sp.timestamp(200))
    geocaching.claim_prize(_sender = carl, _now = sp.timestamp(100), _valid = False)
    geocaching.claim_prize(_sender = bob, _now = sp.timestamp(1000), _valid = False)
    geocaching.claim_prize(_sender = alice, _now = sp.timestamp(1000))

        
