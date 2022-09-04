---
layout: post
title:  Ethernaut challenges writeup Part III (Challenges 13 to 16).
excerpt_separator: <!--more-->
category: DeFi
---

Hi There!. Let's continue reviewing my solutions for [Ethernaut](https://ethernaut.openzeppelin.com/). In today's post we'll review challenges 13 to 16.

<!--more-->

# Challenges write up

## Gatekeeper One

The main idea behind tis challenge is to be able to pass three checks performed in the code that act as "gates". This level was a real headcache as I knew the idea to solve it but was horribly missing the exact value to pass the sencond check.

The first gate it's pretty simple and the idea to pass it was explained in the [Telephone](https://nahueldsanchez.com.ar/Solving-Ethernaut-Challenges-01-07/) challenge. One way to pass this fist check is to create a contract that calls the contract implemented in the challenge and call this first contract. This way `tx.origin` (User Address) != `msg.sender` (contract #1 address). The second gate was the real headcache as when evaluated the remaining Gas value in the execution modulo 8191 should be 0. To properly calcute this I had to debug quite a few times the contract until I found the exact Gas value spent by the execution until that point (254 in my case). After calculating this I used the following horrible Python code to bruteforce a Gas value that will meet the condition required: 

```
// Python code to calculate Gas value to meet Gate Two condition:

for x in range(30000,50000):
    if((x-254) % 8191) == 0:
        print(x)
```

The last gate is easier and it requires to play with bitmasks and how Solidity trucantes values when casting variables. I developed the contract below to pass this level.

### Further Reading

- Units and Globally Available Variables - https://docs.soliditylang.org/en/v0.8.3/units-and-global-variables.html
- Convert address to bytes8 - https://ethereum.stackexchange.com/questions/83905/convert-address-to-bytes8

### Solution Code

```
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

interface IGatekeeperOne {
    function enter(bytes8 _gateKey) external returns (bool);
}

contract GatekeeperTwoAttacker {

    //using SafeMath for uint256;
    address victim;

    constructor(address _GatekeeperContract) {
        victim = _GatekeeperContract;
    }

    function attack() public {
        bytes8 _gateKey = bytes8(uint64(uint160(tx.origin))) & 0xFFFFFFFF0000FFFF;
        bytes memory payload = abi.encodeWithSignature("enter(bytes8)", _gateKey);
        (bool success, bytes memory returnData) = address(victim).call{gas: 49400}(payload);
        require(success);
    }

}

```

## Gatekeeper Two

1. First gate is the same idea than in the previous challenge.
2. Second gate was interesting, contract had to return a size of 0 when `extcodesize(addr)` was used. For that we had the hint to read `section 7` of the Ethereum yellow Paper. In the part that I copied below we find a very interesting behavior. If we use a SELFDESTRUCT instruction in the contract's constructor we'll be able to meet the condition required.

```
7.1. Subtleties.
Note that while the initialization code is executing, the newly created address exists but with no intrinsic body code. Thus any message call received by it during this time causes no code to be executed. If the initialization execution ends with a SELFDESTRUCT instruction, the matter is moot since the account will be deleted before the transaction is completed. For a normal STOP code, or if the code returned is otherwise empty, then the state is left with a zombie account, and any remaining balance will be locked into the account forever.
```
3. For the 3rd gate the key is to understand how the XOR operation works. If we simplify how the contract checks if `_gateKey` is correct we can say: `X ^ _gateKey` should be equal to `uint64(0) - 1`. This value `uint64(0) - 1` it's fixed and we can calculate it. I used a dummy contract that emitted an event with the result (that I knew it was 0xFFFFFFFFFFFFFFFF). Knowing this we can rewrite the expression to: `_gatekey == X ^ 0xFFFFFFFFFFFFFFFF`. The last task is to calculate X, and for that we can use the same expression that the challenge uses, but replace msg.sender for `this(address)` as we need to pass the address of our contract (which is in fact what the challenge will see when using `msg.sender`). Then `X = bytes8(uint64(bytes8(keccak256(abi.encodePacked(address(this)))))`

