"""
List of constants which are useful in communications
"""

# Single character constant
STX = chr(2)
ETX = chr(3)
EOT = chr(4)
ENQ = chr(5)
ACK = chr(6)

# A dictionary of constants this is useful in e.g. "{STX} message{ETX}".format(**COMMAND_CHARS)
ASCII_CHARS = {
    "STX": STX,
    "ACK": ACK,
    "EOT": EOT,
    "ENQ": ENQ,
    "ETX": ETX}
