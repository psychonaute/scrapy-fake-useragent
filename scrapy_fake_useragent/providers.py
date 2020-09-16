import logging
from abc import abstractmethod

import fake_useragent
from faker import Faker
from random_user_agent.user_agent import UserAgent
from random_user_agent.params import HardwareType, SoftwareType, SoftwareName, SoftwareEngine, OperatingSystem, Popularity


logger = logging.getLogger(__name__)


class BaseProvider:
    """
    Base class for providers.
    Doesn't provide much functionality for now,
    but it is a good placeholder for future additions.
    """

    def __init__(self, settings):
        self.settings = settings

        # Each provider should set their own type of UA
        self._ua_type = None

    @abstractmethod
    def get_random_ua(self):
        """
        Method needs to be implemented per provider based on BaseProvider.
        """


class FixedUserAgentProvider(BaseProvider):
    """Provides a fixed UA string, specified in Scrapy's settings.py"""

    def __init__(self, settings):
        BaseProvider.__init__(self, settings)

        fixed_ua = settings.get('USER_AGENT', '')

        # If the USER_AGENT setting is not set, the useragent will be empty
        self._ua = fixed_ua or ''

    def get_random_ua(self):
        return self._ua


class FakeUserAgentProvider(BaseProvider):
    """
    Provides a random, real-world set of UA strings,
    powered by the fake_useragent library.
    """

    DEFAULT_UA_TYPE = 'random'

    def __init__(self, settings):
        BaseProvider.__init__(self, settings)

        self._ua_type = settings.get('FAKE_USERAGENT_RANDOM_UA_TYPE',
                                     self.DEFAULT_UA_TYPE)

        fallback = settings.get('FAKEUSERAGENT_FALLBACK', None)
        self._ua = fake_useragent.UserAgent(fallback=fallback)

    def get_random_ua(self):
        """
        If the UA type attribute is not found,
        fake user agent provider falls back to fallback by default.
        No need to handle AttributeError.
        """
        return getattr(self._ua, self._ua_type)


class FakerProvider(BaseProvider):
    """
    Provides a random set of UA strings, powered by the Faker library.
    """

    DEFAULT_UA_TYPE = 'user_agent'

    def __init__(self, settings):
        BaseProvider.__init__(self, settings)

        self._ua = Faker()
        self._ua_type = settings.get('FAKER_RANDOM_UA_TYPE',
                                     self.DEFAULT_UA_TYPE)

    def get_random_ua(self):
        try:
            return getattr(self._ua, self._ua_type)()
        except AttributeError:
            logger.debug("Couldn't retrieve '%s' UA type. "
                         "Using default: '%s'",
                         self._ua_type, self.DEFAULT_UA_TYPE)
            return getattr(self._ua, self.DEFAULT_UA_TYPE)()


class RandomUserAgentProvider(BaseProvider):
    """
    Provides a random set of UA strings, powered by the Faker library.
    """

    DEFAULT_UA_TYPE = ''

    def __init__(self, settings):
        BaseProvider.__init__(self, settings)

        self._ua_type = settings.get('RANDOMUSERAGENT_RANDOM_UA_TYPE',
                                     self.DEFAULT_UA_TYPE)
        # mapping Enum class - init params equivalence
        CLASS_MAP = {
                'hardware_types': HardwareType,
                'software_types': SoftwareType,
                'software_names': SoftwareName,
                'software_engines': SoftwareEngine,
                'operating_systems': OperatingSystem,
                'popularity': Popularity,
            }

        # loop through our filters list to retrieve their init param's value
        params = {}
        for filter_cat, filter_value in self._ua_type.items():
            match = getattr(CLASS_MAP[filter_cat], filter_value.upper(), None)
            if match:
                params[filter_cat] = match.value
            else:
                logger.error("Error: Couldn't find a matching filter for '%s' ",filter_value ) 
                raise Exception("Could'nt find a matching filter for: '%s' ",filter_value ) 
        
        # build a list of 100 UA to randomly pick from
        self._ua = UserAgent(**params, limit=100)

    def get_random_ua(self):
        try:
            ua = self._ua.get_random_user_agent()
            nb_ua = len(self._ua.user_agents)
            if nb_ua < 100:
                logger.warning("Only '%s' UAs matched those criterions: '%s'. "
                            "Try using less restrictive ones",
                            nb_ua, " | ".join(self._ua_type))
            return ua
        except IndexError:
            logger.debug("Couldn't retrieve UA type matching those criterions: '%s'. ",
                         "Beware of conflicting ones like 'ANDROID | COMPUTER' "
                         "Using default: '%s'",
                         " | ".join(self._ua_type), self.DEFAULT_UA_TYPE)
            return getattr(self._ua, self.DEFAULT_UA_TYPE)()