### Further Reading

- Solidity Assembly Reference - https://docs.soliditylang.org/en/v0.4.21/assembly.html
- Ethereum Beige Paper - https://cryptopapers.info/assets/pdf/eth_beige.pdf
- Ethereum Yellow Paper - https://ethereum.github.io/yellowpaper/paper.pdf
- ABI encode vs packedencode - https://forum.openzeppelin.com/t/abi-encode-vs-abi-encodepacked/2948/4

### Solution Code

```
// SPDX-License-Identifier: MIT
pragma solidity ^0.6.0;

interface IGatekeeerTwo {
    function enter(bytes8 _gateKey) external returns (bool);
}

contract GatekeeperTwoSol {

    address gatekeeperContract;

    constructor(address _gatekeeperContract) public {
        gatekeeperContract = _gatekeeperContract;
        bytes8 _gateKey = bytes8(uint64(bytes8(keccak256(abi.encodePacked(address(this))))) ^ uint64(0) - 1);
        IGatekeeerTwo(gatekeeperContract).enter(_gateKey);
        selfdestruct(payable(0x7EF2e0048f5bAeDe046f6BF797943daF4ED8CB47));
    }

}
```

## Naught Coin

This challenge was relatively easy for me, as I previously solved Damn Vulnerable DeFi Challenges and had an idea of the ERC20 standard. The idea to solve it is using the `transferFrom` method which in this case is not being modified by the `timelock`. The steps to win the challenge are:

1. First allow the spending of tokens, calling `contract.approve(player, web3.utils.toWei("1000000", "ether"))`.
2. Transfer the tokens using `contract.transferFrom(player, "<address>", web3.utils.toWei("1000000", "ether"))`.

As the challenge's solution explains, the main issue is that the developer who created this contract did not fully understand the code being used.

### Further Reading

- ERC20 Standard - https://github.com/ethereum/EIPs/blob/master/EIPS/eip-20.md

## Preservation

I loved this challenge. `delegatecall` it is a very powerful function but a dangerous one and can get messy very quickly. I learned about the big differences between [contracts and libraries](https://docs.soliditylang.org/en/v0.7.2/contracts.html#libraries). I also found some parallelism with being able to overwrite function pointers to call arbitrary functions and maybe because of that I quickly got the idea to solve this level.

The main idea in this challenge is to somehow we should be capable of modifying the `owner` of the instance we are given. I started to review the contract and decided to call function `setFirstTime` with a `uint` value of `0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF`. After that I decided to review the contract's storage:

```
await contract.setFirstTime(("0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF"))

await web3.eth.getStorageAt(instance,0)

'0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff'
```
And at that moment all what happened made sense. For me it was very useful to have fresh in my mind challenge #6 - Delegation. While looking at the value stored in `slot 0`. I assumed that the following happened:

1. When calling `setFirstTime`, the code for `setTime` is executed.
2. BUT THE STATE OF the Preservation contract is used. This means that the contract's `slot 0` is used. And this overwrites the value stored in `timeZone1Library`.
3. I corroborated this calling `setSecondTime` with a different value and checking again what was stored in Preservation contract's `slot 0`.

The next step was to think how to leverage this behavior. I decided to store in `timeZone1Library` the address of a malicious contract with a `setTime` function. This way once the Preservation contract calls `setTime` via the `delegatecall` will end up calling the malicious contract.

This malicious contract had defined three variables to had the same layout that the victim contract and in its `setTime` function changed the `owner` variable to my address, effectively changing Preservation's contract `owner` variable.

### Further Reading

- Libraries - https://docs.soliditylang.org/en/v0.7.2/contracts.html#libraries

### Solution code

```
// SPDX-License-Identifier: MIT
pragma solidity ^0.6.0;

contract Attacker {
    address public foo;
    address public bar;
    address public owner;

    function setTime(uint _time) public {
        owner = 0x922e34D7d34C70Df760DF873BC6F99a10dea516E;
  }
}
```

