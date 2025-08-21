import textwrap


def show_menu():
    """
    Displays the menu to the user and returns their choice.
    """
    menu = """\n
    ================ MENU ================
    [1]\tPerguntar
    [2]\tSair
    => """
    return input(textwrap.dedent(menu))
