from utils.text_format import render_poll_bar


def test_render_poll_bar():
    bar = render_poll_bar(50, length=10)
    assert bar.count("█") == 5
    assert bar.count("░") == 5
