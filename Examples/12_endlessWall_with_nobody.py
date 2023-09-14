import smartpy as sp

#specific address that does not exist in tezos
nobody = sp.address("KT18amZmM5W7qDWVt2pH6uj7sCEd3kbzLrHT")


@sp.module
def main():
    
    nobody = sp.address("KT18amZmM5W7qDWVt2pH6uj7sCEd3kbzLrHT")
    
    class EndlessWall(sp.Contract):
       def __init__(self, initial_text):
           self.data.wall_text = initial_text
           self.data.nb_calls = 0
           self.data.owner = nobody
    
       @sp.entrypoint
       def write_message(self, message):
           assert (sp.len(message) <= 30) and (sp.len(message) >= 3), "invalid size message"
           assert sp.amount == sp.tez(1), "incorrect amount"
           self.data.wall_text += ", " + message + " forever"
           self.data.nb_calls += 1
    
       @sp.entrypoint
       def claim(self, requested_amount):
            assert sp.sender == self.data.owner, "not your money"
            sp.send(self.data.owner, requested_amount)  
  
@sp.add_test(name = "Add my name")
def test():
   alice=sp.test_account("Alice").address
   bob=sp.test_account("Bob").address
   eve=sp.test_account("Eve").address
   c1 = main.EndlessWall(initial_text = "Axel on Tezos forever")
   scenario = sp.test_scenario(main)
   scenario += c1
   scenario.h3(" Testing write_message is ok ")
    #scenario write_message ok
   c1.write_message("Ana & Jack").run(sender = eve, amount = sp.tez(1))
   c1.write_message("freeCodeCamp").run(sender = bob, amount = sp.tez(1))
   scenario.verify(c1.data.wall_text == "Axel on Tezos forever, Ana & Jack forever, freeCodeCamp forever")
   scenario.h3(" Checking calls fail due to invalid size message ")
    #checking write_message fails for size message
   c1.write_message("this message is 31 letters long").run(sender = alice, valid = False, amount = sp.tez(1))
   c1.write_message("AB").run(sender = alice, valid = False, amount = sp.tez(1))
   scenario.h3(" Checking calls pass for limit size messages ")
    #checking write_message passes for size message
   c1.write_message("LLL").run(sender = alice, amount = sp.tez(1))
   c1.write_message("this message has 30 characters").run(sender = eve, amount = sp.tez(1) )
   scenario.verify(c1.data.nb_calls == 4)
   scenario.h3(" Checking calls pass or fail for right amount")
   #checking testing amounts
   c1.write_message("testing right amount").run(sender = eve,amount = sp.tez(1))
   c1.write_message("testing lesser amount").run(sender = eve,amount = sp.mutez(999999), valid = False)
   c1.write_message("testing bigger amount").run(sender = bob, amount = sp.mutez(1000001), valid = False)
   c1.write_message("testing correct amount").run(sender = bob, amount = sp.tez(1))
   scenario.h3(" Checking only owner can claim balance in the contract")
   #checking claim entrypoint
   c1.claim(sp.tez(3)).run(sender = bob, valid = False)
   c1.claim(sp.tez(4)).run(sender = nobody)
   c1.write_message("this message has 30 characters").run(sender = eve, amount = sp.tez(1) )
   scenario.verify(c1.data.nb_calls == 7)
   scenario.h3(" Checking calls pass or fail for right amount")
   #checking testing amounts
   c1.write_message("testing right amount").run(sender = eve,amount = sp.tez(1))
   c1.write_message("testing lesser amount").run(sender = eve,amount = sp.mutez(999999), valid = False)
   c1.write_message("testing bigger amount").run(sender = bob, amount = sp.mutez(1000001), valid = False)
   c1.write_message("testing correct amount").run(sender = bob, amount = sp.tez(1))
   scenario.h3(" Checking only owner can claim balance in the contract")
   #checking claim entrypoint
   c1.claim(sp.tez(3)).run(sender = bob, valid = False)
   c1.claim(sp.tez(4)).run(sender = nobody)
