import smartpy as sp

@sp.module
def main():

    class EndlessWall(sp.Contract):
       def __init__(self, initial_text, owner, deadline):
           self.data.wall_text = initial_text
           self.data.nb_calls = 0
           self.data.owner = owner
           self.data.deadline = deadline
    
       @sp.entrypoint
       def write_message(self, message):
           assert (sp.len(message) <= 30) and (sp.len(message) >= 3), "invalid size message"
           assert sp.amount == sp.tez(1), "incorrect amount"
           assert sp.now <= self.data.deadline, "After deadline"
           self.data.wall_text += ", " + message + " forever"
           self.data.nb_calls += 1
    
       @sp.entrypoint
       def claim(self, requested_amount):
            assert sp.sender == self.data.owner, "not your money"
            sp.send(self.data.owner, requested_amount)     
  
@sp.add_test()
def test():
    alice = sp.test_account("Alice").address
    bob = sp.test_account("Bob").address
    eve = sp.test_account("Eve").address
    c1 = main.EndlessWall(initial_text = "Axel on Tezos forever", owner=alice, deadline = sp.timestamp_from_utc(2025, 12, 31, 23, 59, 59))
    sc = sp.test_scenario("Test", main)
    sc += c1
    sc.h3(" Testing write_message is ok ")
    #sc write_message ok
    c1.write_message("Ana & Jack", _sender = eve, _amount = sp.tez(1), _now = sp.timestamp(0) )
    c1.write_message("freeCodeCamp", _sender = bob, _amount = sp.tez(1), _now = sp.timestamp(0) )
    sc.verify(c1.data.wall_text == "Axel on Tezos forever, Ana & Jack forever, freeCodeCamp forever")
    sc.h3(" Checking calls fail due to invalid size message ")
    #checking write_message fails for size message
    c1.write_message("this message is 31 letters long", _sender = alice, _valid = False, _amount = sp.tez(1))
    c1.write_message("AB", _sender = alice, _valid = False, _amount = sp.tez(1))
    sc.h3(" Checking calls pass for limit size messages ")
    #checking write_message passes for size message
    c1.write_message("LLL", _sender = alice, _amount = sp.tez(1))
    c1.write_message("this message has 30 characters", _sender = eve, _amount = sp.tez(1) )
    sc.verify(c1.data.nb_calls == 4)
    sc.h3(" Checking calls pass or fail for right amount")
    #checking testing amounts
    c1.write_message("testing right amount", _sender = eve, _amount = sp.tez(1))
    c1.write_message("testing lesser amount", _sender = eve, _amount = sp.mutez(999999), _valid = False)
    c1.write_message("testing bigger amount", _sender = bob, _amount = sp.mutez(1000001), _valid = False)
    c1.write_message("testing correct amount", _sender = bob, _amount = sp.tez(1))
    sc.h3(" Checking only owner can claim balance in the contract")
    #checking claim entrypoint
    c1.claim(sp.tez(3), _sender = bob, _valid = False)
    c1.claim(sp.tez(4), _sender = alice)
    sc.h3(" Checking deadline passes or fails")
    #checking deadline
    c1.write_message("Bob wrote this",
        _sender = bob,
        _amount = sp.tez(1),
        _now = sp.timestamp_from_utc(2025, 12, 31, 23, 59, 58),
    )
    c1.write_message("Eve wrote this",
        _sender = eve,
        _amount = sp.tez(1),
        _now = sp.timestamp_from_utc(2026, 1, 1, 0, 0, 1),
        _valid = False,
    )
