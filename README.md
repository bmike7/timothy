# Timothy

A ~~Dumbo~~ PostgreSQL guardian

The name is inspired by Dumbo's [Timothy](https://disney.fandom.com/wiki/Timothy_Q._Mouse):

> Timothy is a stowaway of a traveling circus, where he becomes
  the self-appointed guardian and mentor of Dumbo.


## Prerequisites

Install:

- `libql` which includes `pg_dump` & `psql`.
- `uv tool install poethepoet`


## 💾 Installation

You can add this library to your Python project. For example when
using `uv`:

```
$ uv add "timothy @ git+https://github.com/bmike7/timothy.git"
```


## 💅 Motivation

When working with PostgreSQL databases, one needs to perform
administrative tasks. As a DB admin, you need to have a solid
backup strategy in place.
However, when you start working on an existing DB which grew over
time and wasn't maintained properly, then you can end up with a
DB that is in a corrupted state. A straightforward `pg_dump` won't
work any longer due to something like `ERROR: invalid page in block 9698 of relation ...`
for example.

> 💡 Explanation
>
> The DB might have ended up in this state if someone's strategy
> in the past has been to make OS snapshots. If at that point a
> DB transaction was running, then it won't be valid anymore.
>
> As a mental image, you can compare this to pulling out a USB from
> a computer while copying files. You can't expect those files
> were copied to the USB successfully.


Before even trying to resolve this corrupt state, you want to have
a backup in case you screw something up.

**😵‍💫 At that point you might feel lost because you failed at making a
backup**.


🚀 Luckily, there is a way to clone such corrupt DB, but it involves
some more steps. That is what this library automates.
