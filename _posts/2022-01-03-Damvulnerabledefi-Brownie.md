---
layout: post
title:  Damn Vulnerable Defi Challenges in Brownie, a Python-based dev framework
excerpt_separator: <!--more-->
---

## Introduction

Hello, happy new year! In the last months of 2021, I've been working on this project. Thanks to my friend and college [Pablo Artuso](https://twitter.com/lmkalg) I started to learn about Blockchain and the challenges and opportunities that this new technology has.

I was quickly interested in how the security aspects of smart contracts. As part of my learning process I found [damn vulnerable
defi challenges](https://www.damnvulnerabledefi.xyz/), created by @tinchoabbate. that seemed a good place to start practicing.

<!--more-->

## Damn vulnerable Defi in Brownie

Besides learning about Smart Contract security I also wanted to learn about how to program smart contracts and the development tools that are already available. As I feel comfortable writing Python I quickly found [Brownie](https://github.com/eth-brownie/brownie) "A Python-based development and testing framework" for the Eterheum Virtual Machine".

Brownie has an excellent documentation and after a short time I could use the framework in a solid way without much trouble. My problem was that the challenges wrote by Martin are designed to be solved using other tools and Javascript as the main language. I decided that it could be a good idea to "port" those challenges to Brownie, so anyone has an alternative and can play with them knowning Python as well.

I created the [Damn Vulnerable Defi Brownie version](https://github.com/nahueldsanchez/dvd_brownie) for that purpose. It currently has challenges 1 to 4 and I plan to continue adding the rest in the near future.

I hope that you enjoy this small project and find it useful. All the credits and merit go to [Tincho](https://www.notonlyowner.com/) for the challenges and [Ben Hauser](https://github.com/iamdefinitelyahuman) for the Brownie project.