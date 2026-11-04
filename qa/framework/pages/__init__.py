"""Page Object base classes and implementations for Web and Mobile."""

from qa.framework.pages.base_mobile_page import BaseMobilePage
from qa.framework.pages.base_page import BaseWebPage
from qa.framework.pages.mobile_chat_screen import MobileChatScreen
from qa.framework.pages.web_chat_page import WebChatPage

__all__ = ["BaseMobilePage", "BaseWebPage", "MobileChatScreen", "WebChatPage"]
