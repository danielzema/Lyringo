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
  pre: str = "|" + " " * pad
  suf: str = (length - len(text) - 1 - len(pre)) * " " + "|"

  return pre + text + suf

def print_lines(n: int):
  for _ in range(n):
    print("|" + " " * (MAGIC_LEN - 2) + "|")


def print_in_box(text: str, side_pad: int = 1, ver_pad: int = 1):
  """
  # Print
  Prints ***text*** in a box
  """
  print(BOX_HORIZONTAL)
  print_lines(ver_pad)
  print(pad_line(text, side_pad, MAGIC_LEN))
  print_lines(ver_pad)
  print(BOX_HORIZONTAL)

if __name__ == "__main__":
  pass