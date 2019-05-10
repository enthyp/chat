import pytest
import chat.communication as irc


def test_IRCMessage_correct():
    msg = irc.Message(':nick JOINED channel1 channel2 :Wow, nick really joined ::channel1 and channel2!')
    assert msg.prefix == 'nick'
    assert msg.command == 'JOINED'
    assert msg.params == ['channel1', 'channel2', 'Wow, nick really joined ::channel1 and channel2!']


def test_IRCMessage_RPL_PWD():
    msg = irc.Message('RPL_PWD')
    assert msg.prefix == ''
    assert msg.command == 'RPL_PWD'
    assert msg.params == []


def test_IRCMessage_ERR_TAKEN():
    msg = irc.Message('ERR_TAKEN nick')
    assert msg.prefix == ''
    assert msg.command == 'ERR_TAKEN'
    assert msg.params == ['nick']


def test_IRCMessage_empty():
    with pytest.raises(irc.BadMessage) as e:
        irc.Message('')
    assert 'Empty string.' in str(e)


def test_IRCMessage_no_command():
    with pytest.raises(irc.BadMessage) as e:
        irc.Message(':prefix :bad_command param1 param2')
    assert 'No command.' in str(e)
