---
layout: post
title:  Solving Damn Vulnerable DeFi Challenges Series (VII). Free Rider.
excerpt_separator: <!--more-->
category: DeFi
---

Hello! I wanted to continue the habit of publishing regularly. Today's posts continues our saga solving and porting Damn Vulnerable DeFi challenges. During the last week I spent some time solving challenge #10 - Free Rider. I really liked it as it challenged me learning about the following topics:

- Flash swaps in Uniswap!
- NFT and the EIP-721 standard
- Common pitfalls when using `loops` and `msg.value`

I've ported this challenge to Brownie, you can find it [here](https://github.com/nahueldsanchez/dvd_brownie/tree/master/free-rider)

Let's dive into it!.

<!--more-->

# Free Rider challenge writeup

## Quick introduction

This level starts with the following statement:

```
A new marketplace of Damn Valuable NFTs has been released! There's been an initial mint of 6 NFTs, which are available for sale in the marketplace. Each one at 15 ETH.

A buyer has shared with you a secret alpha: the marketplace is vulnerable and all tokens can be taken. Yet the buyer doesn't know how to do it. So it's offering a payout of 45 ETH for whoever is willing to take the NFTs out and send them their way.

You want to build some rep with this buyer, so you've agreed with the plan.

Sadly you only have 0.5 ETH in balance. If only there was a place where you could get free ETH, at least for an instant.
```

The challenge is clear, we need to steal all the NFTs from a marketplace that has some kind of exploitable bug. Based on this idea I started digging into the contracts:

