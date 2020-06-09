#### File Formats
_.tsf_ = tremor scene file  
_.lcr_ = lindenmayer configuration ruleset

#### File Format Specification
##### LCR Files
**Ruleset:**
 * define letters using `=` like `X=[expression]`
 * define axiom as `axiom=[expression]`
 * anything not symbolic is a variable defined by the user  
**Parameters:**
 * see main/lsystems/parser.py/LSystem