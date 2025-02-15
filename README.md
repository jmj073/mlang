# 나랑 ChatGPT가 만든 프로그래밍 언어

## 문법

``` 
program         → statement*
statement       → assignment | if_stmt | while_stmt | expr_stmt
assignment      → IDENT "=" expression
if_stmt         → "if" expression ":" block ("else:" block)?
while_stmt      → "while" expression ":" block
expr_stmt       → expression
block           → NEWLINE INDENT statement+ DEDENT
expression      → term (("+" | "-") term)*
term            → factor (("*" | "/") factor)*
factor          → NUMBER | IDENT | "(" expression ")"
```