- [Marketplace selling the NFTs](https://raw.githubusercontent.com/tinchoabbate/damn-vulnerable-defi/v2.2.0/contracts/free-rider/FreeRiderNFTMarketplace.sol)

There is another contract that implements the buyer who wants the NFTs, but that's not important for now.

After taking a look at the contract and focusing mainly in the `buyMany` function that allows a user to buy several NFTs passing as argument and array of IDs, see below:

```
function buyMany(uint256[] calldata tokenIds) external payable nonReentrant {
    for (uint256 i = 0; i < tokenIds.length; i++) {
        _buyOne(tokenIds[i]);
    }
}
```

This function has the following interesting properties:

- Has the `nonReentrant` modifier, which makes it safe against any common reentrancy attack.
- It's `payable`, allowing the user to send the amount of Ether required to buy the NFTs.
- It has a `loop` (This will be a key point later)

The function simply loops over the array of NFTs IDs and for each one calls the helper function `_buyOne`:

```
function _buyOne(uint256 tokenId) private {       
    uint256 priceToPay = offers[tokenId];
    require(priceToPay > 0, "Token is not being offered");

    require(msg.value >= priceToPay, "Amount paid is not enough");

    amountOfOffers--;

    // transfer from seller to buyer
    token.safeTransferFrom(token.ownerOf(tokenId), msg.sender, tokenId);

    // pay seller
    payable(token.ownerOf(tokenId)).sendValue(priceToPay);

    emit NFTBought(msg.sender, tokenId, priceToPay);
}    
```

This function does a few sanity checks first, checking that the ID for the NFT is listed to sell and that `msg.value` (the Ether sent by the user to pay) is higher than the NFT value.

## The vulnerability

Looking at the code of this two functions we can spot a critical security issue. *The internal function `_buyOne` is reusing `msg.value` multiple times via the loop of the external function `buyMany`*.  This at first sight can be a little tricky to spot because the use of multiple functions, but the effect is the same.

This type of vulnerability was found previously in big projects:

- [Opyn Hacks: Root Cause Analysis](https://peckshield.medium.com/opyn-hacks-root-cause-analysis-c65f3fe249db)
- [Detecting MISO and Opyn’s msg.value reuse vulnerability with Slither](https://blog.trailofbits.com/2021/12/16/detecting-miso-and-opyns-msg-value-reuse-vulnerability-with-slither/)

The problem is that the same `msg.value` is used multiple times to buy different things. I think that the idea from the developer side is that `msg.value` is automatically decremented each time is used, but that's not the case.

Exploiting this bug an attacker spending only `15 Ether` could buy all the NFTs, as all of them cost the same. The issue is that we only have `0.5 Ether` available... but what about this hint:

```
...
If only there was a place where you could get free ETH, at least for an instant.
```

Also if we look at the deployment script we can see that Uniswap V2 is being deployed. Let's discuss about Uniswap and its Flash Swaps!

## Uniswap V2 Flash swaps

### Brief Introduction

According to Uniswap's documentation, flash swaps allow you to: "...withdraw up to the full reserves of any ERC20 token on Uniswap and execute arbitrary logic at no upfront cost, provided that by the end of the transaction you either:

- pay for the withdrawn ERC20 tokens with the corresponding pair tokens
- return the withdrawn ERC20 tokens along with a small fee

Flash swaps are incredibly useful because they obviate upfront capital requirements and unnecessary order-of-operations constraints for multi-step transactions involving Uniswap."

And based on that use cases this is what we need!. In our scenario we will perform a flash swap and borrow the Ether needed to buy the NFTs.

### Triggering a Flash Swap

I was a bit afraid as I thought that this step could be very complicated to achieve. Luckily there are excellent resources on how to perform this. I found the following to be super useful for me:

- [Smart Contract Programmer's YT channel - Uniswap V2 - Flash Swap DeFi](https://www.youtube.com/watch?v=MxTgk-kvtRM)
- [Learn to execute Flash Swaps ⚡on Uniswap by yourself](https://dev.to/uv-labs/executing-flash-swaps-on-uniswap-6ch)
- [Uniswap Documentation](https://docs.uniswap.org/protocol/V2/guides/smart-contract-integration/using-flash-swaps)

I'll try to summarize the issues I had and what I've learned.

Basically speaking, and according to all what I read, a Flash Swap is performed almost in the same way that a normal swap is done but including an extra parameter. Well... at least in theory. When I started looking at the code I found that, normally when executing swaps in Uniswap V2 the most common way to perform them is using any of the functions provided by the [Uniswap's Router](https://github.com/Uniswap/v2-periphery/blob/master/contracts/UniswapV2Router02.sol), such as:

- swapTokensForExactTokens
- swapTokensForExactETH
- And so on...

When I looked at flash swap's documentation it referred to a `swap` function that I didn't find. That's because at the end, the functions that I listed before are wrappers which provide additional controls and security measures but ultimately interact with Uniswap's pairs that actually perform the swaps. To perform a swap, the router ends up calling a function called [`_swap`](https://github.com/Uniswap/v2-periphery/blob/master/contracts/UniswapV2Router02.sol#L212), that at [line 219](https://github.com/Uniswap/v2-periphery/blob/master/contracts/UniswapV2Router02.sol#L219) calls pair's function [`swap`](https://github.com/Uniswap/v2-core/blob/master/contracts/UniswapV2Pair.sol#L158).

The only difference between a traditional swap and a flash swap relies on the last parameter passed to the swap function. Let's review the function's signature:

```
function swap(uint amount0Out, uint amount1Out, address to, bytes calldata data) external lock
```

For a traditional swap, parameter `data` is `bytes(0)`. In comparison, [according to the documentation](https://docs.uniswap.org/protocol/V2/guides/smart-contract-integration/using-flash-swaps) if we pass any other value in the `data` parameter Uniswap will understand that we are executing a flash swap.

As we need to perform different actions when we receive the loaned amount (including paying the loan and a small fee) Uniswap will call an specific function in our contract: 

```
function uniswapV2Call(address sender, uint amount0, uint amount1, bytes calldata data)
```

In our case this function will not only repay the debt but also trigger the NFTs buying process. We'll see this better in the following sections.

## ERC721 - onERC721Received

The last piece of information that we need to know about it's the `onERC721Received` function. This function is part of the [EIP-721: EIP-721: Non-Fungible Token Standard](https://eips.ethereum.org/EIPS/eip-721). It allows for the execution of code once an NFT has been received. The sender calls this function on the recipient, between other things to be sure that the recipient can handle the reception of the NFT.

This means that our contract will need to implement this function to be able to receive the NFTs once we buy them. Otherwise the transaction will revert.

The function has the following parameters:

```
/// @param _operator The address which called `safeTransferFrom` function
/// @param _from The address which previously owned the token
/// @param _tokenId The NFT identifier which is being transferred
/// @param _data Additional data with no specified format
/// @return `bytes4(keccak256("onERC721Received(address,address,uint256,bytes)"))`
///  unless throwing
```

In our case the most important thing to bear in mind is what we have to return, namely:

```
bytes4(keccak256("onERC721Received(address,address,uint256,bytes)"))
```

Implementing this function, our contract will be able to receive the NFTs. If we look at the [FreeRiderBuyer.sol contract](https://github.com/tinchoabbate/damn-vulnerable-defi/blob/v2.2.0/contracts/free-rider/FreeRiderBuyer.sol), that's in charge of receive the NFTs once we steal them and pay us our reward, we can see that it also implements this function.

## The Exploit

Now that we have all the information, let's see how to exploit this level!. The steps that we'll perform are:

1. Ask Uniswap for a flash swap of 15 ETH to buy the NFTs.
2. Once we receive the Ether, function `uniswapV2Call` will be called in our contract.
3. Inside function `uniswapV2Call` we'll call function `buyMany` from the NFT marketplace.
4. When calling `buyMany` we'll exploit the vulnerability that we have discovered. We'll send `15 Ether` and pass an array with the IDs of all the NFTs we want to buy. The vulnerable contract will reuse the same `15 Ether` and allow us to buy all NFTs.
5. Once we receive each NFT, this will trigger the execution of function `onERC721Received`. In my case I've decided to separate the process and craft another function to transfer the NFTs to the buyer. In this case, I only need to return `IERC721Receiver.onERC721Received.selector`.
6. After having the NFTs under our control, I'll transfer back to the `Buyer Contract`.
7. Once I performed all steps I'll withdraw the balance from the `Attacker Contract` back to the `Attacker` account to pass the challenge.

### Exploit Code review

I implemented the steps described above in the following [contract](https://github.com/nahueldsanchez/dvd_brownie/blob/master/free-rider/contracts/AttackerContract.sol). Let's quickly review how it works:

The attack starts calling `attack()` function. This function triggers the flash swap of `15 ETH`. The most interesting part of this is that the `_flashSwap()` functions interacts with the DVT/WETH pair:

```
...
bytes memory data = abi.encode(weth, _weth_amount);
IUniswapV2Pair(dvt_weth_pair).swap(
    amount0Out,
    amount1Out,
    address(this),
    data
);
...
```
The code above is the one triggering the flash swap as the `data` parameter is non-zero. Once we receive the funds the `uniswapV2Call` function kicks in, and during this function the vulnerability is exploited:

```
...
IWETH(weth).withdraw(amount);
IFreeRiderNFTMarketplace(marketplace).buyMany{value: 15 ether}(ids);
IERC721(nft).setApprovalForAll(ATTACKER, true);

uint256 fee = ((amount * 3) / 997) + 1;
uint256 amountToRepay = amount + fee;
IWETH(weth).deposit{value: amountToRepay}();
IWETH(tokenBorrow).transfer(pair, amountToRepay);
...
```

We basically convert the `WETH` obtained back to `ETH`, call `buyMany` passing only `15 ETH`, give control over all NFTs to the attacker account, and return the borrowed `WETH` plus a small fee.

Once the attack finishes, we can use `function transferNFTs()` to transfer NFTs back to the buyer and `withdraw` to take the funds out of the contract back to the attacker account.

## Conclusions

This challenge implements a bug that was found in at least two big projects, [this one](https://samczsun.com/two-rights-might-make-a-wrong/) and this [other one](https://peckshield.medium.com/opyn-hacks-root-cause-analysis-c65f3fe249db). Using `msg.value` inside a loop it is always dangerous and it raise a red flag in the auditor's head.

I hope that you have enjoyed the blog post. Remember that you can play around with this level in the [port for Brownie that I created](https://github.com/nahueldsanchez/dvd_brownie/tree/master/free-rider) See you soon!

## Sources

- [EIP-721](https://eips.ethereum.org/EIPS/eip-721) - https://eips.ethereum.org/EIPS/eip-721
- [Uniswap testing](https://medium.com/uv-labs/uniswap-testing-1d88ca523bf0)- https://medium.com/uv-labs/uniswap-testing-1d88ca523bf0
- [Learn to execute Flash Swaps on Uniswap by yourself](https://dev.to/uv-labs/executing-flash-swaps-on-uniswap-6ch) - https://dev.to/uv-labs/executing-flash-swaps-on-uniswap-6ch
- [Uniswap V2 - Flash Swap | DeFi](https://www.youtube.com/watch?v=MxTgk-kvtRM) - https://www.youtube.com/watch?v=MxTgk-kvtRM
- [Uniswap docs](https://docs.uniswap.org/protocol/V2/guides/smart-contract-integration/using-flash-swaps) - https://docs.uniswap.org/protocol/V2/guides/smart-contract-integration/using-flash-swaps
- [Uniswap Flash Swaps](https://docs.uniswap.org/protocol/V2/guides/smart-contract-integration/using-flash-swaps) - https://docs.uniswap.org/protocol/V2/guides/smart-contract-integration/using-flash-swaps
- [Uniswap Example Flash Swap](https://github.com/Uniswap/v2-periphery/blob/master/contracts/examples/ExampleFlashSwap.sol) - https://github.com/Uniswap/v2-periphery/blob/master/contracts/examples/ExampleFlashSwap.sol
- [ERC721](https://docs.openzeppelin.com/contracts/2.x/api/token/erc721#IERC721Receiver-onERC721Received-address-address-uint256-bytes-) - https://docs.openzeppelin.com/contracts/2.x/api/token/erc721#IERC721Receiver-onERC721Received-address-address-uint256-bytes-