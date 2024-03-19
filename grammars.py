sys1Sys2 = '''root ::= choice
choice ::= "System1"|"System2"'''

list = '''root ::= item+

# Excludes various line break characters
item ::= "- " [^\r\n\x0b\x0c\x85\u2028\u2029]+ "\n"'''

yesNo = '''root ::= choice
choice ::= "Yes"|"No"'''

