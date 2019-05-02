import pytest
import chat.irc as irc


# TODO: more of this?
def test_IRCMessage_correct():
    msg = irc.IRCMessage(':nick JOINED channel1 :Wow, nick really joined ::channel1!')
    assert msg.prefix == 'nick'
    assert msg.command == 'JOINED'
    assert msg.params == ['channel1', 'Wow, nick really joined ::channel1!']


def test_IRCMessage_incorrect():
    with pytest.raises(irc.IRCBadMessage) as e:
        irc.IRCMessage(':prefix :bad_command param1 param2')
    assert 'No command.' in str(e)
