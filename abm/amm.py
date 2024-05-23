import numpy as np 


class AMM(object):
    """
    Uniswap Automated Market Maker.
    See Section 6 above, "Institution and Agent Message Space," for a description of 
    this institution's functionality. 
    
    """
    def __init__(self,transaction_fee = 0, ratio_error_tol = 1e-7, debug=False):
        
        self.reserve_x = 0
        self.reserve_y = 0
        
        self.constant_product = 0
        self.governance_tokens = 0
        self.lp_tokens = 0 
        
        self.transaction_fee = transaction_fee
        
        self.debug = debug
        self.ratio_error_tol = ratio_error_tol
        
    def setup_pool(self, quantity_x=0, quantity_y=0):
        """
        Establishes a liquidity pool with constant_product = quantity_x * quantity_y.
        Returns liqudity tokens to the agent who sets it up. 
        See 1.A "Establish Liquidity" above for explanation of math. 
        """
        self.reserve_x  = quantity_x
        self.reserve_y = quantity_y
        
        self.constant_product = self.reserve_x*self.reserve_y
        
        lp_minted  = np.sqrt(self.constant_product)
        self.lp_tokens = lp_minted
        
        return lp_minted 
        
    def request_info(self):
        """
        Simple method that informs an agent of the current reserve amounts of 
        X and Y in the liquidity pool. 
        See 1.B "Get Current Amount of Reserves" above for explanation of math. 
        """
        info_dict ={"reserve_x": self.reserve_x, "reserve_y": self.reserve_y,
                       "transaction_fee": self.transaction_fee}
        return info_dict
    
    def provide_liquidity(self,quantity_x, quantity_y): 
        """
        Allows agents to add tokens X and Y to the liquidity pool. 
        Agents must submit X and Y in the exact ratio of the current reserves. 
        Otherwise, method returns an error. 
        If successful, agents receive liquidity tokens in response. 
        See 1.C "Add Liquidity" for an explanation of math. 
        """
        ratio_submitted = quantity_x/quantity_y 
        current_reserve_ratio = self.reserve_x/self.reserve_y
        
        
        if self.debug:
            print(f"-"*10, f"PROVIDE LIQUIDITY ",f"-"*10)
            print(f"-"*10, f"PRIOR LIQUIDITY ",f"-"*10)
            print(f"Reserve X:{self.reserve_x}\n"+
                 f"Reserve Y:{self.reserve_y}\n" +
                 f"Total pool tokens :{self.lp_tokens}")
        
        
        if abs(ratio_submitted - current_reserve_ratio) < self.ratio_error_tol:
            
            lp_minted = (quantity_x/self.reserve_x)*self.lp_tokens
            
            self.lp_tokens = self.lp_tokens + lp_minted 
            self.reserve_x = self.reserve_x + quantity_x 
            self.reserve_y = self.reserve_y + quantity_y 
            
            if self.debug:
                print(f"-"*10, f"AFTER LIQUIDITY INSERTED",f"-"*10)
                print(f"Reserve X:{self.reserve_x}\n"+
                     f"Reserve Y:{self.reserve_y}\n" +
                     f"Total pool tokens :{self.lp_tokens}")

            return lp_minted
        else: 
            print(f"ERROR: incorrect ratio of quantity x and y submitted")
    
    def withdraw_liquidity(self, lp_burned):
        """
        Allows agents to 'burn' liquidity tokens and receive tokens X and Y in return. 
        See 1.D "Remove Liquidity" for an explanation of math. 
        """
        total_lp_tokens = self.lp_tokens
        reserve_x = self.reserve_x
        reserve_y = self.reserve_y 
        
        if self.debug:
            print(f"-"*10, f"WITHDRAW LIQUIDITY ",f"-"*10)
            print(f"-"*10, f"PRIOR LIQUIDITY WITHDRAWN ",f"-"*10)
            print(f"Reserve X:{self.reserve_x}\n"+
                 f"Reserve Y:{self.reserve_y}\n" +
                 f"Total pool tokens :{self.lp_tokens}")

        #calculate tokens to be returned 
        quantity_x = (lp_burned/total_lp_tokens)*reserve_x
        quantity_y = (lp_burned/total_lp_tokens)*reserve_y
        
        #update state 
        self.reserve_x = self.reserve_x - quantity_x
        self.reserve_y = self.reserve_y - quantity_y 
        self.lp_tokens = self.lp_tokens - lp_burned
        
        if self.debug:
            print(f"-"*10, f"AFTER LIQUIDITY WITHDRAWN",f"-"*10)
            print(f"Reserve X:{self.reserve_x}\n"+
                  f"Reserve Y:{self.reserve_y}\n" +
                  f"Total pool tokens :{self.lp_tokens}")

        return_amt_dict = {"quantity_x": quantity_x, "quantity_y": quantity_y}
        
        return return_amt_dict
    
    def request_price(self, transaction_type = "buy",token = None, quantity = 1):
        """
        This method provides you with a price you would have to pay if you want 
        to buy a certain quantity of tokens. However, if you want to sell a certain
        quantity of tokens it offers you a price the institution would pay you. 
        
        Details about this math can be found in the introduction of section 6, 
        plus in 2.B "Buy Tokens" and 2.C "Sell Tokens."
        """
        
        if transaction_type == "buy" : 
            if token == 'x': 
                
                gamma = 1 - self.transaction_fee 
                delta_x = quantity
                new_reserve_x = self.reserve_x - delta_x
                reserve_y = self.reserve_y

                k = self.constant_product
                

                price = (k/(new_reserve_x) - reserve_y)/gamma

                return price

            elif token == 'y':
                
                gamma = 1 - self.transaction_fee 
                delta_y = quantity
                new_reserve_y = self.reserve_y - delta_y
                reserve_x = self.reserve_x

                k = self.constant_product
                

                price = (k/(new_reserve_y) - reserve_x)/gamma

                return price 

            else :
                print(f"ERROR, token = {token} is not traded in this pool")
        
        elif transaction_type == "sell":
            if token == 'x':
                
                gamma = 1 - self.transaction_fee
                delta_x = quantity 
                new_reserve_x = self.reserve_x + delta_x*gamma
                reserve_y = self.reserve_y

                k = self.constant_product
                
                price = reserve_y - k/(new_reserve_x) 
                
                return price
            
            elif token == 'y': 
                
                gamma = 1 - self.transaction_fee
                delta_y = quantity 
                new_reserve_y = self.reserve_y + delta_y*gamma
                reserve_x = self.reserve_x

                k = self.constant_product
                
                price = reserve_x - k/(new_reserve_y) 
                
                return price
            else:
                print(f"ERROR, token = {token} is not traded in this pool")
        else:
            print(f"ERROR, wrong transaction type requested, transaction_type = {transaction_type}")

     
    def sell_tokens(self, token = None, quantity = 0): 
        """
        Allows agents to sell a fixed amount of token X or Y, and 
        receive a quantity of the opposite token in exchange. 
        Then, the institution updates its reserves in the liquidity pool accordingly. 
        See Section 2.C above, "Sell Tokens," for a description.
        """
        if token == 'x': 
            
            x_offered = quantity
            y_returned = self.request_price("sell",token,x_offered)
            
            if self.debug:
                print(f"-"*10, f"SELL TOKEN = {token}", f"-"*10)
                print(f" "*10, f"BEFORE TRADE", f" "*10)
                print(f"Reserve X:{self.reserve_x}\n"+
                      f"Reserve Y:{self.reserve_y}\n" +
                      f"k : {self.constant_product}\n")

            self.reserve_x = self.reserve_x + x_offered
            self.reserve_y = self.reserve_y - y_returned
            
            self.constant_product = self.reserve_x*self.reserve_y
            
            if self.debug:
                print(f" "*10, f"AFTER TRADE", f" "*10)
                print(f"Reserve X:{self.reserve_x}\n"+
                      f"Reserve Y:{self.reserve_y}\n" +
                      f"k : {self.constant_product}\n")

            returned_dict = {"token_returned": "y", "quantity_returned": y_returned}
            
            return returned_dict
        
        elif token == 'y': 
            
            y_offered = quantity
            x_returned = self.request_price("sell",token,y_offered)
            
            if self.debug:
                print(f"-"*10, f"SELL TOKEN = {token}", f"-"*10)
                print(f" "*10, f"BEFORE TRADE", f" "*10)
                print(f"Reserve X:{self.reserve_x}\n"+
                      f"Reserve Y:{self.reserve_y}\n" +
                      f"k : {self.constant_product}\n")

            self.reserve_x = self.reserve_x - x_returned
            self.reserve_y = self.reserve_y + y_offered            
            self.constant_product = self.reserve_x*self.reserve_y
            
            if self.debug:
                print(f" "*10, f"AFTER TRADE", f" "*10)
                print(f"Reserve X:{self.reserve_x}\n"+
                      f"Reserve Y:{self.reserve_y}\n" +
                      f"k : {self.constant_product}\n")

            returned_dict = {"token_returned": "x", "quantity_returned": x_returned}
            
            
            return returned_dict
        else:
            print(f"ERROR, token = {token} is not traded in this pool")
    
    def sell_tokens_min_price(self, token = None, quantity = 0, min_price  = 0 ): 
        """
        Allows agents to sell a fixed amount of token X or Y, and 
        receive a quantity of the opposite token in exchange.
        The Agent is also allowed to specify a min price and the trade only executese if the
        min price condition is met. 
        Then, the institution updates its reserves in the liquidity pool accordingly. 
        See Section 2.C above, "Sell Tokens," for a description.
        """
        if token == 'x': 
            
            x_offered = quantity
            y_returned = self.request_price("sell",token,x_offered)
            
            if y_returned >= min_price: 
                if self.debug:
                    print(f"-"*10, f"SELL TOKEN = {token}", f"-"*10)
                    print(f" "*10, f"BEFORE TRADE", f" "*10)
                    print(f"Reserve X:{self.reserve_x}\n"+
                          f"Reserve Y:{self.reserve_y}\n" +
                          f"k : {self.constant_product}\n")

                self.reserve_x = self.reserve_x + x_offered
                self.reserve_y = self.reserve_y - y_returned

                self.constant_product = self.reserve_x*self.reserve_y

                if self.debug:
                    print(f" "*10, f"AFTER TRADE", f" "*10)
                    print(f"Reserve X:{self.reserve_x}\n"+
                          f"Reserve Y:{self.reserve_y}\n" +
                          f"k : {self.constant_product}\n")

                returned_dict = {"token_returned": "y", "quantity_returned": y_returned}

                return returned_dict
            
            else : 
                
                print(f"-"*10, f"SELL TOKEN = {token}, FAILED", f"-"*10)
                print(f"y_returned  < min_price ")
                print(f"y_returned = {y_returned}" 
                      f"min_price = {min_price}")
                return {"token_returned": "y" , "quantity_returned": "NoTrade"}
                
                
        
        elif token == 'y': 
    
            y_offered = quantity
            x_returned = self.request_price("sell",token,y_offered)
            
            if y_returned >= min_price: 
            
                if self.debug:
                    print(f"-"*10, f"SELL TOKEN = {token}", f"-"*10)
                    print(f" "*10, f"BEFORE TRADE", f" "*10)
                    print(f"Reserve X:{self.reserve_x}\n"+
                          f"Reserve Y:{self.reserve_y}\n" +
                          f"k : {self.constant_product}\n")

                self.reserve_x = self.reserve_x - x_returned
                self.reserve_y = self.reserve_y + y_offered            
                self.constant_product = self.reserve_x*self.reserve_y

                if self.debug:
                    print(f" "*10, f"AFTER TRADE", f" "*10)
                    print(f"Reserve X:{self.reserve_x}\n"+
                          f"Reserve Y:{self.reserve_y}\n" +
                          f"k : {self.constant_product}\n")

                returned_dict = {"token_returned": "x", "quantity_returned": x_returned}


                return returned_dict
            else :
                print(f"-"*10, f"SELL TOKEN = {token}, FAILED", f"-"*10)
                print(f"x_returned  < min_price ")
                print(f"x_returned = {x_returned}" 
                      f"min_price = {min_price}")
                return {"token_returned": "x" , "quantity_returned": "NoTrade"}
                
        else:
            print(f"ERROR, token = {token} is not traded in this pool")
        
    def buy_tokens(self, token = None, quantity = 0 ):
        """
        Allows agents to request a fixed amount of token X or Y to buy.
        This method returns the price that agent will have to pay, denominated
        in the opposite token. 
        Then, the institution updates its reserves in the liquidity pool accordingly. 
        See Section 2.C above, "Buy Tokens," for a description.
        """
        if token == 'x': 
            
            x_requested = quantity
            y_needed = self.request_price("buy",token, x_requested)
            
            if self.debug:
                print(f"-"*10, f"BUY TOKEN = {token}", f"-"*10)
                print(f" "*10, f"BEFORE TRADE", f" "*10)
                print(f"Reserve X:{self.reserve_x}\n"+
                      f"Reserve Y:{self.reserve_y}\n" +
                      f"k : {self.constant_product}\n")

            self.reserve_x = self.reserve_x - x_requested
            self.reserve_y = self.reserve_y + y_needed
                    
            self.constant_product = self.reserve_x*self.reserve_y
            
            if self.debug:
                print(f" "*10, f"AFTER TRADE", f" "*10)
                print(f"Reserve X:{self.reserve_x}\n"+
                      f"Reserve Y:{self.reserve_y}\n" +
                      f"k : {self.constant_product}\n")

            returned_dict = {"token_needed": "y", "quantity_needed": y_needed}
            
            
            return returned_dict
        
        elif token == 'y': 
            
            y_requested = quantity
            x_needed = self.request_price("sell",token,y_requested)
            
            if self.debug:
                print(f"-"*10, f"BUY TOKEN = {token}", f"-"*10)
                print(f" "*10, f"BEFORE TRADE", f" "*10)
                print(f"Reserve X:{self.reserve_x}\n"+
                      f"Reserve Y:{self.reserve_y}\n" +
                      f"k : {self.constant_product}\n")

            self.reserve_x = self.reserve_x + x_needed
            self.reserve_y = self.reserve_y - y_requested
        
            self.constant_product = self.reserve_x*self.reserve_y
            
            if self.debug:
                print(f" "*10, f"AFTER TRADE", f" "*10)
                print(f"Reserve X:{self.reserve_x}\n"+
                      f"Reserve Y:{self.reserve_y}\n" +
                      f"k : {self.constant_product}\n")

            returned_dict = {"token_needed": "x", "quantity_needed": x_needed}
            
            return returned_dict
        
        else:
            print(f"ERROR, token = {token} is not traded in this pool")
            
            
    def buy_tokens_max_price(self, token = None, quantity = 0, max_price=0 ):
        """
        Allows agents to request a fixed amount of token X or Y to buy.
        This method returns the price that agent will have to pay, denominated
        in the opposite token. 
        The swap only proceeds if the price required is lower than a specified max_price parameter. 
        Then, the institution updates its reserves in the liquidity pool accordingly. 
        See Section 2.C above, "Buy Tokens," for a description.
        """
        if token == 'x': 
            
            x_requested = quantity
            y_needed = self.request_price("buy",token, x_requested)
            
            if y_needed <= max_price: 
            
                if self.debug:
                    print(f"-"*10, f"BUY TOKEN = {token}", f"-"*10)
                    print(f" "*10, f"BEFORE TRADE", f" "*10)
                    print(f"Reserve X:{self.reserve_x}\n"+
                          f"Reserve Y:{self.reserve_y}\n" +
                          f"k : {self.constant_product}\n")

                self.reserve_x = self.reserve_x - x_requested
                self.reserve_y = self.reserve_y + y_needed

                self.constant_product = self.reserve_x*self.reserve_y

                if self.debug:
                    print(f" "*10, f"AFTER TRADE", f" "*10)
                    print(f"Reserve X:{self.reserve_x}\n"+
                          f"Reserve Y:{self.reserve_y}\n" +
                          f"k : {self.constant_product}\n")

                returned_dict = {"token_needed": "y", "quantity_needed": y_needed}

                return returned_dict
            
            else : 
                print(f"-"*10, f"BUY TOKEN = {token}, FAILED", f"-"*10)
                print(f"y_needed  > max_price ")
                print(f"y_needed = {y_needed}" 
                      f"max_price = {max_price}")
                return {"token_needed": "y" , "quantity_needed": "NoTrade"}

        elif token == 'y': 
            
            y_requested = quantity
            x_needed = self.request_price("sell",token,y_requested)
            
            if x_needed <= max_price: 
            
                if self.debug:
                    print(f"-"*10, f"BUY TOKEN = {token}", f"-"*10)
                    print(f" "*10, f"BEFORE TRADE", f" "*10)
                    print(f"Reserve X:{self.reserve_x}\n"+
                          f"Reserve Y:{self.reserve_y}\n" +
                          f"k : {self.constant_product}\n")

                self.reserve_x = self.reserve_x + x_needed
                self.reserve_y = self.reserve_y - y_requested

                self.constant_product = self.reserve_x*self.reserve_y

                if self.debug:
                    print(f" "*10, f"AFTER TRADE", f" "*10)
                    print(f"Reserve X:{self.reserve_x}\n"+
                          f"Reserve Y:{self.reserve_y}\n" +
                          f"k : {self.constant_product}\n")

                returned_dict = {"token_needed": "x", "quantity_needed": x_needed}

                return returned_dict
            
            else : 
                print(f"-"*10, f"BUY TOKEN = {token}, FAILED", f"-"*10)
                print(f"x_needed  > max_price ")
                print(f"x_needed = {x_needed}" 
                      f"max_price = {max_price}")
                return {"token_needed": "x" , "quantity_needed": "NoTrade"}

        else:
            print(f"ERROR, token = {token} is not traded in this pool")
            
    def provide_liquidity_min_amount(self,amount_x_desired,amount_y_desired, amount_x_min = 0, amount_y_min = 0):
        """
        Provides utility based on certain conditions
        
        """
        if self.debug:
            print(f"-"*10, f"PROVIDE LIQUIDITY ",f"-"*10)
            print(f"-"*10, f"PRIOR LIQUIDITY ",f"-"*10)
            print(f"Reserve X:{self.reserve_x}\n"+
                 f"Reserve Y:{self.reserve_y}\n" +
                 f"Total pool tokens :{self.lp_tokens}")
            print(f"AGENT PARAMS")
            print(f"amount_x_desired = {amount_x_desired}")
            print(f"amount_y_desired = {amount_y_desired}")
            print(f"amount_x_min = {amount_x_min}")
            print(f"amount_y_min = {amount_y_min}")
        
        
        
        amount_y_optimal = amount_x_desired * (self.reserve_y / self.reserve_x)
        if amount_y_optimal <= amount_y_desired: 
            if amount_y_optimal >= amount_y_min:
                amount_x = amount_x_desired
                amount_y = amount_y_optimal
                
                lp_minted = (amount_x/self.reserve_x)*self.lp_tokens
            
                self.lp_tokens = self.lp_tokens + lp_minted 
                self.reserve_x = self.reserve_x + amount_x
                self.reserve_y = self.reserve_y + amount_y
            
                if self.debug:
                    print(f"-"*10, f"AFTER LIQUIDITY INSERTED",f"-"*10)
                    print(f"Reserve X:{self.reserve_x}\n"+
                         f"Reserve Y:{self.reserve_y}\n" +
                         f"Total pool tokens :{self.lp_tokens}\n"+
                         f"amount_x = {amount_x}\n"+
                         f"amount_y = {amount_y}\n")

                return lp_minted
        
            else: 
                print("Insufficient Y Amount")
                print(f"amount_y_optimal < amount_y_min")
                print(f"amount_y_optimal =  {amount_y_optimal}")
                print(f"amount_y_min =  {amount_y_min}")

        else: 
            amount_x_optimal = amount_y_desired * (self.reserve_x / self.reserve_y)
            if amount_x_optimal <= amount_x_desired:
                if amount_x_optimal >= amount_x_min: 
                    amount_x = amount_x_optimal
                    amount_y = amount_y_desired
                    
                    lp_minted = (amount_x/self.reserve_x)*self.lp_tokens
            
                    self.lp_tokens = self.lp_tokens + lp_minted 
                    self.reserve_x = self.reserve_x + amount_x
                    self.reserve_y = self.reserve_y + amount_y

                    if self.debug:
                        print(f"-"*10, f"AFTER LIQUIDITY INSERTED",f"-"*10)
                        print(f"amount_x = ")
                        print(f"Reserve X:{self.reserve_x}\n"+
                             f"Reserve Y:{self.reserve_y}\n" +
                             f"Total pool tokens :{self.lp_tokens}\n"+
                             f"amount_x = {amount_x}\n"+
                             f"amount_y = {amount_y}\n")

                    return lp_minted
             
                else: 
                    print("Insufficient X Amount")
                    print(f"amount_x_optimal < amount_x_min")
                    print(f"amount_x_optimal =  {amount_x_optimal}")
                    print(f"amount_x_min =  {amount_x_min}")

         
        if self.debug:
            print(f"-"*10, f"PROVIDE LIQUIDITY ",f"-"*10)
            print(f"-"*10, f"PRIOR LIQUIDITY ",f"-"*10)
            print(f"Reserve X:{self.reserve_x}\n"+
                 f"Reserve Y:{self.reserve_y}\n" +
                 f"Total pool tokens :{self.lp_tokens}")
        
            
    def set_transaction_fee(self, transaction_fee):
        """
        sets the transaction fee of the uniswap institution to the specified amount
        """
        self.transaction_fee = transaction_fee
        
        

    

