import smartpy as sp


@sp.module
def main():
    
    drink_type:type = sp.variant(Coca = sp.unit, Fanta = sp.unit, SevenUp = sp.unit, Water = sp.unit)
    drink_type_new:type = sp.variant(Coca = sp.unit, Fanta = sp.unit, SevenUp = sp.unit, Water = sp.unit, Sprite = sp.unit)

    class FavoriteDrinks(sp.Contract):
        def __init__(self):
            self.data.favorite_drinks = sp.big_map({})

        @sp.entrypoint
        def set_favorite(self, drink):
            sp.cast(drink, drink_type)
            self.data.favorite_drinks[sp.sender] = drink

        @sp.onchain_view
        def favorite(self, user):
            return self.data.favorite_drinks[user]
    
    class Restaurant(sp.Contract):
        def __init__(self, favorite_drinks_contract):
            self.data.items = []
            self.data.favorite_drinks_contract = favorite_drinks_contract

        @sp.entrypoint
        def quick_drink(self):
            drink = sp.view("favorite", self.data.favorite_drinks_contract, sp.sender, drink_type).unwrap_some()
            self.data.items.push(drink)            
        
        @sp.entrypoint
        def order_drink(self, drink):
            sp.cast(drink, drink_type)
            price = sp.tez(0)
            with sp.match(drink):
                with sp.case.Coca:
                    price = sp.tez(1)
                with sp.case.Fanta:
                    price = sp.tez(2)
                with sp.case.Water:
                    price = sp.tez(0)
                # etc.
            assert sp.amount == price
            self.data.items.push(drink)
            
    class RestaurantNew(sp.Contract):
        def __init__(self, favorite_drinks_contract):
            self.data.items = []
            self.data.favorite_drinks_contract = favorite_drinks_contract

        @sp.entrypoint
        def quick_drink(self):
            drink = sp.view("favorite", self.data.favorite_drinksContract, sp.sender, drink_type).unwrap_some()
            self.data.items.push(drink)            
        
        @sp.entrypoint
        def order_drink(self, drink):
            sp.cast(drink, drink_type_new)
            price = sp.tez(0)
            with sp.match(drink):
                with sp.case.Coca:
                    price = sp.tez(1)
                with sp.case.Fanta:
                    price = sp.tez(2)
                with sp.case.Water:
                    price = sp.tez(0)
                # etc.
            assert sp.amount == price
            self.data.items.push(drink)

@sp.add_test()
def test():
    alice = sp.test_account("Alice")
    scenario = sp.test_scenario("Test", main)
    c_favorites = main.FavoriteDrinks()
    scenario += c_favorites
    c_favorites.set_favorite(sp.variant("Coca", ()), _sender = alice)   
    c1 = main.Restaurant(c_favorites.address)
    scenario += c1
    scenario.h3("J'ai faim")
    c1.order_drink(sp.variant("Water", ()))
    c1.order_drink(sp.variant("Coca", ()), _valid = False)
    c1.order_drink(sp.variant("Coca", ()), _amount = sp.tez(1), _valid = True)    
    c1.order_drink(sp.variant("Fanta", ()), _valid = False)
    c1.order_drink(sp.variant("Fanta", ()), _amount = sp.tez(2), _valid = True)
    c1.quick_drink(_sender = alice)
    
    c1 = main.RestaurantNew(c_favorites.address)

   
