from typing import List

LYRINGO_ASCII = r"""
$$\   $$\     $$\ $$$$$$$\  $$$$$$\ $$\   $$\  $$$$$$\   $$$$$$\  
$$ |  \$$\   $$  |$$  __$$\ \_$$  _|$$$\  $$ |$$  __$$\ $$  __$$\ 
$$ |   \$$\ $$  / $$ |  $$ |  $$ |  $$$$\ $$ |$$ /  \__|$$ /  $$ |
$$ |    \$$$$  /  $$$$$$$  |  $$ |  $$ $$\$$ |$$ |$$$$\ $$ |  $$ |
$$ |     \$$  /   $$  __$$<   $$ |  $$ \$$$$ |$$ |\_$$ |$$ |  $$ |
$$ |      $$ |    $$ |  $$ |  $$ |  $$ |\$$$ |$$ |  $$ |$$ |  $$ |
$$$$$$$$\ $$ |    $$ |  $$ |$$$$$$\ $$ | \$$ |\$$$$$$  | $$$$$$  |
\________|\__|    \__|  \__|\______|\__|  \__| \______/  \______/ 
"""

MAGIC_LEN: int = 66
BOX_HORIZONTAL: str = "+" + (MAGIC_LEN - 2) * "-" + "+"

def print_lyringo():
    print(LYRINGO_ASCII)

def pad_line(text: str, pad: int, length: int):
    text = text.strip()
    pre: str = "|" + " " * pad
    suf: str = (length - len(text) - 1 - len(pre)) * " " + "|"

    return pre + text + suf

def print_lines(n: int):
    for _ in range(n):
        print("|" + " " * (MAGIC_LEN - 2) + "|")

def needs_wrap(text: str | int, pad: int = 1) -> bool:
    return (len(text) if isinstance(text, str) else text) > (MAGIC_LEN - 2 - pad)

def wrap(text: str) -> List[str]:
    """
    Wraps the given line to fit inside the box
    """
    res = []

    words = text.split()

    line_len: int = 0
    line: str = ""
    for word in words:
        line_len += len(word) + 1
        if needs_wrap(line_len):
            res.append(line)
            line = ""
            line_len = 0
        line += word + " "

    res.append(line)
    return res

def print_in_box(text: str | List[str], side_pad: int = 1, ver_pad: int = 1):
    """
    Prints text inside a prespecified box with adjustable padding

    To print multiple lines, pass in a list of strings
    """

    def print_line(text: str):
        texts = [text]
        if needs_wrap(text):
            texts = wrap(text)
        
        for line in texts:
            print(pad_line(line, side_pad, MAGIC_LEN))

    # TOP LINE
    print(BOX_HORIZONTAL)
    print_lines(ver_pad)

    # Text
    if isinstance(text, str):
        print_line(text)
    else:
        for line in text:
            print_line(line)

    # BOTTOM LINE
    print_lines(ver_pad)
    print(BOX_HORIZONTAL)

def welcome():
    print_lyringo()
    welcome_text = [
        "Welcome to Lyringo!",
        "Learn new languages by translating your favourite songs."
    ]
    print_in_box(welcome_text)

    instructions_text = [
        "There are two alternatives for selecting a song:",
        "",
        "1 - Let Lyringo choose a random song from your playlist.",
        "2 - Manually search for a song."
    ]
    print_in_box(instructions_text)
  
if __name__ == "__main__":
    tip: str  = "2. Try to translate to your chosen language, press ENTER when you are done."

    print(wrap(tip))
    print_in_box(tip)

    # TODO, fix this case:
    s: str  = "j" * (MAGIC_LEN)
    print_in_box(s)