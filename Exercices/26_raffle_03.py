import smartpy as sp
@sp.module
def main():

    class Raffle(sp.Contract):
        
        def __init__(self, bidAmount, depositAmount, deadlineCommit, deadlineReveal):
                self.data.bidAmount = bidAmount
                self.data.depositAmount = depositAmount
                self.data.deadlineCommit = deadlineCommit
                self.data.deadlineReveal = deadlineReveal
                self.data.players = sp.big_map()
                self.data.nbPlayers = 0
                self.data.totalDeposits = sp.mutez(0)
                self.data.total = 0
                self.data.nbRevealed = 0
            
        
        @sp.entrypoint
        def bid(self, hashValue):
            assert sp.amount == self.data.bidAmount + self.data.depositAmount
            assert sp.now < self.data.deadlineCommit
            self.data.players[self.data.nbPlayers] = sp.record(address = sp.sender, hashValue = hashValue, revealed = False)
            self.data.nbPlayers += 1
            self.data.totalDeposits += self.data.depositAmount
        
        @sp.entrypoint
        def reveal(self, idPlayer, value):
            assert sp.now < self.data.deadlineReveal
            player = self.data.players[idPlayer]
            assert player.hashValue == sp.blake2b(sp.pack(value))
            self.data.players[idPlayer].revealed = True
            self.data.total += value
            self.data.nbRevealed += 1
        
        @sp.entrypoint
        def claimPrize(self):
            assert sp.now > self.data.deadlineReveal
            idWinner = sp.mod(self.data.total, self.data.nbPlayers)
            winner = self.data.players[idWinner].address
            assert self.data.players[idWinner].revealed
            amount = sp.mul(self.data.bidAmount, self.data.nbPlayers)
            amount += sp.split_tokens(self.data.totalDeposits, 1, self.data.nbRevealed)
            sp.send(winner, amount)
            del self.data.players[idWinner]
        
        @sp.entrypoint
        def claimDeposit(self, idPlayer):
            assert sp.now > self.data.deadlineReveal
            player = self.data.players[idPlayer]
            assert player.revealed
            user = player.address
            sended = sp.split_tokens(self.data.totalDeposits, 1, self.data.nbRevealed)
            sp.send(user, sended)
            del self.data.players[idPlayer]

# Tests
@sp.add_test(name="testing raffle")
def test():
    scenario = sp.test_scenario(main)
    alice = sp.test_account("alice").address
    bob = sp.test_account("Bob").address
    raffle = main.Raffle(sp.tez(1), sp.tez(1000), sp.timestamp(100), sp.timestamp(200))
    scenario += raffle
    scenario.h3("Bid phase")
    raffle.bid(sp.blake2b(sp.pack(10001))).run(sender = alice, amount = sp.tez(1001), now = sp.timestamp(0))
    scenario.verify(raffle.data.players[0].address == alice)
    scenario.verify(raffle.data.players[0].revealed == False)
    scenario.verify(raffle.data.nbPlayers == 1)
    raffle.bid(sp.blake2b(sp.pack(10002))).run(sender = bob, amount = sp.tez(1001), now = sp.timestamp(0))
    scenario.verify(raffle.data.players[1].address == bob)
    scenario.verify(raffle.data.players[1].revealed == False)
    scenario.verify(raffle.data.nbPlayers == 2)
    #Test the reveal entrypoint
    scenario.h1("Reveal phase")
    raffle.reveal(idPlayer=0, value=10001).run(sender = alice, now = sp.timestamp(150))
    scenario.verify(raffle.data.players[0].revealed == True)
    raffle.reveal(idPlayer=1, value=10002).run(sender = bob, now = sp.timestamp(150))
    scenario.verify(raffle.data.players[1].revealed == True)
    # Test the claimPrize entrypoint
    scenario.h1("Claim prize phase")
    raffle.claimPrize().run(sender = bob, now = sp.timestamp(250))
    raffle.claimDeposit(0).run(sender = alice, now = sp.timestamp(250))
    scenario.verify(raffle.balance == sp.tez(0))
    #Test the claimDeposit entrypoint
    scenario.h1("Claim deposit phase")
    raffle.claimDeposit(0).run(sender = alice)

